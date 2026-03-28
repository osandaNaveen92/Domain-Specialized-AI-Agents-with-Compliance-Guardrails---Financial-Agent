from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from config.db import transactions_collection, matches_collection, journal_collection
from modules.report import generate_audit_report
from modules.journal import generate_journal_entries
from modules.controller import apply_guardrails
from utils.parser import parse_csv
from utils.matcher import match_transactions
from utils.db_utils import (
    clear_collections,
    save_transactions,
    save_matches,
    save_journal_entries,
    log_action,
)

app = FastAPI()
BASE_DIR = Path(__file__).resolve().parent

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
    return list(transactions_collection.find({}, {"_id": 0}))

@app.get("/matches")
def get_matches():
    return list(matches_collection.find({}, {"_id": 0}))

@app.get("/journal")
def get_journal():
    return list(journal_collection.find({}, {"_id": 0}))

@app.post("/approve/{entry_id}")
def approve_entry(entry_id: str):
    journal_collection.update_one(
        {"entry_id": entry_id},
        {"$set": {"status": "APPROVED"}}
    )
    return {"message": "Approved"}

@app.post("/reject/{entry_id}")
def reject_entry(entry_id: str):
    journal_collection.update_one(
        {"entry_id": entry_id},
        {"$set": {"status": "REJECTED"}}
    )
    return {"message": "Rejected"}

@app.post("/run-close")
def run_close():
    bank_file = BASE_DIR / "data" / "sample_bank.csv"
    gl_file = BASE_DIR / "data" / "sample_gl.csv"

    if not bank_file.exists() or not gl_file.exists():
        raise HTTPException(status_code=404, detail="Sample CSV files not found in data directory")

    clear_collections()

    bank_data = parse_csv(str(bank_file), "bank")
    gl_data = parse_csv(str(gl_file), "gl")
    save_transactions(bank_data + gl_data)

    matched, unmatched_bank, unmatched_gl = match_transactions(bank_data, gl_data)
    save_matches(matched, unmatched_bank, unmatched_gl)

    journal_entries = generate_journal_entries(unmatched_bank, unmatched_gl)
    reviewed_entries = apply_guardrails(journal_entries)
    save_journal_entries(reviewed_entries)

    log_action(
        "reconciliation_agent",
        "run_close",
        {
            "bank_records": len(bank_data),
            "gl_records": len(gl_data),
            "matched": len(matched),
            "unmatched_bank": len(unmatched_bank),
            "unmatched_gl": len(unmatched_gl),
            "journal_entries": len(reviewed_entries),
        },
    )

    return {
        "message": "Financial close run completed",
        "summary": {
            "bank_records": len(bank_data),
            "gl_records": len(gl_data),
            "matched": len(matched),
            "unmatched_bank": len(unmatched_bank),
            "unmatched_gl": len(unmatched_gl),
            "journal_entries": len(reviewed_entries),
        },
    }

@app.get("/generate-report")
def generate_report():
    entries = list(journal_collection.find({}, {"_id": 0}))
    generate_audit_report(entries)
    return {"message": "Audit report generated as audit_report.pdf"}
