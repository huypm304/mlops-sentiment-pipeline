"""Predict Lambda — API Gateway proxy for ABSA inference."""

from __future__ import annotations

import json
import os
import time
from typing import Any

from registry.store import RegistryStore

_ENDPOINT = os.getenv("SAGEMAKER_ENDPOINT_NAME", "").strip()
_ENABLE_SAGEMAKER = os.getenv("ENABLE_SAGEMAKER_ENDPOINT", "false").lower() == "true"
_BUCKET = os.getenv("ARTIFACTS_BUCKET", "")
_DEFAULT_MODEL_VERSION = os.getenv("PRODUCTION_MODEL_ID", "absa-v1").strip() or "absa-v1"
_store: RegistryStore | None = None
_sagemaker_client: Any | None = None


def _get_store() -> RegistryStore:
    global _store
    if _store is None:
        _store = RegistryStore()
    return _store


def _get_sagemaker_client() -> Any:
    global _sagemaker_client
    if _sagemaker_client is None:
        import boto3

        _sagemaker_client = boto3.client("sagemaker-runtime")
    return _sagemaker_client


def _response(status: int, body: dict[str, Any]) -> dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(body, ensure_ascii=False),
    }


def _parse_body(event: dict[str, Any]) -> dict[str, Any]:
    raw = event.get("body") or "{}"
    if event.get("isBase64Encoded"):
        import base64

        raw = base64.b64decode(raw).decode("utf-8")
    return json.loads(raw) if isinstance(raw, str) else raw


def _sentiment_label(value: str) -> str:
    normalized = str(value or "NEU").upper()
    mapping = {"NEG": "negative", "POS": "positive", "NEU": "neutral"}
    return mapping.get(normalized, normalized.lower())


def _stub_result(*, latency_ms: int, model_version: str) -> dict[str, Any]:
    return {
        "opinions": [],
        "global_sentiment": "neutral",
        "global_confidence": 0.0,
        "latency_ms": latency_ms,
        "model_version": model_version,
        "note": "SageMaker endpoint disabled — enable enable_sagemaker_endpoint and upload model.tar.gz.",
    }


def _normalize_api_result(raw: dict[str, Any]) -> dict[str, Any]:
    opinions = []
    for opinion in raw.get("opinions") or []:
        if not isinstance(opinion, dict):
            continue
        opinions.append(
            {
                "target": opinion.get("target", ""),
                "aspect": opinion.get("aspect", ""),
                "sentiment": opinion.get("sentiment", "NEU"),
                "confidence": float(opinion.get("calibrated_confidence", opinion.get("confidence", 0.0))),
                "raw_confidence": float(opinion.get("raw_confidence", opinion.get("confidence", 0.0))),
                "calibrated_confidence": float(
                    opinion.get("calibrated_confidence", opinion.get("confidence", 0.0))
                ),
                "start": opinion.get("start"),
                "end": opinion.get("end"),
            }
        )

    return {
        "opinions": opinions,
        "global_sentiment": raw.get("global_sentiment", "NEU"),
        "global_confidence": float(raw.get("global_confidence", 0.0)),
        "global_raw_confidence": float(raw.get("global_raw_confidence", raw.get("global_confidence", 0.0))),
        "model_version": raw.get("model_version") or _DEFAULT_MODEL_VERSION,
        "latency_ms": int(raw.get("latency_ms") or 0),
        "need_review": bool(raw.get("need_review", False)),
        "guardrail_status": raw.get("guardrail_status", "PASS"),
    }


def _invoke_sagemaker(text: str) -> dict[str, Any]:
    if not _ENDPOINT:
        raise RuntimeError("SAGEMAKER_ENDPOINT_NAME is not configured")

    client = _get_sagemaker_client()
    started = time.time()
    response = client.invoke_endpoint(
        EndpointName=_ENDPOINT,
        ContentType="application/json",
        Accept="application/json",
        Body=json.dumps({"text": text}, ensure_ascii=False).encode("utf-8"),
    )
    payload = json.loads(response["Body"].read().decode("utf-8"))
    if not isinstance(payload, dict):
        raise RuntimeError("SageMaker returned a non-object JSON payload")

    if "latency_ms" not in payload:
        payload["latency_ms"] = int((time.time() - started) * 1000)
    return payload


def _run_inference(text: str) -> dict[str, Any]:
    started = time.time()
    if _ENABLE_SAGEMAKER and _ENDPOINT:
        raw = _invoke_sagemaker(text)
        return _normalize_api_result(raw)

    latency_ms = int((time.time() - started) * 1000)
    return _stub_result(latency_ms=latency_ms, model_version=_DEFAULT_MODEL_VERSION)


def _record_prediction(
    *,
    text: str,
    global_sentiment: str,
    global_confidence: float,
    latency_ms: int,
    model_version: str,
    opinions: list[dict[str, Any]],
) -> None:
    store = _get_store()
    if not store.config.predictions_table:
        return

    preview = text.strip()
    if len(preview) > 200:
        preview = preview[:197] + "..."

    guardrail_status = "OK"
    need_review = False
    if global_confidence < 0.32 or not opinions:
        guardrail_status = "WARN"
        need_review = True

    prediction = store.put_prediction(
        {
            "model_id": model_version,
            "model_version": model_version,
            "text_preview": preview,
            "global_sentiment": _sentiment_label(global_sentiment),
            "confidence": round(global_confidence, 4),
            "guardrail_status": guardrail_status,
            "need_review": need_review,
            "latency_ms": latency_ms,
            "aspects": [str(o.get("aspect", "")) for o in opinions if o.get("aspect")],
        }
    )

    if need_review and store.config.review_queue_table:
        store.put_review_item(
            {
                "prediction_id": prediction["prediction_id"],
                "model_id": model_version,
                "text_preview": preview,
                "global_sentiment": _sentiment_label(global_sentiment),
                "confidence": round(global_confidence, 4),
                "guardrail_status": guardrail_status,
                "priority": "urgent" if global_confidence < 0.18 else "normal",
            }
        )


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    route = event.get("rawPath") or event.get("path", "")

    if route.endswith("/health") or event.get("requestContext", {}).get("http", {}).get("path", "").endswith("/health"):
        mode = "sagemaker" if _ENABLE_SAGEMAKER and _ENDPOINT else "local_stub"
        return _response(
            200,
            {
                "status": "ok",
                "model": mode,
                "endpoint": _ENDPOINT or None,
                "bucket": _BUCKET or None,
                "sagemaker_enabled": _ENABLE_SAGEMAKER,
            },
        )

    try:
        payload = _parse_body(event)
        text = (payload.get("text") or "").strip()
        if not text:
            return _response(400, {"detail": "text is required"})

        result = _run_inference(text)
        _record_prediction(
            text=text,
            global_sentiment=str(result.get("global_sentiment", "NEU")),
            global_confidence=float(result.get("global_confidence", 0.0)),
            latency_ms=int(result.get("latency_ms", 0)),
            model_version=str(result.get("model_version", _DEFAULT_MODEL_VERSION)),
            opinions=list(result.get("opinions") or []),
        )
        return _response(200, result)
    except json.JSONDecodeError:
        return _response(400, {"detail": "invalid JSON body"})
    except RuntimeError as exc:
        return _response(503, {"detail": str(exc)})
    except Exception as exc:  # noqa: BLE001
        return _response(500, {"detail": str(exc)})
