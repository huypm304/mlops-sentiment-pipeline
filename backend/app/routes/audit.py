from fastapi import APIRouter, HTTPException

from backend.app.schemas.audit import AuditRunRequest, AuditRunResponse
from backend.app.services import audit as audit_service
from backend.app.services import datasets as datasets_service

router = APIRouter(prefix="/audit", tags=["audit"])


@router.get("/reports")
async def list_audit_reports():
    return {"reports": audit_service.list_reports()}


@router.get("/reports/latest")
async def latest_audit_report():
    reports = audit_service.list_reports(limit=1)
    if not reports:
        raise HTTPException(
            status_code=404,
            detail="No audit reports yet. Upload train+dev and POST /datasets/{id}/audit first.",
        )
    report = audit_service.load_report(reports[0]["report_id"])
    if not report:
        raise HTTPException(status_code=404, detail="Report file missing")
    return report


@router.get("/reports/{report_id}")
async def get_audit_report(report_id: str):
    report = audit_service.load_report(report_id)
    if not report:
        raise HTTPException(status_code=404, detail=f"Report '{report_id}' not found")
    return report


@router.post("/run", response_model=AuditRunResponse)
async def run_audit(body: AuditRunRequest):
    try:
        manifest = datasets_service.get_dataset(body.dataset_id)
        train_path = datasets_service.resolve_split_path(body.dataset_id, "train")
        dev_path = datasets_service.resolve_split_path(body.dataset_id, "dev")
        test_path = None
        if "test" in manifest.get("splits", {}):
            test_path = datasets_service.resolve_split_path(body.dataset_id, "test")
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    try:
        report = audit_service.run_bundle_audit(
            train_path=train_path,
            dev_path=dev_path,
            test_path=test_path,
            dataset_id=body.dataset_id,
            dataset_key=f"datasets/local/{body.dataset_id}",
            source_label=f"{manifest.get('name', body.dataset_id)} · train+dev",
        )
        datasets_service.record_audit_result(body.dataset_id, audit_service.BUNDLE_SPLIT, report)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AuditRunResponse(
        report_id=report["report_id"],
        passed=report["passed"],
        data_level_status=str(report.get("data_level_status") or "unknown"),
        summary=report.get("summary") or {},
        benchmarks=report.get("benchmarks") or [],
        dataset_id=body.dataset_id,
    )
