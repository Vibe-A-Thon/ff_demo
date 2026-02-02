"""PDF export helpers for evidence packs."""

from __future__ import annotations

from io import BytesIO
from typing import Any, Dict, List

def _load_reportlab():
    try:
        from reportlab.lib.pagesizes import LETTER  # type: ignore
        from reportlab.lib.styles import getSampleStyleSheet  # type: ignore
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer  # type: ignore
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("reportlab is required for PDF exports") from exc
    return LETTER, getSampleStyleSheet, SimpleDocTemplate, Paragraph, Spacer


def _format_list(items: List[str]) -> str:
    if not items:
        return "None"
    return ", ".join(items)


def _format_kv_block(payload: Dict[str, Any]) -> str:
    lines = []
    for key, value in payload.items():
        lines.append(f"{key}: {value}")
    return "<br />".join(lines) if lines else "None"


def build_evidence_pack_pdf(pack: Dict[str, Any]) -> bytes:
    """Render an evidence pack as PDF.

    Args:
        pack: Evidence pack payload.

    Returns:
        bytes: PDF bytes.
    """
    LETTER, getSampleStyleSheet, SimpleDocTemplate, Paragraph, Spacer = _load_reportlab()
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Evidence Pack {pack.get('id', '')}", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Summary", styles["Heading2"]))
    story.append(Paragraph(pack.get("narrative", "No narrative provided."), styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Triggered Rules", styles["Heading2"]))
    story.append(Paragraph(_format_list(pack.get("triggered_rules", [])), styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Contributing Factors", styles["Heading2"]))
    factors = pack.get("contributing_factors", [])
    if factors:
        for factor in factors:
            story.append(Paragraph(_format_kv_block(factor), styles["BodyText"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("None", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Approvals", styles["Heading2"]))
    approvals = pack.get("approvals", [])
    if approvals:
        for approval in approvals:
            story.append(Paragraph(_format_kv_block(approval), styles["BodyText"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("None", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Metrics", styles["Heading2"]))
    story.append(Paragraph(_format_kv_block(pack.get("metrics", {})), styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Checksum", styles["Heading2"]))
    story.append(Paragraph(str(pack.get("checksum", "")), styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Checksum Chain", styles["Heading2"]))
    chain = pack.get("checksum_chain", [])
    if chain:
        for entry in chain:
            story.append(Paragraph(_format_kv_block(entry), styles["BodyText"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("None", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Evidence Logs", styles["Heading2"]))
    logs = pack.get("logs", [])
    if logs:
        for log in logs[:50]:
            story.append(Paragraph(_format_kv_block(log), styles["BodyText"]))
            story.append(Spacer(1, 3))
    else:
        story.append(Paragraph("None", styles["BodyText"]))

    document = SimpleDocTemplate(buffer, pagesize=LETTER)
    document.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf


def build_story_report_pdf(report: Dict[str, Any]) -> bytes:
    """Render a story report as PDF.

    Args:
        report: Story report payload.

    Returns:
        bytes: PDF bytes.
    """
    LETTER, getSampleStyleSheet, SimpleDocTemplate, Paragraph, Spacer = _load_reportlab()
    buffer = BytesIO()
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph(f"Story Report {report.get('pack_id', '')}", styles["Title"]))
    story.append(Spacer(1, 12))

    story.append(Paragraph("Narrative", styles["Heading2"]))
    story.append(Paragraph(report.get("narrative") or "No narrative provided.", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Stage Timeline", styles["Heading2"]))
    timeline = report.get("timeline", [])
    if timeline:
        for entry in timeline:
            summary = {
                "stage": entry.get("stage"),
                "step": entry.get("step"),
                "started_at": entry.get("started_at"),
                "ended_at": entry.get("ended_at"),
                "events": entry.get("event_count"),
                "artifacts": entry.get("artifact_count"),
                "rules": ", ".join(entry.get("triggered_rules", [])) or "-",
            }
            story.append(Paragraph(_format_kv_block(summary), styles["BodyText"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No timeline available.", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Diffs", styles["Heading2"]))
    diffs = report.get("diffs", [])
    if diffs:
        for diff in diffs:
            diff_summary = {
                "from": diff.get("from"),
                "to": diff.get("to"),
                "delta_events": diff.get("delta_events"),
                "delta_artifacts": diff.get("delta_artifacts"),
                "rules_added": ", ".join(diff.get("rules_added", [])) or "-",
                "rules_removed": ", ".join(diff.get("rules_removed", [])) or "-",
            }
            story.append(Paragraph(_format_kv_block(diff_summary), styles["BodyText"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No diffs available.", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Approvals", styles["Heading2"]))
    approvals = report.get("approvals", [])
    if approvals:
        for approval in approvals:
            story.append(Paragraph(_format_kv_block(approval), styles["BodyText"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No approvals recorded.", styles["BodyText"]))
    story.append(Spacer(1, 10))

    story.append(Paragraph("Workflow History", styles["Heading2"]))
    history = report.get("workflow_history", [])
    if history:
        for entry in history:
            story.append(Paragraph(_format_kv_block(entry), styles["BodyText"]))
            story.append(Spacer(1, 4))
    else:
        story.append(Paragraph("No workflow history recorded.", styles["BodyText"]))

    document = SimpleDocTemplate(buffer, pagesize=LETTER)
    document.build(story)
    pdf = buffer.getvalue()
    buffer.close()
    return pdf
