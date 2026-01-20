import discord
from config.settings import (
    COLOR_PRIMARY, COLOR_SUCCESS, COLOR_ERROR, 
    COLOR_WARNING, COLOR_DUEL
)
from utils.codeforces_api import CodeforcesAPI

class EmbedBuilder:
    """Utility class for creating Discord embeds"""
    
    @staticmethod
    def error(message):
        """Create an error embed"""
        return discord.Embed(
            title="❌ Error",
            description=message,
            color=COLOR_ERROR
        )
    
    @staticmethod
    def success(message):
        """Create a success embed"""
        return discord.Embed(
            title="✅ Success",
            description=message,
            color=COLOR_SUCCESS
        )
    
    @staticmethod
    def warning(message):
        """Create a warning embed"""
        return discord.Embed(
            title="⚠️ Warning",
            description=message,
            color=COLOR_WARNING
        )
    
    @staticmethod
    def duel_problem(problem, current, total, time_limit):
        """Create an embed for a duel problem"""
        cf_api = CodeforcesAPI()
        embed = discord.Embed(
            title=f"📝 Problem {current} of {total}",
            color=COLOR_PRIMARY
        )
        embed.add_field(
            name="Problem",
            value=f"[{problem['contestId']}{problem['index']} - {problem['name']}]({cf_api.get_problem_url(problem)})",
            inline=False
        )
        embed.add_field(name="Rating", value=problem.get('rating', 'N/A'), inline=True)
        embed.add_field(name="Time Limit", value=f"{time_limit} minutes", inline=True)
        return embed
    
    @staticmethod
    def duel_status(ctx, duel):
        """Create an embed for duel status"""
        opponent_id = duel.get_opponent_id(ctx.author.id)
        opponent = ctx.guild.get_member(opponent_id)
        
        embed = discord.Embed(
            title="⚔️ Duel Status",
            color=COLOR_DUEL
        )
        embed.add_field(
            name="Progress",
            value=f"Problem {duel.current_problem_idx + 1} of {duel.n}",
            inline=False
        )
        embed.add_field(
            name="Your Score",
            value=duel.scores[ctx.author.id],
            inline=True
        )
        embed.add_field(
            name=f"{opponent.name}'s Score",
            value=duel.scores[opponent_id],
            inline=True
        )
        
        return embed
    
    @staticmethod
    def duel_results(duel, challenger, opponent):
        """Create an embed for duel results"""
        challenger_score = duel.scores[duel.challenger_id]
        opponent_score = duel.scores[duel.opponent_id]
        
        embed = discord.Embed(
            title="🏆 Duel Complete!",
            color=COLOR_DUEL
        )
        embed.add_field(name=challenger.name, value=f"**{challenger_score}** points", inline=True)
        embed.add_field(name=opponent.name, value=f"**{opponent_score}** points", inline=True)
        
        if challenger_score > opponent_score:
            embed.add_field(name="Winner", value=f"🎉 {challenger.mention}", inline=False)
        elif opponent_score > challenger_score:
            embed.add_field(name="Winner", value=f"🎉 {opponent.mention}", inline=False)
        else:
            embed.add_field(name="Result", value="🤝 It's a tie!", inline=False)
        
        return embed