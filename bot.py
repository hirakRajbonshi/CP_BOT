import discord
from discord.ext import commands
from config.settings import BOT_PREFIX, INTENTS, DISCORD_BOT_TOKEN, ERROR_CHANNEL_ID
import traceback

from keep_alive import keep_alive


# keep_alive()

class CPBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=INTENTS)
    
    async def setup_hook(self):
        """Load all cogs"""
        await self.load_extension('cogs.authentication')
        await self.load_extension('cogs.problems')
        await self.load_extension('cogs.duels')
        await self.load_extension('cogs.rounds')
    
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')

    # Catch prefix command errors
    async def on_command_error(self, ctx, error):
        error_channel = self.get_channel(ERROR_CHANNEL_ID)
        if not error_channel:
            return

        tb = "".join(traceback.format_exception(type(error), error, error.__traceback__))

        embed = discord.Embed(
            title="⚠️ Command Error",
            description=f"```py\n{tb[:4000]}\n```",
            color=discord.Color.red()
        )

        embed.add_field(name="User", value=str(ctx.author))
        embed.add_field(name="Command", value=str(ctx.command))

        print(f"Error in command '{ctx.command}': {error}")
        await error_channel.send(embed=embed)

    # Catch all other event errors
    async def on_error(self, event, *args, **kwargs):
        error_channel = self.get_channel(ERROR_CHANNEL_ID)
        if not error_channel:
            return

        tb = traceback.format_exc()

        embed = discord.Embed(
            title="⚠️ Event Error",
            description=f"```py\n{tb[:4000]}\n```",
            color=discord.Color.red()
        )

        embed.add_field(name="Event", value=event)
        print(f"Error in event '{event}': {tb}")
        await error_channel.send(embed=embed)

def main():
    
    if not DISCORD_BOT_TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
        return
    
    bot = CPBot()
    bot.run(DISCORD_BOT_TOKEN)

if __name__ == "__main__":
    main()