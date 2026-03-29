from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from modules.report import generate_audit_report
from modules.control_loader import load_controls
from src.data.database import FinancialRepository
from src.governance.engine import GovernanceEngine
from src.models.schemas import ClosePackageResponse, CloseRunResponse, CloseStatusResponse
from src.services.close_service import CloseService

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

controls = load_controls()
repository = FinancialRepository()
governance_engine = GovernanceEngine()
close_service = CloseService(
    repository=repository,
    controls=controls,
    governance_engine=governance_engine,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {"message": "Financial Close Agent API Running", "dashboard": "/dashboard"}

@app.get("/dashboard")
def dashboard():
    return FileResponse(BASE_DIR / "dashboard.html")

@app.get("/transactions")
def get_transactions():
    return repository.get_transactions()

@app.get("/matches")
def get_matches():
    return repository.get_matches()

@app.get("/journal")
def get_journal():
    return repository.get_journal_entries()

@app.post("/approve/{entry_id}")
def approve_entry(entry_id: str, approver: str = "unknown_user"):
    result = repository.update_entry_status(entry_id=entry_id, status="APPROVED", actor=approver)
    if not result["updated"]:
        if result.get("reason") == "sod_violation":
            raise HTTPException(status_code=409, detail=result.get("message"))
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

    repository.log_action("approval_agent", "approve_entry", result)
    return {"message": "Approved", **result}

@app.post("/reject/{entry_id}")
def reject_entry(entry_id: str, approver: str = "unknown_user"):
    result = repository.update_entry_status(entry_id=entry_id, status="REJECTED", actor=approver)
    if not result["updated"]:
        if result.get("reason") == "sod_violation":
            raise HTTPException(status_code=409, detail=result.get("message"))
        raise HTTPException(status_code=404, detail=f"Entry {entry_id} not found")

    repository.log_action("approval_agent", "reject_entry", result)
    return {"message": "Rejected", **result}

@app.post("/close/initiate")
def initiate_close(period: str) -> CloseStatusResponse:
    return close_service.initiate_close(period)


@app.get("/close/status")
def close_status(period: str) -> CloseStatusResponse:
    status = close_service.get_close_status(period)
    if not status:
        raise HTTPException(status_code=404, detail=f"No close run found for period {period}")
    return status


@app.get("/close/package")
def close_package(period: str) -> ClosePackageResponse:
    status = close_service.get_close_status(period)
    if not status:
        raise HTTPException(status_code=404, detail=f"No close run found for period {period}")
    return close_service.build_close_package(period)


@app.post("/run-close")
def run_close(period: str | None = None) -> CloseRunResponse:
    bank_file = BASE_DIR / "data" / "sample_bank.csv"
    gl_file = BASE_DIR / "data" / "sample_gl.csv"

    if not bank_file.exists() or not gl_file.exists():
        raise HTTPException(status_code=404, detail="Sample CSV files not found in data directory")

    return close_service.run_close(bank_file=bank_file, gl_file=gl_file, period=period)


@app.get("/reviews/pending")
def get_pending_reviews():
    return repository.get_pending_reviews()


@app.get("/governance/dashboard")
def get_governance_dashboard():
    return repository.get_governance_dashboard()

@app.get("/generate-report")
def generate_report():
    entries = repository.get_journal_entries()
    generate_audit_report(entries)
    return {"message": "Audit report generated as audit_report.pdf"}
