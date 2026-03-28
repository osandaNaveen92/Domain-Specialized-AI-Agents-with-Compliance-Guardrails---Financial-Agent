def generate_journal_entries(unmatched_bank, unmatched_gl):
    journal_entries = []

    entry_counter = 1

    # Case 1: Bank transaction not in GL → Expense or unknown
    for txn in unmatched_bank:
        entry = {
            "entry_id": f"JE_{entry_counter}",
            "debit_account": "Suspense/Expense",
            "credit_account": "Bank",
            "amount": txn["amount"],
            "reason": f"Unrecorded bank transaction: {txn['description']}",
            "source": "bank",
            "status": "REVIEW_REQUIRED"
        }
        generated_text = f"Generate explanation for unmatched bank txn {txn['transaction_id']}"
        entry["explanation"] = generated_text
        journal_entries.append(entry)
        entry_counter += 1

    # Case 2: GL entry not in Bank → accrual or error
    for txn in unmatched_gl:
        entry = {
            "entry_id": f"JE_{entry_counter}",
            "debit_account": "Bank",
            "credit_account": "Suspense/Liability",
            "amount": txn["amount"],
            "reason": f"GL entry not found in bank: {txn['description']}",
            "source": "gl",
            "status": "REVIEW_REQUIRED"
        }
        generated_text = f"Generate explanation for unmatched GL txn {txn['transaction_id']}"
        entry["explanation"] = generated_text
        journal_entries.append(entry)
        entry_counter += 1

    return journal_entries
