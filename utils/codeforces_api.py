import aiohttp
from config.settings import CODEFORCES_API_BASE, CODEFORCES_PROBLEMSET_URL
from utils.contest_cache import (
    is_contest_cache_valid,
    load_cached_contests,
    save_contests
)
from utils.problem_cache import (
    is_problems_cache_valid,
    load_cached_problems,
    save_problems
)
class CodeforcesAPI:
    """Handles all interactions with the Codeforces API"""
    
    @staticmethod
    async def fetch(session, url):
        """Fetch data from URL"""
        async with session.get(url) as response:
            if response.status == 200:
                return await response.json()
            return None
    
    @staticmethod
    async def get_contests():
        """Fetch contest list (cached, refreshed once per day)"""

        if is_contest_cache_valid():
            return load_cached_contests()

        async with aiohttp.ClientSession() as session:
            data = await CodeforcesAPI.fetch(
                session,
                f"{CODEFORCES_API_BASE}contest.list"
            )

            if data and data.get("status") == "OK":
                contests = data["result"]
                save_contests(contests)
                return contests

        return []
    
    @staticmethod
    async def get_problems():
        """Fetch all problems from Codeforces"""
        if is_problems_cache_valid():
            return load_cached_problems()
        
        async with aiohttp.ClientSession() as session:
            data = await CodeforcesAPI.fetch(session, f"{CODEFORCES_API_BASE}problemset.problems")
            if data and data.get('status') == 'OK':
                save_problems(data['result']['problems'])
                return data['result']['problems']
        return []
    
    @staticmethod
    async def get_user_submissions(handle, count=10):
        """Get recent submissions of a user"""
        async with aiohttp.ClientSession() as session:
            data = await CodeforcesAPI.fetch(
                session, 
                f"{CODEFORCES_API_BASE}user.status?handle={handle}&from=1&count={count}"
            )
            if data and data.get('status') == 'OK':
                return data['result']
        return []
    
    async def check_compilation_error(self, handle, contest_id, problem_index):
        """Check if user has a compilation error on specific problem"""
        submissions = await self.get_user_submissions(handle, 50)
        for sub in submissions:
            problem = sub.get('problem', {})
            if (problem.get('contestId') == contest_id and 
                problem.get('index') == problem_index and
                sub.get('verdict') == 'COMPILATION_ERROR'):
                return True
        return False
    
    @staticmethod
    def get_problem_url(problem):
        """Get the URL for a problem"""
        return f"{CODEFORCES_PROBLEMSET_URL}/{problem['contestId']}/{problem['index']}"
