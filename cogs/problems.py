import discord
from discord.ext import commands
from utils.codeforces_api import CodeforcesAPI
from utils.embeds import EmbedBuilder
import random

class Problems(commands.Cog):
    """Handles problem suggestions"""
    
    def __init__(self, bot):
        self.bot = bot
        self.cf_api = CodeforcesAPI()
    
    @commands.command(name='suggest')
    async def suggest_problem(self, ctx, rating):
        """Suggest a random problem near the given rating"""
        if not rating.isdigit():
            await ctx.send(embed=EmbedBuilder.error("please provide a valid numeric rating!"))
            return

        rating = int(rating)
        problems = await self.cf_api.get_problems()
        
        # Find problems within ±100 rating
        suitable = [p for p in problems if 'rating' in p and abs(p['rating'] - rating) <= 100]
        
        if not suitable:
            await ctx.send(embed=EmbedBuilder.error(f"No problems found near rating {rating}"))
            return
        
        problem = random.choice(suitable)
        
        embed = discord.Embed(
            title=f"📝 {problem['name']}",
            url=self.cf_api.get_problem_url(problem),
            description=f"**Rating:** {problem.get('rating', 'N/A')}",
            color=discord.Color.purple()
        )
        embed.add_field(name="Contest ID", value=problem['contestId'], inline=True)
        embed.add_field(name="Index", value=problem['index'], inline=True)
        # embed.add_field(name="Tags", value=', '.join(problem.get('tags', ['None'])[:5]), inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Problems(bot))