from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


class RiskAssessment(BaseModel):
    score: int = Field(default=0, ge=0, le=100)
    priority: Literal["CRITICAL", "HIGH", "MEDIUM", "LOW", "NONE"] = "NONE"


class ControlSummary(BaseModel):
    total: int = 0
    failed: int = 0
    passed: int = 0


class ControlResult(BaseModel):
    control_id: str
    framework: str
    description: str
    status: Literal["PASS", "FAIL"]
    severity: str
    evidence_required: bool = False


class DecisionHistoryItem(BaseModel):
    action: Literal["APPROVED", "REJECTED"]
    by: str
    at: str


class GovernanceDecision(BaseModel):
    approval_level: Literal["L0", "L1", "L2", "L3"] = "L0"
    requires_human_review: bool = False
    queue_status: Literal["AUTO_CLEARED", "PENDING_REVIEW", "RESOLVED"] = "AUTO_CLEARED"
    reasons: List[str] = Field(default_factory=list)


class JournalEntry(BaseModel):
    entry_id: str
    debit_account: str
    credit_account: str
    amount: float
    reason: str
    source: str
    status: str
    explanation: Optional[str] = None
    transaction_id: Optional[str] = None
    transaction_date: Optional[str] = None
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None
    rejected_by: Optional[str] = None
    rejected_at: Optional[str] = None
    risk: Optional[RiskAssessment] = None
    prepared_by: Optional[str] = None
    governance: Optional[GovernanceDecision] = None
    control_summary: Optional[ControlSummary] = None
    control_results: List[ControlResult] = Field(default_factory=list)
    decision_history: List[DecisionHistoryItem] = Field(default_factory=list)


class CloseRunSummary(BaseModel):
    bank_records: int
    gl_records: int
    matched: int
    unmatched_bank: int
    unmatched_gl: int
    journal_entries: int


class CloseRunResponse(BaseModel):
    message: str
    summary: CloseRunSummary
    metadata: Dict[str, Any] = Field(default_factory=dict)


class CloseTask(BaseModel):
    task_id: str
    name: str
    status: Literal["PENDING", "IN_PROGRESS", "COMPLETED"]
    details: str = ""


class CloseStatusResponse(BaseModel):
    period: str
    status: str
    checklist: List[CloseTask] = Field(default_factory=list)
    updated_at: Optional[str] = None


class ClosePackageResponse(BaseModel):
    period: str
    overall_status: str
    summary: Dict[str, Any] = Field(default_factory=dict)
