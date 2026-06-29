"""Training-run artifact helpers — S3 copy, metric extraction, baseline lookup."""

from __future__ import annotations

from typing import Any

from botocore.exceptions import ClientError

from registry.model_artifacts import (
    _best_train_row,
    _parse_train_log,
    _scores_from_row,
    load_artifacts_from_prefix,
    metrics_summary_from_train_log,
    resolve_artifact_prefixes,
)

RUN_ARTIFACT_NAMES = (
    "train_log.csv",
    "run_config.json",
    "confusion_matrices.jsonl",
    "best_confusion_matrices.json",
    "best_model.pt",
)

DEFAULT_PRODUCTION_PREFIX = "models/v1"


def normalize_pipeline_metrics(raw: dict[str, float]) -> dict[str, float]:
    """Unify registry vs train_log metric key names for compare/deploy."""
    tas = float(raw.get("tas_relaxed_f1") or raw.get("tas_f1") or 0)
    sent = float(raw.get("sent_matched_f1") or raw.get("sentiment_f1") or 0)
    return {
        "tas_relaxed_f1": tas,
        "tas_f1": tas,
        "span_f1": float(raw.get("span_f1") or 0),
        "sent_matched_f1": sent,
        "sentiment_f1": sent,
        "global_f1": float(raw.get("global_f1") or 0),
    }


def metrics_from_train_log_text(train_log_text: str) -> dict[str, float]:
    rows = _parse_train_log(train_log_text)
    best = _best_train_row(rows)
    if not best:
        return {}
    detailed = _scores_from_row(best)
    summary = metrics_summary_from_train_log(train_log_text)
    merged = {**summary, **detailed}
    return normalize_pipeline_metrics(merged)


def _s3_get_text(s3_client: Any, bucket: str, key: str) -> str | None:
    try:
        resp = s3_client.get_object(Bucket=bucket, Key=key)
        return resp["Body"].read().decode("utf-8")
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in {"NoSuchKey", "404", "NotFound"}:
            return None
        raise


def _parse_s3_uri(uri: str) -> tuple[str, str]:
    if not uri.startswith("s3://"):
        raise ValueError(f"Invalid S3 URI: {uri}")
    without_scheme = uri[5:]
    bucket, _, key = without_scheme.partition("/")
    if not bucket or not key:
        raise ValueError(f"Invalid S3 URI: {uri}")
    return bucket, key


def sync_sagemaker_model_tar(
    s3_client: Any,
    artifact_s3_uri: str,
    dest_bucket: str,
    dest_prefix: str,
) -> list[str]:
    """Extract SageMaker model.tar.gz into training-runs/{run_id}/ for evaluate/deploy."""
    import io
    import tarfile

    bucket, key = _parse_s3_uri(artifact_s3_uri)
    resp = s3_client.get_object(Bucket=bucket, Key=key)
    body = resp["Body"].read()
    uploaded: list[str] = []
    dest = dest_prefix.strip("/")
    with tarfile.open(fileobj=io.BytesIO(body), mode="r:gz") as archive:
        for member in archive.getmembers():
            if not member.isfile():
                continue
            payload = archive.extractfile(member)
            if payload is None:
                continue
            dest_key = f"{dest}/{member.name}"
            s3_client.put_object(Bucket=dest_bucket, Key=dest_key, Body=payload.read())
            uploaded.append(dest_key)
    return uploaded


def copy_run_artifacts(
    s3_client: Any,
    bucket: str,
    *,
    source_prefix: str,
    dest_prefix: str,
    filenames: tuple[str, ...] = RUN_ARTIFACT_NAMES,
) -> list[str]:
    """Server-side S3 copy for training outputs (no Lambda download)."""
    src = source_prefix.strip("/")
    dst = dest_prefix.strip("/")
    copied: list[str] = []
    for name in filenames:
        src_key = f"{src}/{name}"
        dst_key = f"{dst}/{name}"
        try:
            s3_client.head_object(Bucket=bucket, Key=src_key)
        except ClientError:
            continue
        s3_client.copy_object(
            CopySource={"Bucket": bucket, "Key": src_key},
            Bucket=bucket,
            Key=dst_key,
        )
        copied.append(dst_key)
    return copied


def load_run_metrics(
    s3_client: Any,
    bucket: str,
    run_prefix: str,
) -> dict[str, float]:
    prefix = run_prefix.strip("/")
    train_log, _, _ = load_artifacts_from_prefix(s3_client, bucket, prefix)
    if not train_log:
        train_log = _s3_get_text(s3_client, bucket, f"{prefix}/train_log.csv")
    if not train_log:
        return {}
    return metrics_from_train_log_text(train_log)


def load_production_baseline_metrics(
    store: Any,
    base_model_id: str,
) -> tuple[dict[str, float], str, str]:
    """Return (metrics, model_id, artifact_prefix) for the production baseline."""
    bucket = store.config.artifacts_bucket
    production = store.get_production_model()
    if production and production.get("metrics"):
        prefix = str(production.get("artifact_prefix") or DEFAULT_PRODUCTION_PREFIX).strip("/")
        return (
            normalize_pipeline_metrics(production["metrics"]),
            str(production.get("model_id", base_model_id)),
            prefix,
        )

    if bucket:
        for prefix in resolve_artifact_prefixes(base_model_id):
            train_log, _, _ = load_artifacts_from_prefix(store._s3, bucket, prefix)
            if train_log:
                return (
                    metrics_from_train_log_text(train_log),
                    base_model_id,
                    prefix.strip("/"),
                )

    return (
        normalize_pipeline_metrics(
            {"tas_f1": 0.72, "span_f1": 0.68, "sentiment_f1": 0.75, "global_f1": 0.73}
        ),
        base_model_id,
        DEFAULT_PRODUCTION_PREFIX,
    )


def build_evaluation_report(
    *,
    run_id: str,
    candidate_model_id: str,
    metrics: dict[str, float],
    mode: str,
    passed: bool,
    message: str = "",
) -> dict[str, Any]:
    return {
        "run_id": run_id,
        "candidate_model_id": candidate_model_id,
        "metrics": metrics,
        "passed": passed,
        "mode": mode,
        "primary_metric": "tas_relaxed_f1",
        "best_f1": metrics.get("tas_relaxed_f1") or metrics.get("global_f1"),
        "message": message,
    }


def _resolve_comparison_primary_metric(
    production_metrics: dict[str, float],
    candidate_metrics: dict[str, float],
    preferred: str = "tas_relaxed_f1",
) -> str:
    """Pick a metric both sides can be scored on (legacy train_log may lack tas_relaxed_f1)."""
    if float(production_metrics.get(preferred, 0)) > 0 or float(candidate_metrics.get(preferred, 0)) > 0:
        return preferred
    for fallback in ("global_f1", "tas_f1", "span_f1", "sent_matched_f1"):
        if float(production_metrics.get(fallback, 0)) > 0 or float(candidate_metrics.get(fallback, 0)) > 0:
            return fallback
    return preferred


def align_mock_candidate_metrics(
    candidate_metrics: dict[str, float],
    production_metrics: dict[str, float],
) -> dict[str, float]:
    """Mock train copies baseline artifacts — reuse registry scores when S3 parse is empty."""
    if float(candidate_metrics.get("tas_relaxed_f1", 0)) > 0:
        return candidate_metrics
    if float(production_metrics.get("tas_relaxed_f1", 0)) <= 0:
        return candidate_metrics
    merged = dict(production_metrics)
    merged.update({key: value for key, value in candidate_metrics.items() if float(value) > 0})
    return normalize_pipeline_metrics(merged)


def build_comparison_report(
    *,
    baseline_model_id: str,
    candidate_model_id: str,
    production_metrics: dict[str, float],
    candidate_metrics: dict[str, float],
    primary_metric: str = "tas_relaxed_f1",
) -> dict[str, Any]:
    keys = ("tas_relaxed_f1", "tas_f1", "span_f1", "sent_matched_f1", "global_f1")
    effective_primary = _resolve_comparison_primary_metric(
        production_metrics, candidate_metrics, primary_metric
    )
    delta = {
        key: round(candidate_metrics.get(key, 0) - production_metrics.get(key, 0), 4)
        for key in keys
    }
    baseline_value = float(production_metrics.get(effective_primary, 0))
    candidate_value = float(candidate_metrics.get(effective_primary, 0))
    metric_gate_passed = candidate_value >= baseline_value
    return {
        "baseline_model_id": baseline_model_id,
        "candidate_model_id": candidate_model_id,
        "production_baseline": production_metrics,
        "candidate_metrics": candidate_metrics,
        "delta": delta,
        "primary_metric": effective_primary,
        "metric_gate_passed": metric_gate_passed,
        "cost_gate_passed": True,
        "promote": metric_gate_passed,
    }
