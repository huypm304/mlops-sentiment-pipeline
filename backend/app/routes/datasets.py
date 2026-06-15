from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from backend.app.schemas.datasets import (
    DatasetAuditResponse,
    DatasetListItem,
    DatasetManifest,
    DatasetUploadResponse,
    SplitAuditResult,
)
from backend.app.services import audit as audit_service
from backend.app.services import datasets as datasets_service

router = APIRouter(prefix="/datasets", tags=["datasets"])


@router.get("")
async def list_datasets() -> dict[str, list[DatasetListItem]]:
    return {"datasets": datasets_service.list_datasets()}


@router.get("/{dataset_id}", response_model=DatasetManifest)
async def get_dataset(dataset_id: str) -> DatasetManifest:
    try:
        return datasets_service.get_dataset(dataset_id)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/upload", response_model=DatasetUploadResponse)
async def upload_dataset(
    name: str = Form(...),
    train: UploadFile = File(...),
    dev: UploadFile = File(...),
    test: UploadFile | None = File(default=None),
) -> DatasetUploadResponse:
    files: dict[str, tuple[str, bytes]] = {}

    async def read_split(split: str, upload: UploadFile) -> None:
        if not upload.filename:
            raise HTTPException(status_code=400, detail=f"{split} file name is required")
        if not upload.filename.lower().endswith(".jsonl"):
            raise HTTPException(status_code=400, detail=f"{split} must be a .jsonl file")
        content = await upload.read()
        if not content.strip():
            raise HTTPException(status_code=400, detail=f"{split} file is empty")
        files[split] = (upload.filename, content)

    try:
        await read_split("train", train)
        await read_split("dev", dev)
        if test is not None and test.filename:
            await read_split("test", test)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        manifest = datasets_service.create_dataset(name=name, files=files)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return DatasetUploadResponse(dataset=manifest)


@router.post("/{dataset_id}/audit", response_model=DatasetAuditResponse)
async def audit_dataset(dataset_id: str) -> DatasetAuditResponse:
    try:
        manifest = datasets_service.get_dataset(dataset_id)
        train_path = datasets_service.resolve_split_path(dataset_id, "train")
        dev_path = datasets_service.resolve_split_path(dataset_id, "dev")
        test_path = None
        if "test" in manifest.get("splits", {}):
            test_path = datasets_service.resolve_split_path(dataset_id, "test")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        report = audit_service.run_bundle_audit(
            train_path=train_path,
            dev_path=dev_path,
            test_path=test_path,
            dataset_id=dataset_id,
            dataset_key=f"datasets/local/{dataset_id}",
            source_label=f"{manifest.get('name', dataset_id)} · train+dev",
        )
        datasets_service.record_audit_result(dataset_id, audit_service.BUNDLE_SPLIT, report)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    score = audit_service.audit_score_from_report(report)
    results = [
        SplitAuditResult(
            split="bundle",
            report_id=report["report_id"],
            passed=bool(report.get("passed")),
            audit_score=score,
            summary=report.get("summary") or {},
        )
    ]

    return DatasetAuditResponse(dataset_id=dataset_id, passed=bool(report.get("passed")), results=results)
