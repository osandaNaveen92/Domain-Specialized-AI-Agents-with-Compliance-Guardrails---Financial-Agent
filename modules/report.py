from reportlab.platypus import SimpleDocTemplate, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

def generate_audit_report(entries):
    doc = SimpleDocTemplate("audit_report.pdf")
    styles = getSampleStyleSheet()

    content = []

    for e in entries:
        text = f"""
        Entry: {e['entry_id']}<br/>
        Amount: {e['amount']}<br/>
        Status: {e['status']}<br/>
        Explanation: {e.get('explanation', '')}<br/><br/>
        """
        content.append(Paragraph(text, styles["Normal"]))

    doc.build(content)