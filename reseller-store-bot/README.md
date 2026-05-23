# Reseller Store Bot

A Telegram bot for managing a reseller store with key management, account management, broadcast messaging, and statistics.

## Features

- **Login System**: Secure login/logout with credentials (LOGIN + PASSWORD)
- **Account Management** (Admin): Create, delete, top-up, and manage reseller accounts
- **Key Management**: Categories, positions, key types with stock management
- **Buy Keys**: Users can purchase keys from available stock
- **Broadcast**: Send messages (text/photo/document/video) to all authorized users
- **Statistics**: Daily, weekly, monthly sales stats, top buyers, net profit
- **Reset Command**: `/reset KEY_CODE` (disabled by default)

## Setup

1. Create a Telegram bot via [@BotFather](https://t.me/BotFather) and get the token.

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Set environment variables:
   ```bash
   export BOT_TOKEN="your_bot_token_here"
   export ADMIN_IDS="123456789"  # Comma-separated Telegram user IDs for super admins
   ```

4. Run the bot:
   ```bash
   python bot.py
   ```

## Creating the First Admin Account

1. Start the bot and send `/login`
2. The first account must be created directly in the database or via the admin panel
3. Set `ADMIN_IDS` in your environment to your Telegram user ID
4. Use `/start` to access the admin panel and create accounts

## Architecture

- **bot.py**: Main bot file with all handlers and conversation flows
- **database.py**: SQLite database operations
- **config.py**: Configuration and environment variables
- **store.db**: SQLite database (auto-created on first run)

## Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Start the bot / show main menu |
| `/login` | Login with credentials |
| `/reset KEY` | Reset a key (disabled) |

## Keyboard Layout

### Admin Menu
```
[Buy keys]  [Account]
[Manage]
[Log out]
```

### User Menu
```
[Buy keys]  [Account]
[Log out]
```

## License

MIT
