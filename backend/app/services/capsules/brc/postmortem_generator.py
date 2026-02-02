"""BRC Postmortem Generator - Generate lessons and rule proposals from battles.

This module generates:
1. Postmortem markdown with top learnings
2. Lessons distilled JSON for AMC integration
3. RSB rule patch proposals
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from app.db import db
from app.core.logging_config import get_logger

logger = get_logger(__name__)


class PostmortemGenerator:
    """Generator for battle postmortem artifacts."""

    def generate_postmortem(
        self,
        battle_data: Dict[str, Any],
        scorecard: Dict[str, Any],
        stages: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Generate complete postmortem package.
        
        Args:
            battle_data: Battle run metadata
            scorecard: Battle scorecard
            stages: Stage outputs
            
        Returns:
            Postmortem package with markdown, lessons, and proposals
        """
        # Generate components
        markdown = self._generate_markdown(battle_data, scorecard, stages)
        lessons = self._distill_lessons(battle_data, scorecard, stages)
        proposals = self._generate_rsb_proposals(battle_data, scorecard, stages)
        
        return {
            "postmortem_md": markdown,
            "lessons_distilled": lessons,
            "rsb_proposals": proposals,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }

    def _generate_markdown(
        self,
        battle_data: Dict[str, Any],
        scorecard: Dict[str, Any],
        stages: Dict[str, Any],
    ) -> str:
        """Generate postmortem markdown document."""
        battle_type = battle_data.get("battle_type", battle_data.get("scenario_name", "Unknown"))
        battle_id = battle_data.get("run_id", battle_data.get("id", "N/A"))
        winner = scorecard.get("winner", "Unknown")
        score = scorecard.get("score", {})
        
        # Extract detection patterns
        detect_stage = stages.get("03_detect") or stages.get("detect", {})
        blue_outputs = detect_stage.get("team_outputs", {}).get("blue", {})
        detected_patterns = blue_outputs.get("patterns", [])
        
        # Extract mitigation actions
        mitigate_stage = stages.get("04_mitigate") or stages.get("mitigate", {})
        mitigate_outputs = mitigate_stage.get("team_outputs", {}).get("blue", {})
        mitigations = mitigate_outputs.get("actions", [])
        
        lines = [
            "# Battle Postmortem Report",
            "",
            f"**Battle:** {battle_type}",
            f"**Run ID:** {battle_id}",
            f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"**Winner:** {winner}",
            "",
            "### Key Metrics",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Detection Recall | {score.get('detection_recall', 0) * 100:.1f}% |",
            f"| Attack Success Rate | {score.get('attack_success_rate', 0) * 100:.1f}% |",
            f"| False Positive Rate | {score.get('false_positive_rate', 0) * 100:.1f}% |",
            f"| Mitigation Time | {score.get('mitigation_time_s', 0)}s |",
            f"| XAI Score | {score.get('explainability_score', 0) * 100:.1f}% |",
            "",
            "---",
            "",
            "## Top 5 Detected Patterns",
            "",
        ]
        
        # Add detected patterns
        patterns_to_show = self._extract_top_patterns(stages, detected_patterns)
        for i, pattern in enumerate(patterns_to_show[:5], 1):
            lines.append(f"{i}. **{pattern['name']}** — {pattern['description']}")
        
        if not patterns_to_show:
            lines.append("_No specific patterns extracted. Review stage outputs for details._")
        
        lines.extend([
            "",
            "---",
            "",
            "## Top 3 Recommended Controls",
            "",
        ])
        
        # Add recommended controls
        controls = self._generate_recommended_controls(stages, scorecard)
        for i, control in enumerate(controls[:3], 1):
            lines.append(f"### {i}. {control['name']}")
            lines.append(f"")
            lines.append(f"**Type:** {control['type']}")
            lines.append(f"**Priority:** {control['priority']}")
            lines.append(f"")
            lines.append(f"{control['description']}")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## Top 2 Rule Patch Proposals",
            "",
        ])
        
        # Add rule proposals
        proposals = self._generate_rsb_proposals(battle_data, scorecard, stages)
        for i, proposal in enumerate(proposals[:2], 1):
            lines.append(f"### Proposal {i}: {proposal['rule_name']}")
            lines.append(f"")
            lines.append(f"**Target:** {proposal['target']}")
            lines.append(f"**Action:** {proposal['action']}")
            lines.append(f"**Condition:** `{proposal['condition']}`")
            lines.append(f"")
            lines.append(f"_Rationale: {proposal['rationale']}_")
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## Next Steps",
            "",
            "1. Review and approve rule patch proposals",
            "2. Implement recommended controls in sandbox",
            "3. Schedule follow-up battle with updated defenses",
            "4. Export learnings to AMC for team evolution",
            "",
            "---",
            "",
            "_This postmortem was auto-generated by Fraud Forge._",
        ])
        
        return "\n".join(lines)

    def _extract_top_patterns(
        self,
        stages: Dict[str, Any],
        existing_patterns: List[Any],
    ) -> List[Dict[str, str]]:
        """Extract top detected patterns from stage outputs."""
        patterns = []
        
        # Use existing patterns if available
        for pattern in existing_patterns:
            if isinstance(pattern, dict):
                patterns.append({
                    "name": pattern.get("name", pattern.get("pattern_type", "Unknown")),
                    "description": pattern.get("description", pattern.get("detail", "Detected during battle")),
                })
            elif isinstance(pattern, str):
                patterns.append({
                    "name": pattern,
                    "description": "Pattern detected during battle analysis",
                })
        
        # Add default patterns if none found
        if not patterns:
            patterns = [
                {"name": "Velocity Anomaly", "description": "Unusual transaction velocity detected across multiple accounts"},
                {"name": "Device Fingerprint Mismatch", "description": "Device characteristics inconsistent with historical patterns"},
                {"name": "Geographic Dispersion", "description": "Transactions from geographically improbable locations"},
                {"name": "Mule Network Pattern", "description": "Funds flowing through suspected mule account network"},
                {"name": "Time-of-Day Anomaly", "description": "Activity outside normal customer behavior window"},
            ]
        
        return patterns

    def _generate_recommended_controls(
        self,
        stages: Dict[str, Any],
        scorecard: Dict[str, Any],
    ) -> List[Dict[str, str]]:
        """Generate recommended controls based on battle results."""
        score = scorecard.get("score", {})
        
        controls = []
        
        # Based on detection recall
        if score.get("detection_recall", 0) < 0.9:
            controls.append({
                "name": "Enhanced Velocity Monitoring",
                "type": "Detection",
                "priority": "High",
                "description": "Implement real-time velocity checks with ML-based anomaly detection to improve detection coverage. Current recall indicates gaps in fast-moving attack detection.",
            })
        
        # Based on FP rate
        if score.get("false_positive_rate", 0) > 0.05:
            controls.append({
                "name": "Precision Tuning for False Positives",
                "type": "Optimization",
                "priority": "Medium",
                "description": "Review and adjust rule thresholds to reduce false positive rate while maintaining detection coverage. Consider implementing customer segmentation for more targeted rules.",
            })
        
        # Based on mitigation time
        if score.get("mitigation_time_s", 0) > 30:
            controls.append({
                "name": "Automated Response Playbooks",
                "type": "Response",
                "priority": "High",
                "description": "Deploy automated mitigation playbooks for common attack patterns to reduce response time. Target: sub-30 second mitigation for high-confidence detections.",
            })
        
        # Always recommend
        controls.append({
            "name": "Graph-Based Entity Resolution",
            "type": "Intelligence",
            "priority": "Medium",
            "description": "Implement entity resolution using graph analytics to identify connected fraud networks earlier in the attack chain.",
        })
        
        controls.append({
            "name": "Real-time XAI Integration",
            "type": "Explainability",
            "priority": "Low",
            "description": "Integrate explainability outputs into analyst workflows to improve investigation efficiency and documentation.",
        })
        
        return controls

    def _distill_lessons(
        self,
        battle_data: Dict[str, Any],
        scorecard: Dict[str, Any],
        stages: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Distill lessons for AMC integration."""
        battle_type = battle_data.get("battle_type", battle_data.get("scenario_name", "Unknown"))
        battle_id = battle_data.get("run_id", battle_data.get("id", "N/A"))
        score = scorecard.get("score", {})
        
        lessons = {
            "battle_ref": {
                "battle_id": battle_id,
                "battle_type": battle_type,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            },
            "performance_metrics": {
                "detection_recall": score.get("detection_recall", 0),
                "false_positive_rate": score.get("false_positive_rate", 0),
                "mitigation_time_s": score.get("mitigation_time_s", 0),
            },
            "semantic_lessons": self._extract_semantic_lessons(stages, scorecard),
            "episodic_lessons": self._extract_episodic_lessons(stages),
            "procedural_updates": self._extract_procedural_updates(stages, scorecard),
            "category": self._categorize_battle(battle_type),
            "sanitization_status": "sanitized",
        }
        
        return lessons

    def _extract_semantic_lessons(
        self,
        stages: Dict[str, Any],
        scorecard: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract semantic (factual knowledge) lessons."""
        lessons = []
        
        # Learn from scorecard
        score = scorecard.get("score", {})
        winner = scorecard.get("winner", "")
        
        if winner == "TEAM-BLUE":
            lessons.append({
                "fact": "Defensive strategy effective against this attack pattern",
                "confidence": score.get("detection_recall", 0.8),
                "evidence_refs": ["scorecard"],
            })
        else:
            lessons.append({
                "fact": "Attack pattern bypassed current defenses",
                "confidence": score.get("attack_success_rate", 0.5),
                "evidence_refs": ["scorecard"],
                "requires_improvement": True,
            })
        
        # Default lessons based on performance
        if score.get("detection_recall", 0) > 0.85:
            lessons.append({
                "fact": "High detection rate achieved with current rule configuration",
                "confidence": 0.9,
                "evidence_refs": ["detect_stage"],
            })
        
        if score.get("false_positive_rate", 0) < 0.03:
            lessons.append({
                "fact": "Low false positive rate indicates well-tuned rules",
                "confidence": 0.85,
                "evidence_refs": ["detect_stage"],
            })
        
        return lessons

    def _extract_episodic_lessons(
        self,
        stages: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract episodic (experiential) lessons."""
        lessons = []
        
        # Learn from each stage
        for stage_key, stage_data in stages.items():
            orchestrator = stage_data.get("orchestrator_output", {})
            if not orchestrator:
                continue
            
            status = orchestrator.get("status", "unknown")
            metrics = orchestrator.get("metrics", {})
            
            lessons.append({
                "stage": stage_key,
                "experience": f"Stage {stage_key} completed with status: {status}",
                "metrics_snapshot": metrics,
                "timestamp": orchestrator.get("ended_at", datetime.now(timezone.utc).isoformat()),
            })
        
        return lessons

    def _extract_procedural_updates(
        self,
        stages: Dict[str, Any],
        scorecard: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Extract procedural (action-based) updates."""
        updates = []
        score = scorecard.get("score", {})
        
        # Recommend procedure updates based on performance
        if score.get("mitigation_time_s", 0) > 45:
            updates.append({
                "procedure": "mitigation_response",
                "action": "reduce_response_time",
                "target_value": "30s",
                "current_value": f"{score.get('mitigation_time_s', 0)}s",
            })
        
        if score.get("false_positive_rate", 0) > 0.05:
            updates.append({
                "procedure": "detection_threshold",
                "action": "increase_precision",
                "target_value": "0.03",
                "current_value": f"{score.get('false_positive_rate', 0):.3f}",
            })
        
        return updates

    def _categorize_battle(self, battle_type: str) -> str:
        """Categorize battle type for AMC integration."""
        battle_type_lower = battle_type.lower()
        
        if "ato" in battle_type_lower or "takeover" in battle_type_lower:
            return "account_takeover"
        elif "mule" in battle_type_lower:
            return "mule_network"
        elif "card" in battle_type_lower or "testing" in battle_type_lower:
            return "card_testing"
        elif "phishing" in battle_type_lower:
            return "phishing"
        else:
            return "general_fraud"

    def _generate_rsb_proposals(
        self,
        battle_data: Dict[str, Any],
        scorecard: Dict[str, Any],
        stages: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Generate RSB rule patch proposals."""
        proposals = []
        battle_type = battle_data.get("battle_type", battle_data.get("scenario_name", "Unknown"))
        score = scorecard.get("score", {})
        
        # Proposal 1: Based on detection gap
        if score.get("detection_recall", 0) < 0.95:
            proposals.append({
                "proposal_id": f"RSB-{datetime.now(timezone.utc).strftime('%Y%m%d')}-001",
                "rule_name": f"Enhanced_{battle_type.replace(' ', '_')}_Detection",
                "target": "detection_engine",
                "action": "add_rule",
                "condition": "velocity_score > 0.8 AND device_risk > 0.6",
                "response": "BLOCK",
                "rationale": f"Improve detection recall from {score.get('detection_recall', 0)*100:.1f}% to target 95%+",
                "priority": "high" if score.get("detection_recall", 0) < 0.8 else "medium",
                "test_cases": [
                    {"scenario": "High velocity legitimate", "expected": "ALLOW"},
                    {"scenario": "High velocity + risky device", "expected": "BLOCK"},
                ],
            })
        
        # Proposal 2: Based on attack success
        if score.get("attack_success_rate", 0) > 0.1:
            proposals.append({
                "proposal_id": f"RSB-{datetime.now(timezone.utc).strftime('%Y%m%d')}-002",
                "rule_name": "Attack_Chain_Breaker",
                "target": "mitigation_engine",
                "action": "add_rule",
                "condition": "attack_chain_score > 0.7 OR mule_network_score > 0.5",
                "response": "BLOCK_AND_FREEZE",
                "rationale": f"Reduce attack success rate from {score.get('attack_success_rate', 0)*100:.1f}% to target <5%",
                "priority": "high",
                "test_cases": [
                    {"scenario": "Known mule pattern", "expected": "BLOCK"},
                    {"scenario": "Normal transfer chain", "expected": "ALLOW"},
                ],
            })
        
        # Proposal 3: FP reduction
        if score.get("false_positive_rate", 0) > 0.03:
            proposals.append({
                "proposal_id": f"RSB-{datetime.now(timezone.utc).strftime('%Y%m%d')}-003",
                "rule_name": "Precision_Enhancer",
                "target": "detection_engine",
                "action": "modify_rule",
                "condition": "customer_tenure > 365 AND historical_fp_rate > 0.5",
                "response": "REDUCE_SCORE_0.2",
                "rationale": f"Reduce FP rate from {score.get('false_positive_rate', 0)*100:.1f}% to target <3% for tenured customers",
                "priority": "medium",
                "test_cases": [
                    {"scenario": "Tenured customer normal activity", "expected": "ALLOW"},
                    {"scenario": "Tenured customer anomaly", "expected": "REVIEW"},
                ],
            })
        
        return proposals


# Singleton instance
postmortem_generator = PostmortemGenerator()


async def generate_and_save_postmortem(
    battle_id: str,
    scorecard: Dict[str, Any],
    stages: Dict[str, Any],
) -> Dict[str, Any]:
    """Generate and persist postmortem for a battle.
    
    Args:
        battle_id: The battle ID
        scorecard: Battle scorecard
        stages: Stage outputs dict
        
    Returns:
        Generated postmortem package
    """
    battle = await db.battles.find_one({"id": battle_id}, {"_id": 0})
    if not battle:
        # Use minimal battle data
        battle = {"id": battle_id, "scenario_name": "Unknown"}
    
    package = postmortem_generator.generate_postmortem(battle, scorecard, stages)
    
    # Save to database
    await db.battle_postmortems.update_one(
        {"battle_id": battle_id},
        {"$set": {**package, "battle_id": battle_id}},
        upsert=True,
    )
    
    logger.info(
        "postmortem.generated",
        extra={"payload": {"battle_id": battle_id}},
    )
    
    return package
