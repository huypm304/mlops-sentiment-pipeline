from pathlib import Path

from fastapi import APIRouter, HTTPException

from backend.app.schemas.audit import AuditRunRequest, AuditRunResponse
from backend.app.services import audit as audit_service

router = APIRouter(prefix="/audit", tags=["audit"])

_DATASETS = {
    "train": audit_service.DEFAULT_DATASET,
    "demo": audit_service.DEMO_DATASET,
}


@router.get("/reports")
async def list_audit_reports():
    return {"reports": audit_service.list_reports()}


@router.get("/reports/latest")
async def latest_audit_report():
    reports = audit_service.list_reports(limit=1)
    if not reports:
        raise HTTPException(status_code=404, detail="No audit reports yet. POST /audit/run first.")
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
    key = body.dataset.strip()
    if key in _DATASETS:
        path = _DATASETS[key]
        dataset_key = f"model/{path.name}"
    else:
        path = Path(key)
        dataset_key = key

    try:
        report = audit_service.run_audit_on_path(path, dataset_key=dataset_key)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc

    return AuditRunResponse(
        report_id=report["report_id"],
        passed=report["passed"],
        summary=report["summary"],
        benchmarks=report["benchmarks"],
    )
