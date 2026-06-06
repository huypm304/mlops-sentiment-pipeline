from pydantic import BaseModel, Field


class AuditRunRequest(BaseModel):
    dataset: str = Field(
        default="train",
        description="Preset: train | demo | or absolute path to .jsonl",
    )


class AuditRunResponse(BaseModel):
    report_id: str
    passed: bool
    summary: dict
    benchmarks: list[dict]
