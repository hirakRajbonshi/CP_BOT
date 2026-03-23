"""Tests for Duel model and DuelService"""
import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from models.duel import Duel
from services.duel_service import DuelService, CheckResult
from repositories.duel_repo import DuelRepo


# ──────────────── Duel Model Tests ────────────────

class TestDuelModel:
    """Tests for the pure Duel data model"""

    def _make_duel(self, n=3, low=800, high=1200):
        duel = Duel(
            challenger_id=111,
            opponent_id=222,
            n=n, low=low, high=high,
            time_per_problem=30,
        )
        return duel

    def test_initial_state(self):
        duel = self._make_duel()
        assert duel.active is False
        assert duel.current_problem_idx == 0
        assert duel.problem_solved is False
        assert duel.scores == {111: 0, 222: 0}

    def test_start(self):
        duel = self._make_duel()
        duel.start()
        assert duel.active is True
        assert duel.start_time is not None
        assert duel.problem_start_time is not None

    def test_get_opponent_id(self):
        duel = self._make_duel()
        assert duel.get_opponent_id(111) == 222
        assert duel.get_opponent_id(222) == 111

    def test_advance_problem(self):
        duel = self._make_duel()
        duel.problems = [{"a": 1}, {"b": 2}, {"c": 3}]
        duel.problem_solved = True

        duel.advance_problem()
        assert duel.current_problem_idx == 1
        assert duel.problem_solved is False

    def test_get_current_problem(self):
        duel = self._make_duel()
        duel.problems = [{"name": "A"}, {"name": "B"}]

        assert duel.get_current_problem()["name"] == "A"
        duel.current_problem_idx = 1
        assert duel.get_current_problem()["name"] == "B"
        duel.current_problem_idx = 5
        assert duel.get_current_problem() is None

    def test_is_complete(self):
        duel = self._make_duel(n=2)
        duel.problems = [{"a": 1}, {"b": 2}]
        assert duel.is_complete() is False
        duel.current_problem_idx = 2
        assert duel.is_complete() is True


# ──────────────── DuelRepo Tests ────────────────

class TestDuelRepo:

    def test_pending_duel_lifecycle(self):
        repo = DuelRepo()
        duel = MagicMock()

        repo.add_pending_duel(222, duel)
        assert repo.is_user_in_duel(222)

        retrieved = repo.get_pending_duel(222)
        assert retrieved is duel
        assert not repo.is_user_in_duel(222)  # popped

    def test_active_duel_lifecycle(self):
        repo = DuelRepo()
        duel = Duel(111, 222, 3, 800, 1200, 30)

        repo.start_duel(duel)
        assert duel.active is True
        assert repo.is_user_in_duel(111)
        assert repo.is_user_in_duel(222)

        assert repo.get_active_duel(111) is duel

        repo.end_duel(duel)
        assert not repo.is_user_in_duel(111)
        assert not repo.is_user_in_duel(222)


# ──────────────── DuelService Tests ────────────────

class TestDuelServiceValidation:

    def test_valid_challenge(self):
        with patch("services.duel_service.UserRepo") as MockRepo:
            MockRepo.get_cf_handle.return_value = "handle"
            error = DuelService.validate_challenge(111, 222, False, 3, 800, 1200)
            assert error is None

    def test_challenge_bot(self):
        error = DuelService.validate_challenge(111, 222, True, 3, 800, 1200)
        assert "bot" in error.lower()

    def test_challenge_self(self):
        error = DuelService.validate_challenge(111, 111, False, 3, 800, 1200)
        assert "yourself" in error.lower()

    def test_invalid_problem_count(self):
        error = DuelService.validate_challenge(111, 222, False, 0, 800, 1200)
        assert "problems" in error.lower()

    def test_invalid_rating_range(self):
        error = DuelService.validate_challenge(111, 222, False, 3, 1500, 800)
        assert "rating" in error.lower()

    def test_unlinked_challenger(self):
        with patch("services.duel_service.UserRepo") as MockRepo:
            MockRepo.get_cf_handle.side_effect = lambda uid: None
            error = DuelService.validate_challenge(111, 222, False, 3, 800, 1200)
            assert "link" in error.lower()


class TestDuelServiceCheckSolution:

    @pytest.fixture
    def service(self):
        return DuelService()

    def test_no_active_duel(self, service):
        duel, result = asyncio.get_event_loop().run_until_complete(
            service.check_solution(999)
        )
        assert duel is None

    def test_already_solved(self, service):
        duel = Duel(111, 222, 3, 800, 1200, 30)
        duel.problems = [{"contestId": 1, "index": "A", "rating": 1000}]
        service.repo.start_duel(duel)
        duel.problem_solved = True  # set AFTER start, since start() resets it

        result_duel, result = asyncio.get_event_loop().run_until_complete(
            service.check_solution(111)
        )
        assert result.already_solved is True
