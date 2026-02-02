"""Historical Metrics Aggregation Service.

Provides time-series aggregations and historical data for dashboard charts.
"""

from typing import Dict, Any, List, Optional
from datetime import datetime, timezone, timedelta
from collections import defaultdict


class HistoricalMetricsAggregator:
    """Aggregates historical metrics from MongoDB run events and telemetry."""

    def __init__(self, db_client):
        """Initialize aggregator with database client.

        Args:
            db_client: MongoDB database client
        """
        self.db = db_client

    async def get_time_series_metrics(
        self,
        days: int = 30,
        granularity: str = "daily"
    ) -> List[Dict[str, Any]]:
        """Get time-series metrics for dashboard charts.

        Args:
            days: Number of days to include in time series
            granularity: Time bucket size ('hourly', 'daily', 'weekly')

        Returns:
            List of time-series data points with aggregated metrics
        """
        # Calculate date range
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(days=days)

        # Fetch all runs in date range
        runs = await self.db.runs.find(
            {
                "started_at": {"$gte": start_date.isoformat()},
                "status": {"$in": ["completed", "running", "failed"]},
            },
            {"_id": 0}
        ).to_list(10000)

        # Fetch all run events
        run_ids = [r.get("id") for r in runs if r.get("id")]
        run_events = await self.db.run_events.find(
            {"run_id": {"$in": run_ids}},
            {"_id": 0}
        ).to_list(50000)

        # Fetch artifacts
        artifacts = await self.db.agent_artifacts.find(
            {"run_id": {"$in": run_ids}},
            {"_id": 0, "run_id": 1, "created_at": 1}
        ).to_list(50000)

        # Group by time buckets
        time_buckets = self._create_time_buckets(start_date, end_date, granularity)
        aggregated_data = defaultdict(lambda: {
            "total_runs": 0,
            "completed_runs": 0,
            "failed_runs": 0,
            "success_rate_values": [],
            "time_to_immunity_values": [],
            "patterns_learned": 0,
            "avg_risk_scores": [],
            "blocked_actions": 0,
            "total_actions": 0,
        })

        # Process runs into time buckets
        for run in runs:
            started_at = run.get("started_at")
            if not started_at:
                continue

            bucket_key = self._get_bucket_key(started_at, granularity)
            if bucket_key not in time_buckets:
                continue

            bucket = aggregated_data[bucket_key]
            bucket["total_runs"] += 1

            status = run.get("status")
            if status == "completed":
                bucket["completed_runs"] += 1
            elif status == "failed":
                bucket["failed_runs"] += 1

            # Add time to immunity (step count)
            step_count = run.get("step_count", 0) or 0
            bucket["time_to_immunity_values"].append(step_count)

            # Add risk score
            metrics = run.get("last_metrics", {})
            avg_score = metrics.get("avg_score")
            if isinstance(avg_score, (int, float)):
                bucket["avg_risk_scores"].append(float(avg_score))

        # Process run events for actions and success rates
        events_by_run = defaultdict(list)
        for event in run_events:
            run_id = event.get("run_id")
            if run_id:
                events_by_run[run_id].append(event)

        for run in runs:
            run_id = run.get("id")
            started_at = run.get("started_at")
            if not run_id or not started_at:
                continue

            bucket_key = self._get_bucket_key(started_at, granularity)
            if bucket_key not in time_buckets:
                continue

            bucket = aggregated_data[bucket_key]
            events = events_by_run.get(run_id, [])

            # Calculate actions
            actions_total = 0
            actions_blocked = 0

            for event in events:
                if event.get("event_type") not in {"agent.output", "orchestrator.output"}:
                    continue

                outputs = (event.get("payload") or {}).get("outputs") or {}
                respond = outputs.get("respond_actions") or outputs.get("respond") or {}
                actions = respond.get("actions") or []

                if isinstance(actions, list):
                    for action in actions:
                        actions_total += 1
                        if action.get("action") == "block":
                            actions_blocked += 1

            bucket["total_actions"] += actions_total
            bucket["blocked_actions"] += actions_blocked

            # Calculate success rate for this run
            if actions_total > 0:
                success_rate = (actions_blocked / actions_total) * 100
                bucket["success_rate_values"].append(success_rate)

        # Process artifacts for patterns learned
        for artifact in artifacts:
            created_at = artifact.get("created_at")
            if not created_at:
                continue

            bucket_key = self._get_bucket_key(created_at, granularity)
            if bucket_key in time_buckets:
                aggregated_data[bucket_key]["patterns_learned"] += 1

        # Convert to time series format
        time_series = []
        for bucket_key in sorted(time_buckets.keys()):
            data = aggregated_data[bucket_key]

            # Calculate averages
            avg_success_rate = (
                sum(data["success_rate_values"]) / len(data["success_rate_values"])
                if data["success_rate_values"]
                else 0
            )

            avg_time_to_immunity = (
                sum(data["time_to_immunity_values"]) / len(data["time_to_immunity_values"])
                if data["time_to_immunity_values"]
                else 0
            )

            avg_risk_score = (
                sum(data["avg_risk_scores"]) / len(data["avg_risk_scores"])
                if data["avg_risk_scores"]
                else 0
            )

            time_series.append({
                "timestamp": bucket_key,
                "total_runs": data["total_runs"],
                "completed_runs": data["completed_runs"],
                "failed_runs": data["failed_runs"],
                "success_rate": round(avg_success_rate, 2),
                "time_to_immunity": round(avg_time_to_immunity, 2),
                "patterns_learned": data["patterns_learned"],
                "avg_risk_score": round(avg_risk_score, 2),
                "total_actions": data["total_actions"],
                "blocked_actions": data["blocked_actions"],
            })

        return time_series

    async def get_aggregated_dashboard_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get aggregated metrics for dashboard summary cards.

        Args:
            days: Number of days to aggregate

        Returns:
            Dictionary with aggregated metrics
        """
        # Get time series data
        time_series = await self.get_time_series_metrics(days=days)

        # Calculate overall aggregates
        total_runs = sum(item["total_runs"] for item in time_series)
        total_completed = sum(item["completed_runs"] for item in time_series)
        total_patterns = sum(item["patterns_learned"] for item in time_series)

        success_rates = [item["success_rate"] for item in time_series if item["success_rate"] > 0]
        avg_success_rate = sum(success_rates) / len(success_rates) if success_rates else 0

        time_to_immunity_values = [
            item["time_to_immunity"] for item in time_series if item["time_to_immunity"] > 0
        ]
        avg_time_to_immunity = (
            sum(time_to_immunity_values) / len(time_to_immunity_values)
            if time_to_immunity_values
            else 0
        )

        total_actions = sum(item["total_actions"] for item in time_series)
        total_blocked = sum(item["blocked_actions"] for item in time_series)
        block_rate = (total_blocked / total_actions * 100) if total_actions > 0 else 0

        return {
            "period_days": days,
            "total_battles": total_runs,
            "completed_battles": total_completed,
            "avg_success_rate": round(avg_success_rate, 2),
            "patterns_learned": total_patterns,
            "avg_time_to_immunity": round(avg_time_to_immunity, 2),
            "total_actions": total_actions,
            "blocked_actions": total_blocked,
            "block_rate": round(block_rate, 2),
            "time_series": time_series,
        }

    async def get_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """Analyze trends in metrics over time.

        Args:
            days: Number of days to analyze

        Returns:
            Dictionary with trend analysis
        """
        time_series = await self.get_time_series_metrics(days=days)

        if len(time_series) < 2:
            return {
                "success_rate_trend": "stable",
                "run_volume_trend": "stable",
                "patterns_trend": "stable",
            }

        # Calculate trends (comparing first half to second half)
        midpoint = len(time_series) // 2
        first_half = time_series[:midpoint]
        second_half = time_series[midpoint:]

        # Success rate trend
        first_success = sum(item["success_rate"] for item in first_half) / len(first_half)
        second_success = sum(item["success_rate"] for item in second_half) / len(second_half)
        success_change = ((second_success - first_success) / first_success * 100) if first_success > 0 else 0

        # Run volume trend
        first_runs = sum(item["total_runs"] for item in first_half) / len(first_half)
        second_runs = sum(item["total_runs"] for item in second_half) / len(second_half)
        runs_change = ((second_runs - first_runs) / first_runs * 100) if first_runs > 0 else 0

        # Patterns learned trend
        first_patterns = sum(item["patterns_learned"] for item in first_half) / len(first_half)
        second_patterns = sum(item["patterns_learned"] for item in second_half) / len(second_half)
        patterns_change = ((second_patterns - first_patterns) / first_patterns * 100) if first_patterns > 0 else 0

        def _trend(change: float) -> str:
            if change > 5:
                return "increasing"
            elif change < -5:
                return "decreasing"
            return "stable"

        return {
            "success_rate_trend": _trend(success_change),
            "success_rate_change_pct": round(success_change, 2),
            "run_volume_trend": _trend(runs_change),
            "run_volume_change_pct": round(runs_change, 2),
            "patterns_trend": _trend(patterns_change),
            "patterns_change_pct": round(patterns_change, 2),
        }

    def _create_time_buckets(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str
    ) -> Dict[str, datetime]:
        """Create time bucket keys for aggregation.

        Args:
            start_date: Start of time range
            end_date: End of time range
            granularity: Bucket size ('hourly', 'daily', 'weekly')

        Returns:
            Dictionary mapping bucket keys to datetime objects
        """
        buckets = {}
        current = start_date

        if granularity == "hourly":
            delta = timedelta(hours=1)
        elif granularity == "weekly":
            delta = timedelta(weeks=1)
        else:  # daily
            delta = timedelta(days=1)

        while current <= end_date:
            key = self._get_bucket_key(current.isoformat(), granularity)
            buckets[key] = current
            current += delta

        return buckets

    def _get_bucket_key(self, timestamp: str, granularity: str) -> str:
        """Get bucket key for a timestamp.

        Args:
            timestamp: ISO formatted timestamp string
            granularity: Bucket size ('hourly', 'daily', 'weekly')

        Returns:
            Bucket key string
        """
        try:
            dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        except (ValueError, AttributeError):
            return ""

        if granularity == "hourly":
            return dt.strftime("%Y-%m-%dT%H:00:00Z")
        elif granularity == "weekly":
            # Get Monday of the week
            start_of_week = dt - timedelta(days=dt.weekday())
            return start_of_week.strftime("%Y-%m-%d")
        else:  # daily
            return dt.strftime("%Y-%m-%d")
