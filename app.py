from fastapi import FastAPI
from config.db import transactions_collection, matches_collection, journal_collection
from modules.report import generate_audit_report

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Financial Close Agent API Running"}

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

@app.get("/generate-report")
def generate_report():
    entries = list(journal_collection.find({}, {"_id": 0}))
    generate_audit_report(entries)
    return {"message": "Audit report generated as audit_report.pdf"}