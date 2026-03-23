import discord
from discord.ext import commands
from services.auth_service import AuthService
from utils.codeforces_api import CodeforcesAPI
from utils.embeds import EmbedBuilder


class Authentication(commands.Cog):
    """Discord UI for Codeforces account authentication"""

    def __init__(self, bot):
        self.bot = bot

    @commands.command(name='link')
    async def link_account(self, ctx, cf_handle: str):
        """Link Discord account with Codeforces handle"""
        if await AuthService.is_already_linked(ctx.author.id):
            await ctx.send(embed=EmbedBuilder.error(
                "Your account is already linked! Use `;status` to check your linked handle."
            ))
            return

        verify_problem = await AuthService.start_linking(ctx.author.id, cf_handle)
        if not verify_problem:
            await ctx.send(embed=EmbedBuilder.error(
                "Unable to fetch problems. Please try again later."
            ))
            return

        embed = discord.Embed(
            title="🔗 Account Linking",
            description="To verify your Codeforces account, please submit a "
                        "solution with **COMPILATION ERROR** to the following problem:",
            color=discord.Color.blue()
        )
        embed.add_field(
            name="Problem",
            value=(
                f"[{verify_problem['contestId']}{verify_problem['index']} - "
                f"{verify_problem['name']}]"
                f"({CodeforcesAPI.get_problem_url(verify_problem)})"
            ),
            inline=False
        )
        embed.add_field(name="CF Handle", value=cf_handle, inline=True)
        embed.add_field(name="Next Step", value="Use `;verify` after submitting", inline=True)
        await ctx.send(embed=embed)

    @commands.command(name='verify')
    async def verify_account(self, ctx):
        """Verify the authentication by checking for compilation error"""
        await ctx.send("🔍 Checking your submission...")

        success, result = await AuthService.verify_account(ctx.author.id)

        if success:
            embed = discord.Embed(
                title="✅ Account Linked Successfully!",
                description=f"Your Discord account is now linked with CF handle: **{result}**",
                color=discord.Color.green()
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(embed=EmbedBuilder.error(result))

    @commands.command(name='status')
    async def status(self, ctx):
        """Check your linked CF handle"""
        cf_handle = AuthService.get_status(ctx.author.id)

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