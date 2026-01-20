# Competitive Programming Discord Bot

A feature-rich Discord bot for competitive programming enthusiasts with Codeforces integration.

## Features

- **Account Linking**: Secure Codeforces handle verification via compilation error
- **Problem Suggestions**: Get random problems based on rating
- **Duel System**: Challenge friends to competitive programming duels

## Setup

1. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment:**

   ```bash
   cp .env.example .env
   # Edit .env and add your Discord bot token
   ```

3. **Enable Discord Bot Intents:**

   - Go to Discord Developer Portal
   - Enable: Message Content Intent, Server Members Intent

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## Commands

### Authentication

- `;link <cf_handle>` - Link your Codeforces account
- `;verify` - Verify your account linkage
- `;status` - Check your status

### Problems

- `;suggest <rating>` - Get a random problem near the specified rating

### Duels

- `;challenge @user n low high t` - Challenge a user to a duel
  - `@user`: User to challenge
  - `n`: Number of problems (1-10)
  - `low`: Minimum problem rating
  - `high`: Maximum problem rating
  - `t`: Time in minutes per problem
- `;accept` - Accept a pending challenge
- `;check` - Check if you solved the current problem
- `;forfeit` - Forfeit the current duel

## Project Structure

```
cp-discord-bot/
├── bot.py              # Main bot entry point
├── cogs/               # Command modules
├── models/             # Data models
├── utils/              # Utility functions
├── config/             # Configuration
└── data/               # Persistent storage
```
