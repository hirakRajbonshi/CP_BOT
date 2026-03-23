from dataclasses import dataclass, field
from typing import Optional, List
from models.round import Round
from repositories.round_repo import RoundRepo
from repositories.user_repo import UserRepo
from utils.codeforces_api import CodeforcesAPI
from config.settings import MIN_PROBLEMS, MAX_PROBLEMS


MAX_ROUND_PLAYERS = 5  # challenger + 4 opponents max


@dataclass
class RoundCheckResult:
    """Result of checking round submissions"""
    winner_id: Optional[int] = None   # player who solved the problem first
    points: int = 0
    round_complete: bool = False
    time_up: bool = False
    already_solved: bool = False
    no_solution: bool = False


class RoundService:
    """Business logic for multi-player rounds — stateful, holds RoundRepo"""

    def __init__(self):
        self.repo = RoundRepo()

    # -------------------- Validation --------------------

    @staticmethod
    def validate_round(challenger_id, opponents, n, low, high):
        """Return an error string, or None if valid.

        `opponents` is a list of (member_id, is_bot) tuples.
        """
        if not opponents:
            return "You must challenge at least one other player!"

        if len(opponents) > MAX_ROUND_PLAYERS - 1:
            return f"You can challenge at most {MAX_ROUND_PLAYERS - 1} opponents (round max {MAX_ROUND_PLAYERS} players)!"

        for opp_id, opp_is_bot in opponents:
            if opp_is_bot:
                return "Cannot include a bot in a round!"
            if opp_id == challenger_id:
                return "Cannot challenge yourself!"

        opp_ids = [opp_id for opp_id, _ in opponents]
        if len(opp_ids) != len(set(opp_ids)):
            return "Cannot challenge the same person twice!"

        if not (MIN_PROBLEMS <= n <= MAX_PROBLEMS):
            return f"Number of problems must be between {MIN_PROBLEMS} and {MAX_PROBLEMS}!"

        if low > high:
            return "Low rating must be less than or equal to high rating!"

        if not UserRepo.get_cf_handle(challenger_id):
            return "You need to link your CF account first! Use `;link <handle>`"

        for opp_id, _ in opponents:
            if not UserRepo.get_cf_handle(opp_id):
                return f"Player <@{opp_id}> needs to link their CF account first!"

        return None

    # -------------------- Round Lifecycle --------------------

    async def create_round(self, challenger_id, opponent_ids, n, low, high, t):
        """Create a round, generate problems, and store it as PENDING.

        Returns the Round on success (waiting for accepts), or None on failure.
        """
        all_ids = [challenger_id] + list(opponent_ids)
        for uid in all_ids:
            if self.repo.is_user_in_round(uid):
                return None

        round_ = Round(challenger_id, opponent_ids, n, low, high, t)
        if not await round_.generate_problems():
            return None

        self.repo.add_pending_round(challenger_id, round_)
        return round_

    def accept_round(self, opponent_id):
        """Opponent accepts their invite.

        Returns (round, all_accepted) where:
          - round is the Round object
          - all_accepted is True if this was the last acceptance (round should start now)
        Returns (None, False) if no invite found.
        """
        round_, all_accepted = self.repo.accept(opponent_id)
        if not round_:
            return None, False

        if all_accepted:
            self.repo.start_round(round_)

        return round_, all_accepted

    def reject_round(self, opponent_id):
        """Opponent rejects — cancels the whole pending round.

        Returns the cancelled Round or None if no invite found.
        """
        return self.repo.reject(opponent_id)

    def cancel_round(self, challenger_id):
        """Challenger cancels a pending round. Returns the Round or None."""
        round_ = self.repo.get_pending_round(challenger_id)
        if round_:
            self.repo.remove_pending_round(challenger_id)
        return round_

    # -------------------- In-Game --------------------

    async def check_solution(self, user_id):
        """Check submissions for the active round.

        Returns (round, RoundCheckResult).
        """
        round_ = self.repo.get_active_round(user_id)
        result = RoundCheckResult()

        if not round_ or not round_.active:
            return None, result

        # Time up?
        if round_.is_time_up():
            result.time_up = True
            round_.advance_problem()
            if round_.is_complete():
                result.round_complete = True
                self.repo.end_round(round_)
            return round_, result

        # Already solved?
        if round_.problem_solved:
            result.already_solved = True
            return round_, result

        # Fetch submissions for all players
        subs = {}
        for pid in round_.player_ids:
            subs[pid] = await self._get_first_ac(round_, pid)

        eligible = {pid: sub for pid, sub in subs.items() if sub is not None}

        if not eligible:
            result.no_solution = True
            return round_, result

        # Earliest AC wins
        winner_id = min(eligible, key=lambda pid: eligible[pid]["creationTimeSeconds"])

        problem = round_.get_current_problem()
        result.winner_id = winner_id
        result.points = problem.get("rating", 1000)

        round_.problem_solved = True
        round_.scores[winner_id] += result.points

        round_.advance_problem()
        if round_.is_complete():
            result.round_complete = True
            self.repo.end_round(round_)

        return round_, result

    def get_round_status(self, user_id):
        """Return the active round for a user, or None."""
        round_ = self.repo.get_active_round(user_id)
        if round_ and round_.active:
            return round_
        return None

    def forfeit(self, user_id):
        """Remove the player from the active round.

        Returns (round_, continues) where continues=True if round goes on.
        """
        round_ = self.repo.get_active_round(user_id)
        if not round_ or not round_.active:
            return None, False

        self.repo.remove_player_from_active(user_id)
        continues = round_.remove_player(user_id)

        if not continues:
            self.repo.end_round(round_)

        return round_, continues

    # -------------------- Helpers --------------------

    @staticmethod
    async def _get_first_ac(round_, user_id):
        handle = UserRepo.get_cf_handle(user_id)
        if not handle:
            return None

        problem = round_.get_current_problem()
        if not problem:
            return None

        contest_id = problem["contestId"]
        index = problem["index"]

        submissions = await CodeforcesAPI.get_user_submissions(handle, 20)
        for sub in submissions:
            if (
                sub["verdict"] == "OK"
                and sub["problem"]["contestId"] == contest_id
                and sub["problem"]["index"] == index
            ):
                return sub
        return None
