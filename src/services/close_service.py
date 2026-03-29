from pathlib import Path
from datetime import datetime
from typing import List

from modules.control_evaluator import apply_controls
from modules.controller import apply_guardrails
from modules.journal import generate_journal_entries
from src.data.database import FinancialRepository
from src.governance.engine import GovernanceEngine
from src.models.schemas import CloseRunResponse, CloseRunSummary
from utils.matcher import match_transactions
from utils.parser import parse_csv


class CloseService:
    def __init__(
        self,
        repository: FinancialRepository,
        controls: List[dict],
        governance_engine: GovernanceEngine | None = None,
    ) -> None:
        self.repository = repository
        self.controls = controls
        self.governance_engine = governance_engine or GovernanceEngine()

    def initiate_close(self, period: str):
        close_doc = self.repository.initiate_close(period)
        self.repository.log_action("close_manager", "initiate_close", {"period": period})
        return close_doc

    def get_close_status(self, period: str):
        return self.repository.get_close_status(period)

    def build_close_package(self, period: str):
        package = self.repository.build_close_package(period)
        self.repository.complete_close_task(period, "Close Package", "Close package generated")
        self.repository.log_action("close_manager", "build_close_package", {"period": period})
        return package

    def run_close(self, bank_file: Path, gl_file: Path, period: str | None = None) -> CloseRunResponse:
        self.repository.clear_runtime_data()

        bank_data = parse_csv(str(bank_file), "bank")
        gl_data = parse_csv(str(gl_file), "gl")
        all_dates = [
            txn["date"]
            for txn in bank_data + gl_data
            if isinstance(txn.get("date"), str) and len(txn["date"]) >= 7
        ]
        close_period = period or (max(all_dates)[:7] if all_dates else datetime.utcnow().strftime("%Y-%m"))

        self.repository.initiate_close(close_period)
        self.repository.update_close_status(close_period, "IN_PROGRESS")
        self.repository.complete_close_task(close_period, "Data Collection", "Loaded bank and GL CSV files")
        self.repository.save_transactions(bank_data + gl_data)

        matched, unmatched_bank, unmatched_gl = match_transactions(bank_data, gl_data)
        self.repository.save_matches(matched, unmatched_bank, unmatched_gl)
        self.repository.complete_close_task(
            close_period,
            "Reconciliation",
            f"Matched={len(matched)}, Unmatched Bank={len(unmatched_bank)}, Unmatched GL={len(unmatched_gl)}",
        )

        journal_entries = generate_journal_entries(unmatched_bank, unmatched_gl)
        reviewed_entries = apply_guardrails(journal_entries)
        self.repository.complete_close_task(
            close_period,
            "Journal Generation",
            f"Generated journal entries={len(reviewed_entries)}",
        )

        reviewed_entries = apply_controls(
            reviewed_entries,
            self.controls,
            context={"close_period": close_period},
        )
        self.repository.complete_close_task(
            close_period,
            "Controls Evaluation",
            "Framework controls and risk scoring completed",
        )
        reviewed_entries = self.governance_engine.apply(reviewed_entries)
        pending_reviews = sum(1 for e in reviewed_entries if e.get("status") == "PENDING_REVIEW")
        governance_detail = f"Pending reviews={pending_reviews}"
        self.repository.complete_close_task(close_period, "Governance Review", governance_detail)
        self.repository.save_journal_entries(reviewed_entries)

        close_status = "PENDING_REVIEW" if pending_reviews > 0 else "READY_FOR_APPROVAL"
        self.repository.update_close_status(close_period, close_status)

        summary = CloseRunSummary(
            bank_records=len(bank_data),
            gl_records=len(gl_data),
            matched=len(matched),
            unmatched_bank=len(unmatched_bank),
            unmatched_gl=len(unmatched_gl),
            journal_entries=len(reviewed_entries),
        )

        self.repository.log_action(
            "reconciliation_agent",
            "run_close",
            {
                "bank_records": summary.bank_records,
                "gl_records": summary.gl_records,
                "matched": summary.matched,
                "unmatched_bank": summary.unmatched_bank,
                "unmatched_gl": summary.unmatched_gl,
                "journal_entries": summary.journal_entries,
                "period": close_period,
                "close_status": close_status,
            },
        )

        return CloseRunResponse(
            message="Financial close run completed",
            summary=summary,
            metadata={
                "close_period": close_period,
                "pending_reviews": pending_reviews,
                "close_status": close_status,
            },
        )
