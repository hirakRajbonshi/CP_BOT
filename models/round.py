from datetime import datetime
from utils.codeforces_api import CodeforcesAPI
import random


class Round:
    """Pure data model for a multi-player round (2-5 players).

    Logic is identical to Duel, but supports a list of player IDs.
    The first player to get AC on the current problem advances it for everyone.
    """

    MAX_PLAYERS = 5

    def __init__(self, challenger_id, opponent_ids, n, low, high, time_per_problem):
        self.challenger_id = challenger_id
        self.player_ids = [challenger_id] + list(opponent_ids)  # all players

        self.n = n
        self.low = low
        self.high = high
        self.time_per_problem = time_per_problem

        self.problems = []
        self.current_problem_idx = 0
        self.problem_solved = False  # True once someone has solved the current problem

        self.scores = {pid: 0 for pid in self.player_ids}
        self.solved = {pid: set() for pid in self.player_ids}

        self.start_time = None
        self.problem_start_time = None
        self.active = False

    # -------------------- Properties --------------------

    @property
    def player_count(self):
        return len(self.player_ids)

    # -------------------- Problem Generation --------------------

    async def generate_problems(self):
        """Generate n problems from post-2020 contests, preferring distinct contests"""
        contests = await CodeforcesAPI.get_contests()
        contest_start = {
            c["id"]: c["startTimeSeconds"]
            for c in contests
            if "startTimeSeconds" in c
        }

        CUTOFF_TS = int(datetime(2020, 1, 1).timestamp())
        all_problems = await CodeforcesAPI.get_problems()

        valid_problems = []
        for p in all_problems:
            cid = p.get("contestId")
            rating = p.get("rating")
            if rating is None or cid not in contest_start:
                continue
            if not (self.low <= rating <= self.high):
                continue
            if contest_start[cid] < CUTOFF_TS:
                continue
            valid_problems.append(p)

        if len(valid_problems) < self.n:
            return False

        # Bucket by contest
        contest_buckets = {}
        for p in valid_problems:
            contest_buckets.setdefault(p["contestId"], []).append(p)

        contest_ids = list(contest_buckets.keys())
        random.shuffle(contest_ids)

        # Evenly spaced target ratings
        if self.n > 1:
            targets = [self.low + (self.high - self.low) * i / (self.n - 1) for i in range(self.n)]
        else:
            targets = [(self.low + self.high) // 2]

        selected = []
        used_contests = set()

        for target in targets:
            best_problem = None
            best_diff = float("inf")
            best_contest = None

            for cid in contest_ids:
                if cid in used_contests:
                    continue
                for p in contest_buckets[cid]:
                    diff = abs(p["rating"] - target)
                    if diff < best_diff:
                        best_diff = diff
                        best_problem = p
                        best_contest = cid

            if best_problem:
                selected.append(best_problem)
                used_contests.add(best_contest)
                contest_buckets[best_contest].remove(best_problem)

            if len(selected) == self.n:
                break

        # Fill remaining from any bucket
        if len(selected) < self.n:
            remaining = [p for bucket in contest_buckets.values() for p in bucket]
            remaining.sort(key=lambda p: abs(p["rating"] - targets[len(selected)]))
            for p in remaining:
                selected.append(p)
                if len(selected) == self.n:
                    break

        if len(selected) < self.n:
            return False

        self.problems = selected
        return True

    # -------------------- State Accessors --------------------

    def get_current_problem(self):
        if self.current_problem_idx < len(self.problems):
            return self.problems[self.current_problem_idx]
        return None

    def advance_problem(self):
        self.current_problem_idx += 1
        self.problem_start_time = datetime.now()
        self.problem_solved = False

    def start(self):
        self.active = True
        self.start_time = datetime.now()
        self.problem_start_time = datetime.now()
        self.problem_solved = False

    def is_complete(self):
        return self.current_problem_idx >= self.n

    def is_time_up(self):
        if not self.problem_start_time:
            return False
        elapsed = (datetime.now() - self.problem_start_time).total_seconds() / 60
        return elapsed >= self.time_per_problem

    def remove_player(self, user_id):
        """Remove a player (forfeit). Returns True if round should continue, False if too few remain."""
        if user_id in self.player_ids:
            self.player_ids.remove(user_id)
        return len(self.player_ids) > 1
