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
import threading
import aiohttp
import requests
import logging

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes, ConversationHandler
)

try:
    from bbcXgen import (
        create_account, REGION_LANG, ACCOUNTS_FOLDER, RARE_ACCOUNTS_FOLDER,
        COUPLES_ACCOUNTS_FOLDER, TOKENS_FOLDER, GHOST_ACCOUNTS_FOLDER,
        check_rarity, save_normal_account, save_jwt_token, save_rare_account,
        BASE_FOLDER
    )
    GUEST_GEN_AVAILABLE = True
except ImportError:
    GUEST_GEN_AVAILABLE = False

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

def load_generated_accounts(region=None):
    accounts = []
    if not GUEST_GEN_AVAILABLE:
        return accounts
    folders = [ACCOUNTS_FOLDER, GHOST_ACCOUNTS_FOLDER]
    for folder in folders:
        if not os.path.exists(folder):
            continue
        for fname in os.listdir(folder):
            if not fname.endswith('.json'):
                continue
            if region and region.lower() not in fname.lower() and "ghost" not in fname.lower():
                continue
            try:
                with open(os.path.join(folder, fname), 'r') as f:
                    data = json.load(f)
                    accounts.extend(data)
            except:
                pass
    return accounts

def send_likes_with_account(target_uid, account_uid, account_pw):
    try:
        url = f"https://tokens-asfufvfshnfkhvbb.francecentral-01.azurewebsites.net/ReQuesT?id={target_uid}&type=likes"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return True, resp.text
        return False, f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)

def send_visit_with_account(target_uid, account_uid, account_pw):
    try:
        url = f"https://tokens-asfufvfshnfkhvbb.francecentral-01.azurewebsites.net/ReQuesT?id={target_uid}&type=spam"
        resp = requests.get(url, timeout=15)
        if resp.status_code == 200:
            return True, resp.text
        return False, f"HTTP {resp.status_code}"
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
            InlineKeyboardButton("🔥 Mass Likes", callback_data="menu_masslikes"),
            InlineKeyboardButton("👁 Visitors", callback_data="menu_visitors"),
        ],
        [
            InlineKeyboardButton("🔍 Check UID", callback_data="menu_check"),
            InlineKeyboardButton("🎮 Guest Gen", callback_data="menu_guestgen"),
        ],
        [
            InlineKeyboardButton("⚙️ Settings", callback_data="menu_settings"),
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

    # --- Mass Likes ---
    elif data == "menu_masslikes":
        keyboard = [
            [InlineKeyboardButton("🔥 Send Mass Likes", callback_data="masslikes_start")],
            [InlineKeyboardButton("🔥 Auto Gen + Likes", callback_data="masslikes_autogen")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
        ]
        accounts = load_generated_accounts()
        await query.edit_message_text(
            "🔥 *Mass Likes System*\n━━━━━━━━━━━━━━━━\n"
            f"📦 Available guest accounts: {len(accounts)}\n\n"
            "Send mass likes to any player using\n"
            "guest accounts or auto-generate new ones!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "masslikes_start":
        context.user_data["action"] = "masslikes_uid"
        await query.edit_message_text(
            "🔥 *Mass Likes*\n━━━━━━━━━━━━━━━━\n"
            "Send the *target UID* to send likes to:",
            parse_mode="Markdown"
        )

    elif data == "masslikes_autogen":
        context.user_data["action"] = "masslikes_autogen_uid"
        await query.edit_message_text(
            "🔥 *Auto Gen + Mass Likes*\n━━━━━━━━━━━━━━━━\n"
            "This will generate guest accounts and\n"
            "use them to send likes automatically.\n\n"
            "Send the *target UID*:",
            parse_mode="Markdown"
        )

    # --- Visitors ---
    elif data == "menu_visitors":
        keyboard = [
            [InlineKeyboardButton("👁 Send Visitors", callback_data="visitors_start")],
            [InlineKeyboardButton("👁 Auto Gen + Visit", callback_data="visitors_autogen")],
            [InlineKeyboardButton("🔙 Back", callback_data="menu_main")],
        ]
        accounts = load_generated_accounts()
        await query.edit_message_text(
            "👁 *Profile Visitors System*\n━━━━━━━━━━━━━━━━\n"
            f"📦 Available guest accounts: {len(accounts)}\n\n"
            "Send profile visits to any player\n"
            "using guest accounts!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data == "visitors_start":
        context.user_data["action"] = "visitors_uid"
        await query.edit_message_text(
            "👁 *Send Visitors*\n━━━━━━━━━━━━━━━━\n"
            "Send the *target UID* to visit:",
            parse_mode="Markdown"
        )

    elif data == "visitors_autogen":
        context.user_data["action"] = "visitors_autogen_uid"
        await query.edit_message_text(
            "👁 *Auto Gen + Visit*\n━━━━━━━━━━━━━━━━\n"
            "This will generate guest accounts and\n"
            "use them to visit the profile automatically.\n\n"
            "Send the *target UID*:",
            parse_mode="Markdown"
        )

    # --- Guest Gen ---
    elif data == "menu_guestgen":
        if not GUEST_GEN_AVAILABLE:
            keyboard = [[InlineKeyboardButton("🔙 Back", callback_data="menu_main")]]
            await query.edit_message_text(
                "❌ Guest Gen module not available!\nMake sure bbcXgen.py is in the bot directory.",
                reply_markup=InlineKeyboardMarkup(keyboard)
            )
            return
        regions = [r for r in REGION_LANG.keys() if r != "BR"]
        keyboard = []
        row = []
        for region in regions:
            row.append(InlineKeyboardButton(f"🌍 {region}", callback_data=f"gen_region_{region}"))
            if len(row) == 3:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton("👻 GHOST Mode", callback_data="gen_region_GHOST")])
        keyboard.append([InlineKeyboardButton("📂 View Accounts", callback_data="gen_view")])
        keyboard.append([InlineKeyboardButton("🔙 Back", callback_data="menu_main")])
        await query.edit_message_text(
            "🎮 *Guest Account Generator*\n━━━━━━━━━━━━━━━━\nSelect region:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif data.startswith("gen_region_"):
        region = data.replace("gen_region_", "")
        context.user_data["gen_region"] = region
        context.user_data["action"] = "gen_count"
        is_ghost = region == "GHOST"
        mode_text = "👻 GHOST Mode" if is_ghost else f"🌍 Region: {region}"
        await query.edit_message_text(
            f"🎮 *Guest Gen — {mode_text}*\n━━━━━━━━━━━━━━━━\n"
            f"How many accounts? Send a number (1-50):",
            parse_mode="Markdown"
        )

    elif data == "gen_view":
        msg = "📂 *Generated Accounts*\n━━━━━━━━━━━━━━━━\n"
        total = 0
        for folder_name, folder_path in [("Normal", ACCOUNTS_FOLDER), ("Rare", RARE_ACCOUNTS_FOLDER), ("Couples", COUPLES_ACCOUNTS_FOLDER)]:
            if os.path.exists(folder_path):
                files = [f for f in os.listdir(folder_path) if f.endswith('.json')]
                for fname in files:
                    try:
                        with open(os.path.join(folder_path, fname), 'r') as file:
                            data_list = json.load(file)
                            count = len(data_list)
                            total += count
                            msg += f"📄 {folder_name}/{fname}: {count}\n"
                    except:
                        pass
        ghost_file = os.path.join(GHOST_ACCOUNTS_FOLDER, "ghost.json")
        if os.path.exists(ghost_file):
            try:
                with open(ghost_file, 'r') as file:
                    data_list = json.load(file)
                    total += len(data_list)
                    msg += f"👻 Ghost: {len(data_list)}\n"
            except:
                pass
        msg += f"\n📊 Total: {total} accounts"
        keyboard = [
            [InlineKeyboardButton("🔙 Guest Gen", callback_data="menu_guestgen")],
            [InlineKeyboardButton("🔙 Main Menu", callback_data="menu_main")]
        ]
        await query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

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
            "`/gen <region> <count> <name> <pass>` — Generate guest accounts\n"
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

    # --- Mass Likes Flow ---
    if action == "masslikes_uid":
        if not text.isdigit():
            await update.message.reply_text("❌ UID must be a number!", reply_markup=back_keyboard)
            return
        context.user_data["action"] = "masslikes_count"
        context.user_data["masslikes_target"] = text
        await update.message.reply_text(
            f"✅ Target: `{text}`\n\nHow many times to send likes? (1-20):",
            parse_mode="Markdown"
        )
        return

    if action == "masslikes_count":
        try:
            count = int(text)
            if count < 1 or count > 20:
                await update.message.reply_text("❌ Enter 1-20.", reply_markup=back_keyboard)
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid number!", reply_markup=back_keyboard)
            return
        target_uid = context.user_data.get("masslikes_target")
        context.user_data["action"] = None
        status_msg = await update.message.reply_text(
            f"🔥 *Sending Mass Likes*\n━━━━━━━━━━━━━━━━\n"
            f"Target: `{target_uid}`\nRounds: {count}\n\n⏳ Working...",
            parse_mode="Markdown"
        )
        success_count = 0
        for i in range(count):
            ok, result = send_likes_with_account(target_uid, None, None)
            if ok:
                success_count += 1
            try:
                await status_msg.edit_text(
                    f"🔥 Sending likes... {i+1}/{count}\n✅ Success: {success_count}"
                )
            except:
                pass
            await asyncio.sleep(1)
        await status_msg.edit_text(
            f"🔥 *Mass Likes Complete!*\n━━━━━━━━━━━━━━━━\n"
            f"Target: `{target_uid}`\n"
            f"✅ Success: {success_count}/{count}",
            reply_markup=back_keyboard,
            parse_mode="Markdown"
        )
        return

    if action == "masslikes_autogen_uid":
        if not text.isdigit():
            await update.message.reply_text("❌ UID must be a number!", reply_markup=back_keyboard)
            return
        context.user_data["action"] = "masslikes_autogen_count"
        context.user_data["masslikes_target"] = text
        await update.message.reply_text(
            f"✅ Target: `{text}`\n\nHow many accounts to generate & use? (1-10):",
            parse_mode="Markdown"
        )
        return

    if action == "masslikes_autogen_count":
        if not GUEST_GEN_AVAILABLE:
            await update.message.reply_text("❌ Guest Gen module not available!", reply_markup=back_keyboard)
            context.user_data["action"] = None
            return
        try:
            count = int(text)
            if count < 1 or count > 10:
                await update.message.reply_text("❌ Enter 1-10.", reply_markup=back_keyboard)
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid number!", reply_markup=back_keyboard)
            return
        target_uid = context.user_data.get("masslikes_target")
        context.user_data["action"] = None
        status_msg = await update.message.reply_text(
            f"🔥 *Auto Gen + Mass Likes*\n━━━━━━━━━━━━━━━━\n"
            f"Target: `{target_uid}`\n"
            f"⏳ Generating {count} accounts...",
            parse_mode="Markdown"
        )
        generated = []
        def gen_and_like():
            for i in range(count):
                acc = create_account("ME", "M3SBIOS", "M3SBIOS", False)
                if acc:
                    generated.append(acc)
        thread = threading.Thread(target=gen_and_like)
        thread.start()
        while thread.is_alive():
            await asyncio.sleep(3)
            try:
                await status_msg.edit_text(
                    f"⏳ Generated: {len(generated)}/{count} accounts..."
                )
            except:
                pass
        thread.join()
        success_count = 0
        for acc in generated:
            ok, _ = send_likes_with_account(target_uid, acc.get("uid"), acc.get("password"))
            if ok:
                success_count += 1
            await asyncio.sleep(1)
        await status_msg.edit_text(
            f"🔥 *Auto Gen + Likes Complete!*\n━━━━━━━━━━━━━━━━\n"
            f"Target: `{target_uid}`\n"
            f"📦 Generated: {len(generated)} accounts\n"
            f"✅ Likes sent: {success_count}/{len(generated)}",
            reply_markup=back_keyboard,
            parse_mode="Markdown"
        )
        return

    # --- Visitors Flow ---
    if action == "visitors_uid":
        if not text.isdigit():
            await update.message.reply_text("❌ UID must be a number!", reply_markup=back_keyboard)
            return
        context.user_data["action"] = "visitors_count"
        context.user_data["visitors_target"] = text
        await update.message.reply_text(
            f"✅ Target: `{text}`\n\nHow many visits to send? (1-20):",
            parse_mode="Markdown"
        )
        return

    if action == "visitors_count":
        try:
            count = int(text)
            if count < 1 or count > 20:
                await update.message.reply_text("❌ Enter 1-20.", reply_markup=back_keyboard)
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid number!", reply_markup=back_keyboard)
            return
        target_uid = context.user_data.get("visitors_target")
        context.user_data["action"] = None
        status_msg = await update.message.reply_text(
            f"👁 *Sending Visitors*\n━━━━━━━━━━━━━━━━\n"
            f"Target: `{target_uid}`\nRounds: {count}\n\n⏳ Working...",
            parse_mode="Markdown"
        )
        success_count = 0
        for i in range(count):
            ok, result = send_visit_with_account(target_uid, None, None)
            if ok:
                success_count += 1
            try:
                await status_msg.edit_text(
                    f"👁 Sending visits... {i+1}/{count}\n✅ Success: {success_count}"
                )
            except:
                pass
            await asyncio.sleep(1)
        await status_msg.edit_text(
            f"👁 *Visitors Complete!*\n━━━━━━━━━━━━━━━━\n"
            f"Target: `{target_uid}`\n"
            f"✅ Success: {success_count}/{count}",
            reply_markup=back_keyboard,
            parse_mode="Markdown"
        )
        return

    if action == "visitors_autogen_uid":
        if not text.isdigit():
            await update.message.reply_text("❌ UID must be a number!", reply_markup=back_keyboard)
            return
        context.user_data["action"] = "visitors_autogen_count"
        context.user_data["visitors_target"] = text
        await update.message.reply_text(
            f"✅ Target: `{text}`\n\nHow many accounts to generate & use? (1-10):",
            parse_mode="Markdown"
        )
        return

    if action == "visitors_autogen_count":
        if not GUEST_GEN_AVAILABLE:
            await update.message.reply_text("❌ Guest Gen module not available!", reply_markup=back_keyboard)
            context.user_data["action"] = None
            return
        try:
            count = int(text)
            if count < 1 or count > 10:
                await update.message.reply_text("❌ Enter 1-10.", reply_markup=back_keyboard)
                return
        except ValueError:
            await update.message.reply_text("❌ Invalid number!", reply_markup=back_keyboard)
            return
        target_uid = context.user_data.get("visitors_target")
        context.user_data["action"] = None
        status_msg = await update.message.reply_text(
            f"👁 *Auto Gen + Visitors*\n━━━━━━━━━━━━━━━━\n"
            f"Target: `{target_uid}`\n"
            f"⏳ Generating {count} accounts...",
            parse_mode="Markdown"
        )
        generated = []
        def gen_and_visit():
            for i in range(count):
                acc = create_account("ME", "M3SBIOS", "M3SBIOS", False)
                if acc:
                    generated.append(acc)
        thread = threading.Thread(target=gen_and_visit)
        thread.start()
        while thread.is_alive():
            await asyncio.sleep(3)
            try:
                await status_msg.edit_text(
                    f"⏳ Generated: {len(generated)}/{count} accounts..."
                )
            except:
                pass
        thread.join()
        success_count = 0
        for acc in generated:
            ok, _ = send_visit_with_account(target_uid, acc.get("uid"), acc.get("password"))
            if ok:
                success_count += 1
            await asyncio.sleep(1)
        await status_msg.edit_text(
            f"👁 *Auto Gen + Visitors Complete!*\n━━━━━━━━━━━━━━━━\n"
            f"Target: `{target_uid}`\n"
            f"📦 Generated: {len(generated)} accounts\n"
            f"✅ Visits sent: {success_count}/{len(generated)}",
            reply_markup=back_keyboard,
            parse_mode="Markdown"
        )
        return

    # --- Guest Gen Flow ---
    if action == "gen_count":
        try:
            count = int(text)
            if count < 1 or count > 50:
                await update.message.reply_text("\u274c Enter a number between 1-50.", reply_markup=back_keyboard)
                return
            context.user_data["gen_count"] = count
            context.user_data["action"] = "gen_name"
            await update.message.reply_text(
                f"\u2705 Count: {count}\n\nNow send the *account name prefix*:\n(e.g. `Player`, `Bot`)",
                parse_mode="Markdown"
            )
        except ValueError:
            await update.message.reply_text("\u274c Invalid number! Send a number (1-50).")
        return

    if action == "gen_name":
        if not text:
            await update.message.reply_text("\u274c Name cannot be empty!")
            return
        context.user_data["gen_name"] = text
        context.user_data["action"] = "gen_pass"
        await update.message.reply_text(
            f"\u2705 Name prefix: {text}\n\nNow send the *password prefix*:\n(e.g. `mypass`, `bot123`)",
            parse_mode="Markdown"
        )
        return

    if action == "gen_pass":
        if not text:
            await update.message.reply_text("\u274c Password prefix cannot be empty!")
            return
        region = context.user_data.get("gen_region", "ME")
        count = context.user_data.get("gen_count", 1)
        name = context.user_data.get("gen_name", "Player")
        pass_prefix = text
        is_ghost = region == "GHOST"
        actual_region = "BR" if is_ghost else region
        mode_text = "\ud83d\udc7b GHOST" if is_ghost else f"\ud83c\udf0d {region}"

        context.user_data["action"] = None
        status_msg = await update.message.reply_text(
            f"\ud83d\ude80 *Starting Guest Gen*\n"
            f"\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n"
            f"Region: {mode_text}\n"
            f"Count: {count}\n"
            f"Name: {name}\n"
            f"Password: {pass_prefix}\n\n"
            f"\u23f3 Generating... 0/{count}",
            parse_mode="Markdown"
        )

        loop = asyncio.get_event_loop()
        results = []

        def gen_worker():
            for i in range(count):
                result = create_account(actual_region, name, pass_prefix, is_ghost)
                if result:
                    results.append(result)

        thread = threading.Thread(target=gen_worker)
        thread.start()

        last_count = 0
        while thread.is_alive():
            await asyncio.sleep(3)
            if len(results) != last_count:
                last_count = len(results)
                try:
                    await status_msg.edit_text(
                        f"\u23f3 Generating... {last_count}/{count}\n"
                        f"Region: {mode_text}"
                    )
                except:
                    pass
        thread.join()

        if results:
            msg = f"\u2705 *Generation Complete!*\n\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\u2501\n\ud83d\udcca Generated: {len(results)}/{count}\n\n"
            for acc in results[:10]:
                msg += (
                    f"\ud83d\udc64 `{acc.get('name', 'N/A')}`\n"
                    f"  UID: `{acc.get('uid', 'N/A')}`\n"
                    f"  ID: `{acc.get('account_id', 'N/A')}`\n"
                    f"  PW: `{acc.get('password', 'N/A')}`\n\n"
                )
            if len(results) > 10:
                msg += f"... and {len(results) - 10} more (saved to files)\n"
            msg += f"\n\ud83d\udcc1 Saved to: `{BASE_FOLDER}`"
        else:
            msg = f"\u274c No accounts generated. API might be down or rate-limited. Try again later."

        await status_msg.edit_text(msg, reply_markup=back_keyboard, parse_mode="Markdown")
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

async def cmd_gen(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not GUEST_GEN_AVAILABLE:
        await update.message.reply_text("❌ Guest Gen module not available!")
        return
    if len(context.args) < 4:
        await update.message.reply_text(
            "Usage: /gen <region> <count> <name> <password_prefix>\n"
            "Example: /gen ME 5 Player mypass\n"
            "Regions: ME, IND, ID, VN, TH, BD, PK, TW, CIS, SAC, GHOST"
        )
        return
    region = context.args[0].upper()
    try:
        count = int(context.args[1])
        if count < 1 or count > 50:
            await update.message.reply_text("❌ Count must be 1-50!")
            return
    except ValueError:
        await update.message.reply_text("❌ Invalid count!")
        return
    name = context.args[2]
    pass_prefix = context.args[3]
    is_ghost = region == "GHOST"
    actual_region = "BR" if is_ghost else region
    mode_text = "👻 GHOST" if is_ghost else f"🌍 {region}"
    status_msg = await update.message.reply_text(
        f"🚀 Generating {count} accounts ({mode_text})...\n⏳ 0/{count}"
    )
    results = []
    def gen_worker():
        for i in range(count):
            result = create_account(actual_region, name, pass_prefix, is_ghost)
            if result:
                results.append(result)
    thread = threading.Thread(target=gen_worker)
    thread.start()
    last_count = 0
    while thread.is_alive():
        await asyncio.sleep(3)
        if len(results) != last_count:
            last_count = len(results)
            try:
                await status_msg.edit_text(f"⏳ Generating... {last_count}/{count} ({mode_text})")
            except:
                pass
    thread.join()
    if results:
        msg = f"✅ Generated {len(results)}/{count} accounts:\n\n"
        for acc in results[:10]:
            msg += f"👤 {acc.get('name','N/A')} | UID: {acc.get('uid','N/A')} | PW: {acc.get('password','N/A')}\n"
        if len(results) > 10:
            msg += f"... +{len(results)-10} more\n"
        msg += f"\n📁 Saved to: {BASE_FOLDER}"
    else:
        msg = "❌ No accounts generated. Try again later."
    await status_msg.edit_text(msg)

async def cmd_masslikes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /masslikes <uid> [count]\nExample: /masslikes 123456789 5")
        return
    uid = context.args[0]
    count = int(context.args[1]) if len(context.args) > 1 else 5
    count = max(1, min(count, 20))
    status_msg = await update.message.reply_text(f"🔥 Sending {count} rounds of likes to {uid}...")
    success = 0
    for i in range(count):
        ok, _ = send_likes_with_account(uid, None, None)
        if ok:
            success += 1
        await asyncio.sleep(1)
    await status_msg.edit_text(f"🔥 Mass Likes Done!\nTarget: {uid}\n✅ {success}/{count} rounds")

async def cmd_visit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Usage: /visit <uid> [count]\nExample: /visit 123456789 5")
        return
    uid = context.args[0]
    count = int(context.args[1]) if len(context.args) > 1 else 5
    count = max(1, min(count, 20))
    status_msg = await update.message.reply_text(f"👁 Sending {count} visits to {uid}...")
    success = 0
    for i in range(count):
        ok, _ = send_visit_with_account(uid, None, None)
        if ok:
            success += 1
        await asyncio.sleep(1)
    await status_msg.edit_text(f"👁 Visitors Done!\nTarget: {uid}\n✅ {success}/{count} visits")

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
        "/masslikes <uid> [count] — Mass likes\n"
        "/visit <uid> [count] — Send visitors\n"
        "/gen <region> <count> <name> <pw> — Generate accounts\n"
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
    app.add_handler(CommandHandler("masslikes", cmd_masslikes))
    app.add_handler(CommandHandler("visit", cmd_visit))
    app.add_handler(CommandHandler("gen", cmd_gen))
    app.add_handler(CommandHandler("check", cmd_check))

    # Text input handler (for button-triggered actions)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))

    print("🤖 Telegram bot started!")
    print("Press Ctrl+C to stop")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
