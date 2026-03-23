import sys
import os
import time

# Add root directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from utils.data_manager import DataManager
from utils.contest_cache import is_contest_cache_valid, load_cached_contests, save_contests
from utils.problem_cache import is_problems_cache_valid, load_cached_problems, save_problems

def test_data_manager():
    print("Testing DataManager...")
    
    # Test link_user
    DataManager.link_user("12345", "tourist")
    handle = DataManager.get_cf_handle("12345")
    assert handle == "tourist", f"Expected tourist, got {handle}"
    print("  - link_user/get_cf_handle: PASS")
    
    # Test pending_auth
    DataManager.add_pending_auth("67890", "peter", "1A")
    auth = DataManager.get_pending_auth("67890")
    assert auth['cf_handle'] == "peter", f"Expected peter, got {auth['cf_handle']}"
    assert auth['problem_id'] == "1A", f"Expected 1A, got {auth['problem_id']}"
    print("  - add_pending_auth/get_pending_auth: PASS")
    
    DataManager.remove_pending_auth("67890")
    auth = DataManager.get_pending_auth("67890")
    assert auth is None, "Expected None for removed pending auth"
    print("  - remove_pending_auth: PASS")

def test_caching():
    print("Testing Caching...")
    
    # Test contest cache
    contests = [{"id": 1, "name": "Codeforces Round 1"}]
    save_contests(contests)
    assert is_contest_cache_valid() is True, "Contest cache should be valid"
    loaded_contests = load_cached_contests()
    assert loaded_contests == contests, f"Expected {contests}, got {loaded_contests}"
    print("  - contest cache save/load/validity: PASS")
    
    # Test problem cache
    problems = [{"contestId": 1, "index": "A", "name": "Problem A"}]
    save_problems(problems)
    assert is_problems_cache_valid() is True, "Problem cache should be valid"
    loaded_problems = load_cached_problems()
    assert loaded_problems == problems, f"Expected {problems}, got {loaded_problems}"
    print("  - problem cache save/load/validity: PASS")

if __name__ == "__main__":
    try:
        test_data_manager()
        test_caching()
        print("\nAll SQLite database tests passed successfully!")
    except Exception as e:
        print(f"\nTests failed: {e}")
        sys.exit(1)
