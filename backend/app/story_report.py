"""Story-mode report helpers for evidence packs."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List


def _parse_ts(value: str | None) -> datetime:
    if not value:
        return datetime.now(timezone.utc)
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return datetime.now(timezone.utc)


def _extract_triggered_rules(events: List[Dict[str, Any]]) -> List[str]:
    rules = set()
    for event in events:
        payload = event.get("payload", {})
        outputs = payload.get("outputs") or {}
        for candidate in [payload.get("rule_id"), outputs.get("rule_id")]:
            if candidate:
                rules.add(candidate)
        rulespec = outputs.get("rulespec") or payload.get("rulespec")
        if isinstance(rulespec, dict):
            rule_id = rulespec.get("rule_id")
            if rule_id:
                rules.add(rule_id)
        triggered_rules = outputs.get("triggered_rules") or payload.get("triggered_rules")
        if isinstance(triggered_rules, list):
            for rule_id in triggered_rules:
                if rule_id:
                    rules.add(rule_id)
    return list(rules)


def _stage_markers(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    markers = []
    for event in events:
        if event.get("event_type") != "stage.changed":
            continue
        payload = event.get("payload", {})
        markers.append(
            {
                "stage": payload.get("stage"),
                "step": payload.get("step"),
                "timestamp": event.get("created_at"),
            }
        )
    markers.sort(key=lambda item: _parse_ts(item.get("timestamp")).timestamp())
    return markers


def build_stage_timeline(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    sorted_events = sorted(events, key=lambda item: _parse_ts(item.get("created_at")).timestamp())
    markers = _stage_markers(sorted_events)
    if not markers:
        return []

    timeline = []
    for idx, marker in enumerate(markers):
        start_ts = _parse_ts(marker.get("timestamp"))
        end_ts = _parse_ts(markers[idx + 1]["timestamp"]) if idx + 1 < len(markers) else None
        stage_events = [
            event
            for event in sorted_events
            if _parse_ts(event.get("created_at")) >= start_ts
            and (end_ts is None or _parse_ts(event.get("created_at")) < end_ts)
        ]
        rules = _extract_triggered_rules(stage_events)
        artifact_events = [event for event in stage_events if event.get("event_type") in {"agent.output", "orchestrator.output"}]
        timeline.append(
            {
                "stage": marker.get("stage"),
                "step": marker.get("step"),
                "started_at": marker.get("timestamp"),
                "ended_at": end_ts.isoformat() if end_ts else None,
                "event_count": len(stage_events),
                "artifact_count": len(artifact_events),
                "triggered_rules": rules,
            }
        )
    return timeline


def build_stage_diffs(timeline: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    diffs = []
    for idx in range(1, len(timeline)):
        prev = timeline[idx - 1]
        curr = timeline[idx]
        diffs.append(
            {
                "from": prev.get("stage"),
                "to": curr.get("stage"),
                "delta_events": curr.get("event_count", 0) - prev.get("event_count", 0),
                "delta_artifacts": curr.get("artifact_count", 0) - prev.get("artifact_count", 0),
                "rules_added": list(set(curr.get("triggered_rules", [])) - set(prev.get("triggered_rules", []))),
                "rules_removed": list(set(prev.get("triggered_rules", [])) - set(curr.get("triggered_rules", []))),
            }
        )
    return diffs


def build_story_report(
    pack: Dict[str, Any],
    run: Dict[str, Any] | None,
    events: List[Dict[str, Any]],
    approvals: List[Dict[str, Any]],
) -> Dict[str, Any]:
    timeline = build_stage_timeline(events)
    if not timeline:
        summaries = pack.get("stage_summaries", []) or []
        if summaries:
            ordered = sorted(summaries, key=lambda item: _parse_ts(item.get("timestamp")).timestamp())
            timeline = []
            for idx, entry in enumerate(ordered):
                started_at = entry.get("timestamp")
                next_entry = ordered[idx + 1] if idx + 1 < len(ordered) else None
                ended_at = next_entry.get("timestamp") if next_entry else None
                timeline.append(
                    {
                        "stage": entry.get("stage"),
                        "step": entry.get("step"),
                        "started_at": started_at,
                        "ended_at": ended_at,
                        "event_count": entry.get("event_count", 0),
                        "artifact_count": entry.get("artifact_count", 0),
                        "triggered_rules": entry.get("triggered_rules", []) or [],
                    }
                )
    diffs = build_stage_diffs(timeline)
    workflow_history = (run or {}).get("workflow_history", [])
    return {
        "pack_id": pack.get("id"),
        "run_id": pack.get("run_id"),
        "battle_id": pack.get("battle_id"),
        "narrative": pack.get("narrative"),
        "workflow_state": (run or {}).get("workflow_state", pack.get("workflow_state")),
        "workflow_history": workflow_history,
        "timeline": timeline,
        "diffs": diffs,
        "approvals": approvals,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }


def build_story_markdown(report: Dict[str, Any]) -> str:
    lines = [
        f"# Story Report — Evidence Pack {report.get('pack_id', '')}",
        "",
        f"Run: {report.get('run_id') or 'N/A'}",
        f"Battle: {report.get('battle_id') or 'N/A'}",
        f"Workflow State: {report.get('workflow_state') or 'N/A'}",
        "",
        "## Narrative",
        report.get("narrative") or "No narrative provided.",
        "",
        "## Stage Timeline",
    ]
    timeline = report.get("timeline", [])
    if timeline:
        lines.append("| Stage | Step | Started | Ended | Events | Artifacts | Triggered Rules |")
        lines.append("| --- | --- | --- | --- | --- | --- | --- |")
        for entry in timeline:
            rules = ", ".join(entry.get("triggered_rules", [])) or "-"
            lines.append(
                f"| {entry.get('stage') or '-'} | {entry.get('step') or '-'} | {entry.get('started_at') or '-'} | {entry.get('ended_at') or '-'} | {entry.get('event_count', 0)} | {entry.get('artifact_count', 0)} | {rules} |"
            )
    else:
        lines.append("No stage timeline available.")

    lines.extend(["", "## Diffs"])
    diffs = report.get("diffs", [])
    if diffs:
        for diff in diffs:
            added = ", ".join(diff.get("rules_added", [])) or "-"
            removed = ", ".join(diff.get("rules_removed", [])) or "-"
            lines.append(
                f"- {diff.get('from')} → {diff.get('to')}: events {diff.get('delta_events')}, artifacts {diff.get('delta_artifacts')}, rules +[{added}] -[{removed}]"
            )
    else:
        lines.append("No diffs available.")

    lines.extend(["", "## Approvals"])
    approvals = report.get("approvals", [])
    if approvals:
        for approval in approvals:
            stage = approval.get("stage") or approval.get("approval_action") or "Approval"
            approver = approval.get("approver_id") or approval.get("requestor_id") or "Unknown"
            status = approval.get("status") or "pending"
            timestamp = approval.get("timestamp") or approval.get("created_at") or ""
            lines.append(f"- {stage}: {status} by {approver} ({timestamp})")
    else:
        lines.append("No approvals recorded.")

    lines.extend(["", "## Workflow History"])
    history = report.get("workflow_history", [])
    if history:
        for entry in history:
            state = entry.get("state")
            actor = entry.get("actor_id")
            note = entry.get("notes")
            timestamp = entry.get("timestamp")
            lines.append(f"- {state} by {actor} at {timestamp}. {note or ''}")
    else:
        lines.append("No workflow history recorded.")

    return "\n".join(lines)
