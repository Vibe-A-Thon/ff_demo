"""Counterfactual and Similar-Case Retrieval Service.

This service provides advanced counterfactual generation and similar-case
retrieval functionality linked to real evidence packs and telemetry data.

Features:
- Feature-based counterfactual generation with evidence linkage
- Rule-based counterfactual suggestions
- Similar-case retrieval using vector similarity and rule-matching
- Evidence pack similarity scoring with detailed breakdown
- LLM-enhanced explanation generation (optional)
"""

from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timezone
import hashlib
import json
import re

from app.models import EvidenceItem, Counterfactual, SimilarCase, ExplanationBundle


# Feature importance weights for counterfactual analysis
FEATURE_WEIGHTS = {
    "risk_score": 0.25,
    "velocity_score": 0.20,
    "device_risk_score": 0.15,
    "geo_risk_score": 0.10,
    "behavior_score": 0.10,
    "amount": 0.10,
    "anomaly_count": 0.05,
    "model_score": 0.05,
}

# Categorical feature mappings for counterfactuals
CATEGORICAL_LEVELS = {
    "device_risk": ["low", "medium", "high", "critical"],
    "geo_risk": ["low", "medium", "high", "critical"],
    "ip_risk": ["low", "medium", "high", "critical"],
    "behavior_risk": ["low", "medium", "high", "critical"],
    "risk_level": ["low", "medium", "high", "critical"],
}

# Decision outcome hierarchy for counterfactuals
DECISION_HIERARCHY = {
    "block": ["review", "allow"],
    "review": ["allow"],
    "allow": [],
    "monitor": ["allow"],
}


class CounterfactualService:
    """Service for generating counterfactuals linked to real evidence."""

    def __init__(self, db_client=None, vector_store=None, llm_client=None):
        """Initialize the counterfactual service.

        Args:
            db_client: Database client for evidence pack retrieval.
            vector_store: Vector store for semantic similarity.
            llm_client: Optional LLM client for enhanced explanations.
        """
        self.db = db_client
        self.vector_store = vector_store
        self.llm_client = llm_client

    def extract_features_from_evidence(
        self, evidence_items: List[EvidenceItem]
    ) -> Dict[str, Any]:
        """Extract numeric and categorical features from evidence items.

        Args:
            evidence_items: List of evidence items to extract features from.

        Returns:
            Dict containing extracted features with their values and sources.
        """
        features: Dict[str, Any] = {}
        
        for item in evidence_items:
            payload = item.payload or {}
            if not isinstance(payload, dict):
                continue
                
            for key, value in payload.items():
                if key in FEATURE_WEIGHTS and isinstance(value, (int, float)):
                    if key not in features or abs(value) > abs(features[key]["value"]):
                        features[key] = {
                            "value": float(value),
                            "evidence_id": item.evidence_id,
                            "evidence_type": item.evidence_type,
                            "source_tool": item.source_tool,
                            "kind": "numeric",
                        }
                elif key in CATEGORICAL_LEVELS and isinstance(value, str):
                    level_idx = CATEGORICAL_LEVELS[key].index(value.lower()) if value.lower() in CATEGORICAL_LEVELS[key] else -1
                    if level_idx >= 0:
                        if key not in features or level_idx > CATEGORICAL_LEVELS[key].index(features[key]["raw"]):
                            features[key] = {
                                "value": level_idx / (len(CATEGORICAL_LEVELS[key]) - 1),
                                "raw": value.lower(),
                                "evidence_id": item.evidence_id,
                                "evidence_type": item.evidence_type,
                                "source_tool": item.source_tool,
                                "kind": "categorical",
                            }
                # Also check for score suffix patterns
                elif key.endswith("_score") and isinstance(value, (int, float)):
                    if key not in features:
                        features[key] = {
                            "value": float(value),
                            "evidence_id": item.evidence_id,
                            "evidence_type": item.evidence_type,
                            "source_tool": item.source_tool,
                            "kind": "numeric",
                        }
        
        return features

    def extract_rules_from_evidence(
        self, evidence_items: List[EvidenceItem], events: List[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Extract triggered rules from evidence and events.

        Args:
            evidence_items: List of evidence items.
            events: Optional list of run events.

        Returns:
            List of rule dictionaries with IDs and thresholds.
        """
        rules: Dict[str, Dict[str, Any]] = {}
        
        # Extract from evidence items
        for item in evidence_items:
            payload = item.payload or {}
            if isinstance(payload.get("triggered_rules"), list):
                for rule_id in payload["triggered_rules"]:
                    if rule_id and rule_id not in rules:
                        rules[rule_id] = {
                            "rule_id": rule_id,
                            "evidence_id": item.evidence_id,
                            "threshold": payload.get(f"{rule_id}_threshold"),
                            "actual_value": payload.get(f"{rule_id}_value"),
                        }
            if payload.get("rule_id"):
                rule_id = payload["rule_id"]
                if rule_id not in rules:
                    rules[rule_id] = {
                        "rule_id": rule_id,
                        "evidence_id": item.evidence_id,
                        "threshold": payload.get("threshold"),
                        "actual_value": payload.get("value"),
                    }
        
        # Extract from events
        if events:
            for event in events:
                event_payload = event.get("payload", {})
                outputs = event_payload.get("outputs", {})
                for source in [event_payload, outputs]:
                    if isinstance(source.get("triggered_rules"), list):
                        for rule_id in source["triggered_rules"]:
                            if rule_id and rule_id not in rules:
                                rules[rule_id] = {
                                    "rule_id": rule_id,
                                    "event_type": event.get("event_type"),
                                    "threshold": source.get(f"{rule_id}_threshold"),
                                    "actual_value": source.get(f"{rule_id}_value"),
                                }
                    if source.get("rule_id") and source["rule_id"] not in rules:
                        rules[source["rule_id"]] = {
                            "rule_id": source["rule_id"],
                            "event_type": event.get("event_type"),
                            "threshold": source.get("threshold"),
                            "actual_value": source.get("value"),
                        }
        
        return list(rules.values())

    def generate_feature_counterfactuals(
        self,
        features: Dict[str, Any],
        current_decision: str,
        run_metrics: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """Generate counterfactuals based on feature modifications.

        Args:
            features: Extracted features dictionary.
            current_decision: Current decision outcome.
            run_metrics: Optional run metrics for additional context.

        Returns:
            List of counterfactual dictionaries.
        """
        counterfactuals: List[Dict[str, Any]] = []
        target_outcomes = DECISION_HIERARCHY.get(current_decision, ["allow"])
        if not target_outcomes:
            return counterfactuals
        
        primary_outcome = target_outcomes[0]
        
        # Sort features by weight importance
        sorted_features = sorted(
            [(k, v) for k, v in features.items() if k in FEATURE_WEIGHTS],
            key=lambda x: FEATURE_WEIGHTS.get(x[0], 0) * x[1]["value"],
            reverse=True,
        )
        
        # Generate counterfactuals for top numeric features
        for feature_name, feature_data in sorted_features[:3]:
            if feature_data["kind"] != "numeric":
                continue
                
            value = feature_data["value"]
            weight = FEATURE_WEIGHTS.get(feature_name, 0.1)
            
            # Calculate target value based on feature type
            if "count" in feature_name or "anomal" in feature_name:
                target = max(int(round(value * 0.5)), 0)
                change_value = f"≤ {target}"
            else:
                reduction_factor = 0.7 if weight > 0.15 else 0.75
                target = round(value * reduction_factor, 3)
                change_value = f"≤ {target}"
            
            counterfactuals.append({
                "label": f"Reduce {feature_name.replace('_', ' ').title()}",
                "description": f"If {feature_name.replace('_', ' ')} was {change_value} instead of {round(value, 3)}, the decision would likely change.",
                "changes": {feature_name: change_value},
                "expected_outcome": primary_outcome,
                "confidence": round(weight * 0.9, 3),
                "evidence_links": [feature_data["evidence_id"]] if feature_data.get("evidence_id") else [],
                "feature_importance": weight,
                "original_value": round(value, 3),
                "target_value": target,
            })
        
        # Generate counterfactuals for categorical features
        categorical_features = [
            (k, v) for k, v in features.items() 
            if k in CATEGORICAL_LEVELS and v["kind"] == "categorical"
        ]
        
        for feature_name, feature_data in categorical_features[:2]:
            current_level = feature_data["raw"]
            levels = CATEGORICAL_LEVELS[feature_name]
            current_idx = levels.index(current_level) if current_level in levels else len(levels) - 1
            
            if current_idx > 0:
                target_level = levels[max(current_idx - 2, 0)]
                counterfactuals.append({
                    "label": f"Lower {feature_name.replace('_', ' ').title()}",
                    "description": f"If {feature_name.replace('_', ' ')} was '{target_level}' instead of '{current_level}', the decision would likely change.",
                    "changes": {feature_name: target_level},
                    "expected_outcome": primary_outcome,
                    "confidence": round(0.8 - (current_idx * 0.1), 3),
                    "evidence_links": [feature_data["evidence_id"]] if feature_data.get("evidence_id") else [],
                    "original_value": current_level,
                    "target_value": target_level,
                })
        
        return counterfactuals

    def generate_rule_counterfactuals(
        self,
        rules: List[Dict[str, Any]],
        current_decision: str,
    ) -> List[Dict[str, Any]]:
        """Generate counterfactuals based on rule threshold modifications.

        Args:
            rules: List of triggered rules with thresholds.
            current_decision: Current decision outcome.

        Returns:
            List of rule-based counterfactual dictionaries.
        """
        counterfactuals: List[Dict[str, Any]] = []
        target_outcomes = DECISION_HIERARCHY.get(current_decision, ["allow"])
        if not target_outcomes:
            return counterfactuals
        
        primary_outcome = target_outcomes[0]
        
        for rule in rules[:3]:
            rule_id = rule.get("rule_id", "Unknown")
            threshold = rule.get("threshold")
            actual_value = rule.get("actual_value")
            
            if threshold is not None and actual_value is not None:
                try:
                    threshold_val = float(threshold)
                    actual_val = float(actual_value)
                    
                    # Determine if value should be below or above threshold
                    if actual_val > threshold_val:
                        target = round(threshold_val * 0.9, 3)
                        counterfactuals.append({
                            "label": f"Pass rule {rule_id}",
                            "description": f"If actual value was ≤ {target} (threshold: {threshold_val}), rule {rule_id} would not trigger.",
                            "changes": {f"{rule_id}_value": f"≤ {target}"},
                            "expected_outcome": primary_outcome,
                            "confidence": 0.85,
                            "evidence_links": [rule.get("evidence_id")] if rule.get("evidence_id") else [],
                            "rule_id": rule_id,
                            "original_value": actual_val,
                            "threshold": threshold_val,
                            "target_value": target,
                        })
                except (ValueError, TypeError):
                    pass
            else:
                # Generic rule-based counterfactual
                counterfactuals.append({
                    "label": f"Avoid triggering {rule_id}",
                    "description": f"If rule {rule_id} was not triggered, the decision might change.",
                    "changes": {f"{rule_id}": "not_triggered"},
                    "expected_outcome": primary_outcome,
                    "confidence": 0.7,
                    "evidence_links": [rule.get("evidence_id")] if rule.get("evidence_id") else [],
                    "rule_id": rule_id,
                })
        
        return counterfactuals

    def generate_combined_counterfactuals(
        self,
        features: Dict[str, Any],
        rules: List[Dict[str, Any]],
        current_decision: str,
        run_metrics: Dict[str, Any] = None,
    ) -> List[Dict[str, Any]]:
        """Generate combined feature and rule counterfactuals.

        Args:
            features: Extracted features dictionary.
            rules: List of triggered rules.
            current_decision: Current decision outcome.
            run_metrics: Optional run metrics.

        Returns:
            List of combined counterfactuals, ranked by confidence.
        """
        feature_cfs = self.generate_feature_counterfactuals(
            features, current_decision, run_metrics
        )
        rule_cfs = self.generate_rule_counterfactuals(rules, current_decision)
        
        # Combine and rank by confidence
        all_cfs = feature_cfs + rule_cfs
        all_cfs.sort(key=lambda x: x.get("confidence", 0), reverse=True)
        
        return all_cfs[:5]  # Return top 5

    async def generate_llm_counterfactual_explanation(
        self,
        counterfactual: Dict[str, Any],
        context: str = "",
    ) -> str:
        """Generate LLM-enhanced explanation for a counterfactual.

        Args:
            counterfactual: The counterfactual dictionary.
            context: Additional context for the explanation.

        Returns:
            LLM-generated explanation string.
        """
        if not self.llm_client:
            return counterfactual.get("description", "")
        
        try:
            prompt = (
                "You are a fraud defense explainability agent. Generate a clear, "
                "regulator-friendly explanation for this counterfactual scenario. "
                "Keep it synthetic and defensive.\n\n"
                f"Counterfactual: {counterfactual.get('label')}\n"
                f"Changes: {json.dumps(counterfactual.get('changes', {}))}\n"
                f"Expected outcome: {counterfactual.get('expected_outcome')}\n"
                f"Context: {context}\n\n"
                "Provide a 2-3 sentence explanation."
            )
            
            response = await self.llm_client.chat_completions_create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You provide fraud defense explanations."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=150,
            )
            return response.strip()
        except Exception:
            return counterfactual.get("description", "")


class SimilarCaseService:
    """Service for retrieving similar cases linked to real evidence."""

    def __init__(self, db_client=None, vector_store=None):
        """Initialize the similar case service.

        Args:
            db_client: Database client for evidence pack retrieval.
            vector_store: Vector store for semantic similarity.
        """
        self.db = db_client
        self.vector_store = vector_store

    def build_case_signature(
        self,
        run_id: str,
        decision: str,
        evidence_items: List[EvidenceItem],
        events: List[Dict[str, Any]] = None,
        run_metrics: Dict[str, Any] = None,
    ) -> Dict[str, Any]:
        """Build a comprehensive case signature for similarity matching.

        Args:
            run_id: Run identifier.
            decision: Decision outcome.
            evidence_items: List of evidence items.
            events: Optional list of run events.
            run_metrics: Optional run metrics.

        Returns:
            Case signature dictionary.
        """
        # Extract rules
        rules = set()
        for item in evidence_items:
            payload = item.payload or {}
            if isinstance(payload.get("triggered_rules"), list):
                rules.update(payload["triggered_rules"])
            if payload.get("rule_id"):
                rules.add(payload["rule_id"])
        
        if events:
            for event in events:
                payload = event.get("payload", {})
                outputs = payload.get("outputs", {})
                for source in [payload, outputs]:
                    if isinstance(source.get("triggered_rules"), list):
                        rules.update(source["triggered_rules"])
                    if source.get("rule_id"):
                        rules.add(source["rule_id"])
        
        # Extract artifact types
        artifacts = set()
        for item in evidence_items:
            artifacts.add(f"evidence:{item.evidence_type}")
            if item.source_tool:
                artifacts.add(f"tool:{item.source_tool}")
        
        if events:
            for event in events:
                if event.get("event_type"):
                    artifacts.add(f"event:{event['event_type']}")
                payload = event.get("payload", {})
                if payload.get("team"):
                    artifacts.add(f"team:{payload['team']}")
                if payload.get("agent"):
                    artifacts.add(f"agent:{payload['agent']}")
        
        # Extract tokens for text similarity
        token_source = " ".join([item.summary for item in evidence_items])
        tokens = set(re.split(r"[^a-zA-Z0-9]+", token_source.lower()))
        tokens = {t for t in tokens if t and len(t) > 2}
        
        # Extract numeric metrics
        metrics = {}
        if run_metrics:
            for key in ["avg_score", "risk_score", "success_rate", "detection_rate"]:
                if isinstance(run_metrics.get(key), (int, float)):
                    metrics[key] = float(run_metrics[key])
        
        # Extract feature values
        features = {}
        for item in evidence_items:
            payload = item.payload or {}
            for key in FEATURE_WEIGHTS:
                if isinstance(payload.get(key), (int, float)):
                    features[key] = float(payload[key])
        
        return {
            "run_id": run_id,
            "decision": decision,
            "rules": rules,
            "artifacts": artifacts,
            "tokens": tokens,
            "metrics": metrics,
            "features": features,
            "evidence_count": len(evidence_items),
            "signature_hash": self._compute_signature_hash(rules, artifacts, decision),
        }

    def _compute_signature_hash(
        self, rules: set, artifacts: set, decision: str
    ) -> str:
        """Compute a hash for the case signature.

        Args:
            rules: Set of triggered rules.
            artifacts: Set of artifact types.
            decision: Decision outcome.

        Returns:
            SHA-256 hash of the signature.
        """
        content = json.dumps({
            "rules": sorted(list(rules)),
            "artifacts": sorted(list(artifacts)),
            "decision": decision,
        }, sort_keys=True)
        return hashlib.sha256(content.encode()).hexdigest()[:16]

    def build_pack_signature(self, pack: Dict[str, Any]) -> Dict[str, Any]:
        """Build a signature from an evidence pack for comparison.

        Args:
            pack: Evidence pack dictionary.

        Returns:
            Pack signature dictionary.
        """
        rules = set(pack.get("triggered_rules") or [])
        
        artifacts = set()
        for artifact in pack.get("artifacts") or []:
            if artifact.get("event_type"):
                artifacts.add(f"event:{artifact['event_type']}")
            if artifact.get("agent"):
                artifacts.add(f"agent:{artifact['agent']}")
            if artifact.get("team"):
                artifacts.add(f"team:{artifact['team']}")
        
        # Extract tokens from narrative and XAI bundle
        summary = pack.get("narrative", "")
        xai_bundle = pack.get("xai_bundle") or {}
        if xai_bundle.get("summary"):
            summary = f"{summary} {xai_bundle['summary']}"
        tokens = set(re.split(r"[^a-zA-Z0-9]+", summary.lower()))
        tokens = {t for t in tokens if t and len(t) > 2}
        
        # Extract metrics
        metrics = {}
        pack_metrics = pack.get("metrics") or {}
        for key in ["avg_score", "risk_score", "success_rate", "detection_rate"]:
            if isinstance(pack_metrics.get(key), (int, float)):
                metrics[key] = float(pack_metrics[key])
        
        # Extract decision
        decision = pack_metrics.get("decision") or xai_bundle.get("decision_id")
        
        return {
            "pack_id": pack.get("id"),
            "run_id": pack.get("run_id"),
            "battle_id": pack.get("battle_id"),
            "decision": decision,
            "rules": rules,
            "artifacts": artifacts,
            "tokens": tokens,
            "metrics": metrics,
            "evidence_count": len(pack.get("artifacts") or []),
            "signature_hash": self._compute_signature_hash(rules, artifacts, decision or ""),
        }

    def score_similarity(
        self,
        current: Dict[str, Any],
        candidate: Dict[str, Any],
    ) -> Tuple[float, Dict[str, Any]]:
        """Score the similarity between two case signatures.

        Args:
            current: Current case signature.
            candidate: Candidate case signature.

        Returns:
            Tuple of (similarity_score, detailed_breakdown).
        """
        def jaccard(left: set, right: set) -> float:
            if not left or not right:
                return 0.0
            return len(left & right) / max(len(left | right), 1)

        def numeric_similarity(val1: Optional[float], val2: Optional[float]) -> float:
            if val1 is None or val2 is None:
                return 0.0
            gap = abs(val1 - val2)
            return max(1.0 - min(gap, 1.0), 0.0)

        # Compute individual similarity scores
        rules_score = jaccard(current.get("rules", set()), candidate.get("rules", set()))
        artifacts_score = jaccard(current.get("artifacts", set()), candidate.get("artifacts", set()))
        tokens_score = jaccard(current.get("tokens", set()), candidate.get("tokens", set()))
        
        # Decision match
        decision_match = 1.0 if (
            current.get("decision") and 
            current.get("decision") == candidate.get("decision")
        ) else 0.0
        
        # Metric similarity (average of available metrics)
        current_metrics = current.get("metrics", {})
        candidate_metrics = candidate.get("metrics", {})
        metric_scores = []
        for key in ["avg_score", "risk_score"]:
            if key in current_metrics and key in candidate_metrics:
                metric_scores.append(numeric_similarity(
                    current_metrics[key], candidate_metrics[key]
                ))
        metric_score = sum(metric_scores) / max(len(metric_scores), 1) if metric_scores else 0.0
        
        # Feature similarity
        current_features = current.get("features", {})
        candidate_features = candidate.get("features", {})
        feature_scores = []
        for key in FEATURE_WEIGHTS:
            if key in current_features and key in candidate_features:
                feature_scores.append(numeric_similarity(
                    current_features[key], candidate_features[key]
                ))
        feature_score = sum(feature_scores) / max(len(feature_scores), 1) if feature_scores else 0.0
        
        # Hash match bonus (exact signature match)
        hash_bonus = 0.1 if (
            current.get("signature_hash") and 
            current.get("signature_hash") == candidate.get("signature_hash")
        ) else 0.0
        
        # Weighted combination
        weights = {
            "rules": 0.25,
            "artifacts": 0.15,
            "tokens": 0.15,
            "decision": 0.15,
            "metrics": 0.15,
            "features": 0.15,
        }
        
        similarity = (
            rules_score * weights["rules"] +
            artifacts_score * weights["artifacts"] +
            tokens_score * weights["tokens"] +
            decision_match * weights["decision"] +
            metric_score * weights["metrics"] +
            feature_score * weights["features"] +
            hash_bonus
        )
        
        # Find matched rules and artifacts
        matched_rules = list(current.get("rules", set()) & candidate.get("rules", set()))
        matched_artifacts = list(current.get("artifacts", set()) & candidate.get("artifacts", set()))
        
        details = {
            "rules": round(rules_score, 4),
            "artifacts": round(artifacts_score, 4),
            "tokens": round(tokens_score, 4),
            "decision": round(decision_match, 4),
            "metrics": round(metric_score, 4),
            "features": round(feature_score, 4),
            "hash_bonus": round(hash_bonus, 4),
            "matched_rules": matched_rules,
            "matched_artifacts": matched_artifacts,
            "weights": weights,
        }
        
        return round(min(similarity, 1.0), 4), details

    async def find_similar_cases(
        self,
        current_signature: Dict[str, Any],
        packs: List[Dict[str, Any]],
        exclude_run_id: str = None,
        min_similarity: float = 0.2,
        max_results: int = 5,
    ) -> List[Dict[str, Any]]:
        """Find similar cases from evidence packs.

        Args:
            current_signature: Current case signature.
            packs: List of evidence packs to search.
            exclude_run_id: Run ID to exclude from results.
            min_similarity: Minimum similarity threshold.
            max_results: Maximum number of results.

        Returns:
            List of similar case dictionaries.
        """
        similar_cases = []
        
        for pack in packs:
            if exclude_run_id and pack.get("run_id") == exclude_run_id:
                continue
            
            candidate_signature = self.build_pack_signature(pack)
            similarity, details = self.score_similarity(current_signature, candidate_signature)
            
            if similarity < min_similarity:
                continue
            
            similar_cases.append({
                "case_id": pack.get("id"),
                "run_id": pack.get("run_id"),
                "battle_id": pack.get("battle_id"),
                "summary": pack.get("narrative", "Evidence pack summary"),
                "similarity": similarity,
                "metadata": {
                    "evidence_pack_id": pack.get("id"),
                    "matched_rules": details.get("matched_rules", []),
                    "matched_artifacts": details.get("matched_artifacts", []),
                    "score_breakdown": details,
                    "decision": candidate_signature.get("decision"),
                    "evidence_count": candidate_signature.get("evidence_count", 0),
                    "created_at": pack.get("created_at"),
                },
            })
        
        # Sort by similarity and return top results
        similar_cases.sort(key=lambda x: x["similarity"], reverse=True)
        return similar_cases[:max_results]

    async def find_similar_by_vector(
        self,
        query_embedding: List[float],
        collection: str = "evidence_packs",
        top_k: int = 10,
        min_score: float = 0.5,
    ) -> List[Dict[str, Any]]:
        """Find similar cases using vector similarity.

        Args:
            query_embedding: Query embedding vector.
            collection: Vector store collection name.
            top_k: Number of results to retrieve.
            min_score: Minimum similarity score.

        Returns:
            List of similar case dictionaries.
        """
        if not self.vector_store:
            return []
        
        try:
            results = await self.vector_store.query(
                collection_name=collection,
                query_embeddings=[query_embedding],
                n_results=top_k,
            )
            
            similar_cases = []
            for i, (doc_id, score) in enumerate(zip(
                results.get("ids", [[]])[0],
                results.get("distances", [[]])[0],
            )):
                if score >= min_score:
                    metadata = results.get("metadatas", [[]])[0][i] if results.get("metadatas") else {}
                    similar_cases.append({
                        "case_id": doc_id,
                        "summary": results.get("documents", [[]])[0][i] if results.get("documents") else "",
                        "similarity": round(score, 4),
                        "metadata": metadata,
                    })
            
            return similar_cases
        except Exception:
            return []


def build_enhanced_explanation_bundle(
    run_id: str,
    decision: str,
    evidence_items: List[EvidenceItem],
    events: List[Dict[str, Any]] = None,
    run_metrics: Dict[str, Any] = None,
    similar_packs: List[Dict[str, Any]] = None,
) -> ExplanationBundle:
    """Build an enhanced explanation bundle with counterfactuals and similar cases.

    Args:
        run_id: Run identifier.
        decision: Decision outcome.
        evidence_items: List of evidence items.
        events: Optional list of run events.
        run_metrics: Optional run metrics.
        similar_packs: Optional list of evidence packs for similar case matching.

    Returns:
        ExplanationBundle with counterfactuals and similar cases.
    """
    from app.xai_utils import build_evidence_graph
    
    # Initialize services
    cf_service = CounterfactualService()
    sc_service = SimilarCaseService()
    
    # Extract features and rules
    features = cf_service.extract_features_from_evidence(evidence_items)
    rules = cf_service.extract_rules_from_evidence(evidence_items, events)
    
    # Generate counterfactuals
    counterfactuals = cf_service.generate_combined_counterfactuals(
        features, rules, decision, run_metrics
    )
    
    # Build case signature and find similar cases
    similar_cases = []
    if similar_packs:
        current_signature = sc_service.build_case_signature(
            run_id, decision, evidence_items, events, run_metrics
        )
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # Already in async context
                similar_cases = []  # Will be populated async
            else:
                similar_cases = loop.run_until_complete(
                    sc_service.find_similar_cases(
                        current_signature, similar_packs, exclude_run_id=run_id
                    )
                )
        except RuntimeError:
            similar_cases = []
    
    # Build evidence graph
    evidence_graph = build_evidence_graph(run_id, evidence_items)
    
    # Build summary
    evidence_types = ", ".join({item.evidence_type for item in evidence_items} or {"signals"})
    summary = f"Decision '{decision}' derived from {len(evidence_items)} evidence items for run {run_id[:8] if len(run_id) > 8 else run_id}."
    details = f"Evidence includes: {evidence_types}. Counterfactuals suggest {len(counterfactuals)} potential outcome changes."
    confidence_statement = "Confidence reflects observed run telemetry, evidence coverage, and similar case matches."
    
    return ExplanationBundle(
        decision_id=decision,
        summary=summary,
        details=details,
        evidence=evidence_items,
        confidence_statement=confidence_statement,
        evidence_graph=evidence_graph.model_dump(),
        counterfactuals=counterfactuals,
        similar_cases=similar_cases,
    )
