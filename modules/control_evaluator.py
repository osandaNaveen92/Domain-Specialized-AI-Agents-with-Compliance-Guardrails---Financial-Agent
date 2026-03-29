from modules.rule_engine import evaluate_rule

SEVERITY_WEIGHTS = {
    "HIGH": 35,
    "MEDIUM": 20,
    "LOW": 10,
}


def _priority_from_score(score):
    if score >= 70:
        return "CRITICAL"
    if score >= 40:
        return "HIGH"
    if score >= 15:
        return "MEDIUM"
    return "LOW" if score > 0 else "NONE"


def apply_controls(entries, controls, context=None):
    results = []
    context = context or {}

    for entry in entries:
        entry = dict(entry)
        entry.setdefault("is_unmatched", entry.get("source") in {"bank", "gl"})
        entry.setdefault("is_complete", bool(entry.get("reason")) and entry.get("amount") is not None)
        entry_results = []

        for control in controls:
            passed = evaluate_rule(entry, control, context=context)

            entry_results.append({
                "control_id": control["control_id"],
                "framework": control["framework"],
                "description": control["description"],
                "status": "PASS" if passed else "FAIL",
                "severity": control["severity"],
                "evidence_required": control["evidence_required"]
            })

        failed_controls = [item for item in entry_results if item["status"] == "FAIL"]
        risk_score = min(
            100,
            sum(SEVERITY_WEIGHTS.get(item.get("severity", "LOW"), 10) for item in failed_controls),
        )

        entry["control_summary"] = {
            "total": len(entry_results),
            "failed": len(failed_controls),
            "passed": len(entry_results) - len(failed_controls),
        }
        entry["risk"] = {
            "score": risk_score,
            "priority": _priority_from_score(risk_score),
        }
        entry["control_results"] = entry_results
        results.append(entry)

    return results
