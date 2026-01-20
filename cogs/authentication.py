import discord
from discord.ext import commands
from utils.codeforces_api import CodeforcesAPI
from utils.data_manager import DataManager
from utils.embeds import EmbedBuilder
import random

class Authentication(commands.Cog):
    """Handles Codeforces account authentication"""
    
    def __init__(self, bot):
        self.bot = bot
        self.data_manager = DataManager()
        self.cf_api = CodeforcesAPI()
    
    @commands.command(name='link')
    async def link_account(self, ctx, cf_handle: str):
        """Link Discord account with Codeforces handle"""

        # Check if already linked
        if self.data_manager.get_cf_handle(ctx.author.id):
            # TODO: Add option to relink accounts
            await ctx.send(embed=EmbedBuilder.error("Your account is already linked! Use `;status` to check your linked handle."))
            return


        # Select a random easy problem for verification
        problems = await self.cf_api.get_problems()
        easy_problems = [p for p in problems if p.get('rating', 0) <= 1000]
        
        if not easy_problems:
            await ctx.send(embed=EmbedBuilder.error("Unable to fetch problems. Please try again later."))
            return
        
        verify_problem = random.choice(easy_problems)
        problem_id = f"{verify_problem['contestId']}{verify_problem['index']}"
        
        self.data_manager.add_pending_auth(ctx.author.id, cf_handle, problem_id)
        
        embed = discord.Embed(
            title="🔗 Account Linking",
            description=f"To verify your Codeforces account, please submit a solution with **COMPILATION ERROR** to the following problem:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Problem",
            value=f"[{verify_problem['contestId']}{verify_problem['index']} - {verify_problem['name']}]({self.cf_api.get_problem_url(verify_problem)})",
            inline=False
        )
        embed.add_field(name="CF Handle", value=cf_handle, inline=True)
        embed.add_field(name="Next Step", value="Use `;verify` after submitting", inline=True)
        
        await ctx.send(embed=embed)
    
    @commands.command(name='verify')
    async def verify_account(self, ctx):
        """Verify the authentication by checking for compilation error"""
        pending = self.data_manager.get_pending_auth(ctx.author.id)
        
        if not pending:
            await ctx.send(embed=EmbedBuilder.error("No pending authentication found. Use `;link <cf_handle>` first."))
            return
        
        cf_handle = pending['cf_handle']
        problem_id = pending['problem_id']
        contest_id = int(''.join(filter(str.isdigit, problem_id)))
        problem_index = ''.join(filter(str.isalpha, problem_id))
        
        await ctx.send("🔍 Checking your submission...")
        
        if await self.cf_api.check_compilation_error(cf_handle, contest_id, problem_index):
            self.data_manager.link_user(ctx.author.id, cf_handle)
            self.data_manager.remove_pending_auth(ctx.author.id)
            
            embed = discord.Embed(
                title="✅ Account Linked Successfully!",
                description=f"Your Discord account is now linked with CF handle: **{cf_handle}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=EmbedBuilder.error("Compilation error not found. Make sure you submitted to the correct problem with a compilation error."))
    
    @commands.command(name='status')
    async def status(self, ctx):
        """Check your linked CF handle"""
        cf_handle = self.data_manager.get_cf_handle(ctx.author.id)
        
        embed = discord.Embed(title="📊 Status", color=discord.Color.blue())
        
        if cf_handle:
            embed.add_field(name="CF Handle", value=cf_handle, inline=False)
            embed.add_field(name="Status", value="✅ Linked", inline=True)
        else:
            embed.add_field(name="CF Handle", value="Not linked", inline=False)
            embed.add_field(name="Status", value="❌ Not linked", inline=True)
            embed.add_field(name="How to link", value="Use `;link <cf_handle>`", inline=False)
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(Authentication(bot))