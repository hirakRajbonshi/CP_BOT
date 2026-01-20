import discord
from discord.ext import commands
import os
from dotenv import load_dotenv
from config.settings import BOT_PREFIX, INTENTS

load_dotenv()

class CPBot(commands.Bot):
    def __init__(self):
        super().__init__(command_prefix=BOT_PREFIX, intents=INTENTS)
    
    async def setup_hook(self):
        """Load all cogs"""
        await self.load_extension('cogs.authentication')
        await self.load_extension('cogs.problems')
        await self.load_extension('cogs.duels')
    
    async def on_ready(self):
        print(f'{self.user} has connected to Discord!')
        print(f'Bot is in {len(self.guilds)} guilds')

def main():
    TOKEN = os.getenv('DISCORD_BOT_TOKEN')
    
    if not TOKEN:
        print("Error: DISCORD_BOT_TOKEN not found in environment variables!")
        print("Please create a .env file with your bot token.")
        return
    
    bot = CPBot()
    bot.run(TOKEN)

if __name__ == "__main__":
    main()