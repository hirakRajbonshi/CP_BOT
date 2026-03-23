from dataclasses import dataclass
from typing import Optional
from models.duel import Duel
from repositories.duel_repo import DuelRepo
from repositories.user_repo import UserRepo
from utils.codeforces_api import CodeforcesAPI
from config.settings import MIN_PROBLEMS, MAX_PROBLEMS


@dataclass
class CheckResult:
    """Result of checking duel submissions"""
    winner_id: Optional[int] = None
    loser_id: Optional[int] = None
    points: int = 0
    duel_complete: bool = False
    time_up: bool = False
    already_solved: bool = False
    no_solution: bool = False


class DuelService:
    """Business logic for duels — stateful, holds DuelRepo"""

    def __init__(self):
        self.repo = DuelRepo()

    # -------------------- Validation --------------------

    @staticmethod
    def validate_challenge(challenger_id, opponent_id, opponent_is_bot, n, low, high):
        """Return an error string, or None if valid."""
        if opponent_is_bot:
            return "Cannot challenge a bot!"
        if opponent_id == challenger_id:
            return "Cannot challenge yourself!"
        if not (MIN_PROBLEMS <= n <= MAX_PROBLEMS):
            return f"Number of problems must be between {MIN_PROBLEMS} and {MAX_PROBLEMS}!"
        if low > high:
            return "Low rating must be less than or equal to high rating!"
        if not UserRepo.get_cf_handle(challenger_id):
            return "You need to link your CF account first! Use `;link <handle>`"
        if not UserRepo.get_cf_handle(opponent_id):
            return "Opponent needs to link their CF account first!"
        return None

    # -------------------- Challenge Lifecycle --------------------

    async def create_challenge(self, challenger_id, opponent_id, n, low, high, t):
        """Create a duel, generate problems, and store it as pending.

        Returns the Duel on success, or None if not enough problems.
        """
        if self.repo.is_user_in_duel(challenger_id) or self.repo.is_user_in_duel(opponent_id):
            return None

        duel = Duel(challenger_id, opponent_id, n, low, high, t)
        if not await duel.generate_problems():
            return None

        self.repo.add_pending_duel(opponent_id, duel)
        return duel

    def accept_challenge(self, opponent_id):
        """Accept and start a pending duel. Returns the Duel or None."""
        duel = self.repo.get_pending_duel(opponent_id)
        if not duel:
            return None
        self.repo.start_duel(duel)
        return duel

    def reject_challenge(self, opponent_id):
        """Reject a pending duel. Returns the Duel or None."""
        duel = self.repo.get_pending_duel(opponent_id)
        return duel  # already popped by get_pending_duel

    # -------------------- In-Game --------------------

    async def check_solution(self, user_id):
        """Check submissions for the active duel.

        Returns (duel, CheckResult).
        """
        duel = self.repo.get_active_duel(user_id)
        result = CheckResult()

        if not duel or not duel.active:
            return None, result

        # Time up?
        if duel.is_time_up():
            result.time_up = True
            duel.advance_problem()
            if duel.is_complete():
                result.duel_complete = True
                self.repo.end_duel(duel)
            return duel, result

        # Already solved?
        if duel.problem_solved:
            result.already_solved = True
            return duel, result

        opponent_id = duel.get_opponent_id(user_id)

        user_sub = await self._get_first_ac(duel, user_id)
        opp_sub = await self._get_first_ac(duel, opponent_id)

        if not user_sub and not opp_sub:
            result.no_solution = True
            return duel, result

        # Determine winner
        if user_sub and not opp_sub:
            result.winner_id = user_id
        elif opp_sub and not user_sub:
            result.winner_id = opponent_id
        else:
            if user_sub["creationTimeSeconds"] < opp_sub["creationTimeSeconds"]:
                result.winner_id = user_id
            else:
                result.winner_id = opponent_id

        result.loser_id = opponent_id if result.winner_id == user_id else user_id

        # Award points
        duel.problem_solved = True
        problem = duel.get_current_problem()
        result.points = problem.get("rating", 1000)
        duel.scores[result.winner_id] += result.points

        duel.advance_problem()
        if duel.is_complete():
            result.duel_complete = True
            self.repo.end_duel(duel)

        return duel, result

    def get_duel_status(self, user_id):
        """Return the active duel for a user, or None."""
        duel = self.repo.get_active_duel(user_id)
        if duel and duel.active:
            return duel
        return None

    def forfeit(self, user_id):
        """Forfeit the active duel. Returns (duel, opponent_id) or (None, None)."""
        duel = self.repo.get_active_duel(user_id)
        if not duel or not duel.active:
            return None, None
        opponent_id = duel.get_opponent_id(user_id)
        self.repo.end_duel(duel)
        return duel, opponent_id

    # -------------------- Helpers --------------------

    @staticmethod
    async def _get_first_ac(duel, user_id):
        """Get the first AC submission for the current duel problem."""
        handle = UserRepo.get_cf_handle(user_id)
        if not handle:
            return None

        problem = duel.get_current_problem()
        contest_id = problem["contestId"]
        index = problem["index"]

        submissions = await CodeforcesAPI.get_user_submissions(handle)
        for sub in submissions:
            if (
                sub["verdict"] == "OK"
                and sub["problem"]["contestId"] == contest_id
                and sub["problem"]["index"] == index
            ):
                return sub
        return None
