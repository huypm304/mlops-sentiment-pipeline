from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services import pipeline as pipeline_service

router = APIRouter(prefix="/pipeline", tags=["pipeline"])


class TriggerRequest(BaseModel):
    dataset_key: str = Field(
        default="datasets/raw/latest.jsonl",
        description="S3 key or logical path for the dataset to audit/train on",
    )
    requested_by: str = "admin-ui"


@router.get("/config")
async def pipeline_config():
    return pipeline_service.get_pipeline_config()


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
            dataset_key=body.dataset_key,
            requested_by=body.requested_by,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return run
