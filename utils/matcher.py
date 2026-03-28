from datetime import datetime
from rapidfuzz import fuzz

def is_date_close(d1, d2, days=2):
    d1 = datetime.strptime(d1, "%Y-%m-%d")
    d2 = datetime.strptime(d2, "%Y-%m-%d")
    return abs((d1 - d2).days) <= days

def match_transactions(bank_data, gl_data):
    matched = []
    unmatched_bank = []
    unmatched_gl = gl_data.copy()

    for b in bank_data:
        found = False

        for g in unmatched_gl:
            confidence = fuzz.ratio(b["description"], g["description"])
            if (b["amount"] == g["amount"] and is_date_close(b["date"], g["date"]) and confidence > 80):
                matched.append({
                    "bank": b,
                    "gl": g,
                    "confidence": confidence
                })
                unmatched_gl.remove(g)
                found = True
                break

        if not found:
            unmatched_bank.append(b)

    return matched, unmatched_bank, unmatched_gl