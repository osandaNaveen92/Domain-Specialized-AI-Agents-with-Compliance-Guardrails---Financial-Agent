from typing import Dict, List


class GovernanceEngine:
    def __init__(
        self,
        l1_threshold: float = 10000,
        l2_threshold: float = 50000,
        l3_threshold: float = 250000,
        low_confidence_threshold: float = 70.0,
    ) -> None:
        self.l1_threshold = l1_threshold
        self.l2_threshold = l2_threshold
        self.l3_threshold = l3_threshold
        self.low_confidence_threshold = low_confidence_threshold

    def _level_for_amount(self, amount: float) -> str:
        amount = abs(amount)
        if amount > self.l3_threshold:
            return "L3"
        if amount > self.l2_threshold:
            return "L2"
        if amount > self.l1_threshold:
            return "L1"
        return "L0"

    def evaluate_entry(self, entry: Dict) -> Dict:
        reasons: List[str] = []
        amount = float(entry.get("amount", 0))
        risk_score = int(entry.get("risk", {}).get("score", 0))
        confidence = float(entry.get("match_confidence", 100.0))

        approval_level = self._level_for_amount(amount)
        if approval_level != "L0":
            reasons.append(f"Materiality gate {approval_level} triggered")

        if risk_score >= 40:
            reasons.append("High risk score requires reviewer sign-off")

        if confidence < self.low_confidence_threshold:
            reasons.append("Low confidence requires human verification")

        if entry.get("control_summary", {}).get("failed", 0) > 0:
            reasons.append("Control failures detected")

        requires_human_review = len(reasons) > 0
        queue_status = "PENDING_REVIEW" if requires_human_review else "AUTO_CLEARED"

        decision = {
            "approval_level": approval_level,
            "requires_human_review": requires_human_review,
            "queue_status": queue_status,
            "reasons": reasons,
        }

        updated = dict(entry)
        updated["governance"] = decision

        if requires_human_review and updated.get("status") not in {"APPROVED", "REJECTED"}:
            updated["status"] = "PENDING_REVIEW"
        elif not requires_human_review and updated.get("status") == "REVIEW_REQUIRED":
            updated["status"] = "READY_FOR_APPROVAL"

        return updated

    def apply(self, entries: List[Dict]) -> List[Dict]:
        return [self.evaluate_entry(entry) for entry in entries]

