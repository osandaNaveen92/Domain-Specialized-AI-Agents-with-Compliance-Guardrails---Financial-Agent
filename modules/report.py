from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_audit_report(entries):
    doc = SimpleDocTemplate("audit_report.pdf")
    styles = getSampleStyleSheet()

    content = []
    content.append(Paragraph("Financial Close Audit Report", styles["Title"]))

    framework_summary = {}
    risk_summary = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0, "NONE": 0}
    approvals = 0
    rejections = 0

    for e in entries:
        for result in e.get("control_results", []):
            fw = result.get("framework", "UNKNOWN")
            if fw not in framework_summary:
                framework_summary[fw] = {"PASS": 0, "FAIL": 0}
            framework_summary[fw][result.get("status", "PASS")] += 1

        priority = e.get("risk", {}).get("priority", "NONE")
        if priority not in risk_summary:
            risk_summary[priority] = 0
        risk_summary[priority] += 1

        if e.get("status") == "APPROVED":
            approvals += 1
        if e.get("status") == "REJECTED":
            rejections += 1

    content.append(Paragraph("<br/><b>Framework Control Summary</b>", styles["Heading2"]))
    if framework_summary:
        for fw, counts in framework_summary.items():
            content.append(
                Paragraph(f"{fw}: PASS {counts['PASS']} | FAIL {counts['FAIL']}", styles["Normal"])
            )
    else:
        content.append(Paragraph("No control results available.", styles["Normal"]))

    content.append(Paragraph("<br/><b>Risk Summary</b>", styles["Heading2"]))
    content.append(
        Paragraph(
            " | ".join(f"{k}: {v}" for k, v in risk_summary.items()),
            styles["Normal"],
        )
    )

    content.append(Paragraph("<br/><b>Approval Summary</b>", styles["Heading2"]))
    content.append(Paragraph(f"Approved: {approvals} | Rejected: {rejections}", styles["Normal"]))
    content.append(Paragraph("<br/><b>Entry Details</b>", styles["Heading2"]))

    for e in entries:
        failed_controls = [
            r.get("control_id") for r in e.get("control_results", []) if r.get("status") == "FAIL"
        ]
        approved_by = e.get("approved_by") or e.get("rejected_by") or "-"
        text = f"""
        Entry: {e['entry_id']}<br/>
        Amount: {e['amount']}<br/>
        Status: {e['status']}<br/>
        Risk: {e.get('risk', {}).get('priority', 'NONE')} ({e.get('risk', {}).get('score', 0)})<br/>
        Approved/Rejected By: {approved_by}<br/>
        Failed Controls: {", ".join(failed_controls) if failed_controls else "None"}<br/>
        Explanation: {e.get('explanation', '')}<br/><br/>
        """
        content.append(Paragraph(text, styles["Normal"]))

    doc.build(content)
