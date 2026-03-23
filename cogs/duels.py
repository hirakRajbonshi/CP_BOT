import discord
from discord.ext import commands
from services.duel_service import DuelService
from utils.embeds import EmbedBuilder


class Duels(commands.Cog):
    """Discord UI for duel challenges"""

    def __init__(self, bot):
        self.bot = bot
        self.duel_service = DuelService()

    @commands.command(name='challenge')
    async def challenge(
        self, 
        ctx, 
        opponent: discord.Member = commands.parameter(
            description="The user to challenge",
        ), 
        n: int = commands.parameter(
            converter=int,
            default=3,
            description="Number of problems",
        ), 
        low: int = commands.parameter(
            converter=int,
            default=800,
            description="Low rating",
        ), 
        high: int = commands.parameter(
            converter=int,
            default=1600,
            description="High rating",
        ), 
        t: int = commands.parameter(
            converter=int,
            default=10,
            description="Time per problem",
        ) 
    ):
        """
        Challenge another user to a duel
        ;challenge @user <n> <low> <high> <t>
        """
        error = DuelService.validate_challenge(
            ctx.author.id, opponent.id, opponent.bot, n, low, high
        )
        if error:
            await ctx.send(embed=EmbedBuilder.error(error))
            return

        if self.duel_service.repo.is_user_in_duel(ctx.author.id) or \
           self.duel_service.repo.is_user_in_duel(opponent.id):
            await ctx.send(embed=EmbedBuilder.error("One of you is already in an active duel!"))
            return

        await ctx.send("⏳ Generating problems...")
        duel = await self.duel_service.create_challenge(
            ctx.author.id, opponent.id, n, low, high, t
        )

        if not duel:
            await ctx.send(embed=EmbedBuilder.error(
                "Not enough problems found in the specified rating range!"
            ))
            return

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
        duel = self.duel_service.accept_challenge(ctx.author.id)

        if not duel:
            await ctx.send(embed=EmbedBuilder.error("No pending challenge found for you!"))
            return

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
        duel = self.duel_service.reject_challenge(ctx.author.id)

        if not duel:
            await ctx.send(embed=EmbedBuilder.error("No pending challenge found for you!"))
            return

        challenger = ctx.guild.get_member(duel.challenger_id)
        await ctx.send(f"❌ {ctx.author.mention} rejected the duel challenge from {challenger.mention}.")

    @commands.command(name='check')
    async def check_solution(self, ctx):
        """Check if you solved the current problem"""
        duel, result = await self.duel_service.check_solution(ctx.author.id)

        if duel is None:
            await ctx.send(embed=EmbedBuilder.error("You are not in an active duel!"))
            return

        if result.time_up:
            await ctx.send("⏰ Time is up! Moving to next problem...")
            if result.duel_complete:
                await self._end_duel(ctx, duel)
            else:
                await self._show_next_problem(ctx, duel)
            return

        if result.already_solved:
            await ctx.send("❌ This problem is already solved. Moving on...")
            return

        await ctx.send("🔍 Checking submissions...")

        if result.no_solution:
            await ctx.send("❌ No accepted solutions found yet.")
            return

        winner = ctx.guild.get_member(result.winner_id)
        loser = ctx.guild.get_member(result.loser_id)

        await ctx.send(
            f"🏆 **{winner.mention} solved first!** +{result.points} points\n\n"
            f"📊 **Score:**\n"
            f"{winner.mention}: {duel.scores[result.winner_id]}\n"
            f"{loser.mention}: {duel.scores[result.loser_id]}"
        )

        if result.duel_complete:
            await self._end_duel(ctx, duel)
        else:
            await self._show_next_problem(ctx, duel)

    @commands.command(name='duelstatus')
    async def duel_status(self, ctx):
        """Check your current duel status"""
        duel = self.duel_service.get_duel_status(ctx.author.id)

        if not duel:
            await ctx.send(embed=EmbedBuilder.error("You are not in an active duel!"))
            return

        embed = EmbedBuilder.duel_status(ctx, duel)
        await ctx.send(embed=embed)

    @commands.command(name='forfeit')
    async def forfeit_duel(self, ctx):
        """Forfeit the current duel"""
        duel, opponent_id = self.duel_service.forfeit(ctx.author.id)

        if not duel:
            await ctx.send(embed=EmbedBuilder.error("You are not in an active duel!"))
            return

        opponent = ctx.guild.get_member(opponent_id)
        await ctx.send(f"🏳️ {ctx.author.mention} forfeited! {opponent.mention} wins!")

    # -------------------- Helpers --------------------

    async def _show_next_problem(self, ctx, duel):
        problem = duel.get_current_problem()
        if not problem:
            await self._end_duel(ctx, duel)
            return

        embed = EmbedBuilder.duel_problem(
            problem,
            duel.current_problem_idx + 1,
            duel.n,
            duel.time_per_problem
        )
        await ctx.send(embed=embed)

    async def _end_duel(self, ctx, duel):
        challenger = ctx.guild.get_member(duel.challenger_id)
        opponent = ctx.guild.get_member(duel.opponent_id)
        embed = EmbedBuilder.duel_results(duel, challenger, opponent)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Duels(bot))
