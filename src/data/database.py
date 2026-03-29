from datetime import datetime
from typing import Dict, List

from config.db import (
    audit_collection,
    close_runs_collection,
    journal_collection,
    matches_collection,
    transactions_collection,
)


class FinancialRepository:
    def _default_close_checklist(self) -> List[Dict]:
        return [
            {"task_id": "T1", "name": "Data Collection", "status": "PENDING", "details": ""},
            {"task_id": "T2", "name": "Reconciliation", "status": "PENDING", "details": ""},
            {"task_id": "T3", "name": "Journal Generation", "status": "PENDING", "details": ""},
            {"task_id": "T4", "name": "Controls Evaluation", "status": "PENDING", "details": ""},
            {"task_id": "T5", "name": "Governance Review", "status": "PENDING", "details": ""},
            {"task_id": "T6", "name": "Close Package", "status": "PENDING", "details": ""},
        ]

    def initiate_close(self, period: str) -> Dict:
        now = datetime.utcnow().isoformat()
        existing = close_runs_collection.find_one({"period": period}, {"_id": 0})
        if existing:
            return existing

        doc = {
            "period": period,
            "status": "INITIATED",
            "checklist": self._default_close_checklist(),
            "created_at": now,
            "updated_at": now,
        }
        close_runs_collection.insert_one(doc)
        return close_runs_collection.find_one({"period": period}, {"_id": 0})

    def get_close_status(self, period: str) -> Dict | None:
        return close_runs_collection.find_one({"period": period}, {"_id": 0})

    def update_close_status(self, period: str, status: str) -> None:
        close_runs_collection.update_one(
            {"period": period},
            {"$set": {"status": status, "updated_at": datetime.utcnow().isoformat()}},
        )

    def update_close_task(self, period: str, task_name: str, status: str, details: str = "") -> None:
        doc = self.get_close_status(period)
        if not doc:
            return
        checklist = doc.get("checklist", [])
        for item in checklist:
            if item.get("name") == task_name:
                item["status"] = status
                if details:
                    item["details"] = details
        close_runs_collection.update_one(
            {"period": period},
            {"$set": {"checklist": checklist, "updated_at": datetime.utcnow().isoformat()}},
        )

    def complete_close_task(self, period: str, task_name: str, details: str = "") -> None:
        self.update_close_task(period, task_name, "COMPLETED", details)

    def in_progress_close_task(self, period: str, task_name: str, details: str = "") -> None:
        self.update_close_task(period, task_name, "IN_PROGRESS", details)

    def get_transactions(self) -> List[Dict]:
        return list(transactions_collection.find({}, {"_id": 0}))

    def get_matches(self) -> List[Dict]:
        return list(matches_collection.find({}, {"_id": 0}))

    def get_journal_entries(self) -> List[Dict]:
        return list(journal_collection.find({}, {"_id": 0}))

    def get_journal_entry(self, entry_id: str) -> Dict | None:
        return journal_collection.find_one({"entry_id": entry_id}, {"_id": 0})

    def get_pending_reviews(self) -> List[Dict]:
        return list(
            journal_collection.find(
                {"status": {"$in": ["PENDING_REVIEW", "REVIEW_REQUIRED"]}},
                {"_id": 0},
            )
        )

    def get_governance_dashboard(self) -> Dict:
        entries = self.get_journal_entries()
        by_level = {"L0": 0, "L1": 0, "L2": 0, "L3": 0}
        status_counts = {"PENDING_REVIEW": 0, "READY_FOR_APPROVAL": 0, "APPROVED": 0, "REJECTED": 0}

        for entry in entries:
            level = entry.get("governance", {}).get("approval_level")
            if level in by_level:
                by_level[level] += 1

            status = entry.get("status")
            if status in status_counts:
                status_counts[status] += 1

        return {
            "total_entries": len(entries),
            "pending_reviews": len([e for e in entries if e.get("status") == "PENDING_REVIEW"]),
            "by_approval_level": by_level,
            "status_breakdown": status_counts,
        }

    def build_close_package(self, period: str) -> Dict:
        close_status = self.get_close_status(period) or {}
        entries = self.get_journal_entries()

        framework_summary = {}
        for entry in entries:
            for result in entry.get("control_results", []):
                fw = result.get("framework", "UNKNOWN")
                if fw not in framework_summary:
                    framework_summary[fw] = {"PASS": 0, "FAIL": 0}
                framework_summary[fw][result.get("status", "PASS")] += 1

        approved = len([e for e in entries if e.get("status") == "APPROVED"])
        rejected = len([e for e in entries if e.get("status") == "REJECTED"])
        pending = len([e for e in entries if e.get("status") == "PENDING_REVIEW"])

        return {
            "period": period,
            "overall_status": close_status.get("status", "UNKNOWN"),
            "summary": {
                "journal_entries": len(entries),
                "approved_entries": approved,
                "rejected_entries": rejected,
                "pending_reviews": pending,
                "framework_controls": framework_summary,
                "checklist": close_status.get("checklist", []),
            },
        }

    def clear_runtime_data(self) -> None:
        transactions_collection.delete_many({})
        matches_collection.delete_many({})
        journal_collection.delete_many({})

    def save_transactions(self, transactions: List[Dict]) -> None:
        if transactions:
            transactions_collection.insert_many(transactions)

    def save_matches(self, matched: List[Dict], unmatched_bank: List[Dict], unmatched_gl: List[Dict]) -> None:
        records = []

        for item in matched:
            b = item["bank"]
            g = item["gl"]
            records.append(
                {
                    "bank_id": b["transaction_id"],
                    "gl_id": g["transaction_id"],
                    "status": "matched",
                    "confidence": item.get("confidence", 0),
                }
            )

        for b in unmatched_bank:
            records.append(
                {
                    "bank_id": b["transaction_id"],
                    "gl_id": None,
                    "status": "unmatched_bank",
                }
            )

        for g in unmatched_gl:
            records.append(
                {
                    "bank_id": None,
                    "gl_id": g["transaction_id"],
                    "status": "unmatched_gl",
                }
            )

        if records:
            matches_collection.insert_many(records)

    def save_journal_entries(self, entries: List[Dict]) -> None:
        if entries:
            journal_collection.insert_many(entries)

    def update_entry_status(self, entry_id: str, status: str, actor: str) -> Dict:
        current = self.get_journal_entry(entry_id)
        if not current:
            return {"updated": False, "entry_id": entry_id, "reason": "not_found"}

        preparer = current.get("prepared_by")
        if preparer and preparer == actor and status == "APPROVED":
            return {
                "updated": False,
                "entry_id": entry_id,
                "reason": "sod_violation",
                "message": "Segregation of duties violation: preparer cannot approve own entry",
            }

        now = datetime.utcnow().isoformat()
        base_update = {
            "$set": {"status": status, "governance.queue_status": "RESOLVED"},
            "$push": {"decision_history": {"action": status, "by": actor, "at": now}},
        }

        if status == "APPROVED":
            base_update["$set"].update({"approved_by": actor, "approved_at": now})
        if status == "REJECTED":
            base_update["$set"].update({"rejected_by": actor, "rejected_at": now})

        journal_collection.update_one({"entry_id": entry_id}, base_update)
        return {"updated": True, "entry_id": entry_id, "status": status, "actor": actor, "at": now}

    def log_action(self, agent: str, action: str, details: Dict) -> None:
        audit_collection.insert_one(
            {
                "timestamp": str(datetime.now()),
                "agent": agent,
                "action": action,
                "details": details,
            }
        )
