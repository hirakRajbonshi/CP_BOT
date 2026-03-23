import asyncio
import sys
import os

# Add parent directory to path so we can import our modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.auth_service import AuthService
from services.problem_service import ProblemService
from services.duel_service import DuelService
from repositories.user_repo import UserRepo

duel_service = DuelService()

async def main():
    current_user_id = 11111  # Default mock user
    opponent_id = 22222      # Default mock opponent

    while True:
        print("\n" + "="*40)
        print("      CP Bot Services Tester (CLI)      ")
        print("="*40)
        print(f"Current User ID: {current_user_id} | Opponent ID: {opponent_id}")
        print("-" * 40)
        print("0. Change Current User ID")
        print("11. Switch to Opponent (Swap IDs)")
        print("\n--- AuthService ---")
        print("1. Link Account")
        print("2. Verify Account")
        print("3. Check Status")
        print("\n--- ProblemService ---")
        print("4. Suggest Problem")
        print("\n--- DuelService ---")
        print("5. Challenge Opponent")
        print("6. Accept Challenge (as current user)")
        print("7. Reject Challenge (as current user)")
        print("8. Check Solution")
        print("9. Check Duel Status")
        print("10. Forfeit Duel")
        print("\n12. Exit")
        print("="*40)
        
        choice = input("Enter choice: ").strip()
        
        try:
            if choice == "0":
                uid = input("Enter new User ID (int): ").strip()
                if uid.isdigit():
                    current_user_id = int(uid)
                    print(f"Changed current user ID to {current_user_id}")
                else:
                    print("Invalid ID.")
            
            elif choice == "11":
                current_user_id, opponent_id = opponent_id, current_user_id
                print(f"Swapped! You are now acting as {current_user_id}. Opponent is {opponent_id}.")

            elif choice == "1":
                handle = input("Enter Codeforces handle: ").strip()
                print("Fetching problems...")
                res = await AuthService.start_linking(current_user_id, handle)
                if res:
                    print(f"\n[OK] Link started for {handle}.")
                    print(f"Please submit with COMPILATION ERROR to {res['contestId']}{res['index']} - {res['name']}")
                    print(f"Link: https://codeforces.com/problemset/problem/{res['contestId']}/{res['index']}")
                else:
                    print("\n[ERROR] Failed to start linking (could not fetch problems).")
            
            elif choice == "2":
                print("Checking Codeforces for your submission...")
                success, msg = await AuthService.verify_account(current_user_id)
                if success:
                    print(f"\n[OK] Successfully linked! Your handle is {msg}.")
                else:
                    print(f"\n[ERROR] {msg}")

            elif choice == "3":
                status = AuthService.get_status(current_user_id)
                if status:
                    print(f"\n[STATUS] Linked to Codeforces handle: {status}")
                else:
                    print("\n[STATUS] Not linked.")

            elif choice == "4":
                rating_input = input("Enter target rating (or press Enter to auto-detect/random): ").strip()
                rating = int(rating_input) if rating_input.isdigit() else None
                
                print("Suggesting problem...")
                prob, r = await ProblemService.get_suggested_problem(current_user_id, rating)
                if prob:
                    print(f"\n[SUGGESTION] Rated ~{r}")
                    print(f"{prob['contestId']}{prob['index']} - {prob['name']} (Rating: {prob.get('rating', 'N/A')})")
                    print(f"Link: https://codeforces.com/problemset/problem/{prob['contestId']}/{prob['index']}")
                else:
                    print(f"\n[ERROR] {r}")

            elif choice == "5":
                n_input = input("Number of problems (default 1): ").strip()
                low_input = input("Low rating (default 800): ").strip()
                high_input = input("High rating (default 1200): ").strip()
                t_input = input("Time per problem in mins (default 30): ").strip()

                n = int(n_input) if n_input else 1
                low = int(low_input) if low_input else 800
                high = int(high_input) if high_input else 1200
                t = int(t_input) if t_input else 30
                
                err = DuelService.validate_challenge(current_user_id, opponent_id, False, n, low, high)
                if err:
                    print(f"\n[VALIDATION ERROR] {err}")
                else:
                    print("\nGenerating problems... this might take a few seconds.")
                    duel = await duel_service.create_challenge(current_user_id, opponent_id, n, low, high, t)
                    if duel:
                        print(f"\n[SUCCESS] Challenge created for {opponent_id}!")
                        print("Switch to the opponent (Option 11) to Accept or Reject.")
                    else:
                        print("\n[ERROR] Challenge creation failed (not enough problems matching criteria).")

            elif choice == "6":
                duel = duel_service.accept_challenge(current_user_id)
                if duel:
                    print("\n[SUCCESS] Duel accepted! The duel has started.")
                    prob = duel.get_current_problem()
                    print(f"First problem: {prob['contestId']}{prob['index']} - {prob['name']}")
                else:
                    print("\n[ERROR] No pending challenge found for you.")

            elif choice == "7":
                duel = duel_service.reject_challenge(current_user_id)
                if duel:
                    print("\n[OK] Challenge rejected.")
                else:
                    print("\n[ERROR] No pending challenge found for you.")

            elif choice == "8":
                print("Checking Codeforces API for both players' submissions...")
                duel, res = await duel_service.check_solution(current_user_id)
                if not duel:
                    print("\n[ERROR] You are not in an active duel.")
                else:
                    print(f"\n[CHECK RESULTS]")
                    if res.time_up:
                        print("Time is up! Advancing to the next problem.")
                    elif res.already_solved:
                        print("This problem is already solved.")
                    elif res.no_solution:
                        print("No accepted solutions found yet.")
                    elif res.winner_id:
                        print(f"Player {res.winner_id} solved it first and got {res.points} points!")
                    
                    if res.duel_complete:
                        print("\n🏆 Duel is now complete!")
                        print(f"Final Scores: {duel.scores}")
                    elif res.time_up or res.winner_id:
                        prob = duel.get_current_problem()
                        if prob:
                            print(f"\nNext problem: {prob['contestId']}{prob['index']} - {prob['name']}")

            elif choice == "9":
                duel = duel_service.get_duel_status(current_user_id)
                if duel:
                    print(f"\n[DUEL STATUS] Active!")
                    print(f"Problem: {duel.current_problem_idx + 1} / {duel.n}")
                    print(f"Scores: {duel.scores}")
                    prob = duel.get_current_problem()
                    if prob:
                         print(f"Current problem: {prob['contestId']}{prob['index']} - {prob['name']}")
                else:
                    print("\n[STATUS] You are not in an active duel.")

            elif choice == "10":
                duel, opp = duel_service.forfeit(current_user_id)
                if duel:
                    print(f"\n[FORFEIT] You forfeited. Player {opp} wins the duel.")
                else:
                    print("\n[ERROR] You are not in an active duel.")

            elif choice == "12":
                print("Exiting...")
                break

            else:
                print("Invalid choice. Please select a number from the menu.")
                
        except Exception as e:
            print(f"\n[EXCEPTION] An error occurred: {e}")

if __name__ == "__main__":
    # To fix 'RuntimeError: Event loop is closed' on Windows
    if sys.platform == 'win32':
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nExiting...")
