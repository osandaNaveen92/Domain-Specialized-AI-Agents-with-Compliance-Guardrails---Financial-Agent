from datetime import datetime


def evaluate_rule(entry, control, context=None):
    context = context or {}
    rule = control["rule_type"]

    if rule == "amount_match":
        # For unmatched journal entries created during reconciliation, this control should fail
        # until underlying transactions are actually matched in a future close run.
        if entry.get("match_status") is not None:
            return entry.get("match_status") == "matched"
        return not entry.get("is_unmatched", False)

    if rule == "completeness_check":
        return entry.get("is_complete", True) and not entry.get("is_unmatched", False)

    if rule == "date_validation":
        txn_date = entry.get("transaction_date")
        close_period = context.get("close_period")
        if not txn_date or not close_period:
            return True
        try:
            parsed = datetime.strptime(txn_date, "%Y-%m-%d")
            return parsed.strftime("%Y-%m") == close_period
        except ValueError:
            return False

    if rule == "threshold_check":
        threshold = float(control.get("threshold", 0))
        amount = abs(float(entry.get("amount", 0)))
        approved = entry.get("status") == "APPROVED"
        return amount <= threshold or approved

    return True
