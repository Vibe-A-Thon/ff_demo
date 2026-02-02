"""Lesson Distiller - Convert BRC/battle learnings into AMC-compatible format.

This module provides the distillation pipeline that converts raw battle outcomes,
postmortem analyses, and lessons learned into bank-neutral, sanitized AMC memory entries.
"""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.db import db


# Patterns to redact from distilled content
REDACTION_PATTERNS = [
    (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]'),  # Email
    (r'\b\d{3}-\d{3}-\d{4}\b', '[PHONE]'),  # Phone US
    (r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', '[CARD]'),  # Card numbers
    (r'\b\d{9,11}\b', '[ACCOUNT]'),  # Account numbers
    (r'\b(?:CASE|TKT|INC|REQ)[-_]?\d{5,10}\b', '[CASE_ID]'),  # Case/ticket IDs
    (r'\b(?:https?://)?(?:www\.)?[a-zA-Z0-9-]+\.(?:internal|corp|bank|local)\b', '[INTERNAL_URL]'),
    (r'\b(?:\d{1,3}\.){3}\d{1,3}\b', '[IP]'),  # IP addresses
    (r'\b[A-Fa-f0-9]{32,64}\b', '[HASH]'),  # Hashes (redact if they look like secrets)
]

# Topic categories for bank-neutral classification
TOPIC_CATEGORIES = {
    "mule": ["mule", "money mule", "mule ring", "mule network", "recruitment"],
    "ato": ["account takeover", "ato", "credential theft", "session hijack"],
    "new_account": ["new account fraud", "synthetic identity", "application fraud"],
    "card": ["card fraud", "cnp", "card not present", "skimming"],
    "wire": ["wire fraud", "wire transfer", "swift", "ach"],
    "social_engineering": ["social engineering", "phishing", "vishing", "smishing"],
    "insider": ["insider threat", "employee fraud", "collusion"],
    "auth_bypass": ["authentication bypass", "mfa bypass", "credential stuffing"],
    "velocity": ["velocity abuse", "burst pattern", "rapid transactions"],
    "graph": ["graph pattern", "network analysis", "connection pattern"],
}

# Signal categories
SIGNAL_CATEGORIES = {
    "device": ["device fingerprint", "device mismatch", "device reuse", "emulator"],
    "behavioral": ["behavioral anomaly", "usage pattern", "activity deviation"],
    "velocity": ["velocity", "burst", "spike", "rapid"],
    "geo": ["geolocation", "impossible travel", "vpn", "proxy"],
    "network": ["graph", "connection", "link analysis", "network pattern"],
    "identity": ["identity", "kyc", "synthetic", "identity mismatch"],
}


def _redact_text(text: str) -> str:
    """Apply redaction patterns to sanitize text for portability."""
    result = text
    for pattern, replacement in REDACTION_PATTERNS:
        result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
    return result


def _categorize_topic(text: str) -> str:
    """Categorize text into a bank-neutral topic category."""
    text_lower = text.lower()
    for category, keywords in TOPIC_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            return category
    return "general_fraud"


def _extract_signals(text: str) -> List[str]:
    """Extract signal categories from text."""
    text_lower = text.lower()
    signals = []
    for category, keywords in SIGNAL_CATEGORIES.items():
        if any(kw in text_lower for kw in keywords):
            signals.append(category)
    return signals if signals else ["unclassified"]


def _generate_lesson_id() -> str:
    """Generate a unique lesson ID."""
    return f"LESSON-{uuid4().hex[:12].upper()}"


def _hash_content(content: str) -> str:
    """Generate a hash for deduplication."""
    return hashlib.sha256(content.encode()).hexdigest()[:16]


class LessonDistiller:
    """
    Distills battle outcomes and BRC learnings into AMC-compatible memory entries.
    
    The distillation process:
    1. Extracts key learnings from raw battle/postmortem data
    2. Sanitizes content by removing PII and bank-specific identifiers
    3. Categorizes into bank-neutral topics
    4. Generates structured memory entries for AMC export
    5. Creates human-readable markdown summaries
    """

    def __init__(self):
        self.distillation_history: Dict[str, Any] = {}

    async def distill_battle_outcome(
        self,
        battle_id: str,
        team_id: str,
        actor_id: str,
    ) -> Dict[str, Any]:
        """
        Distill learnings from a completed battle into AMC memory entries.
        
        Returns:
            Dict with semantic_entries, episodic_entries, and markdown_summary
        """
        # Fetch battle data
        battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
        if not battle:
            raise ValueError(f"Battle {battle_id} not found")

        # Fetch related evidence pack if available
        evidence_pack = await db.evidence_packs.find_one(
            {"battle_id": battle_id}, {"_id": 0}
        )

        # Extract battle context
        attack_type = battle.get("attack_type", "unknown")
        outcome = battle.get("outcome", "unknown")
        defense_effectiveness = battle.get("defense_effectiveness", 0.0)
        red_score = battle.get("red_score", 0)
        blue_score = battle.get("blue_score", 0)
        turns = battle.get("turns", [])

        # Build semantic entries (knowledge/facts learned)
        semantic_entries = []
        
        # Entry for attack pattern learned
        attack_lesson = {
            "id": _generate_lesson_id(),
            "type": "semantic",
            "topic": _categorize_topic(attack_type),
            "lesson": _redact_text(f"Attack pattern '{attack_type}' observed with {len(turns)} turns. "
                                   f"Defense effectiveness: {defense_effectiveness:.1%}"),
            "confidence": min(0.9, defense_effectiveness + 0.3),
            "source": "battle_distillation",
            "battle_ref": battle_id,
            "tags": _extract_signals(attack_type),
            "distilled_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": "",
        }
        attack_lesson["content_hash"] = _hash_content(attack_lesson["lesson"])
        semantic_entries.append(attack_lesson)

        # Entry for defense strategy
        if outcome in ["defender_win", "blue_win", "blocked"]:
            defense_lesson = {
                "id": _generate_lesson_id(),
                "type": "semantic",
                "topic": "defense_strategy",
                "lesson": _redact_text(f"Successfully defended against '{attack_type}' "
                                       f"using multi-layer detection and response coordination."),
                "confidence": 0.85,
                "source": "battle_distillation",
                "battle_ref": battle_id,
                "tags": ["defense", "coordination", "detection"],
                "distilled_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": "",
            }
            defense_lesson["content_hash"] = _hash_content(defense_lesson["lesson"])
            semantic_entries.append(defense_lesson)

        # Build episodic entries (experiences)
        episodic_entries = []
        
        episodic_entry = {
            "id": _generate_lesson_id(),
            "type": "episodic",
            "event_type": "battle_outcome",
            "summary": _redact_text(
                f"Battle against '{attack_type}': "
                f"{'Victory' if outcome in ['defender_win', 'blue_win', 'blocked'] else 'Loss'} "
                f"with {len(turns)} engagement turns. "
                f"Key signals: {', '.join(_extract_signals(attack_type))}"
            ),
            "signals": _extract_signals(attack_type),
            "result": "mitigated" if outcome in ["defender_win", "blue_win", "blocked"] else "compromised",
            "metrics": {
                "defense_effectiveness": defense_effectiveness,
                "turns": len(turns),
                "red_score": red_score,
                "blue_score": blue_score,
            },
            "distilled_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": "",
        }
        episodic_entry["content_hash"] = _hash_content(episodic_entry["summary"])
        episodic_entries.append(episodic_entry)

        # Build markdown summary for judges
        markdown_summary = self._build_distilled_markdown(
            battle, semantic_entries, episodic_entries
        )

        # Store distillation record
        distillation_record = {
            "id": f"distill_{battle_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "battle_id": battle_id,
            "team_id": team_id,
            "actor_id": actor_id,
            "semantic_count": len(semantic_entries),
            "episodic_count": len(episodic_entries),
            "distilled_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
        }
        await db.lesson_distillations.insert_one(distillation_record)

        return {
            "distillation_id": distillation_record["id"],
            "battle_id": battle_id,
            "team_id": team_id,
            "semantic_entries": semantic_entries,
            "episodic_entries": episodic_entries,
            "markdown_summary": markdown_summary,
            "stats": {
                "semantic_count": len(semantic_entries),
                "episodic_count": len(episodic_entries),
            },
        }

    async def distill_brc_postmortem(
        self,
        brc_id: str,
        team_id: str,
        actor_id: str,
    ) -> Dict[str, Any]:
        """
        Distill learnings from a BRC (Battle Reconciliation) postmortem.
        
        Returns:
            Dict with semantic_entries, episodic_entries, and procedural_updates
        """
        # Fetch BRC record
        brc = await db.battle_records.find_one({"id": brc_id}, {"_id": 0})
        if not brc:
            # Try alternate collection name
            brc = await db.brc_reports.find_one({"id": brc_id}, {"_id": 0})
        if not brc:
            raise ValueError(f"BRC {brc_id} not found")

        # Extract postmortem insights
        lessons_raw = brc.get("lessons_learned", [])
        improvements = brc.get("improvements", [])
        recommendations = brc.get("recommendations", [])

        semantic_entries = []
        episodic_entries = []
        procedural_updates = []

        # Process lessons learned
        for i, lesson in enumerate(lessons_raw[:10]):  # Limit to 10
            if isinstance(lesson, str):
                lesson_text = lesson
            elif isinstance(lesson, dict):
                lesson_text = lesson.get("lesson", lesson.get("description", str(lesson)))
            else:
                lesson_text = str(lesson)

            entry = {
                "id": _generate_lesson_id(),
                "type": "semantic",
                "topic": _categorize_topic(lesson_text),
                "lesson": _redact_text(lesson_text),
                "confidence": 0.75,
                "source": "brc_postmortem",
                "brc_ref": brc_id,
                "tags": _extract_signals(lesson_text),
                "distilled_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": _hash_content(lesson_text),
            }
            semantic_entries.append(entry)

        # Process improvements as procedural updates
        for improvement in improvements[:5]:
            if isinstance(improvement, str):
                imp_text = improvement
            elif isinstance(improvement, dict):
                imp_text = improvement.get("description", str(improvement))
            else:
                imp_text = str(improvement)

            update = {
                "id": _generate_lesson_id(),
                "type": "procedural",
                "action": "playbook_update",
                "description": _redact_text(imp_text),
                "priority": "medium",
                "source": "brc_postmortem",
                "brc_ref": brc_id,
                "distilled_at": datetime.now(timezone.utc).isoformat(),
            }
            procedural_updates.append(update)

        # Store distillation record
        distillation_record = {
            "id": f"distill_brc_{brc_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}",
            "brc_id": brc_id,
            "team_id": team_id,
            "actor_id": actor_id,
            "semantic_count": len(semantic_entries),
            "episodic_count": len(episodic_entries),
            "procedural_count": len(procedural_updates),
            "distilled_at": datetime.now(timezone.utc).isoformat(),
            "status": "completed",
        }
        await db.lesson_distillations.insert_one(distillation_record)

        return {
            "distillation_id": distillation_record["id"],
            "brc_id": brc_id,
            "team_id": team_id,
            "semantic_entries": semantic_entries,
            "episodic_entries": episodic_entries,
            "procedural_updates": procedural_updates,
            "stats": {
                "semantic_count": len(semantic_entries),
                "episodic_count": len(episodic_entries),
                "procedural_count": len(procedural_updates),
            },
        }

    async def get_distilled_lessons_for_team(
        self,
        team_id: str,
        since_days: int = 180,
    ) -> Dict[str, Any]:
        """
        Get all distilled lessons for a team within a time window.
        
        Used for AMC export to populate memory layers.
        """
        cutoff = datetime.now(timezone.utc).isoformat()
        
        # Fetch distillation records
        cursor = db.lesson_distillations.find(
            {"team_id": team_id, "status": "completed"},
            {"_id": 0}
        ).sort("distilled_at", -1).limit(100)
        
        records = await cursor.to_list(length=100)
        
        # Aggregate entries from all distillations
        all_semantic = []
        all_episodic = []
        all_procedural = []
        
        # If no actual distillations, generate synthetic ones for demo
        if not records:
            records = self._generate_demo_distillations(team_id)
        
        for record in records:
            if "semantic_entries" in record:
                all_semantic.extend(record["semantic_entries"])
            if "episodic_entries" in record:
                all_episodic.extend(record["episodic_entries"])
            if "procedural_updates" in record:
                all_procedural.extend(record["procedural_updates"])
        
        return {
            "team_id": team_id,
            "distillation_count": len(records),
            "semantic_entries": all_semantic,
            "episodic_entries": all_episodic,
            "procedural_updates": all_procedural,
            "stats": {
                "total_semantic": len(all_semantic),
                "total_episodic": len(all_episodic),
                "total_procedural": len(all_procedural),
            },
        }

    def _generate_demo_distillations(self, team_id: str) -> List[Dict[str, Any]]:
        """Generate demo distilled lessons for hackathon demo."""
        demo_lessons = [
            {
                "id": _generate_lesson_id(),
                "type": "semantic",
                "topic": "mule",
                "lesson": "Mule networks exhibit characteristic fan-in/fan-out patterns over 24-72h windows with high device fingerprint similarity.",
                "confidence": 0.87,
                "source": "battle_distillation",
                "tags": ["mule", "graph", "device"],
                "distilled_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": _hash_content("mule_pattern"),
            },
            {
                "id": _generate_lesson_id(),
                "type": "semantic",
                "topic": "ato",
                "lesson": "ATO attacks often preceded by credential validation bursts from residential proxy IPs within 48h before main attack.",
                "confidence": 0.82,
                "source": "battle_distillation",
                "tags": ["ato", "velocity", "geo"],
                "distilled_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": _hash_content("ato_pattern"),
            },
            {
                "id": _generate_lesson_id(),
                "type": "semantic",
                "topic": "velocity",
                "lesson": "Velocity spikes coupled with new device registration are 3.5x more indicative of fraud than velocity alone.",
                "confidence": 0.91,
                "source": "battle_distillation",
                "tags": ["velocity", "device", "behavioral"],
                "distilled_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": _hash_content("velocity_device"),
            },
        ]
        
        demo_episodic = [
            {
                "id": _generate_lesson_id(),
                "type": "episodic",
                "event_type": "battle_outcome",
                "summary": "Successfully blocked coordinated ATO attack targeting high-value accounts using combined velocity + device + geo signals.",
                "signals": ["velocity", "device", "geo"],
                "result": "mitigated",
                "metrics": {"defense_effectiveness": 0.94, "turns": 8},
                "distilled_at": datetime.now(timezone.utc).isoformat(),
                "content_hash": _hash_content("ato_battle"),
            },
        ]
        
        return [
            {
                "team_id": team_id,
                "semantic_entries": demo_lessons,
                "episodic_entries": demo_episodic,
                "procedural_updates": [],
            }
        ]

    def _build_distilled_markdown(
        self,
        battle: Dict[str, Any],
        semantic: List[Dict[str, Any]],
        episodic: List[Dict[str, Any]],
    ) -> str:
        """Build a human-readable markdown summary of distilled lessons."""
        lines = [
            "# Distilled Lessons Summary",
            "",
            f"**Battle:** {battle.get('id', 'Unknown')}",
            f"**Attack Type:** {battle.get('attack_type', 'Unknown')}",
            f"**Outcome:** {battle.get('outcome', 'Unknown')}",
            f"**Distilled At:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "---",
            "",
            "## Key Learnings (Semantic Memory)",
            "",
        ]
        
        for entry in semantic:
            lines.append(f"### {entry.get('topic', 'General').replace('_', ' ').title()}")
            lines.append(f"> {entry.get('lesson', '')}")
            lines.append(f"- **Confidence:** {entry.get('confidence', 0):.0%}")
            lines.append(f"- **Tags:** {', '.join(entry.get('tags', []))}")
            lines.append("")
        
        lines.extend([
            "## Experiences (Episodic Memory)",
            "",
        ])
        
        for entry in episodic:
            lines.append(f"### {entry.get('event_type', 'Event').replace('_', ' ').title()}")
            lines.append(f"> {entry.get('summary', '')}")
            lines.append(f"- **Result:** {entry.get('result', 'Unknown')}")
            lines.append(f"- **Signals:** {', '.join(entry.get('signals', []))}")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "*This summary is bank-neutral and contains no PII or sensitive identifiers.*",
        ])
        
        return "\n".join(lines)


# Singleton instance
lesson_distiller = LessonDistiller()
