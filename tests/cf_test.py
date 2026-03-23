import asyncio
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.codeforces_api import CodeforcesAPI

async def main():
    default_handle = "tourist"
    
    while True:
        print("\n" + "="*40)
        print("    Codeforces API Tester (CLI)    ")
        print("="*40)
        print(f"Current Handle: {default_handle}")
        print("-" * 40)
        print("0. Change Handle")
        print("1. Get User Rating")
        print("2. Get Contests (cached)")
        print("3. Get Problems (cached)")
        print("4. Get User Submissions")
        print("5. Check Compilation Error")
        print("\n6. Exit")
        print("="*40)
        
        choice = input("Enter choice: ").strip()
        
        try:
            if choice == "0":
                handle = input("Enter new CF handle: ").strip()
                if handle:
                    default_handle = handle
                    print(f"Changed handle to {default_handle}")
                    
            elif choice == "1":
                print(f"Fetching rating for {default_handle}...")
                rating = await CodeforcesAPI.get_user_rating(default_handle)
                if rating is not None:
                    print(f"\n[OK] Rating for {default_handle}: {rating}")
                else:
                    print(f"\n[ERROR] Could not fetch rating or user not found.")
                    
            elif choice == "2":
                print("Fetching contests (might take a moment if caching for the first time)...")
                contests = await CodeforcesAPI.get_contests()
                print(f"\n[OK] Fetched {len(contests)} contests.")
                if contests:
                    print("Top 3 recent contests:")
                    for c in contests[:3]:
                        print(f"  - {c.get('id')}: {c.get('name')} (Phase: {c.get('phase')})")
                        
            elif choice == "3":
                print("Fetching problems (might take a moment if caching for the first time)...")
                problems = await CodeforcesAPI.get_problems()
                print(f"\n[OK] Fetched {len(problems)} problems.")
                if problems:
                    print("Sample 3 problems:")
                    for p in problems[:3]:
                        print(f"  - {p.get('contestId')}{p.get('index')} - {p.get('name')} (Rating: {p.get('rating', 'N/A')})")
                        
            elif choice == "4":
                count_str = input("Enter number of submissions to fetch (default 10): ").strip()
                count = int(count_str) if count_str.isdigit() else 10
                print(f"Fetching up to {count} submissions for {default_handle}...")
                subs = await CodeforcesAPI.get_user_submissions(default_handle, count)
                print(f"\n[OK] Fetched {len(subs)} submissions.")
                for i, sub in enumerate(subs[:5]):
                    prob = sub.get('problem', {})
                    verdict = sub.get('verdict', 'UNKNOWN')
                    print(f"  {i+1}. {prob.get('contestId')}{prob.get('index')} - {prob.get('name')}: {verdict}")
                if len(subs) > 5:
                    print(f"  ... and {len(subs) - 5} more.")
                    
            elif choice == "5":
                contest_id = input("Enter Contest ID (e.g. 1542): ").strip()
                problem_index = input("Enter Problem Index (e.g. A): ").strip()
                if contest_id.isdigit() and problem_index:
                    print(f"Checking for compilation error by {default_handle} on {contest_id}{problem_index}...")
                    has_ce = await CodeforcesAPI.check_compilation_error(default_handle, int(contest_id), problem_index.upper())
                    if has_ce:
                        print(f"\n[OK] Found Compilation Error submission for {contest_id}{problem_index} by {default_handle}!")
                    else:
                        print(f"\n[NOT FOUND] No Compilation Error submission found in recent history.")
                else:
                    print("Invalid input for Contest ID or Problem Index.")
                    
            elif choice == "6":
                print("Exiting...")
                break
                
            else:
                print("Invalid choice. Please select a number from the menu.")
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            print(f"\n[EXCEPTION] An error occurred: {e}")

if __name__ == "__main__":
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
