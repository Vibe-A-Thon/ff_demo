"""Tests for Brain Surgery Service - APMC hot-swap, merge, and rollback operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

# Mock DB before importing the service
@pytest.fixture
def mock_db():
    """Mock database for testing."""
    with patch("app.services.capsules.amc.brain_surgery_service.db") as mock:
        mock.brain_surgery_sessions = MagicMock()
        mock.amc_states = MagicMock()
        mock.amc_rollback_snapshots = MagicMock()
        mock.amc_activations = MagicMock()
        mock.amc_rollbacks = MagicMock()
        mock.teams = MagicMock()
        mock.agents = MagicMock()
        mock.agent_artifacts = MagicMock()
        mock.agent_tasks = MagicMock()
        yield mock


@pytest.fixture
def brain_surgery_service(mock_db):
    """Create a fresh BrainSurgeryService instance."""
    from app.services.capsules.amc.brain_surgery_service import BrainSurgeryService
    return BrainSurgeryService()


@pytest.fixture
def sample_baseline_snapshot():
    """Sample baseline snapshot for testing."""
    return {
        "team_id": "blue",
        "team_name": "Blue Team",
        "agent_count": 3,
        "memory_counts": {
            "agent-blue-01": {"semantic": 10, "episodic": 5},
            "agent-blue-02": {"semantic": 8, "episodic": 3},
            "agent-blue-03": {"semantic": 12, "episodic": 7},
        },
        "agents": [
            {"agent_id": "agent-blue-01", "name": "Blue Orchestrator", "role": "Orchestrator", "semantic": 10, "episodic": 5},
            {"agent_id": "agent-blue-02", "name": "Blue Detector", "role": "Detector", "semantic": 8, "episodic": 3},
            {"agent_id": "agent-blue-03", "name": "Blue Responder", "role": "Responder", "semantic": 12, "episodic": 7},
        ],
        "totals": {"semantic": 30, "episodic": 15},
        "source": "baseline",
    }


class TestBrainSurgeryService:
    """Test suite for BrainSurgeryService."""

    @pytest.mark.asyncio
    async def test_start_surgery_session_without_amc(self, brain_surgery_service, mock_db, sample_baseline_snapshot):
        """Test starting a surgery session without an AMC file."""
        # Setup
        mock_db.brain_surgery_sessions.update_one = AsyncMock()
        
        with patch(
            "app.services.capsules.amc.brain_surgery_service.build_baseline_snapshot",
            new_callable=AsyncMock,
            return_value=sample_baseline_snapshot,
        ):
            # Execute
            session = await brain_surgery_service.start_surgery_session(
                team_id="blue",
                actor_id="test-user",
                amc_payload=None,
            )
        
        # Assert
        assert session is not None
        assert session["team_id"] == "blue"
        assert session["actor_id"] == "test-user"
        assert session["status"] == "initialized"
        assert session["baseline"] == sample_baseline_snapshot
        assert session["import_preview"] is None
        assert session["hot_swap_ready"] is False
        assert "session_id" in session
        assert session["session_id"].startswith("surgery_blue_")

    @pytest.mark.asyncio
    async def test_resolve_conflict(self, brain_surgery_service, mock_db):
        """Test resolving a conflict in a surgery session."""
        # Setup
        session_id = "surgery_blue_20260202_120000"
        initial_session = {
            "session_id": session_id,
            "team_id": "blue",
            "conflicts": [
                {
                    "id": "conflict_1",
                    "type": "role_change",
                    "title": "Role change",
                    "detail": "Test conflict",
                    "resolution": None,
                },
            ],
            "status": "conflicts_detected",
        }
        brain_surgery_service.active_sessions[session_id] = initial_session.copy()
        mock_db.brain_surgery_sessions.update_one = AsyncMock()
        
        # Execute
        result = await brain_surgery_service.resolve_conflict(
            session_id=session_id,
            conflict_id="conflict_1",
            resolution="keep_existing",
            actor_id="test-user",
        )
        
        # Assert
        assert result is not None
        conflict = result["conflicts"][0]
        assert conflict["resolution"] == "keep_existing"
        assert conflict["resolved_by"] == "test-user"
        assert "resolved_at" in conflict
        assert result["status"] == "ready_for_merge"  # All conflicts resolved

    @pytest.mark.asyncio
    async def test_run_sandbox_validation(self, brain_surgery_service, mock_db):
        """Test running sandbox validation."""
        # Setup
        session_id = "surgery_blue_20260202_120000"
        initial_session = {
            "session_id": session_id,
            "team_id": "blue",
            "status": "ready_for_merge",
            "conflicts": [],
        }
        brain_surgery_service.active_sessions[session_id] = initial_session.copy()
        mock_db.brain_surgery_sessions.update_one = AsyncMock()
        
        # Execute
        result = await brain_surgery_service.run_sandbox_validation(
            session_id=session_id,
            actor_id="test-user",
        )
        
        # Assert
        assert result is not None
        assert result["sandbox_results"] is not None
        assert "tests" in result["sandbox_results"]
        assert len(result["sandbox_results"]["tests"]) == 5
        assert "summary" in result["sandbox_results"]
        assert result["sandbox_results"]["summary"]["total"] == 5
        # Status should be one of passed or failed based on results
        assert result["status"] in ["sandbox_passed", "sandbox_failed"]

    @pytest.mark.asyncio
    async def test_execute_hot_swap_sod_violation(self, brain_surgery_service, mock_db):
        """Test that hot-swap fails with SoD violation when actor is session starter."""
        # Setup
        session_id = "surgery_blue_20260202_120000"
        initial_session = {
            "session_id": session_id,
            "team_id": "blue",
            "actor_id": "same-user",  # Same user started the session
            "status": "sandbox_passed",
            "hot_swap_ready": True,
        }
        brain_surgery_service.active_sessions[session_id] = initial_session.copy()
        
        # Execute & Assert
        with pytest.raises(ValueError, match="SoD violation"):
            await brain_surgery_service.execute_hot_swap(
                session_id=session_id,
                actor_id="same-user",  # Same user trying to execute
                mode="hot_swap",
            )

    @pytest.mark.asyncio
    async def test_execute_hot_swap_success(self, brain_surgery_service, mock_db, sample_baseline_snapshot):
        """Test successful hot-swap execution."""
        # Setup
        session_id = "surgery_blue_20260202_120000"
        initial_session = {
            "session_id": session_id,
            "team_id": "blue",
            "actor_id": "starter-user",  # Different user started
            "status": "sandbox_passed",
            "hot_swap_ready": True,
            "merged_preview": sample_baseline_snapshot,
        }
        brain_surgery_service.active_sessions[session_id] = initial_session.copy()
        mock_db.brain_surgery_sessions.update_one = AsyncMock()
        mock_db.amc_states.update_one = AsyncMock()
        mock_db.amc_states.find_one = AsyncMock(return_value=None)
        mock_db.amc_activations.insert_one = AsyncMock()
        mock_db.amc_rollback_snapshots.insert_one = AsyncMock()
        
        with patch(
            "app.services.capsules.amc.brain_surgery_service.build_baseline_snapshot",
            new_callable=AsyncMock,
            return_value=sample_baseline_snapshot,
        ):
            # Execute
            result = await brain_surgery_service.execute_hot_swap(
                session_id=session_id,
                actor_id="different-user",  # Different user executing
                mode="hot_swap",
            )
        
        # Assert
        assert result is not None
        assert result["status"] == "hot_swap_active"
        assert result["activation"] is not None
        assert result["activation"]["mode"] == "hot_swap"
        assert result["activation"]["executed_by"] == "different-user"
        assert "rollback_snapshot_id" in result

    @pytest.mark.asyncio
    async def test_execute_rollback(self, brain_surgery_service, mock_db, sample_baseline_snapshot):
        """Test rollback execution."""
        # Setup
        snapshot = {
            "snapshot_id": "rollback_blue_20260202_110000",
            "team_id": "blue",
            "baseline_snapshot": sample_baseline_snapshot,
            "previous_state": {},
            "status": "available",
        }
        cursor_mock = MagicMock()
        cursor_mock.sort = MagicMock(return_value=cursor_mock)
        cursor_mock.limit = MagicMock(return_value=cursor_mock)
        cursor_mock.to_list = AsyncMock(return_value=[snapshot])
        mock_db.amc_rollback_snapshots.find = MagicMock(return_value=cursor_mock)
        mock_db.amc_rollback_snapshots.update_one = AsyncMock()
        mock_db.amc_states.update_one = AsyncMock()
        mock_db.amc_rollbacks.insert_one = AsyncMock()
        
        # Execute
        result = await brain_surgery_service.execute_rollback(
            team_id="blue",
            snapshot_id=None,  # Use most recent
            actor_id="test-user",
        )
        
        # Assert
        assert result is not None
        assert result["rollback"] is not None
        assert result["rollback"]["team_id"] == "blue"
        assert result["rollback"]["status"] == "completed"
        assert result["restored_snapshot"] == snapshot

    @pytest.mark.asyncio
    async def test_get_knowledge_graph_for_merge(self, brain_surgery_service, mock_db, sample_baseline_snapshot):
        """Test building knowledge graph for merge visualization."""
        # Setup
        session_id = "surgery_blue_20260202_120000"
        session = {
            "session_id": session_id,
            "team_id": "blue",
            "baseline": sample_baseline_snapshot,
            "import_preview": sample_baseline_snapshot,
            "merged_preview": sample_baseline_snapshot,
            "conflicts": [],
        }
        brain_surgery_service.active_sessions[session_id] = session
        
        # Execute
        result = await brain_surgery_service.get_knowledge_graph_for_merge(session_id)
        
        # Assert
        assert result is not None
        assert "baseline" in result
        assert "import" in result
        assert "merged" in result
        assert "conflicts" in result
        
        # Check baseline graph structure
        baseline_graph = result["baseline"]
        assert "nodes" in baseline_graph
        assert "edges" in baseline_graph
        assert len(baseline_graph["nodes"]) > 0  # Should have team + agents + memory nodes

    @pytest.mark.asyncio
    async def test_list_sessions(self, brain_surgery_service, mock_db):
        """Test listing surgery sessions."""
        # Setup
        sessions = [
            {"session_id": "surgery_blue_1", "team_id": "blue", "status": "completed"},
            {"session_id": "surgery_blue_2", "team_id": "blue", "status": "active"},
        ]
        cursor_mock = MagicMock()
        cursor_mock.sort = MagicMock(return_value=cursor_mock)
        cursor_mock.limit = MagicMock(return_value=cursor_mock)
        cursor_mock.to_list = AsyncMock(return_value=sessions)
        mock_db.brain_surgery_sessions.find = MagicMock(return_value=cursor_mock)
        
        # Execute
        result = await brain_surgery_service.list_sessions(
            team_id="blue",
            status=None,
            limit=20,
        )
        
        # Assert
        assert result is not None
        assert len(result) == 2
        assert result[0]["team_id"] == "blue"

    @pytest.mark.asyncio
    async def test_get_active_state_with_existing(self, brain_surgery_service, mock_db, sample_baseline_snapshot):
        """Test getting active state when one exists."""
        # Setup
        existing_state = {
            "team_id": "blue",
            "active_snapshot": sample_baseline_snapshot,
            "activated_at": "2026-02-02T12:00:00Z",
        }
        mock_db.amc_states.find_one = AsyncMock(return_value=existing_state)
        
        # Execute
        result = await brain_surgery_service.get_active_state("blue")
        
        # Assert
        assert result is not None
        assert result["team_id"] == "blue"
        assert result["active_snapshot"] == sample_baseline_snapshot

    @pytest.mark.asyncio
    async def test_get_active_state_fallback_to_baseline(self, brain_surgery_service, mock_db, sample_baseline_snapshot):
        """Test getting active state fallback when none exists."""
        # Setup
        mock_db.amc_states.find_one = AsyncMock(return_value=None)
        
        with patch(
            "app.services.capsules.amc.brain_surgery_service.build_baseline_snapshot",
            new_callable=AsyncMock,
            return_value=sample_baseline_snapshot,
        ):
            # Execute
            result = await brain_surgery_service.get_active_state("blue")
        
        # Assert
        assert result is not None
        assert result["team_id"] == "blue"
        assert result["source"] == "baseline"


class TestConflictDetection:
    """Test suite for conflict detection functionality."""

    @pytest.mark.asyncio
    async def test_detect_role_change_conflict(self, brain_surgery_service, mock_db, sample_baseline_snapshot):
        """Test detection of role change conflicts."""
        # Setup
        import_snapshot = sample_baseline_snapshot.copy()
        import_snapshot["agents"] = [
            {"agent_id": "agent-blue-01", "name": "Blue Orchestrator", "role": "NewRole", "semantic": 10, "episodic": 5},  # Changed role
        ]
        
        # Execute
        conflicts = await brain_surgery_service._detect_conflicts(
            sample_baseline_snapshot,
            import_snapshot,
            {},
        )
        
        # Assert
        assert len(conflicts) > 0
        role_conflicts = [c for c in conflicts if c["type"] == "role_change"]
        assert len(role_conflicts) == 1
        assert "agent-blue-01" in role_conflicts[0]["agent_id"]

    @pytest.mark.asyncio
    async def test_detect_knowledge_drift_conflict(self, brain_surgery_service, mock_db, sample_baseline_snapshot):
        """Test detection of significant knowledge drift conflicts."""
        # Setup
        import_snapshot = sample_baseline_snapshot.copy()
        import_snapshot["memory_counts"] = {
            "agent-blue-01": {"semantic": 100, "episodic": 5},  # Large semantic change (+90)
        }
        import_snapshot["agents"] = [
            {"agent_id": "agent-blue-01", "name": "Blue Orchestrator", "role": "Orchestrator", "semantic": 100, "episodic": 5},
        ]
        
        # Execute
        conflicts = await brain_surgery_service._detect_conflicts(
            sample_baseline_snapshot,
            import_snapshot,
            {},
        )
        
        # Assert
        drift_conflicts = [c for c in conflicts if c["type"] == "knowledge_drift"]
        assert len(drift_conflicts) == 1
        assert "+90" in drift_conflicts[0]["detail"]


class TestSandboxValidation:
    """Test suite for sandbox validation functionality."""

    @pytest.mark.asyncio
    async def test_sandbox_test_cases(self, brain_surgery_service, mock_db):
        """Test that sandbox validation runs all expected test cases."""
        # Setup
        session_id = "surgery_blue_20260202_120000"
        session = {
            "session_id": session_id,
            "team_id": "blue",
            "status": "ready_for_merge",
        }
        brain_surgery_service.active_sessions[session_id] = session.copy()
        mock_db.brain_surgery_sessions.update_one = AsyncMock()
        
        # Execute
        result = await brain_surgery_service.run_sandbox_validation(
            session_id=session_id,
            actor_id="test-user",
        )
        
        # Assert
        tests = result["sandbox_results"]["tests"]
        test_names = [t["name"] for t in tests]
        
        expected_tests = [
            "Memory Coherence Check",
            "Skill Graph Compatibility",
            "Reasoning Pattern Validation",
            "Guardrail Enforcement Check",
            "Rollback Safety Check",
        ]
        
        for expected in expected_tests:
            assert expected in test_names, f"Missing test: {expected}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
