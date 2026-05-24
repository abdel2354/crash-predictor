"""
Free Fire OB53 Bot - Telegram Control Panel
Connects the FF TCP bot with a Telegram bot interface using inline keyboard buttons.

Usage:
  1. Set your Telegram bot token in config.json or TELEGRAM_BOT_TOKEN env var
  2. Run: python telegram_bot.py
"""

import os
import json
import asyncio
import aiohttp
import requests
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- Config ---
CONFIG_FILE = "config.json"

def load_config():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, "r") as f:
            return json.load(f)
    return {}

def save_config(cfg):
    with open(CONFIG_FILE, "w") as f:
        json.dump(cfg, f, indent=2)

def get_token():
    cfg = load_config()
    return cfg.get("telegram_token") or os.environ.get("TELEGRAM_BOT_TOKEN", "")

def get_bot_credentials():
    try:
        with open("bot.txt", "r") as f:
            content = f.read()
        import re
        uid_match = re.search(r'(?:uid\s*[=:]\s*)(\d+)', content, re.IGNORECASE)
        pass_match = re.search(r'(?:password\s*[=:]\s*)([^\s\n\r]+)', content, re.IGNORECASE)
        if uid_match and pass_match:
            return uid_match.group(1), pass_match.group(1)
    except:
        pass
    return None, None

# --- Conversation states ---
WAITING_UID = 1
WAITING_GUILD_ID = 2
WAITING_GUILD_JOIN = 3
WAITING_GUILD_LEAVE = 4

# --- API Functions ---
async def api_add_friend(uid, password, friend_uid):
    try:
        url = f"https://mafuuuuu-add.vercel.app/mafu-add_friend?uid={uid}&password={password}&player_id={friend_uid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    return True, await resp.text()
                return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)

async def api_remove_friend(uid, password, friend_uid):
    try:
        url = f"https://mafuuuuu-add.vercel.app/mafu-remove_friend?uid={uid}&password={password}&player_id={friend_uid}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    return True, await resp.text()
                return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)

async def api_guild_info(guild_id, region="IND"):
    try:
        url = f"https://danger-guild-management-web.vercel.app/guild?guild_id={guild_id}&region={region}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    return True, await resp.json()
                return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)

async def api_guild_join(guild_id, guest_uid, guest_pw):
    try:
        url = f"https://danger-guild-management-web.vercel.app/join?guild_id={guild_id}&uid={guest_uid}&password={guest_pw}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    return True, await resp.text()
                return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)

async def api_guild_leave(guild_id, guest_uid, guest_pw):
    try:
        url = f"https://danger-guild-management-web.vercel.app/leave?guild_id={guild_id}&uid={guest_uid}&password={guest_pw}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                if resp.status == 200:
                    return True, await resp.text()
                return False, f"HTTP {resp.status}"
    except Exception as e:
        return False, str(e)

def get_player_likes(uid):
    try:
        text = requests.get(
            f"https://tokens-asfufvfshnfkhvbb.francecentral-01.azurewebsites.net/ReQuesT?id={uid}&type=likes",
            timeout=10
        ).text
        import re
        get = lambda p: re.search(p, text)
        name = get(r"PLayer NamE\s*:\s*(.+)")
        lb = get(r"LiKes BeFore\s*:\s*(\d+)")
        la = get(r"LiKes After\s*:\s*(\d+)")
        lg = get(r"LiKes GiVen\s*:\s*(\d+)")
        return (
            name.group(1).strip() if name else "Unknown",
            int(lb.group(1)) if lb else 0,
            int(la.group(1)) if la else 0,
            int(lg.group(1)) if lg else 0
        )
    except:
        return "Unknown", 0, 0, 0

def check_uid_status(uid):
    try:
        api = requests.get(
            "https://panel-g2ccathtf6gdcmdw.polandcentral-01.azurewebsites.net/Uids",
            timeout=10
        )
        if api.status_code not in [200, 201]:
            return None
        lines = api.text.splitlines()
        import re
        for i, line in enumerate(lines):
            if f' - Uid : {uid}' in line:
                expire, status = None, None
                for sub_line in lines[i:]:
                    if "Expire In" in sub_line:
                        expire = re.search(r"Expire In\s*:\s*(.*)", sub_line).group(1).strip()
                    if "Status" in sub_line:
                        status = re.search(r"Status\s*:\s*(\w+)", sub_line).group(1)
                    if expire and status:
                        return status, expire
                return None
        return None
    except:
        return None


# ========================
# Telegram Handler Functions
# ========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [
            InlineKeyboardButton("👥 Friend System", callback_data="menu_friend"),
            InlineKeyboardButton("🏰 Guild System", callback_data="menu_guild"),
        ],
        [
            InlineKeyboardButton("📊 Player Info", callback_data="menu_player"),
            InlineKeyboardButton("❤️ Likes", callback_data="menu_likes"),
        ],
        [
            InlineKeyboardButton("🔍 Check UID", callback_data="menu_check"),
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="menu_help"),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    welcome = (
        "🎮 *Free Fire OB53 Bot*\n"
        "━━━━━━━━━━━━━━━━\n"
        "Welcome! Choose a category:\n"
    )
    if update.message:
        await update.message.reply_text(welcome, reply_markup=reply_markup, parse_mode="Markdown")
    elif update.callback_query:
        await update.callback_query.edit_message_text(welcome, reply_markup=reply_markup, parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    # --- Main Menu ---
    if data == "menu_main":
        await start(update, context)
        return

    # --- Friend System ---
    elif data == "menu_friend":
        keyboard = [
            [
                InlineKeyboardButton("➕ Add Friend", callback_data="friend_add"),
                InlineKeyboardButton("➖ Remove Friend", callback_data="friend_remove"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
        ]
        await query.edit_message_text(
            "👥 *Friend System*\n━━━━━━━━━━━━━━━━\nChoose an action:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "friend_add":
        context.user_data["action"] = "add_friend"
        await query.edit_message_text(
            "➕ *Add Friend*\n━━━━━━━━━━━━━━━━\nSend the player UID:",
            parse_mode="Markdown"
        )

    elif data == "friend_remove":
        context.user_data["action"] = "remove_friend"
        await query.edit_message_text(
            "➖ *Remove Friend*\n━━━━━━━━━━━━━━━━\nSend the player UID:",
            parse_mode="Markdown"
        )

    # --- Guild System ---
    elif data == "menu_guild":
        keyboard = [
            [InlineKeyboardButton("📊 Guild Info", callback_data="guild_info")],
            [
                InlineKeyboardButton("📥 Join Guild", callback_data="guild_join"),
                InlineKeyboardButton("📤 Leave Guild", callback_data="guild_leave"),
            ],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
        ]
        await query.edit_message_text(
            "🏰 *Guild System*\n━━━━━━━━━━━━━━━━\nChoose an action:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "guild_info":
        context.user_data["action"] = "guild_info"
        await query.edit_message_text(
            "📊 *Guild Info*\n━━━━━━━━━━━━━━━━\n"
            "Send guild ID (optionally with region):\n"
            "Example: `123456` or `123456 IND`",
            parse_mode="Markdown"
        )

    elif data == "guild_join":
        context.user_data["action"] = "guild_join"
        await query.edit_message_text(
            "📥 *Join Guild*\n━━━━━━━━━━━━━━━━\n"
            "Send: `guild_id uid password`\n"
            "Example: `123456 987654 mypass`",
            parse_mode="Markdown"
        )

    elif data == "guild_leave":
        context.user_data["action"] = "guild_leave"
        await query.edit_message_text(
            "📤 *Leave Guild*\n━━━━━━━━━━━━━━━━\n"
            "Send: `guild_id uid password`\n"
            "Example: `123456 987654 mypass`",
            parse_mode="Markdown"
        )

    # --- Player Info ---
    elif data == "menu_player":
        context.user_data["action"] = "player_info"
        await query.edit_message_text(
            "📊 *Player Info*\n━━━━━━━━━━━━━━━━\nSend the player UID:",
            parse_mode="Markdown"
        )

    # --- Likes ---
    elif data == "menu_likes":
        context.user_data["action"] = "likes"
        await query.edit_message_text(
            "❤️ *Send Likes*\n━━━━━━━━━━━━━━━━\nSend the player UID:",
            parse_mode="Markdown"
        )

    # --- Check UID ---
    elif data == "menu_check":
        context.user_data["action"] = "check_uid"
        await query.edit_message_text(
            "🔍 *Check UID Status*\n━━━━━━━━━━━━━━━━\nSend the player UID:",
            parse_mode="Markdown"
        )

    # --- Settings ---
    elif data == "menu_settings":
        bot_uid, _ = get_bot_credentials()
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
        ]
        await query.edit_message_text(
            f"⚙️ *Settings*\n━━━━━━━━━━━━━━━━\n"
            f"Bot UID: `{bot_uid or 'Not configured'}`\n"
            f"Config: `{CONFIG_FILE}`\n",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    # --- Help ---
    elif data == "menu_help":
        keyboard = [
            [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
        ]
        help_text = (
            "❓ *Help - Available Commands*\n"
            "━━━━━━━━━━━━━━━━━━━\n\n"
            "👥 *Friend System:*\n"
            "  ➕ Add Friend — Add friend by UID\n"
            "  ➖ Remove Friend — Remove friend by UID\n\n"
            "🏰 *Guild System:*\n"
            "  📊 Guild Info — Get guild details\n"
            "  📥 Join Guild — Join with guest account\n"
            "  📤 Leave Guild — Leave with guest account\n\n"
            "📊 *Player Info:*\n"
            "  Get player name, level, bio, etc.\n\n"
            "❤️ *Likes:*\n"
            "  Send likes to a player\n\n"
            "🔍 *Check UID:*\n"
            "  Check if UID is banned/active\n\n"
            "━━━━━━━━━━━━━━━━━━━\n"
            "💡 *Text Commands:*\n"
            "`/start` — Main menu\n"
            "`/help` — This help\n"
            "`/addfriend <uid>` — Quick add friend\n"
            "`/removefriend <uid>` — Quick remove friend\n"
            "`/guildinfo <id> [region]` — Guild info\n"
            "`/guildjoin <id> <uid> <pw>` — Join guild\n"
            "`/guildleave <id> <uid> <pw>` — Leave guild\n"
            "`/like <uid>` — Send likes\n"
            "`/check <uid>` — Check UID status\n"
        )
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")


async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    action = context.user_data.get("action")
    text = update.message.text.strip()

    back_keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
    ])

    if not action:
        await update.message.reply_text(
            "Use /start to open the menu.",
            reply_markup=back_keyboard
        )
        return

    context.user_data["action"] = None

    # --- Add Friend ---
    if action == "add_friend":
        if not text.isdigit() or len(text) < 8:
            await update.message.reply_text("❌ Invalid UID! Must be 8+ digits.", reply_markup=back_keyboard)
            return
        await update.message.reply_text(f"⏳ Adding friend {text}...")
        bot_uid, bot_pw = get_bot_credentials()
        if not bot_uid:
            await update.message.reply_text("❌ Bot credentials not found in bot.txt!", reply_markup=back_keyboard)
            return
        success, result = await api_add_friend(bot_uid, bot_pw, text)
        if success:
            await update.message.reply_text(f"✅ Friend request sent to {text}!\n{result}", reply_markup=back_keyboard)
        else:
            await update.message.reply_text(f"❌ Failed: {result}", reply_markup=back_keyboard)

    # --- Remove Friend ---
    elif action == "remove_friend":
        if not text.isdigit() or len(text) < 8:
            await update.message.reply_text("❌ Invalid UID! Must be 8+ digits.", reply_markup=back_keyboard)
            return
        await update.message.reply_text(f"⏳ Removing friend {text}...")
        bot_uid, bot_pw = get_bot_credentials()
        if not bot_uid:
            await update.message.reply_text("❌ Bot credentials not found in bot.txt!", reply_markup=back_keyboard)
            return
        success, result = await api_remove_friend(bot_uid, bot_pw, text)
        if success:
            await update.message.reply_text(f"✅ Friend {text} removed!\n{result}", reply_markup=back_keyboard)
        else:
            await update.message.reply_text(f"❌ Failed: {result}", reply_markup=back_keyboard)

    # --- Guild Info ---
    elif action == "guild_info":
        parts = text.split()
        guild_id = parts[0]
        region = parts[1].upper() if len(parts) > 1 else "IND"
        await update.message.reply_text(f"⏳ Fetching guild info for {guild_id}...")
        success, data = await api_guild_info(guild_id, region)
        if success and isinstance(data, dict):
            msg = (
                f"🏰 *Guild Info*\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"Name: {data.get('guild_name', data.get('name', 'Unknown'))}\n"
                f"ID: {guild_id}\n"
                f"Level: {data.get('guild_level', data.get('level', 'N/A'))}\n"
                f"Members: {data.get('guild_members', data.get('members', 'N/A'))}/{data.get('guild_capacity', data.get('capacity', 'N/A'))}\n"
                f"Leader: {data.get('guild_leader', data.get('leader', 'N/A'))}\n"
                f"Region: {region}"
            )
            await update.message.reply_text(msg, reply_markup=back_keyboard, parse_mode="Markdown")
        elif success:
            await update.message.reply_text(f"✅ Guild Info:\n{data}", reply_markup=back_keyboard)
        else:
            await update.message.reply_text(f"❌ Failed: {data}", reply_markup=back_keyboard)

    # --- Guild Join ---
    elif action == "guild_join":
        parts = text.split()
        if len(parts) < 3:
            await update.message.reply_text("❌ Format: `guild_id uid password`", reply_markup=back_keyboard, parse_mode="Markdown")
            return
        await update.message.reply_text(f"⏳ Joining guild {parts[0]}...")
        success, result = await api_guild_join(parts[0], parts[1], parts[2])
        if success:
            await update.message.reply_text(f"✅ Joined guild {parts[0]}!\n{result}", reply_markup=back_keyboard)
        else:
            await update.message.reply_text(f"❌ Failed: {result}", reply_markup=back_keyboard)

    # --- Guild Leave ---
    elif action == "guild_leave":
        parts = text.split()
        if len(parts) < 3:
            await update.message.reply_text("❌ Format: `guild_id uid password`", reply_markup=back_keyboard, parse_mode="Markdown")
            return
        await update.message.reply_text(f"⏳ Leaving guild {parts[0]}...")
        success, result = await api_guild_leave(parts[0], parts[1], parts[2])
        if success:
            await update.message.reply_text(f"✅ Left guild {parts[0]}!\n{result}", reply_markup=back_keyboard)
        else:
            await update.message.reply_text(f"❌ Failed: {result}", reply_markup=back_keyboard)

    # --- Player Info ---
    elif action == "player_info":
        if not text.isdigit() or len(text) < 8:
            await update.message.reply_text("❌ Invalid UID!", reply_markup=back_keyboard)
            return
        await update.message.reply_text(f"⏳ Fetching player info for {text}...")
        try:
            from xHeaders import GeT_PLayer_InFo, GeTToK
            info = GeT_PLayer_InFo(text, GeTToK())
            if info:
                await update.message.reply_text(f"📊 Player Info:\n{info}", reply_markup=back_keyboard)
            else:
                await update.message.reply_text("❌ Could not get player info.", reply_markup=back_keyboard)
        except Exception as e:
            await update.message.reply_text(f"❌ Error: {str(e)[:100]}", reply_markup=back_keyboard)

    # --- Likes ---
    elif action == "likes":
        if not text.isdigit() or len(text) < 8:
            await update.message.reply_text("❌ Invalid UID!", reply_markup=back_keyboard)
            return
        await update.message.reply_text(f"⏳ Sending likes to {text}...")
        name, before, after, given = get_player_likes(text)
        msg = (
            f"❤️ *Likes Result*\n"
            f"━━━━━━━━━━━━━━━━\n"
            f"Player: {name}\n"
            f"Before: {before}\n"
            f"After: {after}\n"
            f"Given: {given}"
        )
        await update.message.reply_text(msg, reply_markup=back_keyboard, parse_mode="Markdown")

    # --- Check UID ---
    elif action == "check_uid":
        if not text.isdigit() or len(text) < 8:
            await update.message.reply_text("❌ Invalid UID!", reply_markup=back_keyboard)
            return
        await update.message.reply_text(f"⏳ Checking UID {text}...")
        result = check_uid_status(text)
        if result:
            status, expire = result
            msg = (
                f"🔍 *UID Check*\n"
                f"━━━━━━━━━━━━━━━━\n"
                f"UID: `{text}`\n"
                f"Status: {status}\n"
                f"Expires: {expire}"
            )
        else:
            msg = f"🔍 UID `{text}` — Not found or no active subscription."
        await update.message.reply_text(msg, reply_markup=back_keyboard, parse_mode="Markdown")


# --- Quick text commands ---
async def cmd_addfriend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /addfriend <uid>")
        return
    uid = context.args[0]
    bot_uid, bot_pw = get_bot_credentials()
    if not bot_uid:
        await update.message.reply_text("❌ Bot credentials not found!")
        return
    await update.message.reply_text(f"⏳ Adding friend {uid}...")
    success, result = await api_add_friend(bot_uid, bot_pw, uid)
    await update.message.reply_text(f"✅ Done!\n{result}" if success else f"❌ Failed: {result}")

async def cmd_removefriend(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /removefriend <uid>")
        return
    uid = context.args[0]
    bot_uid, bot_pw = get_bot_credentials()
    if not bot_uid:
        await update.message.reply_text("❌ Bot credentials not found!")
        return
    await update.message.reply_text(f"⏳ Removing friend {uid}...")
    success, result = await api_remove_friend(bot_uid, bot_pw, uid)
    await update.message.reply_text(f"✅ Done!\n{result}" if success else f"❌ Failed: {result}")

async def cmd_guildinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /guildinfo <guild_id> [region]")
        return
    guild_id = context.args[0]
    region = context.args[1].upper() if len(context.args) > 1 else "IND"
    await update.message.reply_text(f"⏳ Fetching guild {guild_id}...")
    success, data = await api_guild_info(guild_id, region)
    if success and isinstance(data, dict):
        msg = (
            f"🏰 Guild: {data.get('guild_name', data.get('name', 'Unknown'))}\n"
            f"Level: {data.get('guild_level', data.get('level', 'N/A'))}\n"
            f"Members: {data.get('guild_members', data.get('members', 'N/A'))}\n"
            f"Leader: {data.get('guild_leader', data.get('leader', 'N/A'))}"
        )
        await update.message.reply_text(msg)
    else:
        await update.message.reply_text(f"❌ Failed: {data}")

async def cmd_guildjoin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /guildjoin <guild_id> <uid> <password>")
        return
    await update.message.reply_text(f"⏳ Joining guild {context.args[0]}...")
    success, result = await api_guild_join(context.args[0], context.args[1], context.args[2])
    await update.message.reply_text(f"✅ Done!\n{result}" if success else f"❌ Failed: {result}")

async def cmd_guildleave(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 3:
        await update.message.reply_text("Usage: /guildleave <guild_id> <uid> <password>")
        return
    await update.message.reply_text(f"⏳ Leaving guild {context.args[0]}...")
    success, result = await api_guild_leave(context.args[0], context.args[1], context.args[2])
    await update.message.reply_text(f"✅ Done!\n{result}" if success else f"❌ Failed: {result}")

async def cmd_like(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /like <uid>")
        return
    uid = context.args[0]
    await update.message.reply_text(f"⏳ Sending likes to {uid}...")
    name, before, after, given = get_player_likes(uid)
    await update.message.reply_text(
        f"❤️ Player: {name}\nBefore: {before}\nAfter: {after}\nGiven: {given}"
    )

async def cmd_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /check <uid>")
        return
    uid = context.args[0]
    await update.message.reply_text(f"⏳ Checking {uid}...")
    result = check_uid_status(uid)
    if result:
        status, expire = result
        await update.message.reply_text(f"🔍 UID: {uid}\nStatus: {status}\nExpires: {expire}")
    else:
        await update.message.reply_text(f"🔍 UID {uid} — Not found.")

async def cmd_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "🎮 *Free Fire OB53 Bot Commands*\n\n"
        "/start — Main menu with buttons\n"
        "/addfriend <uid> — Add friend\n"
        "/removefriend <uid> — Remove friend\n"
        "/guildinfo <id> [region] — Guild info\n"
        "/guildjoin <id> <uid> <pw> — Join guild\n"
        "/guildleave <id> <uid> <pw> — Leave guild\n"
        "/like <uid> — Send likes\n"
        "/check <uid> — Check UID status\n"
        "/help — This message\n"
    )
    await update.message.reply_text(help_text, parse_mode="Markdown")


def main():
    token = get_token()
    if not token:
        print("❌ No Telegram bot token found!")
        print("Set it in config.json: {\"telegram_token\": \"YOUR_TOKEN\"}")
        print("Or set TELEGRAM_BOT_TOKEN environment variable")
        return

    app = Application.builder().token(token).build()

    # Button handler
    app.add_handler(CallbackQueryHandler(button_handler))

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", cmd_help))
    app.add_handler(CommandHandler("addfriend", cmd_addfriend))
    app.add_handler(CommandHandler("removefriend", cmd_removefriend))
    app.add_handler(CommandHandler("guildinfo", cmd_guildinfo))
    app.add_handler(CommandHandler("guildjoin", cmd_guildjoin))
    app.add_handler(CommandHandler("guildleave", cmd_guildleave))
    app.add_handler(CommandHandler("like", cmd_like))
    app.add_handler(CommandHandler("check", cmd_check))

    # Text input handler (for button-triggered actions)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    print("🤖 Telegram bot started!")
    print("Press Ctrl+C to stop")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
