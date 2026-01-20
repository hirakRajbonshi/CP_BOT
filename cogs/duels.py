import discord
from discord.ext import commands
from models.duel import Duel, DuelManager
from utils.data_manager import DataManager
from utils.embeds import EmbedBuilder
from config.settings import MIN_PROBLEMS, MAX_PROBLEMS

class Duels(commands.Cog):
    """Handles duel challenges between users"""
    
    def __init__(self, bot):
        self.bot = bot
        self.duel_manager = DuelManager()
        self.data_manager = DataManager()
    
    @commands.command(name='challenge')
    async def challenge(self, ctx, opponent: discord.Member, n: int, low: int, high: int, t: int):
        """Challenge another user to a duel"""
        # Validation
        if opponent.bot:
            await ctx.send(embed=EmbedBuilder.error("Cannot challenge a bot!"))
            return
        
        if opponent.id == ctx.author.id:
            await ctx.send(embed=EmbedBuilder.error("Cannot challenge yourself!"))
            return
        
        if not (MIN_PROBLEMS <= n <= MAX_PROBLEMS):
            await ctx.send(embed=EmbedBuilder.error(f"Number of problems must be between {MIN_PROBLEMS} and {MAX_PROBLEMS}!"))
            return
        
        if low > high:
            await ctx.send(embed=EmbedBuilder.error("Low rating must be less than or equal to high rating!"))
            return
        
        # Check if users have linked accounts
        if not self.data_manager.get_cf_handle(ctx.author.id):
            await ctx.send(embed=EmbedBuilder.error("You need to link your CF account first! Use `;link <handle>`"))
            return
        
        if not self.data_manager.get_cf_handle(opponent.id):
            await ctx.send(embed=EmbedBuilder.error(f"{opponent.mention} needs to link their CF account first!"))
            return
        
        # Check if already in a duel
        if self.duel_manager.is_user_in_duel(ctx.author.id) or self.duel_manager.is_user_in_duel(opponent.id):
            await ctx.send(embed=EmbedBuilder.error("One of you is already in an active duel!"))
            return
        
        # Create duel
        duel = Duel(ctx.author.id, opponent.id, n, low, high, t)
        
        await ctx.send("⏳ Generating problems...")
        if not await duel.generate_problems():
            await ctx.send(embed=EmbedBuilder.error("Not enough problems found in the specified rating range!"))
            return
        
        # Store pending duel
        self.duel_manager.add_pending_duel(opponent.id, duel)
        
        embed = discord.Embed(
            title="⚔️ Duel Challenge!",
            description=f"{ctx.author.mention} challenges {opponent.mention}",
            color=discord.Color.red()
        )
        embed.add_field(name="Problems", value=n, inline=True)
        embed.add_field(name="Rating Range", value=f"{low} - {high}", inline=True)
        embed.add_field(name="Time per Problem", value=f"{t} minutes", inline=True)
        embed.set_footer(text=f"{opponent.name}, use ';accept' to accept the challenge!")
        
        await ctx.send(embed=embed)
    
    @commands.command(name='accept')
    async def accept_challenge(self, ctx):
        """Accept a pending challenge"""
        duel = self.duel_manager.get_pending_duel_for_opponent(ctx.author.id)
        
        if not duel:
            await ctx.send(embed=EmbedBuilder.error("No pending challenge found for you!"))
            return
        
        # Start duel
        self.duel_manager.start_duel(duel)
        
        problem = duel.get_current_problem()
        
        embed = EmbedBuilder.duel_problem(problem, 1, duel.n, duel.time_per_problem)
        embed.title = "⚔️ Duel Started!"
        embed.set_footer(text="Use ';check' to check if you solved it!")
        
        challenger = ctx.guild.get_member(duel.challenger_id)
        await ctx.send(f"{challenger.mention} {ctx.author.mention}")
        await ctx.send(embed=embed)
    
    @commands.command(name='reject')
    async def reject_challenge(self, ctx):
        """Reject a pending challenge"""
        duel = self.duel_manager.get_pending_duel_for_opponent(ctx.author.id)
        
        if not duel:
            await ctx.send(embed=EmbedBuilder.error("No pending challenge found for you!"))
            return
        
        challenger = ctx.guild.get_member(duel.challenger_id)
        await ctx.send(f"❌ {ctx.author.mention} rejected the duel challenge from {challenger.mention}.")
        
        self.duel_manager.remove_pending_duel(ctx.author.id)

    @commands.command(name='check')
    async def check_solution(self, ctx):
        """Check if you solved the current problem (earliest AC wins)"""

        duel = self.duel_manager.get_active_duel(ctx.author.id)

        if not duel or not duel.active:
            await ctx.send(embed=EmbedBuilder.error("You are not in an active duel!"))
            return

        if duel.is_time_up():
            await ctx.send("⏰ Time is up! Moving to next problem...")
            duel.advance_problem()

            if duel.is_complete():
                await self.end_duel(ctx, duel)
                return

            await self.show_next_problem(ctx, duel)
            return

        if duel.problem_solved:
            await ctx.send("❌ This problem is already solved. Moving on...")
            return

        await ctx.send("🔍 Checking submissions...")

        user_id = ctx.author.id
        opponent_id = duel.get_opponent_id(user_id)

        # Fetch submissions
        user_sub = await duel.get_first_ac_submission(user_id, self.data_manager)
        opp_sub  = await duel.get_first_ac_submission(opponent_id, self.data_manager)

        if not user_sub and not opp_sub:
            await ctx.send("❌ No accepted solutions found yet.")
            return

        # Decide winner
        winner_id = None
        winner_time = None

        if user_sub and not opp_sub:
            winner_id = user_id
            winner_time = user_sub["creationTimeSeconds"]

        elif opp_sub and not user_sub:
            winner_id = opponent_id
            winner_time = opp_sub["creationTimeSeconds"]

        else:
            # Both solved → compare timestamps
            if user_sub["creationTimeSeconds"] < opp_sub["creationTimeSeconds"]:
                winner_id = user_id
                winner_time = user_sub["creationTimeSeconds"]
            else:
                winner_id = opponent_id
                winner_time = opp_sub["creationTimeSeconds"]

        # Award points
        duel.problem_solved = True
        problem = duel.get_current_problem()
        points = problem.get("rating", 1000)

        duel.scores[winner_id] += points

        winner = ctx.guild.get_member(winner_id)
        loser = ctx.guild.get_member(opponent_id if winner_id == user_id else user_id)

        await ctx.send(
            f"🏆 **{winner.mention} solved first!** +{points} points\n\n"
            f"📊 **Score:**\n"
            f"{winner.mention}: {duel.scores[winner_id]}\n"
            f"{loser.mention}: {duel.scores[loser.id]}"
        )

        duel.advance_problem()

        if duel.is_complete():
            await self.end_duel(ctx, duel)
            return

        await self.show_next_problem(ctx, duel)

    
    @commands.command(name='duelstatus')
    async def duel_status(self, ctx):
        """Check your current duel status"""
        duel = self.duel_manager.get_active_duel(ctx.author.id)
        
        if not duel or not duel.active:
            await ctx.send(embed=EmbedBuilder.error("You are not in an active duel!"))
            return
        
        embed = EmbedBuilder.duel_status(ctx, duel)
        await ctx.send(embed=embed)
    
    @commands.command(name='forfeit')
    async def forfeit_duel(self, ctx):
        """Forfeit the current duel"""
        duel = self.duel_manager.get_active_duel(ctx.author.id)
        
        if not duel or not duel.active:
            await ctx.send(embed=EmbedBuilder.error("You are not in an active duel!"))
            return
        
        opponent_id = duel.get_opponent_id(ctx.author.id)
        opponent = ctx.guild.get_member(opponent_id)
        
        await ctx.send(f"🏳️ {ctx.author.mention} forfeited! {opponent.mention} wins!")
        
        self.duel_manager.end_duel(duel)
    
    async def show_next_problem(self, ctx, duel):
        """Show the next problem in the duel"""
        problem = duel.get_current_problem()
        
        if not problem:
            await self.end_duel(ctx, duel)
            return
        
        embed = EmbedBuilder.duel_problem(
            problem, 
            duel.current_problem_idx + 1, 
            duel.n, 
            duel.time_per_problem
        )
        
        await ctx.send(embed=embed)
    
    async def end_duel(self, ctx, duel):
        """End the duel and show final scores"""
        challenger = ctx.guild.get_member(duel.challenger_id)
        opponent = ctx.guild.get_member(duel.opponent_id)
        
        embed = EmbedBuilder.duel_results(duel, challenger, opponent)
        await ctx.send(embed=embed)
        
        # Clean up
        self.duel_manager.end_duel(duel)

async def setup(bot):
    await bot.add_cog(Duels(bot))
