"""
FF Bot Telegram Controller
Controls all bot accounts from Telegram with inline keyboard.
Supports glory farming, guild operations, squad management.
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
        except Exception:
            pass
    return token


# ─── Keyboards ──────────────────────────────────────────────────────

def main_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔑 Login All", callback_data="login_all"),
         InlineKeyboardButton("🤖 Status", callback_data="status")],
        [InlineKeyboardButton("⚔️ Glory Farm", callback_data="glory_start"),
         InlineKeyboardButton("🛑 Stop Glory", callback_data="glory_stop")],
        [InlineKeyboardButton("🏰 Guild Join", callback_data="guild_join"),
         InlineKeyboardButton("🚪 Guild Leave", callback_data="guild_leave")],
        [InlineKeyboardButton("👥 Squad", callback_data="form_squad"),
         InlineKeyboardButton("🎮 Match", callback_data="start_match")],
        [InlineKeyboardButton("📊 Glory Stats", callback_data="glory_stats"),
         InlineKeyboardButton("📋 Accounts", callback_data="account_info")],
        [InlineKeyboardButton("🔄 Match Cycles", callback_data="match_cycles"),
         InlineKeyboardButton("🔌 Disconnect", callback_data="disconnect_all")],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 Back to Menu", callback_data="back")]
    ])


# ─── Handlers ───────────────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    accounts = manager.load_accounts()
    glory = manager.get_glory_stats()
    text = (
        f"🤖 *FF Multi-Bot Controller*\n"
        f"━━━━━━━━━━━━━━━━━━━━━━\n"
        f"📦 Accounts: {len(accounts)}\n"
        f"🟢 Online: {manager.get_online_count()}\n"
        f"⚔️ Glory: {'Running' if glory['running'] else 'Stopped'}\n"
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
        glory = manager.get_glory_stats()
        text = (
            f"🤖 *FF Multi-Bot Controller*\n"
            f"━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📦 Accounts: {len(accounts)} | 🟢 Online: {manager.get_online_count()}\n"
            f"⚔️ Glory: {'Running' if glory['running'] else 'Stopped'}\n"
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
        text += f"Online: {online}/{len(results)}\n\n"
        for r in results:
            icon = "🟢" if r["status"] == "online" else "🔴"
            text += f"{icon} `{r['name']}` — {r['status']}\n"
        await query.edit_message_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

    # ── Glory Start ──
    elif data == "glory_start":
        if manager.glory_running:
            stats = manager.get_glory_stats()
            await query.edit_message_text(
                f"⚔️ *Glory Already Running!*\n━━━━━━━━━━━━━━━━\n"
                f"Cycles: {stats['cycles']}\n"
                f"Guild: {stats['guild_id']}\n"
                f"Est. Glory: ~{stats['estimated_glory']:,}\n\n"
                f"Use 🛑 Stop Glory to stop first.",
                reply_markup=back_keyboard(),
                parse_mode="Markdown"
            )
            return
        context.user_data["action"] = "glory_guild_input"
        await query.edit_message_text(
            "⚔️ *Glory Farming*\n━━━━━━━━━━━━━━━━\n"
            "Enter the Guild ID to farm glory for:\n\n"
            "_Same method as ffglory.in — bots join guild, form squads, "
            "spam FS to earn dog tags + glory_",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )

    # ── Glory Stop ──
    elif data == "glory_stop":
        if not manager.glory_running:
            await query.edit_message_text(
                "🛑 Glory farming is not running.",
                reply_markup=back_keyboard()
            )
            return
        stats = manager.stop_glory_farming()
        await query.edit_message_text(
            f"🛑 *Glory Farming Stopped*\n━━━━━━━━━━━━━━━━\n"
            f"Cycles completed: {stats['cycles']}\n"
            f"Est. Glory: ~{stats['estimated_glory']:,}\n"
            f"Guild: {stats['guild_id']}",
            reply_markup=back_keyboard(),
            parse_mode="Markdown"
        )

    # ── Glory Stats ──
    elif data == "glory_stats":
        stats = manager.get_glory_stats()
        status = "Running" if stats["running"] else "Stopped"
        text = (
            f"📊 *Glory Stats*\n━━━━━━━━━━━━━━━━\n"
            f"Status: {status}\n"
            f"Guild: {stats.get('guild_id', 'N/A')}\n"
            f"Cycles: {stats['cycles']}\n"
            f"Squads: {stats.get('squads_active', 0)}\n"
            f"FS Sent: {stats.get('total_fs_sent', 0):,}\n"
            f"Est. Glory: ~{stats.get('estimated_glory', 0):,}\n"
            f"Bots: {stats.get('bots_online', 0)}/{stats.get('bots_total', 0)}\n"
        )
        if stats.get("started_at"):
            text += f"Started: {stats['started_at'][:19]}\n"
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
                "Need at least 2 online bots!\nUse 🔑 Login All first.",
                reply_markup=back_keyboard()
            )
            return
        await query.edit_message_text("👥 *Forming squad(s)...*", parse_mode="Markdown")
        squads = await manager.form_multi_squads()
        if isinstance(squads, list) and squads:
            text = f"👥 *Squads Formed!*\n━━━━━━━━━━━━━━━━\n"
            for i, sq in enumerate(squads):
                text += f"\nSquad {i+1}:\n"
                text += f"  👑 Leader: {sq['leader'].name}\n"
                text += f"  🔑 Code: `{sq['code']}`\n"
                text += f"  👥 {', '.join(sq['bot_names'])}\n"
        else:
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
                text = f"Squad failed: {info}"
        await query.edit_message_text(text, reply_markup=back_keyboard(), parse_mode="Markdown")

    # ── Start Match ──
    elif data == "start_match":
        online_bots = [b for b in manager.bots if b.connected]
        if not online_bots:
            await query.edit_message_text("No bots online!", reply_markup=back_keyboard())
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

    # ── Account Info ──
    elif data == "account_info":
        accounts = manager.load_accounts()
        text = f"📋 *Accounts*\n━━━━━━━━━━━━━━━━\n"
        text += f"Total: {len(accounts)}\n\n"
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

    # ── Glory Guild ID input ──
    if action == "glory_guild_input":
        context.user_data["action"] = None
        guild_id = text
        status_msg = await update.message.reply_text(
            f"⚔️ *Starting Glory Farming*\n━━━━━━━━━━━━━━━━\n"
            f"Guild: `{guild_id}`\n\n"
            f"Step 1: Joining guild...\n"
            f"Step 2: Logging in bots...\n"
            f"Step 3: Forming squads...\n"
            f"Step 4: FS spam + glory loop...\n\n"
            f"⏳ Starting...",
            parse_mode="Markdown"
        )

        chat_id = update.effective_chat.id
        app = context.application

        async def glory_callback(msg):
            try:
                await app.bot.send_message(chat_id=chat_id, text=f"⚔️ {msg}")
            except Exception:
                pass

        # Run glory farming in background
        async def run_glory():
            result = await manager.start_glory_farming(
                guild_id=guild_id,
                cycles=0,  # Infinite
                fs_duration=10,
                match_wait=120,
                cooldown=10,
                callback=glory_callback
            )
            try:
                await app.bot.send_message(
                    chat_id=chat_id,
                    text=f"⚔️ *Glory Farming Ended*\n"
                         f"Cycles: {result.get('cycles', 0)}\n"
                         f"Est. Glory: ~{result.get('estimated_glory', 0):,}",
                    parse_mode="Markdown"
                )
            except Exception:
                pass

        manager.glory_task = asyncio.create_task(run_glory())
        return

    # ── Guild Join input ──
    elif action == "guild_join_input":
        context.user_data["action"] = None
        status_msg = await update.message.reply_text(
            f"🏰 Joining guild `{text}` with all accounts...\n⏳ Please wait...",
            parse_mode="Markdown"
        )
        results = await manager.guild_join_all_api(text)
        success = sum(1 for r in results if r["success"])
        reply = f"🏰 *Guild Join Results*\n━━━━━━━━━━━━━━━━\n"
        reply += f"Success: {success}/{len(results)}\n\n"
        for r in results:
            icon = "🟢" if r["success"] else "🔴"
            reply += f"{icon} `{r['name']}`: {r['msg'][:40]}\n"
        await status_msg.edit_text(reply, reply_markup=back_keyboard(), parse_mode="Markdown")

    # ── Guild Leave input ──
    elif action == "guild_leave_input":
        context.user_data["action"] = None
        status_msg = await update.message.reply_text(
            f"🚪 Leaving guild `{text}` with all bots...",
            parse_mode="Markdown"
        )
        results = await manager.guild_leave_all(text)
        success = sum(1 for r in results if r["success"])
        reply = f"🚪 *Guild Leave Results*\n━━━━━━━━━━━━━━━━\n"
        reply += f"Success: {success}/{len(results)}\n\n"
        for r in results:
            icon = "🟢" if r["success"] else "🔴"
            reply += f"{icon} `{r['name']}`: {r['message'][:40]}\n"
        await status_msg.edit_text(reply, reply_markup=back_keyboard(), parse_mode="Markdown")

    # ── Match Cycles input ──
    elif action == "match_cycles_input":
        context.user_data["action"] = None
        try:
            cycles = int(text)
            cycles = max(1, min(100, cycles))
        except ValueError:
            await update.message.reply_text("Enter a number (1-100)!", reply_markup=back_keyboard())
            return

        status_msg = await update.message.reply_text(
            f"🔄 Starting {cycles} match cycle(s)...\n⏳ This will take a while.",
            parse_mode="Markdown"
        )
        results = await manager.start_match_cycle(cycles=cycles)
        if isinstance(results, str):
            await status_msg.edit_text(f"🔄 {results}", reply_markup=back_keyboard())
        else:
            reply = f"🔄 *Match Cycles Complete*\n━━━━━━━━━━━━━━━━\n"
            for r in results:
                reply += f"Cycle {r['cycle']}: {r['status']}\n"
            await status_msg.edit_text(reply, reply_markup=back_keyboard(), parse_mode="Markdown")


# ─── Main ───────────────────────────────────────────────────────────

def main():
    token = get_token()
    if not token:
        print("Set TELEGRAM_BOT_TOKEN env var or add to config.json")
        sys.exit(1)

    app = Application.builder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    logger.info("Telegram controller starting...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
