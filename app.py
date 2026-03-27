from utils.parser import parse_csv
from utils.matcher import match_transactions
from utils.db_utils import (
    save_transactions,
    save_matches,
    save_journal_entries,
    log_action
)
from modules.explainer import generate_explanation
from modules.journal import generate_journal_entries
from modules.controller import apply_guardrails

def main():
    bank_data = parse_csv("data/sample_bank.csv", "bank")
    gl_data = parse_csv("data/sample_gl.csv", "gl")

    save_transactions(bank_data)
    save_transactions(gl_data)

    matched, unmatched_bank, unmatched_gl = match_transactions(bank_data, gl_data)

    save_matches(matched, unmatched_bank, unmatched_gl)

    log_action("analyst", "matching_completed", {
        "matched": len(matched),
        "unmatched_bank": len(unmatched_bank),
        "unmatched_gl": len(unmatched_gl)
    })

    # Generate Journal Entries
    journal_entries = generate_journal_entries(unmatched_bank, unmatched_gl)

    log_action("analyst", "journal_generated", {
        "count": len(journal_entries)
    })

    # Apply Controller Rules
    reviewed_entries = apply_guardrails(journal_entries)

    # Generate explanations (GenAI layer)
    for entry in reviewed_entries:
        explanation = generate_explanation(entry)
        entry["explanation"] = explanation

        log_action("genai", "explanation_generated", {
            "entry_id": entry["entry_id"]
        })

    log_action("controller", "guardrails_applied", {
        "reviewed": len(reviewed_entries)
    })

    log_action("controller", "guardrails_applied", {
        "reviewed": len(reviewed_entries)
    })

    save_journal_entries(reviewed_entries)

    print("\n--- JOURNAL ENTRIES ---")
    for entry in reviewed_entries:
        print(entry)

if __name__ == "__main__":
    main()