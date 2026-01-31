from typing import Any, Dict, List


def default_team_payloads() -> List[Dict[str, Any]]:
    return [
        {
            "team_id": "red",
            "internal_name": "Red Team",
            "bank_facing_name": "The Challengers",
            "color_token": "red",
            "mission_statement": "Simulate real-world fraudsters and evolve attacks.",
            "capability_tags": ["attack", "simulation", "mutation"],
            "default_agent_roles": ["Orchestrator", "Scenario Generator", "Executor"],
        },
        {
            "team_id": "blue",
            "internal_name": "Blue Team",
            "bank_facing_name": "The Defenders",
            "color_token": "blue",
            "mission_statement": "Detect, prevent, and respond to fraud in real time.",
            "capability_tags": ["detection", "response", "scoring"],
            "default_agent_roles": ["Orchestrator", "Rule Evaluator", "Decision Agent"],
        },
        {
            "team_id": "purple",
            "internal_name": "Purple Team",
            "bank_facing_name": "The Strategists",
            "color_token": "purple",
            "mission_statement": "Design strategies, rules, and threat models.",
            "capability_tags": ["strategy", "rule-design", "threat-model"],
            "default_agent_roles": ["Orchestrator", "Root Cause Analyst", "Rule Author"],
        },
        {
            "team_id": "green",
            "internal_name": "Green Team",
            "bank_facing_name": "The Builders",
            "color_token": "green",
            "mission_statement": "Implement strategies and rules into production code.",
            "capability_tags": ["implementation", "integration", "features"],
            "default_agent_roles": ["Orchestrator", "Rule-to-Code Translator", "Feature Engineer"],
        },
        {
            "team_id": "black",
            "internal_name": "Black Team",
            "bank_facing_name": "The Stressors",
            "color_token": "black",
            "mission_statement": "Stress test robustness and discover edge cases.",
            "capability_tags": ["chaos", "stress", "regression"],
            "default_agent_roles": ["Orchestrator", "Edge-Case Generator", "Chaos Injector"],
        },
        {
            "team_id": "orange",
            "internal_name": "Orange Team",
            "bank_facing_name": "The Gatekeepers",
            "color_token": "orange",
            "mission_statement": "Review, validate, and approve releases.",
            "capability_tags": ["review", "security", "release"],
            "default_agent_roles": ["Orchestrator", "Security Reviewer", "Release Assessor"],
        },
        {
            "team_id": "gold",
            "internal_name": "Gold Team",
            "bank_facing_name": "The Narrators",
            "color_token": "gold",
            "mission_statement": "Explain decisions with evidence and narratives.",
            "capability_tags": ["explainability", "narrative", "audit"],
            "default_agent_roles": ["Orchestrator", "Decision Explainer", "Evidence Trace"],
        },
        {
            "team_id": "white",
            "internal_name": "White Team",
            "bank_facing_name": "The Council",
            "color_token": "white",
            "mission_statement": "Ensure compliance, fairness, and audit readiness.",
            "capability_tags": ["compliance", "ethics", "audit"],
            "default_agent_roles": ["Orchestrator", "Policy Reviewer", "Compliance Auditor"],
        },
    ]


def _agent_payload(
    agent_id: str,
    agent_name: str,
    team_id: str,
    role: str,
    capabilities: List[str],
    inputs: List[str],
    outputs: List[str],
    operating_mode: str,
    guardrails: List[str] | None = None,
) -> Dict[str, Any]:
    return {
        "agent_id": agent_id,
        "agent_name": agent_name,
        "team_id": team_id,
        "role": role,
        "capabilities": capabilities,
        "inputs": inputs,
        "outputs": outputs,
        "operating_mode": operating_mode,
        "guardrails": guardrails or ["synthetic_only"],
    }


def default_agent_payloads() -> List[Dict[str, Any]]:
    return [
        # Red Team
        _agent_payload("red.orchestrator", "Red Orchestrator", "red", "Campaign Manager", ["planning", "delegation", "attack-design"], ["Scenario"], ["AttackPlan"], "auto"),
        _agent_payload("red.scenario_generator", "Fraud Scenario Generator", "red", "Scenario Generator", ["mutation", "scenario-design"], ["Taxonomy"], ["Scenario"], "auto"),
        _agent_payload("red.transaction_executor", "Transaction Fraud Executor", "red", "Executor", ["execution", "simulation"], ["Scenario"], ["SyntheticTransactionStream"], "auto"),
        _agent_payload("red.loan_abuse", "Loan & Deposit Abuse Agent", "red", "Lifecycle Simulator", ["lifecycle", "abuse"], ["Scenario"], ["AttackVariantReport"], "auto"),
        _agent_payload("red.identity_evasion", "Identity & KYC Evasion Agent", "red", "Persona Designer", ["identity", "context"], ["Scenario"], ["SyntheticIdentityBundle"], "auto"),
        _agent_payload("red.bot_swarm", "Bot Swarm Controller", "red", "Collusion Coordinator", ["coordination", "collusion"], ["Scenario"], ["AttackCampaign"], "auto"),
        _agent_payload("red.recon_finder", "Recon & Weak-Signal Finder", "red", "Recon Analyst", ["recon", "weak-signal"], ["Telemetry"], ["ReconFindings"], "auto"),
        _agent_payload("red.adaptive_learning", "Adaptive Learning Agent", "red", "Feedback Learner", ["learning", "mutation"], ["AttackVariantReport"], ["AttackPlan"], "auto"),

        # Blue Team
        _agent_payload("blue.orchestrator", "Blue Orchestrator", "blue", "Defense Manager", ["detection", "response"], ["Telemetry"], ["Decision"], "auto"),
        _agent_payload("blue.rule_evaluator", "Rule Evaluation Agent", "blue", "Rule Evaluator", ["rules", "thresholds"], ["Telemetry"], ["Alerts"], "auto"),
        _agent_payload("blue.behavioral_baseline", "Behavioral Baseline Agent", "blue", "Baseline Analyst", ["behavior", "profiling"], ["Telemetry"], ["Observations"], "auto"),
        _agent_payload("blue.graph_link", "Graph & Link Analysis Agent", "blue", "Link Analyst", ["graph", "ring-detection"], ["Telemetry"], ["GraphInsights"], "auto"),
        _agent_payload("blue.device_risk", "Device & Session Risk Agent", "blue", "Session Risk", ["device", "geo"], ["Telemetry"], ["RiskSignals"], "auto"),
        _agent_payload("blue.model_scoring", "Model Scoring Agent", "blue", "Scoring", ["scoring", "drift"], ["Telemetry"], ["RiskScores"], "auto"),
        _agent_payload("blue.decision_action", "Decision & Action Agent", "blue", "Decisioning", ["decisioning", "policy"], ["RiskScores"], ["Decision"], "auto"),
        _agent_payload("blue.escalation", "Escalation Agent", "blue", "Escalation", ["escalation", "packaging"], ["Decision"], ["IncidentDossier"], "auto"),
        _agent_payload("blue.post_monitor", "Post-Decision Monitor", "blue", "Outcome Monitor", ["monitor", "feedback"], ["Decision"], ["LearningNote"], "auto"),

        # Purple Team
        _agent_payload("purple.orchestrator", "Purple Orchestrator", "purple", "Strategy Manager", ["planning", "delegation"], ["IncidentDossier"], ["RuleSpec"], "semi-auto"),
        _agent_payload("purple.root_cause", "Root Cause Analysis Agent", "purple", "Root Cause", ["analysis", "causal"], ["IncidentDossier"], ["RootCauseReport"], "semi-auto"),
        _agent_payload("purple.rule_author", "Rule Authoring Agent", "purple", "Rule Author", ["rules", "spec"], ["RootCauseReport"], ["RuleSpec"], "semi-auto"),
        _agent_payload("purple.threat_forecast", "Threat Forecasting Agent", "purple", "Threat Forecaster", ["forecasting", "planning"], ["Taxonomy"], ["ThreatForecast"], "semi-auto"),
        _agent_payload("purple.policy_constraint", "Policy Constraint Agent", "purple", "Policy Reviewer", ["policy", "governance"], ["RuleSpec"], ["PolicyNotes"], "semi-auto"),
        _agent_payload("purple.kg_curator", "Knowledge Graph Curator", "purple", "Graph Curator", ["knowledge", "graph"], ["RuleSpec"], ["KnowledgeGraphDelta"], "semi-auto"),
        _agent_payload("purple.requirements_pack", "Requirements Packager", "purple", "Requirements Packager", ["context", "packaging"], ["RuleSpec"], ["RequirementPack"], "semi-auto"),

        # Green Team
        _agent_payload("green.orchestrator", "Green Orchestrator", "green", "Build Manager", ["planning", "delegation"], ["RequirementPack"], ["Patch"], "semi-auto"),
        _agent_payload("green.rule_to_code", "Rule-to-Code Translator", "green", "Rule Translator", ["codegen", "rules"], ["RuleSpec"], ["RuleCode"], "semi-auto"),
        _agent_payload("green.pipeline_integration", "Pipeline & Integration Agent", "green", "Integrator", ["integration", "pipeline"], ["RuleCode"], ["Patch"], "semi-auto"),
        _agent_payload("green.feature_engineer", "Feature Engineering Agent", "green", "Feature Engineer", ["features", "signals"], ["Telemetry"], ["FeatureSet"], "semi-auto"),
        _agent_payload("green.observability", "Observability & Audit Agent", "green", "Observability", ["observability", "audit"], ["Patch"], ["AuditHooks"], "semi-auto"),
        _agent_payload("green.test_generator", "Test Generator", "green", "Test Generator", ["tests", "coverage"], ["RuleSpec"], ["TestReport"], "semi-auto"),
        _agent_payload("green.packaging", "Packaging Agent", "green", "Packager", ["packaging", "rsb"], ["Patch"], ["RSBPackage"], "semi-auto"),

        # Black Team
        _agent_payload("black.orchestrator", "Black Orchestrator", "black", "Test Manager", ["planning", "stress"], ["Patch"], ["StressTestReport"], "auto"),
        _agent_payload("black.adversarial_replay", "Adversarial Replay Agent", "black", "Replay", ["replay", "regression"], ["AttackPlan"], ["ReplayReport"], "auto"),
        _agent_payload("black.edge_case", "Edge-Case Generator", "black", "Edge Case", ["edge-cases", "mutation"], ["Scenario"], ["EdgeCaseReport"], "auto"),
        _agent_payload("black.chaos_injection", "Chaos Injection Agent", "black", "Chaos", ["chaos", "fault"], ["Patch"], ["ChaosRun"], "auto"),
        _agent_payload("black.load_burst", "Load/Burst Simulation Agent", "black", "Load Simulation", ["load", "burst"], ["Scenario"], ["LoadReport"], "auto"),
        _agent_payload("black.regression_auditor", "Regression & Coverage Auditor", "black", "Regression", ["coverage", "regression"], ["TestReport"], ["RegressionReport"], "auto"),
        _agent_payload("black.failure_injection", "Failure Injection Agent", "black", "Failure Injection", ["failure", "resilience"], ["Patch"], ["FailureInjectionReport"], "auto"),

        # Orange Team
        _agent_payload("orange.orchestrator", "Orange Orchestrator", "orange", "Release Manager", ["review", "release"], ["Patch", "TestReport"], ["ApprovalDecision"], "manual"),
        _agent_payload("orange.code_reviewer", "Code Reviewer", "orange", "Code Reviewer", ["security", "review"], ["Patch"], ["ReviewNotes"], "manual"),
        _agent_payload("orange.release_approver", "Release Approver", "orange", "Release Approver", ["approval", "risk"], ["ReviewNotes"], ["ApprovalDecision"], "manual"),
        _agent_payload("orange.runtime_sre", "Runtime SRE/QA", "orange", "Runtime QA", ["sre", "qa"], ["DeploymentPlan"], ["ReleaseNote"], "manual"),

        # Gold Team
        _agent_payload("gold.orchestrator", "Gold Orchestrator", "gold", "Explanation Manager", ["explain", "narrative"], ["Decision"], ["ExplanationPack"], "auto"),
        _agent_payload("gold.explanation_composer", "Explanation Composer", "gold", "Composer", ["explain", "summary"], ["Decision"], ["ExplanationPack"], "auto"),
        _agent_payload("gold.evidence_graph", "Evidence Graph Builder", "gold", "Evidence Graph", ["graph", "lineage"], ["Evidence"], ["EvidenceGraph"], "auto"),
        _agent_payload("gold.counterfactual", "Counterfactual Generator", "gold", "Counterfactual", ["counterfactual", "analysis"], ["Decision"], ["Counterfactual"], "auto"),
        _agent_payload("gold.similar_case", "Similar-Case Retriever", "gold", "Similarity", ["retrieval", "cases"], ["Evidence"], ["SimilarCases"], "auto"),
        _agent_payload("gold.audience_adapter", "Audience Adapter Agent", "gold", "Audience Adapter", ["audience", "tone"], ["ExplanationPack"], ["ExplanationPack"], "auto"),
        _agent_payload("gold.case_narrative", "Case Narrative Agent", "gold", "Narrative", ["narrative", "timeline"], ["Evidence"], ["CaseNarrative"], "auto"),

        # White Team
        _agent_payload("white.orchestrator", "White Orchestrator", "white", "Governance Manager", ["compliance", "audit"], ["ApprovalDecision"], ["CompliancePack"], "manual"),
        _agent_payload("white.policy_checker", "Policy Checker", "white", "Policy Checker", ["policy", "compliance"], ["ApprovalDecision"], ["PolicyChecklist"], "manual"),
        _agent_payload("white.fairness_checker", "Fairness/Reasonableness Checker", "white", "Fairness Checker", ["fairness", "ethics"], ["Decision"], ["FairnessReport"], "manual"),
        _agent_payload("white.audit_pack", "Audit Pack Reviewer", "white", "Audit Reviewer", ["audit", "evidence"], ["Evidence"], ["AuditPack"], "manual"),
        _agent_payload("white.risk_assessor", "Compliance Risk Assessor", "white", "Risk Assessor", ["risk", "governance"], ["Evidence"], ["ComplianceRisk"], "manual"),
    ]
