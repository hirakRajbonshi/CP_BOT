import random
from repositories.user_repo import UserRepo
from utils.codeforces_api import CodeforcesAPI
from config.settings import PROBLEM_RATING_TOLERANCE


class ProblemService:
    """Business logic for problem suggestions"""

    @staticmethod
    async def get_suggested_problem(discord_id, rating=None):
        """Return a random problem near the given (or inferred) rating.

        Returns (problem_dict, resolved_rating) or (None, error_message).
        """
        # Resolve rating
        if rating is None:
            cf_handle = UserRepo.get_cf_handle(discord_id)
            if cf_handle:
                rating = await CodeforcesAPI.get_user_rating(cf_handle)
            if not rating:
                rating = random.randint(800, 2000)

        rating = int(rating)
        problems = await CodeforcesAPI.get_problems()
        suitable = [
            p for p in problems
            if 'rating' in p and abs(p['rating'] - rating) <= PROBLEM_RATING_TOLERANCE
        ]

        if not suitable:
            return None, f"No problems found near rating {rating}"

        return random.choice(suitable), rating
