import discord
from discord.ext import commands
from services.round_service import RoundService
from utils.embeds import EmbedBuilder
from utils.codeforces_api import CodeforcesAPI


class Rounds(commands.Cog):
    """Discord UI for multi-player rounds (2–5 players)"""

    def __init__(self, bot):
        self.bot = bot
        self.round_service = RoundService()

    @commands.command(name='round')
    async def start_round(self, ctx, *args):
        """Challenge multiple players to a round.

        Usage: ;round @p1 @p2 ... <n> <low> <high> <time>
        Example: ;round @alice @bob 3 800 1600 15
        Round starts once all invited players use ;raccept.
        """
        if len(args) < 5:
            await ctx.send(embed=EmbedBuilder.error(
                "Usage: `;round @p1 [@p2 ...] <n> <low> <high> <time>`\n"
                "Example: `;round @alice @bob 3 800 1600 15`"
            ))
            return

        try:
            t    = int(args[-1])
            high = int(args[-2])
            low  = int(args[-3])
            n    = int(args[-4])
        except ValueError:
            await ctx.send(embed=EmbedBuilder.error(
                "Last 4 arguments must be integers: `<n> <low> <high> <time>`"
            ))
            return

        mention_args = args[:-4]
        if not mention_args:
            await ctx.send(embed=EmbedBuilder.error("Please mention at least one opponent."))
            return

        opponents = []
        for arg in mention_args:
            try:
                member = await commands.MemberConverter().convert(ctx, arg)
                opponents.append(member)
            except commands.BadArgument:
                await ctx.send(embed=EmbedBuilder.error(f"Could not resolve member: `{arg}`"))
                return

        opp_tuples = [(m.id, m.bot) for m in opponents]
        error = RoundService.validate_round(ctx.author.id, opp_tuples, n, low, high)
        if error:
            await ctx.send(embed=EmbedBuilder.error(error))
            return

        if self.round_service.repo.is_user_in_round(ctx.author.id):
            await ctx.send(embed=EmbedBuilder.error("You are already in an active or pending round!"))
            return
        for m in opponents:
            if self.round_service.repo.is_user_in_round(m.id):
                await ctx.send(embed=EmbedBuilder.error(
                    f"{m.mention} is already in an active or pending round!"
                ))
                return

        await ctx.send("⏳ Generating problems...")

        opponent_ids = [m.id for m in opponents]
        round_ = await self.round_service.create_round(
            ctx.author.id, opponent_ids, n, low, high, t
        )

        if not round_:
            await ctx.send(embed=EmbedBuilder.error(
                "Not enough problems found in the specified rating range!"
            ))
            return

        # Invite message
        opp_mentions = " ".join(m.mention for m in opponents)
        player_list = "\n".join(
            [f"• {ctx.author.mention} (challenger) — ✅ accepted"] +
            [f"• {m.mention} — ⏳ pending" for m in opponents]
        )
        embed = discord.Embed(
            title="⚔️ Round Challenge!",
            description=f"{ctx.author.mention} has challenged {opp_mentions} to a round!",
            color=discord.Color.gold()
        )
        embed.add_field(name="Players", value=player_list, inline=False)
        embed.add_field(name="Problems", value=n, inline=True)
        embed.add_field(name="Rating Range", value=f"{low} – {high}", inline=True)
        embed.add_field(name="Time per Problem", value=f"{t} minutes", inline=True)
        embed.set_footer(text="Use ';raccept' to join or ';rreject' to decline.")

        await ctx.send(opp_mentions)
        await ctx.send(embed=embed)

    @commands.command(name='raccept')
    async def accept_round(self, ctx):
        """Accept a round invitation"""
        round_, all_accepted = self.round_service.accept_round(ctx.author.id)

        if round_ is None:
            await ctx.send(embed=EmbedBuilder.error("You have no pending round invitation!"))
            return

        if not all_accepted:
            # Show updated acceptance status
            pending_ids = [
                pid for pid in round_.player_ids
                if pid != round_.challenger_id
                and pid not in self.round_service.repo.accepted.get(round_.challenger_id, set())
            ]
            waiting = " ".join(f"<@{pid}>" for pid in pending_ids)
            await ctx.send(
                f"✅ {ctx.author.mention} accepted! "
                f"Waiting for: {waiting}"
            )
        else:
            # All accepted — round is now active
            all_mentions = " ".join(f"<@{pid}>" for pid in round_.player_ids)
            prob = round_.get_current_problem()
            prob_embed = self._problem_embed(prob, 1, round_.n, round_.time_per_problem)

            embed = discord.Embed(
                title="🏆 Round Started!",
                description=f"All players have accepted! A {round_.player_count}-player round has begun!",
                color=discord.Color.gold()
            )
            scores_str = "\n".join(f"• <@{pid}>" for pid in round_.player_ids)
            embed.add_field(name="Players", value=scores_str, inline=False)
            embed.add_field(name="Problems", value=round_.n, inline=True)
            embed.add_field(name="Rating Range", value=f"{round_.low} – {round_.high}", inline=True)
            embed.add_field(name="Time per Problem", value=f"{round_.time_per_problem} min", inline=True)
            embed.set_footer(text="Use ';rcheck' to check submissions!")

            await ctx.send(all_mentions)
            await ctx.send(embed=embed)
            await ctx.send(embed=prob_embed)

    @commands.command(name='rreject')
    async def reject_round(self, ctx):
        """Reject a round invitation — cancels the round for everyone"""
        round_ = self.round_service.reject_round(ctx.author.id)

        if round_ is None:
            await ctx.send(embed=EmbedBuilder.error("You have no pending round invitation!"))
            return

        challenger = ctx.guild.get_member(round_.challenger_id)
        all_mentions = " ".join(f"<@{pid}>" for pid in round_.player_ids)
        await ctx.send(
            f"{all_mentions}\n"
            f"❌ {ctx.author.mention} rejected the round. "
            f"The challenge from {challenger.mention if challenger else 'the challenger'} has been cancelled."
        )

    @commands.command(name='rcheck')
    async def check_solution(self, ctx):
        """Check if anyone solved the current round problem"""
        await ctx.send("🔍 Checking submissions for all players...")

        round_, result = await self.round_service.check_solution(ctx.author.id)

        if round_ is None:
            await ctx.send(embed=EmbedBuilder.error("You are not in an active round!"))
            return

        if result.time_up:
            await ctx.send("⏰ Time is up! Moving to the next problem...")
            if result.round_complete:
                await self._end_round(ctx, round_)
            else:
                await self._show_next_problem(ctx, round_)
            return

        if result.already_solved:
            await ctx.send("❌ This problem is already solved. Wait for the next one!")
            return

        if result.no_solution:
            await ctx.send("❌ No accepted solutions found yet. Keep going!")
            return

        winner = ctx.guild.get_member(result.winner_id)
        scores_str = "\n".join(
            f"<@{pid}>: **{round_.scores[pid]}** pts"
            for pid in round_.player_ids
        )
        await ctx.send(
            f"🏆 **{winner.mention} solved it first!** +{result.points} pts\n\n"
            f"📊 **Scores:**\n{scores_str}"
        )

        if result.round_complete:
            await self._end_round(ctx, round_)
        else:
            await self._show_next_problem(ctx, round_)

    @commands.command(name='rstatus')
    async def round_status(self, ctx):
        """Check the current round status and scores"""
        round_ = self.round_service.get_round_status(ctx.author.id)

        if not round_:
            await ctx.send(embed=EmbedBuilder.error("You are not in an active round!"))
            return

        scores_str = "\n".join(
            f"<@{pid}>: **{round_.scores[pid]}** pts"
            for pid in round_.player_ids
        )
        embed = discord.Embed(title="🏆 Round Status", color=discord.Color.gold())
        embed.add_field(
            name="Progress",
            value=f"Problem {round_.current_problem_idx + 1} of {round_.n}",
            inline=False
        )
        embed.add_field(name="Scores", value=scores_str, inline=False)
        await ctx.send(embed=embed)

    @commands.command(name='rforfeit')
    async def forfeit_round(self, ctx):
        """Forfeit and leave the current round"""
        round_, continues = self.round_service.forfeit(ctx.author.id)

        if round_ is None:
            await ctx.send(embed=EmbedBuilder.error("You are not in an active round!"))
            return

        await ctx.send(f"🏳️ {ctx.author.mention} has forfeited and left the round.")

        if not continues:
            last_id = round_.player_ids[0] if round_.player_ids else None
            if last_id:
                last = ctx.guild.get_member(last_id)
                await ctx.send(f"🏆 Only {last.mention} remains — they win by default!")
            await self._end_round(ctx, round_)

    @commands.command(name='rcancel')
    async def cancel_round(self, ctx):
        """Cancel your pending round invitation (challenger only)"""
        round_ = self.round_service.cancel_round(ctx.author.id)
        if not round_:
            await ctx.send(embed=EmbedBuilder.error("You have no pending round to cancel."))
            return
        all_mentions = " ".join(f"<@{pid}>" for pid in round_.player_ids if pid != ctx.author.id)
        await ctx.send(
            f"{all_mentions}\n❌ {ctx.author.mention} has cancelled the round challenge."
        )

    # -------------------- Helpers --------------------

    def _problem_embed(self, problem, current, total, time_limit):
        embed = discord.Embed(
            title=f"📝 Problem {current} of {total}",
            color=discord.Color.gold()
        )
        embed.add_field(
            name="Problem",
            value=(
                f"[{problem['contestId']}{problem['index']} – {problem['name']}]"
                f"({CodeforcesAPI.get_problem_url(problem)})"
            ),
            inline=False
        )
        embed.add_field(name="Rating", value=problem.get('rating', 'N/A'), inline=True)
        embed.add_field(name="Time Limit", value=f"{time_limit} minutes", inline=True)
        return embed

    async def _show_next_problem(self, ctx, round_):
        problem = round_.get_current_problem()
        if not problem:
            await self._end_round(ctx, round_)
            return
        embed = self._problem_embed(
            problem,
            round_.current_problem_idx + 1,
            round_.n,
            round_.time_per_problem
        )
        await ctx.send(embed=embed)

    async def _end_round(self, ctx, round_):
        sorted_players = sorted(round_.scores.items(), key=lambda x: x[1], reverse=True)
        medals = ["🥇", "🥈", "🥉"]
        podium = ""
        for i, (pid, score) in enumerate(sorted_players):
            medal = medals[i] if i < len(medals) else f"{i+1}."
            podium += f"{medal} <@{pid}>: **{score}** pts\n"

        embed = discord.Embed(
            title="🏁 Round Complete!",
            description=podium,
            color=discord.Color.gold()
        )
        top_id = sorted_players[0][0] if sorted_players else None
        if top_id:
            top = ctx.guild.get_member(top_id)
            if top:
                embed.set_footer(text=f"🏆 Winner: {top.display_name}")

        await ctx.send(embed=embed)


async def setup(bot):
    await bot.add_cog(Rounds(bot))
