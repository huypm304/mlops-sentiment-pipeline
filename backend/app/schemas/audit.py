from pydantic import BaseModel, Field


class AuditRunRequest(BaseModel):
    dataset_id: str = Field(description="Registered dataset id from POST /datasets/upload")


class AuditRunResponse(BaseModel):
    report_id: str
    passed: bool
    data_level_status: str = "unknown"
    summary: dict
    benchmarks: list[dict]
    dataset_id: str
