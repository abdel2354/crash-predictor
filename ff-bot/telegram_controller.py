"""
FF Bot Telegram Controller
Controls all bot accounts from Telegram with inline keyboard.
Uses MultiAccountManager for orchestration.
"""

import os
import sys
import json
import asyncio
import logging
from datetime import datetime

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)

from multi_account_manager import MultiAccountManager

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

manager = MultiAccountManager()

# ─── Config ─────────────────────────────────────────────────────────

def get_token():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", "")
    if not token:
        try:
            with open("config.json", "r") as f:
                cfg = json.load(f)
            token = cfg.get("telegram_token", "")
        except:
            pass
    return token


# ─── Keyboards ──────────────────────────────────────────────────────

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🤖 Bot Status", callback_data="status"),
         InlineKeyboardButton("🔑 Login All", callback_data="login_all")],
        [InlineKeyboardButton("🏰 Guild Join All", callback_data="guild_join"),
         InlineKeyboardButton("🚪 Guild Leave All", callback_data="guild_leave")],
        [InlineKeyboardButton("👥 Form Squad", callback_data="form_squad"),
         InlineKeyboardButton("🎮 Start Match", callback_data="start_match")],
        [InlineKeyboardButton("🔄 Match Cycles", callback_data="match_cycles"),
         InlineKeyboardButton("❤️ Mass Likes", callback_data="mass_likes")],
        [InlineKeyboardButton("📊 Account Info", callback_data="account_info"),
         InlineKeyboardButton("🔌 Disconnect All", callback_data="disconnect_all")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back")]
    ])


# ─── Handlers ───────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accounts = manager.load_accounts()
    text = (
        f"🤖 *FF Multi-Bot Controller*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Accounts loaded: {len(accounts)}\n"
        f"🟢 Bots online: {manager.get_online_count()}\n"
        f"🌍 Regions: ME\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"Choose an action:"
    )
    await update.message.reply_text(text, reply_markup=main_keyboard(), parse_mode="Markdown")


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data == "back":
        accounts = manager.load_accounts()
        text = (
            f"🤖 *FF Multi-Bot Controller*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 Accounts: {len(accounts)} | 🟢 Online: {manager.get_online_count()}\n"
            f"━━━━━━━━━━━━━━━━━━━━━━"
        )
        await query.edit_message_text(text, reply_markup=main_keyboard(), parse_mode="Markdown")
        return

    # ── Status ──
    if data == "status":
        statuses = manager.get_all_status()
        if not statuses:
            accounts = manager.load_accounts()
            text = f"📊 *Bot Status*\n━━━━━━━━━━━━━━━━\n"
            text += f"No bots online.\n{len(accounts)} accounts available.\n"
            text += f"\nUse 🔑 Login All to connect bots."
        else:
            text = f"📊 *Bot Status* ({manager.get_online_count()}/{len(statuses)} online)\n━━━━━━━━━━━━━━━━\n"
            for s in statuses:
                icon = "🟢" if s["connected"] else "🔴"
                text += f"{icon} `{s['name']}` | {s['status']}\n"
        await query.edit_message_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

    # ── Login All ──
    elif data == "login_all":
        await query.edit_message_text(
            "🔑 *Logging in all accounts...*\n⏳ This may take a few minutes.",
            parse_mode="Markdown"
        )
        results = await manager.login_all(delay_between=8)
        online = sum(1 for r in results if r["status"] == "online")
        text = f"🔑 *Login Results*\n━━━━━━━━━━━━━━━━\n"
        text += f"✅ Online: {online}/{len(results)}\n\n"
        for r in results:
            icon = "✅" if r["status"] == "online" else "❌"
            text += f"{icon} `{r['name']}` — {r['status']}\n"
        await query.edit_message_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

    # ── Guild Join ──
    elif data == "guild_join":
        context.user_data["action"] = "guild_join_input"
        await query.edit_message_text(
            "🏰 *Guild Mass Join*\n━━━━━━━━━━━━━━━━\n"
            "Enter the Guild ID:",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )

    # ── Guild Leave ──
    elif data == "guild_leave":
        context.user_data["action"] = "guild_leave_input"
        await query.edit_message_text(
            "🚪 *Guild Mass Leave*\n━━━━━━━━━━━━━━━━\n"
            "Enter the Guild ID:",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )

    # ── Form Squad ──
    elif data == "form_squad":
        if manager.get_online_count() < 2:
            await query.edit_message_text(
                "❌ Need at least 2 online bots!\nUse 🔑 Login All first.",
                reply_markup=back_keyboard()
            )
            return
        await query.edit_message_text("👥 *Forming squad...*", parse_mode="Markdown")
        ok, info = await manager.form_squad()
        if ok:
            text = (
                f"👥 *Squad Formed!*\n━━━━━━━━━━━━━━━━\n"
                f"🔑 Code: `{info['code']}`\n"
                f"👑 Leader: {info['leader']}\n"
                f"👥 Members: {', '.join(info['members'])}\n"
                f"📊 Total: {info['total']}/4"
            )
        else:
            text = f"❌ Squad failed: {info}"
        await query.edit_message_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

    # ── Start Match ──
    elif data == "start_match":
        online_bots = [b for b in manager.bots if b.connected]
        if not online_bots:
            await query.edit_message_text("❌ No bots online!", reply_markup=back_keyboard())
            return
        await query.edit_message_text("🎮 *Starting match...*", parse_mode="Markdown")
        leader = online_bots[0]
        await leader.start_match()
        await query.edit_message_text(
            f"🎮 *Match Started!*\n━━━━━━━━━━━━━━━━\n"
            f"👑 Leader: {leader.name}\n"
            f"📊 Bots in squad: {sum(1 for b in online_bots if b.in_squad)}",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )

    # ── Match Cycles ──
    elif data == "match_cycles":
        context.user_data["action"] = "match_cycles_input"
        await query.edit_message_text(
            "🔄 *Match Cycles (Level Up + Glory)*\n━━━━━━━━━━━━━━━━\n"
            "How many cycles? (1-100):",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )

    # ── Mass Likes ──
    elif data == "mass_likes":
        context.user_data["action"] = "mass_likes_input"
        await query.edit_message_text(
            "❤️ *Mass Likes*\n━━━━━━━━━━━━━━━━\n"
            "Enter target UID:",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )

    # ── Account Info ──
    elif data == "account_info":
        accounts = manager.load_accounts()
        text = f"📊 *Account Summary*\n━━━━━━━━━━━━━━━━\n"
        text += f"📦 Total: {len(accounts)}\n\n"
        for i, acc in enumerate(accounts[:10]):
            text += f"{i+1}. `{acc.get('name', 'N/A')}` | UID: `{acc['uid']}`\n"
        if len(accounts) > 10:
            text += f"\n... and {len(accounts) - 10} more"
        await query.edit_message_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

    # ── Disconnect All ──
    elif data == "disconnect_all":
        await manager.disconnect_all()
        await query.edit_message_text(
            "🔌 *All bots disconnected.*",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for various actions."""
    action = context.user_data.get("action")
    text = update.message.text.strip()

    if action == "guild_join_input":
        context.user_data["action"] = None
        if not text.isdigit():
            await update.message.reply_text("❌ Guild ID must be a number!", reply_markup=back_keyboard())
            return
        status_msg = await update.message.reply_text(
            f"🏰 Joining guild `{text}` with all accounts...\n⏳ Please wait...",
            parse_mode="Markdown"
        )
        results = await manager.guild_join_all_api(text)
        success = sum(1 for r in results if r["success"])
        reply = f"🏰 *Guild Join Results*\n━━━━━━━━━━━━━━━━\n"
        reply += f"✅ Success: {success}/{len(results)}\n\n"
        for r in results:
            icon = "✅" if r["success"] else "❌"
            reply += f"{icon} `{r['name']}`: {r['msg'][:40]}\n"
        await status_msg.edit_text(reply, reply_markup=back_keyboard(), parse_mode="Markdown")

    elif action == "guild_leave_input":
        context.user_data["action"] = None
        if not text.isdigit():
            await update.message.reply_text("❌ Guild ID must be a number!", reply_markup=back_keyboard())
            return
        status_msg = await update.message.reply_text(
            f"🚪 Leaving guild `{text}` with all bots...",
            parse_mode="Markdown"
        )
        results = await manager.guild_leave_all(text)
        success = sum(1 for r in results if r["success"])
        reply = f"🚪 *Guild Leave: {success}/{len(results)}*"
        await status_msg.edit_text(reply, reply_markup=back_keyboard(), parse_mode="Markdown")

    elif action == "match_cycles_input":
        context.user_data["action"] = None
        try:
            cycles = min(max(int(text), 1), 100)
        except:
            await update.message.reply_text("❌ Invalid number!", reply_markup=back_keyboard())
            return
        if manager.get_online_count() < 2:
            await update.message.reply_text(
                "❌ Need at least 2 online bots! Use 🔑 Login All first.",
                reply_markup=back_keyboard()
            )
            return
        status_msg = await update.message.reply_text(
            f"🔄 Starting {cycles} match cycles...\n"
            f"🤖 {manager.get_online_count()} bots online\n⏳ This will take a while...",
        )
        results = await manager.start_match_cycle(cycles=cycles)
        reply = f"🔄 *Match Cycles Complete*\n━━━━━━━━━━━━━━━━\n"
        reply += f"Cycles: {len(results)}/{cycles}\n"
        for r in results:
            reply += f"  ✅ Cycle {r['cycle']}: {r['status']}\n"
        await status_msg.edit_text(reply, reply_markup=back_keyboard(), parse_mode="Markdown")

    elif action == "mass_likes_input":
        context.user_data["action"] = None
        if not text.isdigit():
            await update.message.reply_text("❌ UID must be a number!", reply_markup=back_keyboard())
            return
        status_msg = await update.message.reply_text(
            f"❤️ Sending mass likes to `{text}`...",
            parse_mode="Markdown"
        )
        result = await manager.mass_likes(text)
        await status_msg.edit_text(
            f"❤️ *Mass Likes Done*\n━━━━━━━━━━━━━━━━\n"
            f"Target: `{result['target']}`\n"
            f"Sent: {result['sent']} | Success: {result['success']}",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )


# ─── Main ───────────────────────────────────────────────────────────

def main():
    token = get_token()
    if not token:
        print("❌ No Telegram bot token!")
        print("Set TELEGRAM_BOT_TOKEN env var or config.json")
        return

    app = Application.builder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("🤖 FF Multi-Bot Telegram Controller started!")
    print(f"📦 Accounts: {len(manager.load_accounts())}")
    app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
