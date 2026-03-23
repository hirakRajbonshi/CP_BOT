import discord
from discord.ext import commands
from services.problem_service import ProblemService
from utils.codeforces_api import CodeforcesAPI
from utils.embeds import EmbedBuilder


class Problems(commands.Cog):
    """Discord UI for problem suggestions"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='suggest')
    async def suggest_problem(self, ctx, rating:int = commands.parameter(
        description = "Desired problem rating.",
        default = -1
    )):
        """Suggest a random problem near the given rating"""
        if rating != -1 and not str(rating).lstrip('-').isdigit():
            await ctx.send(embed=EmbedBuilder.error("Please provide a valid numeric rating!"))
            return
        
        resolved_rating = None if rating == -1 else int(rating)
        problem, info = await ProblemService.get_suggested_problem(ctx.author.id, resolved_rating)

        if problem is None:
            await ctx.send(embed=EmbedBuilder.error(info))
            return

        embed = discord.Embed(
            title=f"📝 {problem['name']}",
            url=CodeforcesAPI.get_problem_url(problem),
            description=f"**Rating:** {problem.get('rating', 'N/A')}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Contest ID", value=problem['contestId'], inline=True)
        embed.add_field(name="Index", value=problem['index'], inline=True)
        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Problems(bot))