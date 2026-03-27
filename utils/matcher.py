def match_transactions(bank_data, gl_data):
    matched = []
    unmatched_bank = []
    unmatched_gl = gl_data.copy()

    for b in bank_data:
        found = False

        for g in unmatched_gl:
            if b["amount"] == g["amount"]:
                matched.append((b, g))
                unmatched_gl.remove(g)
                found = True
                break

        if not found:
            unmatched_bank.append(b)

    return matched, unmatched_bank, unmatched_gl