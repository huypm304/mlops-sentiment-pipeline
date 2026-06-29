"""DynamoDB registry operations for all MLOps lifecycle tables."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import boto3
from boto3.dynamodb.conditions import Attr, Key

from registry.config import RegistryConfig, load_config
from registry.convert import from_dynamo, to_dynamo


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


class RegistryStore:
    def __init__(self, config: RegistryConfig | None = None) -> None:
        self.config = config or load_config()
        self._resource = boto3.resource("dynamodb", region_name=self.config.aws_region)
        self._s3 = boto3.client("s3", region_name=self.config.aws_region)

    def _table(self, name: str):
        if not name:
            raise RuntimeError("DynamoDB table name is not configured")
        return self._resource.Table(name)

    @staticmethod
    def _item(record: dict[str, Any]) -> dict[str, Any]:
        return to_dynamo(record)

    @staticmethod
    def _records(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [from_dynamo(item) for item in items]

    # ------------------------------------------------------------------
    # datasets
    # ------------------------------------------------------------------

    def put_dataset(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        item.setdefault("created_at", now_iso())
        item.setdefault("updated_at", item["created_at"])
        self._table(self.config.datasets_table).put_item(Item=self._item(item))
        return from_dynamo(item)

    def get_dataset(self, dataset_id: str) -> dict[str, Any] | None:
        resp = self._table(self.config.datasets_table).query(
            KeyConditionExpression=Key("dataset_id").eq(dataset_id),
            ScanIndexForward=False,
            Limit=1,
        )
        items = resp.get("Items") or []
        return from_dynamo(items[0]) if items else None

    def update_dataset(self, dataset_id: str, created_at: str, updates: dict[str, Any]) -> None:
        reserved = {"dataset_id", "created_at", "updated_at"}
        expr_names: dict[str, str] = {"#updated_at": "updated_at"}
        expr_values: dict[str, Any] = {":updated_at": now_iso()}
        parts = ["#updated_at = :updated_at"]
        idx = 0
        for key, value in updates.items():
            if key in reserved:
                continue
            name_key = f"#k{idx}"
            value_key = f":v{idx}"
            expr_names[name_key] = key
            expr_values[value_key] = value
            parts.append(f"{name_key} = {value_key}")
            idx += 1
        self._table(self.config.datasets_table).update_item(
            Key={"dataset_id": dataset_id, "created_at": created_at},
            UpdateExpression="SET " + ", ".join(parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=to_dynamo(expr_values),
        )

    def delete_dataset(self, dataset_id: str) -> bool:
        record = self.get_dataset(dataset_id)
        if record is None:
            return False
        self._table(self.config.datasets_table).delete_item(
            Key={"dataset_id": dataset_id, "created_at": record["created_at"]},
        )
        return True

    def list_datasets(self, *, limit: int = 50, status: str | None = None) -> list[dict[str, Any]]:
        table = self._table(self.config.datasets_table)
        if status:
            resp = table.query(
                IndexName="status-created_at-index",
                KeyConditionExpression=Key("status").eq(status),
                ScanIndexForward=False,
                Limit=limit,
            )
            return self._records(resp.get("Items") or [])

        resp = table.scan(Limit=limit)
        items = self._records(resp.get("Items") or [])
        items.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        return items[:limit]

    # ------------------------------------------------------------------
    # training_runs
    # ------------------------------------------------------------------

    def put_training_run(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        item.setdefault("created_at", now_iso())
        item.setdefault("updated_at", item["created_at"])
        self._table(self.config.training_runs_table).put_item(Item=self._item(item))
        return from_dynamo(item)

    def get_training_run(self, run_id: str) -> dict[str, Any] | None:
        resp = self._table(self.config.training_runs_table).query(
            KeyConditionExpression=Key("run_id").eq(run_id),
            ScanIndexForward=False,
            Limit=1,
        )
        items = resp.get("Items") or []
        return from_dynamo(items[0]) if items else None

    def update_training_run(self, run_id: str, created_at: str, updates: dict[str, Any]) -> None:
        reserved = {"run_id", "created_at", "updated_at"}
        expr_names: dict[str, str] = {"#updated_at": "updated_at"}
        expr_values: dict[str, Any] = {":updated_at": now_iso()}
        parts = ["#updated_at = :updated_at"]
        idx = 0
        for key, value in updates.items():
            if key in reserved:
                continue
            name_key = f"#k{idx}"
            value_key = f":v{idx}"
            expr_names[name_key] = key
            expr_values[value_key] = value
            parts.append(f"{name_key} = {value_key}")
            idx += 1
        self._table(self.config.training_runs_table).update_item(
            Key={"run_id": run_id, "created_at": created_at},
            UpdateExpression="SET " + ", ".join(parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=to_dynamo(expr_values),
        )

    def list_training_runs(self, *, limit: int = 15, status: str | None = None) -> list[dict[str, Any]]:
        table = self._table(self.config.training_runs_table)
        if status:
            resp = table.query(
                IndexName="status-created_at-index",
                KeyConditionExpression=Key("status").eq(status),
                ScanIndexForward=False,
                Limit=limit,
            )
            return self._records(resp.get("Items") or [])

        resp = table.scan(Limit=max(limit, 25))
        items = self._records(resp.get("Items") or [])
        items.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        return items[:limit]

    # ------------------------------------------------------------------
    # models
    # ------------------------------------------------------------------

    def put_model(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        item.setdefault("version", now_iso())
        self._table(self.config.models_table).put_item(Item=self._item(item))
        return from_dynamo(item)

    def get_model(self, model_id: str, version: str) -> dict[str, Any] | None:
        resp = self._table(self.config.models_table).get_item(
            Key={"model_id": model_id, "version": version}
        )
        item = resp.get("Item")
        return from_dynamo(item) if item else None

    def list_models(self, *, limit: int = 50, status: str | None = None) -> list[dict[str, Any]]:
        table = self._table(self.config.models_table)
        if status:
            resp = table.query(
                IndexName="status-version-index",
                KeyConditionExpression=Key("status").eq(status),
                ScanIndexForward=False,
                Limit=limit,
            )
            return self._records(resp.get("Items") or [])

        resp = table.scan(Limit=max(limit, 25))
        items = self._records(resp.get("Items") or [])
        items.sort(key=lambda row: row.get("version", ""), reverse=True)
        return items[:limit]

    def get_production_model(self) -> dict[str, Any] | None:
        models = self.list_models(status="PRODUCTION", limit=5)
        return models[0] if models else None

    # ------------------------------------------------------------------
    # approval_requests
    # ------------------------------------------------------------------

    def put_approval_request(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        item.setdefault("created_at", now_iso())
        self._table(self.config.approval_table).put_item(Item=self._item(item))
        return from_dynamo(item)

    def get_approval_request(self, approval_id: str) -> dict[str, Any] | None:
        resp = self._table(self.config.approval_table).query(
            KeyConditionExpression=Key("approval_id").eq(approval_id),
            ScanIndexForward=False,
            Limit=1,
        )
        items = resp.get("Items") or []
        return from_dynamo(items[0]) if items else None

    def list_approval_requests(
        self, *, limit: int = 20, status: str | None = None
    ) -> list[dict[str, Any]]:
        table = self._table(self.config.approval_table)
        if status:
            resp = table.query(
                IndexName="status-created_at-index",
                KeyConditionExpression=Key("status").eq(status),
                ScanIndexForward=False,
                Limit=limit,
            )
            return self._records(resp.get("Items") or [])

        resp = table.scan(Limit=limit)
        items = self._records(resp.get("Items") or [])
        items.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        return items[:limit]

    # ------------------------------------------------------------------
    # predictions
    # ------------------------------------------------------------------

    def put_prediction(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        item.setdefault("prediction_id", f"pred-{uuid.uuid4().hex[:12]}")
        item.setdefault("created_at", now_iso())
        self._table(self.config.predictions_table).put_item(Item=self._item(item))
        return from_dynamo(item)

    def list_predictions(
        self,
        *,
        limit: int = 50,
        model_version: str | None = None,
    ) -> list[dict[str, Any]]:
        table = self._table(self.config.predictions_table)
        if model_version:
            resp = table.query(
                IndexName="model_version-created_at-index",
                KeyConditionExpression=Key("model_version").eq(model_version),
                ScanIndexForward=False,
                Limit=limit,
            )
            return self._records(resp.get("Items") or [])

        resp = table.scan(Limit=limit)
        items = self._records(resp.get("Items") or [])
        items.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        return items[:limit]

    def list_predictions_since(
        self,
        start_iso: str,
        *,
        model_version: str | None = None,
        max_items: int = 5000,
    ) -> list[dict[str, Any]]:
        table = self._table(self.config.predictions_table)
        items: list[dict[str, Any]] = []

        if model_version:
            resp = table.query(
                IndexName="model_version-created_at-index",
                KeyConditionExpression=Key("model_version").eq(model_version)
                & Key("created_at").gte(start_iso),
                ScanIndexForward=False,
            )
            items.extend(self._records(resp.get("Items") or []))
            while "LastEvaluatedKey" in resp and len(items) < max_items:
                resp = table.query(
                    IndexName="model_version-created_at-index",
                    KeyConditionExpression=Key("model_version").eq(model_version)
                    & Key("created_at").gte(start_iso),
                    ExclusiveStartKey=resp["LastEvaluatedKey"],
                    ScanIndexForward=False,
                )
                items.extend(self._records(resp.get("Items") or []))
            return items[:max_items]

        resp = table.scan(FilterExpression=Attr("created_at").gte(start_iso))
        items.extend(self._records(resp.get("Items") or []))
        while "LastEvaluatedKey" in resp and len(items) < max_items:
            resp = table.scan(
                FilterExpression=Attr("created_at").gte(start_iso),
                ExclusiveStartKey=resp["LastEvaluatedKey"],
            )
            items.extend(self._records(resp.get("Items") or []))
        items.sort(key=lambda row: row.get("created_at", ""), reverse=True)
        return items[:max_items]

    # ------------------------------------------------------------------
    # monitoring_snapshots
    # ------------------------------------------------------------------

    def put_monitoring_snapshot(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        item.setdefault("snapshot_id", f"snapshot-{uuid.uuid4().hex[:10]}")
        item.setdefault("period_start", now_iso())
        self._table(self.config.monitoring_table).put_item(Item=self._item(item))
        return from_dynamo(item)

    def list_monitoring_snapshots(self, *, limit: int = 24) -> list[dict[str, Any]]:
        resp = self._table(self.config.monitoring_table).scan(Limit=limit)
        items = self._records(resp.get("Items") or [])
        items.sort(key=lambda row: row.get("period_start", ""), reverse=True)
        return items[:limit]

    def get_latest_monitoring_snapshot(self, model_id: str | None = None) -> dict[str, Any] | None:
        snapshots = self.list_monitoring_snapshots(limit=50)
        if model_id:
            for row in snapshots:
                if row.get("model_id") == model_id:
                    return row
            return None
        return snapshots[0] if snapshots else None

    # ------------------------------------------------------------------
    # weekly_reports
    # ------------------------------------------------------------------

    def put_weekly_report(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        item.setdefault("report_id", f"weekly-{uuid.uuid4().hex[:10]}")
        item.setdefault("period_start", now_iso())
        self._table(self.config.weekly_reports_table).put_item(Item=self._item(item))
        return from_dynamo(item)

    def list_weekly_reports(self, *, limit: int = 12) -> list[dict[str, Any]]:
        resp = self._table(self.config.weekly_reports_table).scan(Limit=limit)
        items = self._records(resp.get("Items") or [])
        items.sort(key=lambda row: row.get("period_start", ""), reverse=True)
        return items[:limit]

    def get_weekly_report(self, report_id: str) -> dict[str, Any] | None:
        resp = self._table(self.config.weekly_reports_table).scan(
            FilterExpression=Attr("report_id").eq(report_id),
            Limit=5,
        )
        items = self._records(resp.get("Items") or [])
        return items[0] if items else None

    def get_previous_weekly_report(
        self,
        *,
        before_period_start: str,
        model_id: str | None = None,
    ) -> dict[str, Any] | None:
        reports = self.list_weekly_reports(limit=24)
        for row in reports:
            if row.get("period_start", "") >= before_period_start:
                continue
            if model_id and row.get("model_id") != model_id:
                continue
            return row
        return None

    # ------------------------------------------------------------------
    # review_queue
    # ------------------------------------------------------------------

    def put_review_item(self, record: dict[str, Any]) -> dict[str, Any]:
        item = dict(record)
        item.setdefault("review_id", f"review-{uuid.uuid4().hex[:10]}")
        item.setdefault("created_at", now_iso())
        item.setdefault("status", "PENDING")
        self._table(self.config.review_queue_table).put_item(Item=self._item(item))
        return from_dynamo(item)

    def list_review_queue(
        self,
        *,
        limit: int = 50,
        status: str = "PENDING",
    ) -> list[dict[str, Any]]:
        resp = self._table(self.config.review_queue_table).query(
            IndexName="status-created_at-index",
            KeyConditionExpression=Key("status").eq(status),
            ScanIndexForward=False,
            Limit=limit,
        )
        return self._records(resp.get("Items") or [])

    def update_review_item(self, review_id: str, created_at: str, updates: dict[str, Any]) -> None:
        expr_names: dict[str, str] = {}
        expr_values: dict[str, Any] = {}
        parts: list[str] = []
        for idx, (key, value) in enumerate(updates.items()):
            name_key = f"#k{idx}"
            value_key = f":v{idx}"
            expr_names[name_key] = key
            expr_values[value_key] = value
            parts.append(f"{name_key} = {value_key}")
        self._table(self.config.review_queue_table).update_item(
            Key={"review_id": review_id, "created_at": created_at},
            UpdateExpression="SET " + ", ".join(parts),
            ExpressionAttributeNames=expr_names,
            ExpressionAttributeValues=to_dynamo(expr_values),
        )

    # ------------------------------------------------------------------
    # S3 helpers
    # ------------------------------------------------------------------

    def presign_upload(self, key: str, *, expires_in: int = 900) -> str:
        if not self.config.artifacts_bucket:
            raise RuntimeError("ARTIFACTS_BUCKET is not configured")
        return self._s3.generate_presigned_url(
            "put_object",
            Params={
                "Bucket": self.config.artifacts_bucket,
                "Key": key,
                "ContentType": "application/x-ndjson",
            },
            ExpiresIn=expires_in,
        )

    def put_json_s3(self, key: str, payload: dict[str, Any]) -> str:
        import json

        if not self.config.artifacts_bucket:
            raise RuntimeError("ARTIFACTS_BUCKET is not configured")
        self._s3.put_object(
            Bucket=self.config.artifacts_bucket,
            Key=key,
            Body=json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8"),
            ContentType="application/json",
        )
        return f"s3://{self.config.artifacts_bucket}/{key}"

    def put_file_s3(
        self,
        key: str,
        local_path: Path | str,
        *,
        content_type: str = "application/octet-stream",
    ) -> str:
        path = Path(local_path)
        if not path.is_file():
            raise FileNotFoundError(path)
        if not self.config.artifacts_bucket:
            raise RuntimeError("ARTIFACTS_BUCKET is not configured")
        self._s3.upload_file(
            str(path),
            self.config.artifacts_bucket,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return f"s3://{self.config.artifacts_bucket}/{key}"

    def dataset_record_from_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        splits = manifest.get("splits") or {}
        total_rows = sum(int(info.get("rows", 0)) for info in splits.values())
        dataset_id = manifest["dataset_id"]
        approved_prefix = manifest.get("s3_approved_prefix", "").rstrip("/")
        pending_prefix = f"datasets/pending/{dataset_id}"
        if approved_prefix and manifest.get("status", "").lower() in {"approved", "audited"}:
            prefix = approved_prefix
        else:
            prefix = pending_prefix
        return {
            "dataset_id": dataset_id,
            "created_at": manifest.get("created_at", now_iso()),
            "name": manifest.get("name", dataset_id),
            "status": manifest.get("status", "pending").upper(),
            "s3_uri": f"s3://{self.config.artifacts_bucket}/{prefix}/" if self.config.artifacts_bucket else "",
            "s3_prefix": prefix,
            "num_records": total_rows,
            "splits": list(splits.keys()),
            "audit_passed": bool(manifest.get("audit_passed")),
            "uploaded_by": manifest.get("uploaded_by", "admin-ui"),
            "updated_at": manifest.get("updated_at", now_iso()),
        }
