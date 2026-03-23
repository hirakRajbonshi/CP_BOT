import random
from repositories.user_repo import UserRepo
from utils.codeforces_api import CodeforcesAPI


class AuthService:
    """Business logic for account linking and verification"""

    @staticmethod
    async def is_already_linked(discord_id):
        """Check if a Discord user already has a linked CF account"""
        return UserRepo.get_cf_handle(discord_id) is not None

    @staticmethod
    async def start_linking(discord_id, cf_handle):
        """Pick a verification problem and store the pending auth.

        Returns the chosen problem dict, or None if no problems available.
        """
        problems = await CodeforcesAPI.get_problems()
        easy_problems = [p for p in problems if p.get('rating', 0) <= 1000]

        if not easy_problems:
            return None

        verify_problem = random.choice(easy_problems)
        problem_id = f"{verify_problem['contestId']}{verify_problem['index']}"

        UserRepo.add_pending_auth(discord_id, cf_handle, problem_id)
        return verify_problem

    @staticmethod
    async def verify_account(discord_id):
        """Check for a compilation-error submission and finalise the link.

        Returns (True, cf_handle) on success, or (False, error_message).
        """
        pending = UserRepo.get_pending_auth(discord_id)
        if not pending:
            return False, "No pending authentication found. Use `;link <cf_handle>` first."

        cf_handle = pending['cf_handle']
        problem_id = pending['problem_id']
        contest_id = int(''.join(filter(str.isdigit, problem_id)))
        problem_index = ''.join(filter(str.isalpha, problem_id))

        if await CodeforcesAPI.check_compilation_error(cf_handle, contest_id, problem_index):
            UserRepo.link_user(discord_id, cf_handle)
            UserRepo.remove_pending_auth(discord_id)
            return True, cf_handle

        return False, "Compilation error not found. Make sure you submitted to the correct problem with a compilation error."

    @staticmethod
    def get_status(discord_id):
        """Return the linked CF handle or None"""
        return UserRepo.get_cf_handle(discord_id)
