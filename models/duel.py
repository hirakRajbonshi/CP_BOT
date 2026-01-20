from datetime import datetime
from utils.codeforces_api import CodeforcesAPI
import random


class Duel:
    """Represents a duel between two users"""
    def __init__(self, challenger_id, opponent_id, n, low, high, time_per_problem):
        self.challenger_id = challenger_id
        self.opponent_id = opponent_id

        self.n = n
        self.low = low
        self.high = high
        self.time_per_problem = time_per_problem

        self.problems = []
        self.current_problem_idx = 0
        self.problem_solved = False


        self.scores = {
            challenger_id: 0,
            opponent_id: 0
        }

        self.solved = {
            challenger_id: set(),
            opponent_id: set()
        }

        self.start_time = None
        self.problem_start_time = None
        self.active = False


    # TODO: Optimize problem selection to ensure distinct contests 
    async def generate_problems(self):
        """Generate n problems from post-2020 contests, preferring distinct contests"""

        cf_api = CodeforcesAPI()

        contests = await cf_api.get_contests()
        contest_start = {
            c["id"]: c["startTimeSeconds"]
            for c in contests
            if "startTimeSeconds" in c
        }

        CUTOFF_TS = int(datetime(2020, 1, 1).timestamp())

        all_problems = await cf_api.get_problems()

        valid_problems = []
        # Filter problems: within rating range and from contests after cutoff
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

        # Bucket problems by contest
        contest_buckets = {}
        for p in valid_problems:
            contest_buckets.setdefault(p["contestId"], []).append(p)

        contest_ids = list(contest_buckets.keys())
        random.shuffle(contest_ids)

        # Determine target ratings for evenly spaced problems
        targets = []
        for i in range(self.n):
            if self.n > 1:
                targets.append(
                    self.low + (self.high - self.low) * i / (self.n - 1)
                )
            else:
                targets.append((self.low + self.high) // 2)

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

        if len(selected) < self.n:
            remaining = [
                p for bucket in contest_buckets.values() for p in bucket
            ]
            remaining.sort(
                key=lambda p: abs(
                    p["rating"] - targets[len(selected)]
                )
            )

            for p in remaining:
                selected.append(p)
                if len(selected) == self.n:
                    break

        if len(selected) < self.n:
            return False

        self.problems = selected
        return True


    def get_current_problem(self):
        if self.current_problem_idx < len(self.problems):
            return self.problems[self.current_problem_idx]
        return None

    def advance_problem(self):
        self.current_problem_idx += 1
        self.problem_start_time = datetime.now()
        self.problem_solved = False

    async def get_first_ac_submission(self, user_id, data_manager):
        handle = data_manager.get_cf_handle(user_id)
        if not handle:
            return None

        problem = self.get_current_problem()
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


    # -------------------- Duel State --------------------

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

    def get_opponent_id(self, user_id):
        return (
            self.opponent_id
            if user_id == self.challenger_id
            else self.challenger_id
        )

    # -------------------- Submission Checking --------------------

    async def check_solve(self, user_id, data_manager):
        cf_handle = data_manager.get_cf_handle(user_id)
        if not cf_handle:
            return False

        problem = self.get_current_problem()
        if not problem:
            return False

        submissions = await CodeforcesAPI.get_user_submissions(cf_handle, 20)

        for sub in submissions:
            sub_problem = sub.get('problem', {})

            if (
                sub_problem.get('contestId') == problem.get('contestId')
                and sub_problem.get('index') == problem.get('index')
                and sub.get('verdict') == 'OK'
            ):
                sub_time = datetime.fromtimestamp(
                    sub['creationTimeSeconds']
                )

                if sub_time >= self.problem_start_time:
                    key = f"{problem['contestId']}{problem['index']}"

                    if key not in self.solved[user_id]:
                        self.solved[user_id].add(key)
                        self.scores[user_id] += problem.get('rating', 1000)
                        return True

        return False




class DuelManager:
    """Manages pending and active duels"""

    def __init__(self):
        self.pending_duels = {}  # opponent_id -> Duel
        self.active_duels = {}   # user_id -> Duel

    # -------------------- Pending Duels --------------------

    def add_pending_duel(self, opponent_id, duel):
        self.pending_duels[opponent_id] = duel

    def get_pending_duel_for_opponent(self, opponent_id):
        return self.pending_duels.pop(opponent_id, None)

    # -------------------- Active Duels --------------------

    def start_duel(self, duel):
        duel.start()
        self.active_duels[duel.challenger_id] = duel
        self.active_duels[duel.opponent_id] = duel

    def get_active_duel(self, user_id):
        return self.active_duels.get(user_id)

    # Not sure should consider pending duels?
    def is_user_in_duel(self, user_id):
        return user_id in self.active_duels or user_id in self.pending_duels

    def end_duel(self, duel):
        self.active_duels.pop(duel.challenger_id, None)
        self.active_duels.pop(duel.opponent_id, None)
