"""Tests for Historical Metrics Aggregation.

Tests time-series aggregation and dashboard metrics computation.
"""

import pytest
from datetime import datetime, timezone, timedelta
from app.services.metrics.historical_aggregator import HistoricalMetricsAggregator


class MockDB:
    """Mock database client for testing."""

    def __init__(self):
        self.runs = MockCollection()
        self.run_events = MockCollection()
        self.agent_artifacts = MockCollection()


class MockCollection:
    """Mock MongoDB collection."""

    def __init__(self):
        self._data = []

    def set_data(self, data):
        """Set test data."""
        self._data = data

    def find(self, query, projection=None):
        """Mock find method."""
        return self

    def sort(self, field, direction):
        """Mock sort method."""
        return self

    async def to_list(self, limit):
        """Mock to_list method."""
        return self._data[:limit]


@pytest.fixture
def mock_db():
    """Fixture for mock database."""
    return MockDB()


@pytest.fixture
def aggregator(mock_db):
    """Fixture for aggregator."""
    return HistoricalMetricsAggregator(mock_db)


@pytest.fixture
def sample_runs():
    """Sample run data for testing."""
    base_time = datetime.now(timezone.utc) - timedelta(days=10)
    runs = []

    for i in range(20):
        run_time = base_time + timedelta(days=i // 2)  # 2 runs per day
        runs.append({
            "id": f"run_{i}",
            "status": "completed" if i % 3 != 0 else "failed",
            "started_at": run_time.isoformat(),
            "step_count": 5 + i % 10,
            "last_metrics": {
                "avg_score": 0.5 + (i % 5) * 0.1,
            },
        })

    return runs


@pytest.fixture
def sample_events():
    """Sample event data for testing."""
    events = []

    for run_idx in range(20):
        run_id = f"run_{run_idx}"

        # Add output events with actions
        for event_idx in range(3):
            events.append({
                "run_id": run_id,
                "event_type": "agent.output",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "payload": {
                    "outputs": {
                        "respond_actions": {
                            "actions": [
                                {"action": "block"},
                                {"action": "allow"},
                                {"action": "block" if event_idx % 2 == 0 else "review"},
                            ],
                            "decision": "block" if event_idx % 2 == 0 else "allow",
                        },
                        "score_risk": {
                            "avg_score": 0.7,
                        },
                    },
                },
            })

    return events


@pytest.fixture
def sample_artifacts():
    """Sample artifact data for testing."""
    base_time = datetime.now(timezone.utc) - timedelta(days=10)
    artifacts = []

    for run_idx in range(20):
        run_id = f"run_{run_idx}"
        run_time = base_time + timedelta(days=run_idx // 2)

        # Add 3 artifacts per run
        for _ in range(3):
            artifacts.append({
                "run_id": run_id,
                "created_at": run_time.isoformat(),
            })

    return artifacts


class TestHistoricalMetricsAggregator:
    """Test historical metrics aggregation."""

    @pytest.mark.asyncio
    async def test_time_series_daily_granularity(
        self, aggregator, mock_db, sample_runs, sample_events, sample_artifacts
    ):
        """Test daily time-series aggregation."""
        mock_db.runs.set_data(sample_runs)
        mock_db.run_events.set_data(sample_events)
        mock_db.agent_artifacts.set_data(sample_artifacts)

        time_series = await aggregator.get_time_series_metrics(days=15, granularity="daily")

        assert isinstance(time_series, list)
        assert len(time_series) > 0

        # Check data structure
        for item in time_series:
            assert "timestamp" in item
            assert "total_runs" in item
            assert "completed_runs" in item
            assert "failed_runs" in item
            assert "success_rate" in item
            assert "time_to_immunity" in item
            assert "patterns_learned" in item

    @pytest.mark.asyncio
    async def test_time_series_hourly_granularity(
        self, aggregator, mock_db, sample_runs, sample_events, sample_artifacts
    ):
        """Test hourly time-series aggregation."""
        mock_db.runs.set_data(sample_runs)
        mock_db.run_events.set_data(sample_events)
        mock_db.agent_artifacts.set_data(sample_artifacts)

        time_series = await aggregator.get_time_series_metrics(days=7, granularity="hourly")

        assert isinstance(time_series, list)
        # Hourly buckets should produce more data points
        # (but may be empty if no data in those hours)

    @pytest.mark.asyncio
    async def test_aggregated_dashboard_metrics(
        self, aggregator, mock_db, sample_runs, sample_events, sample_artifacts
    ):
        """Test aggregated dashboard metrics."""
        mock_db.runs.set_data(sample_runs)
        mock_db.run_events.set_data(sample_events)
        mock_db.agent_artifacts.set_data(sample_artifacts)

        metrics = await aggregator.get_aggregated_dashboard_metrics(days=30)

        assert "total_battles" in metrics
        assert "completed_battles" in metrics
        assert "avg_success_rate" in metrics
        assert "patterns_learned" in metrics
        assert "avg_time_to_immunity" in metrics
        assert "time_series" in metrics
        assert "period_days" in metrics

        assert metrics["period_days"] == 30
        assert isinstance(metrics["time_series"], list)

    @pytest.mark.asyncio
    async def test_trend_analysis(
        self, aggregator, mock_db, sample_runs, sample_events, sample_artifacts
    ):
        """Test trend analysis."""
        mock_db.runs.set_data(sample_runs)
        mock_db.run_events.set_data(sample_events)
        mock_db.agent_artifacts.set_data(sample_artifacts)

        trends = await aggregator.get_trend_analysis(days=30)

        assert "success_rate_trend" in trends
        assert "run_volume_trend" in trends
        assert "patterns_trend" in trends

        # Trends should be one of: increasing, decreasing, stable
        assert trends["success_rate_trend"] in ["increasing", "decreasing", "stable"]
        assert trends["run_volume_trend"] in ["increasing", "decreasing", "stable"]
        assert trends["patterns_trend"] in ["increasing", "decreasing", "stable"]

    @pytest.mark.asyncio
    async def test_empty_data(self, aggregator, mock_db):
        """Test handling of empty data."""
        mock_db.runs.set_data([])
        mock_db.run_events.set_data([])
        mock_db.agent_artifacts.set_data([])

        time_series = await aggregator.get_time_series_metrics(days=7)

        assert isinstance(time_series, list)
        # Should return empty buckets with zero values

    def test_bucket_key_generation_daily(self, aggregator):
        """Test daily bucket key generation."""
        timestamp = "2026-02-01T15:30:00Z"
        key = aggregator._get_bucket_key(timestamp, "daily")

        assert key == "2026-02-01"

    def test_bucket_key_generation_hourly(self, aggregator):
        """Test hourly bucket key generation."""
        timestamp = "2026-02-01T15:30:00Z"
        key = aggregator._get_bucket_key(timestamp, "hourly")

        assert key == "2026-02-01T15:00:00Z"

    def test_bucket_key_generation_weekly(self, aggregator):
        """Test weekly bucket key generation."""
        # Wednesday 2026-02-04
        timestamp = "2026-02-04T15:30:00Z"
        key = aggregator._get_bucket_key(timestamp, "weekly")

        # Should return Monday of that week (2026-02-02)
        assert key == "2026-02-02"

    def test_create_time_buckets_daily(self, aggregator):
        """Test daily time bucket creation."""
        start = datetime(2026, 2, 1, tzinfo=timezone.utc)
        end = datetime(2026, 2, 5, tzinfo=timezone.utc)

        buckets = aggregator._create_time_buckets(start, end, "daily")

        assert len(buckets) >= 4  # At least 4 days
        assert "2026-02-01" in buckets
        assert "2026-02-05" in buckets

    def test_create_time_buckets_hourly(self, aggregator):
        """Test hourly time bucket creation."""
        start = datetime(2026, 2, 1, 0, 0, tzinfo=timezone.utc)
        end = datetime(2026, 2, 1, 5, 0, tzinfo=timezone.utc)

        buckets = aggregator._create_time_buckets(start, end, "hourly")

        assert len(buckets) >= 5  # At least 5 hours


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.mark.asyncio
    async def test_realistic_battle_scenario(self, aggregator, mock_db):
        """Test with realistic battle data."""
        # Create 30 days of battle data
        base_time = datetime.now(timezone.utc) - timedelta(days=30)
        runs = []
        events = []
        artifacts = []

        for day in range(30):
            day_time = base_time + timedelta(days=day)

            # 3-5 battles per day
            for battle in range(3 + day % 3):
                run_id = f"run_day{day}_battle{battle}"

                runs.append({
                    "id": run_id,
                    "status": "completed",
                    "started_at": day_time.isoformat(),
                    "step_count": 8 + battle % 5,
                    "last_metrics": {
                        "avg_score": 0.6 + (day % 4) * 0.05,
                    },
                })

                # Events per battle
                for event_num in range(5):
                    events.append({
                        "run_id": run_id,
                        "event_type": "agent.output",
                        "created_at": day_time.isoformat(),
                        "payload": {
                            "outputs": {
                                "respond_actions": {
                                    "actions": [
                                        {"action": "block"},
                                        {"action": "allow"},
                                    ],
                                },
                            },
                        },
                    })

                # Artifacts per battle
                for _ in range(4):
                    artifacts.append({
                        "run_id": run_id,
                        "created_at": day_time.isoformat(),
                    })

        mock_db.runs.set_data(runs)
        mock_db.run_events.set_data(events)
        mock_db.agent_artifacts.set_data(artifacts)

        metrics = await aggregator.get_aggregated_dashboard_metrics(days=30)

        assert metrics["total_battles"] > 0
        assert metrics["patterns_learned"] > 0
        assert len(metrics["time_series"]) > 0

    @pytest.mark.asyncio
    async def test_performance_with_large_dataset(self, aggregator, mock_db):
        """Test performance with large data set."""
        import time

        # Create large dataset
        base_time = datetime.now(timezone.utc) - timedelta(days=30)
        runs = []

        for i in range(1000):  # 1000 runs
            run_time = base_time + timedelta(hours=i)
            runs.append({
                "id": f"run_{i}",
                "status": "completed",
                "started_at": run_time.isoformat(),
                "step_count": 10,
                "last_metrics": {"avg_score": 0.7},
            })

        mock_db.runs.set_data(runs)
        mock_db.run_events.set_data([])
        mock_db.agent_artifacts.set_data([])

        start_time = time.time()
        await aggregator.get_time_series_metrics(days=30)
        elapsed = time.time() - start_time

        # Should complete in reasonable time (< 5 seconds)
        assert elapsed < 5.0
