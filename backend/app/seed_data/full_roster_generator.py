"""
Full 54-Agent Roster Generator for Fraud Forge

This module generates the complete 8-Team / 54-Agent roster for the Fraud Forge
hackathon demo. Each agent has a unique identity, capabilities, and role within
their respective team.

Teams:
- RED TEAM (8 agents): Offensive - Simulates attacks
- BLUE TEAM (8 agents): Defensive - Detects and blocks
- PURPLE TEAM (6 agents): Strategic - Creates rules from failures
- GREEN TEAM (6 agents): Engineering - Codes and deploys fixes
- BLACK TEAM (6 agents): Offensive Specialists - Advanced attacks
- ORANGE TEAM (6 agents): Operations - Monitors and responds
- WHITE TEAM (6 agents): Governance - Approvals and compliance
- GOLD TEAM (8 agents): XAI - Explainability and transparency
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any
import random
import uuid


# ============================================================================
# TEAM DEFINITIONS
# ============================================================================

TEAMS = [
    {
        "team_id": "red_team",
        "internal_name": "Red Team - Challengers",
        "display_name": "Red Challengers",
        "color": "#FF4444",
        "emoji": "🔴",
        "description": "Adversarial team that simulates sophisticated fraud attacks to test defenses",
        "operating_mode": "HOTL",
        "status": "active",
        "mission": "Continuously probe defenses with evolving attack vectors",
        "capabilities": ["attack_simulation", "vulnerability_scanning", "payload_generation", "evasion_techniques"],
        "metrics": {"total_attacks": 0, "success_rate": 0.12, "avg_evasion_score": 0.35}
    },
    {
        "team_id": "blue_team",
        "internal_name": "Blue Team - Defenders",
        "display_name": "Blue Defenders",
        "color": "#4444FF",
        "emoji": "🔵",
        "description": "Defense team that detects, blocks, and learns from fraud attempts",
        "operating_mode": "HITL",
        "status": "active",
        "mission": "Protect assets and continuously improve detection capabilities",
        "capabilities": ["threat_detection", "pattern_matching", "anomaly_detection", "real_time_blocking"],
        "metrics": {"total_blocks": 0, "detection_rate": 0.88, "false_positive_rate": 0.02}
    },
    {
        "team_id": "purple_team",
        "internal_name": "Purple Team - Strategists",
        "display_name": "Purple Strategists",
        "color": "#9944FF",
        "emoji": "🟣",
        "description": "Strategic team that analyzes failures and creates new defense rules",
        "operating_mode": "HITL",
        "status": "active",
        "mission": "Transform attack insights into actionable defense strategies",
        "capabilities": ["rule_generation", "gap_analysis", "threat_modeling", "playbook_creation"],
        "metrics": {"rules_created": 0, "rule_effectiveness": 0.91, "avg_time_to_rule": 45}
    },
    {
        "team_id": "green_team",
        "internal_name": "Green Team - Engineers",
        "display_name": "Green Engineers",
        "color": "#44FF44",
        "emoji": "🟢",
        "description": "Engineering team that codes, tests, and deploys detection rules",
        "operating_mode": "HITL",
        "status": "active",
        "mission": "Build robust, scalable, and maintainable defense systems",
        "capabilities": ["code_generation", "rule_implementation", "testing", "deployment"],
        "metrics": {"patches_deployed": 0, "code_quality": 0.95, "deployment_success_rate": 0.99}
    },
    {
        "team_id": "black_team",
        "internal_name": "Black Team - Specialists",
        "display_name": "Black Specialists",
        "color": "#333333",
        "emoji": "⬛",
        "description": "Advanced offensive specialists focusing on sophisticated attack chains",
        "operating_mode": "HOTL",
        "status": "active",
        "mission": "Execute complex multi-stage attack scenarios",
        "capabilities": ["advanced_evasion", "chain_attacks", "zero_day_simulation", "social_engineering"],
        "metrics": {"complex_attacks": 0, "chain_success_rate": 0.08, "avg_chain_length": 4}
    },
    {
        "team_id": "orange_team",
        "internal_name": "Orange Team - Operations",
        "display_name": "Orange Operators",
        "color": "#FF8844",
        "emoji": "🟠",
        "description": "Operations team that monitors, alerts, and responds to incidents",
        "operating_mode": "HITL",
        "status": "active",
        "mission": "Ensure 24/7 vigilance and rapid incident response",
        "capabilities": ["monitoring", "alerting", "incident_response", "escalation"],
        "metrics": {"alerts_processed": 0, "avg_response_time": 2.5, "escalation_rate": 0.15}
    },
    {
        "team_id": "white_team",
        "internal_name": "White Team - Governance",
        "display_name": "White Council",
        "color": "#FFFFFF",
        "emoji": "⬜",
        "description": "Governance team that approves changes and ensures compliance",
        "operating_mode": "HITL",
        "status": "active",
        "mission": "Maintain control, compliance, and strategic alignment",
        "capabilities": ["approval_workflow", "compliance_check", "risk_assessment", "policy_enforcement"],
        "metrics": {"approvals_processed": 0, "compliance_score": 0.98, "avg_approval_time": 30}
    },
    {
        "team_id": "gold_team",
        "internal_name": "Gold Team - XAI Advisors",
        "display_name": "Gold Advisors",
        "color": "#FFD700",
        "emoji": "🟡",
        "description": "Explainable AI team providing transparency and decision rationale",
        "operating_mode": "HOTL",
        "status": "active",
        "mission": "Make AI decisions transparent, auditable, and trustworthy",
        "capabilities": ["explanation_generation", "decision_audit", "confidence_scoring", "evidence_linking"],
        "metrics": {"explanations_generated": 0, "clarity_score": 0.92, "audit_coverage": 0.99}
    }
]


# ============================================================================
# AGENT DEFINITIONS (54 Total)
# ============================================================================

AGENTS = [
    # ========== RED TEAM (8 agents) ==========
    {
        "agent_id": "red-phantom-01",
        "agent_name": "Red Phantom",
        "team_id": "red_team",
        "role": "red",
        "specialization": "Stealth Attacks",
        "description": "Master of undetectable attack patterns",
        "capabilities": ["stealth_injection", "timing_evasion", "signature_mutation"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "👤",
        "experience_level": "elite",
        "total_runs": 145,
        "success_rate": 0.12
    },
    {
        "agent_id": "red-crimson-02",
        "agent_name": "Crimson Viper",
        "team_id": "red_team",
        "role": "red",
        "specialization": "Velocity Attacks",
        "description": "Specialist in rapid transaction bursts",
        "capabilities": ["velocity_burst", "timing_manipulation", "rate_limit_bypass"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🐍",
        "experience_level": "senior",
        "total_runs": 98,
        "success_rate": 0.15
    },
    {
        "agent_id": "red-shadow-03",
        "agent_name": "Shadow Striker",
        "team_id": "red_team",
        "role": "red",
        "specialization": "ATO Simulation",
        "description": "Account takeover attack specialist",
        "capabilities": ["credential_stuffing", "session_hijack", "mfa_bypass"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🌑",
        "experience_level": "senior",
        "total_runs": 112,
        "success_rate": 0.11
    },
    {
        "agent_id": "red-storm-04",
        "agent_name": "Storm Breaker",
        "team_id": "red_team",
        "role": "red",
        "specialization": "DDoS Patterns",
        "description": "Overwhelm defenses with volume attacks",
        "capabilities": ["volume_attacks", "resource_exhaustion", "cascade_failures"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "⛈️",
        "experience_level": "mid",
        "total_runs": 67,
        "success_rate": 0.08
    },
    {
        "agent_id": "red-ghost-05",
        "agent_name": "Ghost Walker",
        "team_id": "red_team",
        "role": "red",
        "specialization": "Evasion Tactics",
        "description": "Expert in avoiding detection signatures",
        "capabilities": ["signature_evasion", "polymorphic_payloads", "anti_forensics"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "👻",
        "experience_level": "elite",
        "total_runs": 134,
        "success_rate": 0.18
    },
    {
        "agent_id": "red-recon-06",
        "agent_name": "Recon Scout",
        "team_id": "red_team",
        "role": "red",
        "specialization": "Reconnaissance",
        "description": "Maps defense systems before attacks",
        "capabilities": ["system_mapping", "vulnerability_scan", "endpoint_discovery"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🔍",
        "experience_level": "mid",
        "total_runs": 89,
        "success_rate": 0.25
    },
    {
        "agent_id": "red-payload-07",
        "agent_name": "Payload Master",
        "team_id": "red_team",
        "role": "red",
        "specialization": "Payload Engineering",
        "description": "Creates sophisticated attack payloads",
        "capabilities": ["payload_generation", "obfuscation", "encoding_tricks"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "💣",
        "experience_level": "senior",
        "total_runs": 78,
        "success_rate": 0.14
    },
    {
        "agent_id": "red-mutant-08",
        "agent_name": "Mutant Forge",
        "team_id": "red_team",
        "role": "red",
        "specialization": "Attack Mutation",
        "description": "Evolves attacks based on defense patterns",
        "capabilities": ["attack_mutation", "adaptive_evasion", "learning_exploits"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🧬",
        "experience_level": "elite",
        "total_runs": 156,
        "success_rate": 0.16
    },
    
    # ========== BLUE TEAM (8 agents) ==========
    {
        "agent_id": "blue-sentinel-01",
        "agent_name": "Blue Sentinel",
        "team_id": "blue_team",
        "role": "blue",
        "specialization": "Real-time Detection",
        "description": "Primary detection engine for all threats",
        "capabilities": ["real_time_detection", "pattern_matching", "anomaly_scoring"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🛡️",
        "experience_level": "elite",
        "total_runs": 567,
        "detection_rate": 0.92
    },
    {
        "agent_id": "blue-guardian-02",
        "agent_name": "Guardian Shield",
        "team_id": "blue_team",
        "role": "blue",
        "specialization": "Velocity Defense",
        "description": "Specialist in detecting rapid transaction patterns",
        "capabilities": ["velocity_detection", "burst_analysis", "rate_limiting"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🔰",
        "experience_level": "senior",
        "total_runs": 423,
        "detection_rate": 0.89
    },
    {
        "agent_id": "blue-warden-03",
        "agent_name": "Identity Warden",
        "team_id": "blue_team",
        "role": "blue",
        "specialization": "Identity Protection",
        "description": "Detects synthetic and stolen identities",
        "capabilities": ["identity_verification", "synthetic_detection", "document_forensics"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🪪",
        "experience_level": "senior",
        "total_runs": 389,
        "detection_rate": 0.87
    },
    {
        "agent_id": "blue-graph-04",
        "agent_name": "Graph Analyzer",
        "team_id": "blue_team",
        "role": "blue",
        "specialization": "Network Analysis",
        "description": "Detects fraud rings via graph patterns",
        "capabilities": ["graph_analysis", "network_detection", "cluster_identification"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🕸️",
        "experience_level": "senior",
        "total_runs": 312,
        "detection_rate": 0.91
    },
    {
        "agent_id": "blue-behav-05",
        "agent_name": "Behavior Oracle",
        "team_id": "blue_team",
        "role": "blue",
        "specialization": "Behavioral Analysis",
        "description": "Detects anomalies in user behavior",
        "capabilities": ["behavior_modeling", "deviation_detection", "session_analysis"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🧠",
        "experience_level": "elite",
        "total_runs": 445,
        "detection_rate": 0.88
    },
    {
        "agent_id": "blue-device-06",
        "agent_name": "Device Tracker",
        "team_id": "blue_team",
        "role": "blue",
        "specialization": "Device Intelligence",
        "description": "Tracks and validates device fingerprints",
        "capabilities": ["device_fingerprinting", "emulator_detection", "geo_validation"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "📱",
        "experience_level": "mid",
        "total_runs": 278,
        "detection_rate": 0.85
    },
    {
        "agent_id": "blue-rule-07",
        "agent_name": "Rule Engine",
        "team_id": "blue_team",
        "role": "blue",
        "specialization": "Rule Execution",
        "description": "Executes detection rules in real-time",
        "capabilities": ["rule_execution", "condition_evaluation", "action_triggering"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "⚙️",
        "experience_level": "senior",
        "total_runs": 892,
        "detection_rate": 0.94
    },
    {
        "agent_id": "blue-ml-08",
        "agent_name": "ML Predictor",
        "team_id": "blue_team",
        "role": "blue",
        "specialization": "Machine Learning",
        "description": "ML-based fraud prediction models",
        "capabilities": ["ml_scoring", "feature_extraction", "model_inference"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🤖",
        "experience_level": "elite",
        "total_runs": 534,
        "detection_rate": 0.90
    },
    
    # ========== PURPLE TEAM (6 agents) ==========
    {
        "agent_id": "purple-strat-01",
        "agent_name": "Strategy Oracle",
        "team_id": "purple_team",
        "role": "purple",
        "specialization": "Strategic Analysis",
        "description": "Analyzes attack patterns for defense strategy",
        "capabilities": ["pattern_analysis", "strategy_formulation", "gap_identification"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🔮",
        "experience_level": "elite",
        "total_runs": 234,
        "rules_created": 89
    },
    {
        "agent_id": "purple-rule-02",
        "agent_name": "Rule Architect",
        "team_id": "purple_team",
        "role": "purple",
        "specialization": "Rule Design",
        "description": "Designs optimal detection rules",
        "capabilities": ["rule_design", "condition_optimization", "threshold_tuning"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "📐",
        "experience_level": "senior",
        "total_runs": 178,
        "rules_created": 67
    },
    {
        "agent_id": "purple-threat-03",
        "agent_name": "Threat Modeler",
        "team_id": "purple_team",
        "role": "purple",
        "specialization": "Threat Modeling",
        "description": "Models emerging threat scenarios",
        "capabilities": ["threat_modeling", "scenario_planning", "risk_assessment"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🎯",
        "experience_level": "senior",
        "total_runs": 145,
        "rules_created": 45
    },
    {
        "agent_id": "purple-gap-04",
        "agent_name": "Gap Hunter",
        "team_id": "purple_team",
        "role": "purple",
        "specialization": "Gap Analysis",
        "description": "Identifies defense coverage gaps",
        "capabilities": ["coverage_analysis", "gap_detection", "recommendation_engine"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🔎",
        "experience_level": "mid",
        "total_runs": 112,
        "rules_created": 34
    },
    {
        "agent_id": "purple-play-05",
        "agent_name": "Playbook Writer",
        "team_id": "purple_team",
        "role": "purple",
        "specialization": "Playbook Creation",
        "description": "Creates response playbooks",
        "capabilities": ["playbook_creation", "workflow_design", "sop_generation"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "📘",
        "experience_level": "senior",
        "total_runs": 98,
        "rules_created": 28
    },
    {
        "agent_id": "purple-learn-06",
        "agent_name": "Learning Loop",
        "team_id": "purple_team",
        "role": "purple",
        "specialization": "Continuous Learning",
        "description": "Implements learning from battles",
        "capabilities": ["learning_extraction", "pattern_storage", "knowledge_update"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🔄",
        "experience_level": "elite",
        "total_runs": 267,
        "rules_created": 112
    },
    
    # ========== GREEN TEAM (6 agents) ==========
    {
        "agent_id": "green-code-01",
        "agent_name": "Code Forge",
        "team_id": "green_team",
        "role": "green",
        "specialization": "Rule Coding",
        "description": "Converts rules to executable code",
        "capabilities": ["code_generation", "syntax_validation", "optimization"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "💻",
        "experience_level": "elite",
        "total_runs": 189,
        "patches_deployed": 156
    },
    {
        "agent_id": "green-test-02",
        "agent_name": "Test Runner",
        "team_id": "green_team",
        "role": "green",
        "specialization": "Testing",
        "description": "Tests rules before deployment",
        "capabilities": ["unit_testing", "integration_testing", "regression_testing"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🧪",
        "experience_level": "senior",
        "total_runs": 312,
        "patches_deployed": 0
    },
    {
        "agent_id": "green-deploy-03",
        "agent_name": "Deploy Master",
        "team_id": "green_team",
        "role": "green",
        "specialization": "Deployment",
        "description": "Deploys rules to production",
        "capabilities": ["deployment", "rollback", "canary_release"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🚀",
        "experience_level": "senior",
        "total_runs": 178,
        "patches_deployed": 178
    },
    {
        "agent_id": "green-perf-04",
        "agent_name": "Perf Optimizer",
        "team_id": "green_team",
        "role": "green",
        "specialization": "Performance",
        "description": "Optimizes rule performance",
        "capabilities": ["performance_tuning", "latency_reduction", "resource_optimization"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "⚡",
        "experience_level": "senior",
        "total_runs": 134,
        "patches_deployed": 67
    },
    {
        "agent_id": "green-review-05",
        "agent_name": "Code Reviewer",
        "team_id": "green_team",
        "role": "green",
        "specialization": "Code Review",
        "description": "Reviews code quality and security",
        "capabilities": ["code_review", "security_analysis", "best_practices"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "👁️",
        "experience_level": "senior",
        "total_runs": 245,
        "patches_deployed": 0
    },
    {
        "agent_id": "green-doc-06",
        "agent_name": "Doc Generator",
        "team_id": "green_team",
        "role": "green",
        "specialization": "Documentation",
        "description": "Generates rule documentation",
        "capabilities": ["doc_generation", "api_docs", "changelog_creation"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "📝",
        "experience_level": "mid",
        "total_runs": 156,
        "patches_deployed": 0
    },
    
    # ========== BLACK TEAM (6 agents) ==========
    {
        "agent_id": "black-chain-01",
        "agent_name": "Chain Master",
        "team_id": "black_team",
        "role": "black",
        "specialization": "Multi-Stage Attacks",
        "description": "Orchestrates complex attack chains",
        "capabilities": ["chain_orchestration", "stage_coordination", "persistence"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "⛓️",
        "experience_level": "elite",
        "total_runs": 78,
        "success_rate": 0.08
    },
    {
        "agent_id": "black-social-02",
        "agent_name": "Social Engineer",
        "team_id": "black_team",
        "role": "black",
        "specialization": "Social Engineering",
        "description": "Simulates social engineering attacks",
        "capabilities": ["phishing_simulation", "pretexting", "vishing"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🎭",
        "experience_level": "senior",
        "total_runs": 56,
        "success_rate": 0.12
    },
    {
        "agent_id": "black-insider-03",
        "agent_name": "Insider Threat",
        "team_id": "black_team",
        "role": "black",
        "specialization": "Insider Attacks",
        "description": "Simulates malicious insider behavior",
        "capabilities": ["privilege_abuse", "data_exfiltration", "collusion"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🕵️",
        "experience_level": "senior",
        "total_runs": 45,
        "success_rate": 0.15
    },
    {
        "agent_id": "black-zero-04",
        "agent_name": "Zero Day",
        "team_id": "black_team",
        "role": "black",
        "specialization": "Novel Attacks",
        "description": "Creates never-before-seen attack patterns",
        "capabilities": ["novel_attack_generation", "zero_day_simulation", "pattern_creation"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🆕",
        "experience_level": "elite",
        "total_runs": 34,
        "success_rate": 0.25
    },
    {
        "agent_id": "black-persist-05",
        "agent_name": "Persistence",
        "team_id": "black_team",
        "role": "black",
        "specialization": "Long-term Access",
        "description": "Maintains persistent access patterns",
        "capabilities": ["foothold_establishment", "beacon_maintenance", "stealth_ops"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🔗",
        "experience_level": "senior",
        "total_runs": 67,
        "success_rate": 0.10
    },
    {
        "agent_id": "black-lat-06",
        "agent_name": "Lateral Mover",
        "team_id": "black_team",
        "role": "black",
        "specialization": "Lateral Movement",
        "description": "Simulates cross-account movement",
        "capabilities": ["lateral_movement", "pivot_attacks", "trust_exploitation"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "↔️",
        "experience_level": "mid",
        "total_runs": 45,
        "success_rate": 0.09
    },
    
    # ========== ORANGE TEAM (6 agents) ==========
    {
        "agent_id": "orange-mon-01",
        "agent_name": "Monitor Prime",
        "team_id": "orange_team",
        "role": "orange",
        "specialization": "Real-time Monitoring",
        "description": "24/7 system monitoring",
        "capabilities": ["dashboard_monitoring", "metric_tracking", "health_checks"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "📊",
        "experience_level": "senior",
        "total_runs": 1245,
        "alerts_processed": 3456
    },
    {
        "agent_id": "orange-alert-02",
        "agent_name": "Alert Manager",
        "team_id": "orange_team",
        "role": "orange",
        "specialization": "Alert Processing",
        "description": "Triages and routes alerts",
        "capabilities": ["alert_triage", "priority_assignment", "routing"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🔔",
        "experience_level": "senior",
        "total_runs": 2345,
        "alerts_processed": 4567
    },
    {
        "agent_id": "orange-ir-03",
        "agent_name": "Incident Responder",
        "team_id": "orange_team",
        "role": "orange",
        "specialization": "Incident Response",
        "description": "Responds to active incidents",
        "capabilities": ["incident_response", "containment", "recovery"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🚨",
        "experience_level": "elite",
        "total_runs": 567,
        "alerts_processed": 567
    },
    {
        "agent_id": "orange-esc-04",
        "agent_name": "Escalation Agent",
        "team_id": "orange_team",
        "role": "orange",
        "specialization": "Escalation",
        "description": "Escalates critical issues",
        "capabilities": ["escalation", "stakeholder_notification", "sla_tracking"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "📤",
        "experience_level": "mid",
        "total_runs": 234,
        "alerts_processed": 234
    },
    {
        "agent_id": "orange-report-05",
        "agent_name": "Report Generator",
        "team_id": "orange_team",
        "role": "orange",
        "specialization": "Reporting",
        "description": "Generates operational reports",
        "capabilities": ["report_generation", "metric_aggregation", "trend_analysis"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "📈",
        "experience_level": "mid",
        "total_runs": 456,
        "alerts_processed": 0
    },
    {
        "agent_id": "orange-shift-06",
        "agent_name": "Shift Coordinator",
        "team_id": "orange_team",
        "role": "orange",
        "specialization": "Coordination",
        "description": "Coordinates team activities",
        "capabilities": ["shift_handoff", "resource_allocation", "coordination"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "👥",
        "experience_level": "senior",
        "total_runs": 345,
        "alerts_processed": 0
    },
    
    # ========== WHITE TEAM (6 agents) ==========
    {
        "agent_id": "white-approve-01",
        "agent_name": "Approval Gateway",
        "team_id": "white_team",
        "role": "white",
        "specialization": "Approvals",
        "description": "Manages approval workflows",
        "capabilities": ["approval_workflow", "multi_sig", "delegation"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "✅",
        "experience_level": "elite",
        "total_runs": 456,
        "approvals_processed": 789
    },
    {
        "agent_id": "white-comply-02",
        "agent_name": "Compliance Check",
        "team_id": "white_team",
        "role": "white",
        "specialization": "Compliance",
        "description": "Validates compliance requirements",
        "capabilities": ["compliance_validation", "regulation_mapping", "audit_prep"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "📋",
        "experience_level": "senior",
        "total_runs": 567,
        "approvals_processed": 567
    },
    {
        "agent_id": "white-risk-03",
        "agent_name": "Risk Assessor",
        "team_id": "white_team",
        "role": "white",
        "specialization": "Risk Assessment",
        "description": "Assesses change risks",
        "capabilities": ["risk_scoring", "impact_analysis", "mitigation_planning"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "⚖️",
        "experience_level": "senior",
        "total_runs": 345,
        "approvals_processed": 234
    },
    {
        "agent_id": "white-policy-04",
        "agent_name": "Policy Enforcer",
        "team_id": "white_team",
        "role": "white",
        "specialization": "Policy Enforcement",
        "description": "Enforces organizational policies",
        "capabilities": ["policy_enforcement", "exception_handling", "override_tracking"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "🏛️",
        "experience_level": "senior",
        "total_runs": 678,
        "approvals_processed": 456
    },
    {
        "agent_id": "white-audit-05",
        "agent_name": "Audit Trail",
        "team_id": "white_team",
        "role": "white",
        "specialization": "Audit",
        "description": "Maintains complete audit trails",
        "capabilities": ["audit_logging", "trail_verification", "evidence_preservation"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "📜",
        "experience_level": "mid",
        "total_runs": 1234,
        "approvals_processed": 0
    },
    {
        "agent_id": "white-council-06",
        "agent_name": "Council Chair",
        "team_id": "white_team",
        "role": "white",
        "specialization": "Governance",
        "description": "Leads governance decisions",
        "capabilities": ["decision_making", "tie_breaking", "strategic_approval"],
        "status": "active",
        "operating_mode": "HITL",
        "avatar": "👑",
        "experience_level": "elite",
        "total_runs": 234,
        "approvals_processed": 345
    },
    
    # ========== GOLD TEAM (8 agents) ==========
    {
        "agent_id": "gold-xai-01",
        "agent_name": "XAI Oracle",
        "team_id": "gold_team",
        "role": "gold",
        "specialization": "Decision Explanation",
        "description": "Explains AI/ML decision rationale",
        "capabilities": ["decision_explanation", "feature_attribution", "counterfactual_analysis"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🔮",
        "experience_level": "elite",
        "total_runs": 567,
        "explanations_generated": 1234
    },
    {
        "agent_id": "gold-evidence-02",
        "agent_name": "Evidence Linker",
        "team_id": "gold_team",
        "role": "gold",
        "specialization": "Evidence Collection",
        "description": "Links decisions to supporting evidence",
        "capabilities": ["evidence_linking", "trace_building", "citation_generation"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🔗",
        "experience_level": "senior",
        "total_runs": 456,
        "explanations_generated": 890
    },
    {
        "agent_id": "gold-conf-03",
        "agent_name": "Confidence Scorer",
        "team_id": "gold_team",
        "role": "gold",
        "specialization": "Confidence Assessment",
        "description": "Assesses and communicates certainty",
        "capabilities": ["confidence_scoring", "uncertainty_quantification", "calibration"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "📊",
        "experience_level": "senior",
        "total_runs": 678,
        "explanations_generated": 678
    },
    {
        "agent_id": "gold-narrative-04",
        "agent_name": "Narrative Builder",
        "team_id": "gold_team",
        "role": "gold",
        "specialization": "Story Generation",
        "description": "Builds human-readable narratives",
        "capabilities": ["narrative_generation", "plain_language", "context_weaving"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "📖",
        "experience_level": "senior",
        "total_runs": 345,
        "explanations_generated": 567
    },
    {
        "agent_id": "gold-visual-05",
        "agent_name": "Visual Explainer",
        "team_id": "gold_team",
        "role": "gold",
        "specialization": "Visual Explanation",
        "description": "Creates visual explanations",
        "capabilities": ["visualization_generation", "diagram_creation", "highlight_mapping"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🎨",
        "experience_level": "mid",
        "total_runs": 234,
        "explanations_generated": 345
    },
    {
        "agent_id": "gold-counter-06",
        "agent_name": "Counterfactual Agent",
        "team_id": "gold_team",
        "role": "gold",
        "specialization": "Counterfactual Analysis",
        "description": "Generates 'what if' scenarios",
        "capabilities": ["counterfactual_generation", "scenario_simulation", "boundary_analysis"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "🔀",
        "experience_level": "elite",
        "total_runs": 189,
        "explanations_generated": 289
    },
    {
        "agent_id": "gold-audit-07",
        "agent_name": "Audit Explainer",
        "team_id": "gold_team",
        "role": "gold",
        "specialization": "Audit Support",
        "description": "Generates audit-ready explanations",
        "capabilities": ["audit_explanation", "compliance_mapping", "regulator_formatting"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "📑",
        "experience_level": "senior",
        "total_runs": 156,
        "explanations_generated": 234
    },
    {
        "agent_id": "gold-summary-08",
        "agent_name": "Summary Generator",
        "team_id": "gold_team",
        "role": "gold",
        "specialization": "Summarization",
        "description": "Creates executive summaries",
        "capabilities": ["summarization", "key_point_extraction", "executive_briefing"],
        "status": "active",
        "operating_mode": "HOTL",
        "avatar": "📝",
        "experience_level": "mid",
        "total_runs": 267,
        "explanations_generated": 456
    }
]


def generate_full_roster() -> Dict[str, List[Dict[str, Any]]]:
    """
    Generate the complete 54-agent roster with all 8 teams.
    
    Returns:
        Dict containing 'teams' and 'agents' lists
    """
    timestamp = datetime.now(timezone.utc).isoformat()
    
    # Add timestamps to teams
    teams_with_timestamps = []
    for team in TEAMS:
        team_copy = team.copy()
        team_copy["created_at"] = timestamp
        team_copy["updated_at"] = timestamp
        teams_with_timestamps.append(team_copy)
    
    # Add timestamps and last_run to agents
    agents_with_timestamps = []
    for idx, agent in enumerate(AGENTS):
        agent_copy = agent.copy()
        agent_copy["created_at"] = timestamp
        agent_copy["updated_at"] = timestamp
        # Stagger last_run times
        last_run_offset = timedelta(hours=random.randint(1, 48), minutes=random.randint(0, 59))
        agent_copy["last_run"] = (datetime.now(timezone.utc) - last_run_offset).isoformat()
        agents_with_timestamps.append(agent_copy)
    
    return {
        "teams": teams_with_timestamps,
        "agents": agents_with_timestamps
    }


def get_team_summary() -> Dict[str, Any]:
    """Get a summary of all teams and agent counts."""
    team_counts = {}
    for agent in AGENTS:
        team_id = agent["team_id"]
        team_counts[team_id] = team_counts.get(team_id, 0) + 1
    
    return {
        "total_teams": len(TEAMS),
        "total_agents": len(AGENTS),
        "team_breakdown": team_counts,
        "team_names": {t["team_id"]: t["display_name"] for t in TEAMS}
    }


if __name__ == "__main__":
    roster = generate_full_roster()
    summary = get_team_summary()
    
    print("=" * 60)
    print("FRAUD FORGE - FULL 54-AGENT ROSTER")
    print("=" * 60)
    print(f"\nTotal Teams: {summary['total_teams']}")
    print(f"Total Agents: {summary['total_agents']}")
    print("\nTeam Breakdown:")
    for team_id, count in summary['team_breakdown'].items():
        team_name = summary['team_names'].get(team_id, team_id)
        print(f"  - {team_name}: {count} agents")
