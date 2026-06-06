from fastapi import APIRouter, HTTPException

from backend.app.schemas.pipeline import ApprovalDecisionRequest, TriggerRequest
from backend.app.services import pipeline as pipeline_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


@router.get("/config")
async def pipeline_config():
    return pipeline_service.get_pipeline_config()


@router.get("/training-config")
async def training_config():
    return {"training_config": pipeline_service.merge_training_config(None)}


@router.get("/runs")
async def list_runs(limit: int = 15):
    return {"runs": pipeline_service.list_runs(max_results=limit)}


@router.get("/runs/{execution_arn:path}")
async def get_run(execution_arn: str):
    run = pipeline_service.get_run(execution_arn)
    if run is None:
        raise HTTPException(status_code=404, detail="Execution not found")
    return run


@router.post("/trigger")
async def trigger_pipeline(body: TriggerRequest):
    try:
        run = pipeline_service.start_execution(
            dataset_id=body.dataset_id,
            requested_by=body.requested_by,
            base_model_id=body.base_model_id,
            training_config=body.training_config,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return run


@router.get("/approvals/{approval_id}")
async def get_approval(approval_id: str):
    record = pipeline_service.get_approval(approval_id)
    if record is None:
        raise HTTPException(status_code=404, detail="Approval not found")
    return record


@router.post("/approvals/{approval_id}/decide")
async def decide_approval(approval_id: str, body: ApprovalDecisionRequest):
    try:
        return pipeline_service.decide_approval(
            approval_id,
            decision=body.decision,
            decided_by=body.decided_by,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
