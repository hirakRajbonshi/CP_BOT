"""Tests for ProblemService"""
import pytest
import asyncio
from unittest.mock import patch, AsyncMock
from services.problem_service import ProblemService


MOCK_PROBLEMS = [
    {"contestId": 1, "index": "A", "name": "Watermelon", "rating": 800},
    {"contestId": 1, "index": "B", "name": "Boring Apartments", "rating": 900},
    {"contestId": 2, "index": "A", "name": "Divisibility", "rating": 1000},
    {"contestId": 3, "index": "C", "name": "Hard Problem", "rating": 1800},
]


class TestProblemService:

    @patch("services.problem_service.CodeforcesAPI")
    @patch("services.problem_service.UserRepo")
    def test_suggest_with_explicit_rating(self, MockUserRepo, MockCFAPI):
        MockCFAPI.get_problems = AsyncMock(return_value=MOCK_PROBLEMS)

        problem, rating = asyncio.get_event_loop().run_until_complete(
            ProblemService.get_suggested_problem(discord_id=111, rating=850)
        )

        assert problem is not None
        assert abs(problem["rating"] - 850) <= 100
        assert rating == 850

    @patch("services.problem_service.CodeforcesAPI")
    @patch("services.problem_service.UserRepo")
    def test_suggest_no_problems_found(self, MockUserRepo, MockCFAPI):
        MockCFAPI.get_problems = AsyncMock(return_value=MOCK_PROBLEMS)

        problem, info = asyncio.get_event_loop().run_until_complete(
            ProblemService.get_suggested_problem(discord_id=111, rating=3000)
        )

        assert problem is None
        assert "No problems found" in info

    @patch("services.problem_service.CodeforcesAPI")
    @patch("services.problem_service.UserRepo")
    def test_suggest_infers_rating_from_handle(self, MockUserRepo, MockCFAPI):
        MockUserRepo.get_cf_handle.return_value = "tourist"
        MockCFAPI.get_user_rating = AsyncMock(return_value=900)
        MockCFAPI.get_problems = AsyncMock(return_value=MOCK_PROBLEMS)

        problem, rating = asyncio.get_event_loop().run_until_complete(
            ProblemService.get_suggested_problem(discord_id=111, rating=None)
        )

        assert problem is not None
        assert rating == 900

    @patch("services.problem_service.random")
    @patch("services.problem_service.CodeforcesAPI")
    @patch("services.problem_service.UserRepo")
    def test_suggest_random_rating_when_no_handle(self, MockUserRepo, MockCFAPI, mock_random):
        MockUserRepo.get_cf_handle.return_value = None
        MockCFAPI.get_problems = AsyncMock(return_value=MOCK_PROBLEMS)
        # Force the "random" rating to be 900 so it matches mock problems
        mock_random.randint.return_value = 900
        mock_random.choice.side_effect = lambda lst: lst[0]

        problem, rating = asyncio.get_event_loop().run_until_complete(
            ProblemService.get_suggested_problem(discord_id=111, rating=None)
        )

        assert problem is not None
        assert rating == 900
        assert isinstance(rating, int)
