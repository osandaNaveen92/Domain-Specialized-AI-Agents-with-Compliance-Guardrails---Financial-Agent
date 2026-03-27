from modules.explainer import generate_explanation


THRESHOLD_AMOUNT = 5000  # you can change later

def apply_guardrails(journal_entries):
    reviewed_entries = []

    for entry in journal_entries:
        issues = []

        # Rule 1: Threshold check
        if entry["amount"] > THRESHOLD_AMOUNT:
            issues.append("Amount exceeds threshold - manual review required")

        # Rule 2: Basic accounting check
        if entry["debit_account"] == entry["credit_account"]:
            issues.append("Invalid entry: same debit and credit account")

        # Rule 3: Missing reason
        if not entry["reason"]:
            issues.append("Missing explanation")

        # Assign status
        if issues:
            if entry["status"] == "REVIEW_REQUIRED":
                entry["explanation"] = "Manual review required due to policy violation."
            else:
                entry["explanation"] = generate_explanation(entry)
        else:
            entry["status"] = "READY_FOR_APPROVAL"

        reviewed_entries.append(entry)

    return reviewed_entries