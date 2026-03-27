from config.db import transactions_collection, matches_collection

def save_transactions(transactions):
    if transactions:
        transactions_collection.insert_many(transactions)
        
def clear_collections():
    transactions_collection.delete_many({})
    matches_collection.delete_many({})

def save_matches(matched, unmatched_bank, unmatched_gl):
    records = []

    for b, g in matched:
        records.append({
            "bank_id": b["transaction_id"],
            "gl_id": g["transaction_id"],
            "status": "matched"
        })

    for b in unmatched_bank:
        records.append({
            "bank_id": b["transaction_id"],
            "gl_id": None,
            "status": "unmatched_bank"
        })

    for g in unmatched_gl:
        records.append({
            "bank_id": None,
            "gl_id": g["transaction_id"],
            "status": "unmatched_gl"
        })

    if records:
        matches_collection.insert_many(records)