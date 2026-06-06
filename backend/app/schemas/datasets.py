from typing import Literal

from pydantic import BaseModel, Field

DatasetSplit = Literal["train", "dev", "test", "bundle"]
DatasetStatus = Literal["pending", "audited", "approved"]


class SplitFileInfo(BaseModel):
    filename: str
    rows: int
    size_bytes: int


class SplitAuditInfo(BaseModel):
    report_id: str
    passed: bool
    audit_score: float
    error_count: int
    generated_at: str


class DatasetManifest(BaseModel):
    dataset_id: str
    name: str
    status: DatasetStatus
    created_at: str
    updated_at: str
    splits: dict[str, SplitFileInfo]
    audits: dict[str, SplitAuditInfo] = Field(default_factory=dict)
    audit_passed: bool = False


class DatasetListItem(BaseModel):
    dataset_id: str
    name: str
    status: DatasetStatus
    created_at: str
    splits: list[str]
    audit_passed: bool
    audit_score: float | None = None
    total_rows: int


class DatasetUploadResponse(BaseModel):
    dataset: DatasetManifest


class SplitAuditResult(BaseModel):
    split: DatasetSplit
    report_id: str
    passed: bool
    audit_score: float
    summary: dict


class DatasetAuditResponse(BaseModel):
    dataset_id: str
    passed: bool
    results: list[SplitAuditResult]
