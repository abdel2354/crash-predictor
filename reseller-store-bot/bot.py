# M3SB IOS

import logging
from datetime import datetime, timedelta, timezone

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

import database as db
from config import ADMIN_IDS, BOT_TOKEN

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# Conversation states
(
    LOGIN_WAITING,
    ADD_ACCOUNT_LOGIN,
    ADD_ACCOUNT_PASSWORD,
    ADD_CATEGORY_NAME,
    ADD_POSITION_NAME,
    ADD_KEY_TYPE_NAME,
    ADD_KEY_TYPE_PRICE,
    ADD_KEYS_VALUE,
    TOPUP_AMOUNT,
    BROADCAST_CONTENT,
    EDIT_PRICE_VALUE,
    INIT_PRICE_VALUE,
    MANAGE_PRICE_VALUE,
) = range(13)


# ─────────────────── Helpers ───────────────────

def is_logged_in(context: ContextTypes.DEFAULT_TYPE) -> bool:
    return context.user_data.get("account_id") is not None


def is_admin(context: ContextTypes.DEFAULT_TYPE) -> bool:
    session = context.user_data.get("is_admin", 0)
    return session == 1


async def require_admin(query, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not is_logged_in(context) or not is_admin(context):
        await query.edit_message_text(access_denied_text(), parse_mode="HTML")
        return False
    return True


def admin_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["\U0001f6cd Buy keys"],
            ["\U0001f3db Account", "\U0001f680 Log out"],
            ["\U0001f527 Manage", "\U0001f4e6 Stock"],
            ["\U0001f4ca Statistics"],
        ],
        resize_keyboard=True,
    )


def user_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [
            ["\U0001f6cd Buy keys"],
            ["\U0001f3db Account", "\U0001f680 Log out"],
        ],
        resize_keyboard=True,
    )


def login_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        [["\U0001f512 Login"]],
        resize_keyboard=True,
    )


def get_keyboard(context: ContextTypes.DEFAULT_TYPE) -> ReplyKeyboardMarkup:
    if is_admin(context):
        return admin_keyboard()
    return user_keyboard()


def access_denied_text() -> str:
    return (
        "\u274c <b>Access Denied, please</b> /login\n"
        "You don't have permission to use this feature."
        "For access or support, please contact admin \u2192"
    )


# ─────────────────── /start ───────────────────

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if not is_logged_in(context):
        await update.message.reply_text(
            access_denied_text(),
            parse_mode="HTML",
            reply_markup=login_keyboard(),
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "\U0001f44b <b>Hello, welcome to panel!</b>",
        parse_mode="HTML",
        reply_markup=get_keyboard(context),
    )
    return ConversationHandler.END


# ─────────────────── /login ───────────────────

async def login_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if is_logged_in(context):
        await update.message.reply_text(
            "\u2705 You are already logged in!",
            reply_markup=get_keyboard(context),
        )
        return ConversationHandler.END

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("\u274c Cancel", callback_data="cancel_login")]]
    )
    await update.message.reply_text(
        "\U0001f512 <b>Enter the credentials provided by the administrator "
        "in the following format:</b>\n<code>LOGIN\nPASSWORD</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return LOGIN_WAITING


async def login_credentials(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()
    lines = text.split("\n")

    if len(lines) != 2:
        await update.message.reply_text(
            "\u274c <b>Incorrect login or password! Please try again.</b>",
            parse_mode="HTML",
        )
        return LOGIN_WAITING

    login, password = lines[0].strip(), lines[1].strip()
    account = db.get_account_by_login(login)

    if not account or account["password"] != password:
        await update.message.reply_text(
            "\u274c <b>Incorrect login or password! Please try again.</b>",
            parse_mode="HTML",
        )
        return LOGIN_WAITING

    context.user_data["account_id"] = account["id"]
    context.user_data["login"] = account["login"]
    context.user_data["is_admin"] = account["is_admin"]

    db.login_session(update.effective_user.id, account["id"])

    await update.message.reply_text(
        "\U0001f513 <b>You have been successfully authorized!</b>",
        parse_mode="HTML",
        reply_markup=get_keyboard(context),
    )
    return ConversationHandler.END


async def cancel_login_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("\U0001f4cd Canceled")
    return ConversationHandler.END


# ─────────────────── /logout ───────────────────

async def logout_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_logged_in(context):
        await update.message.reply_text(access_denied_text(), parse_mode="HTML")
        return

    db.logout_session(update.effective_user.id)
    context.user_data.clear()

    await update.message.reply_text(
        "\U0001f513 <b>You have successfully logged out!</b>\n"
        "To log in again, use the /login command",
        parse_mode="HTML",
        reply_markup=login_keyboard(),
    )


# ─────────────────── /reset ───────────────────

async def reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "\u2757 This feature is disabled.",
    )


# ─────────────────── Stock ───────────────────

async def stock_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_logged_in(context) or not is_admin(context):
        await update.message.reply_text(access_denied_text(), parse_mode="HTML")
        return

    summary = db.get_stock_summary()

    if not summary:
        await update.message.reply_text(
            "\U0001f4e6 <b>Stock is empty.</b>",
            parse_mode="HTML",
        )
        return

    text = "\U0001f4e6 <b>Stock:</b>\n\n"
    current_cat = None
    for item in summary:
        if item["category_name"] != current_cat:
            current_cat = item["category_name"]
            text += f"\U0001f4c1 <b>{current_cat}</b>\n"
        text += f"  \u2022 {item['key_type_name']}: <code>{item['available']}</code> pcs\n"

    await update.message.reply_text(text, parse_mode="HTML")


# ─────────────────── Statistics (keyboard) ───────────────────

async def statistics_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_logged_in(context) or not is_admin(context):
        await update.message.reply_text(access_denied_text(), parse_mode="HTML")
        return

    total = db.get_total_sales()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4c5 Daily", callback_data="stats_daily"),
            InlineKeyboardButton("\U0001f4c6 Week", callback_data="stats_week"),
            InlineKeyboardButton("\U0001f5d3 Month", callback_data="stats_month"),
        ],
        [
            InlineKeyboardButton("TOP", callback_data="stats_top"),
            InlineKeyboardButton("\U0001f4b0 Net Profit", callback_data="stats_net_profit"),
        ],
    ])

    await update.message.reply_text(
        f"\U0001f4ca <b>All time statistics:</b>\n"
        f"\U0001f4b0 Total sum of sells: <code>{total:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ─────────────────── Login (keyboard button) ───────────────────

async def login_button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    if is_logged_in(context):
        await update.message.reply_text(
            "\u2705 You are already logged in!",
            reply_markup=get_keyboard(context),
        )
        return ConversationHandler.END

    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("\u274c Cancel", callback_data="cancel_login")]]
    )
    await update.message.reply_text(
        "\U0001f512 <b>Enter the credentials provided by the administrator "
        "in the following format:</b>\n<code>LOGIN\nPASSWORD</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return LOGIN_WAITING


# ─────────────────── Account ───────────────────

async def account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_logged_in(context):
        await update.message.reply_text(access_denied_text(), parse_mode="HTML")
        return

    account = db.get_account_by_id(context.user_data["account_id"])
    if not account:
        await update.message.reply_text("\u274c Account not found.")
        return

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4dc Purchase History", callback_data="my_purchase_history"),
            InlineKeyboardButton("\U0001f4b3 Top-up History", callback_data="my_topup_history"),
        ]
    ])

    await update.message.reply_text(
        f"\U0001f464 <b>Your account:</b>\n"
        f"- Login: <code>{account['login']}</code>\n"
        f"- Balance: <code>{account['balance']:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def my_purchase_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_logged_in(context):
        return

    purchases = db.get_purchases_by_account(context.user_data["account_id"])
    if not purchases:
        await query.edit_message_text("\u2757 No purchases yet.")
        return

    text = "\U0001f4dc <b>Purchase History:</b>\n\n"
    for p in purchases[:20]:
        text += (
            f"- <b>{p['key_type_name']}</b> ({p['category_name']})\n"
            f"  Key: <code>{p['key_value']}</code>\n"
            f"  Price: <code>{p['price']:.2f}$</code>\n"
            f"  Date: {p['purchased_at']}\n\n"
        )
    await query.edit_message_text(text, parse_mode="HTML")


async def my_topup_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_logged_in(context):
        return

    topups = db.get_topups_by_account(context.user_data["account_id"])
    if not topups:
        await query.edit_message_text("\u2757 No top-ups yet.")
        return

    text = "\U0001f4b3 <b>Top-up History:</b>\n\n"
    for t in topups[:20]:
        text += (
            f"- Amount: <code>{t['amount']:.2f}$</code>\n"
            f"  By: {t['admin_login']}\n"
            f"  Date: {t['topped_up_at']}\n\n"
        )
    await query.edit_message_text(text, parse_mode="HTML")


# ─────────────────── Manage (Admin Panel) ───────────────────

async def manage_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_logged_in(context) or not is_admin(context):
        await update.message.reply_text(access_denied_text(), parse_mode="HTML")
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f512 Manage accounts", callback_data="manage_accounts")],
        [InlineKeyboardButton("\U0001f50e Look at purchases", callback_data="look_purchases")],
        [InlineKeyboardButton("\U0001f4e2 Broadcast", callback_data="broadcast_start")],
        [InlineKeyboardButton("\U0001f4ca Statistics", callback_data="statistics")],
    ])

    await update.message.reply_text(
        "\U0001f527 <b>Admin Panel</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ─────────────────── Manage Accounts ───────────────────

async def manage_accounts_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    accounts = db.get_all_accounts()
    buttons = [[InlineKeyboardButton("\u2795 Add account", callback_data="add_account")]]

    row = []
    for acc in accounts:
        btn_text = f"{acc['login']} ({acc['balance']:.2f}$)"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"view_account_{acc['id']}"))
        if len(row) == 2:
            buttons.append(row)
            row = []
    if row:
        buttons.append(row)

    buttons.append([InlineKeyboardButton("\u2b05 Go back", callback_data="go_back_manage")])

    await query.edit_message_text(
        "\U0001f464 <b>Choose account to manage:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def go_back_manage_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f512 Manage accounts", callback_data="manage_accounts")],
        [InlineKeyboardButton("\U0001f50e Look at purchases", callback_data="look_purchases")],
        [InlineKeyboardButton("\U0001f4e2 Broadcast", callback_data="broadcast_start")],
        [InlineKeyboardButton("\U0001f4ca Statistics", callback_data="statistics")],
    ])

    await query.edit_message_text(
        "\U0001f527 <b>Admin Panel</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def view_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    account_id = int(query.data.split("_")[-1])
    account = db.get_account_by_id(account_id)
    if not account:
        await query.edit_message_text("\u274c Account not found.")
        return

    context.user_data["managing_account_id"] = account_id

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2795 Add balance", callback_data=f"add_bal_{account_id}"),
            InlineKeyboardButton("\u274c Reset balance", callback_data=f"reset_bal_{account_id}"),
        ],
        [InlineKeyboardButton("\U0001f4e6 View purchases", callback_data=f"view_purchases_{account_id}")],
        [InlineKeyboardButton("\U0001f5d1 Delete account", callback_data=f"delete_acc_{account_id}")],
        [InlineKeyboardButton("\u2b05 Go back", callback_data="manage_accounts")],
    ])

    await query.edit_message_text(
        f"\U0001f464 <b>Info about account:</b>\n"
        f"- Login: <code>{account['login']}</code>\n"
        f"- Password: <code>{account['password']}</code>\n"
        f"- Balance: <code>{account['balance']:.2f}$</code>\n"
        f"- Created: <code>{account['created_at']}</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def reset_bal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    account_id = int(query.data.split("_")[-1])
    db.reset_balance(account_id)

    account = db.get_account_by_id(account_id)
    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2795 Add balance", callback_data=f"add_bal_{account_id}"),
            InlineKeyboardButton("\u274c Reset balance", callback_data=f"reset_bal_{account_id}"),
        ],
        [InlineKeyboardButton("\U0001f4e6 View purchases", callback_data=f"view_purchases_{account_id}")],
        [InlineKeyboardButton("\U0001f5d1 Delete account", callback_data=f"delete_acc_{account_id}")],
        [InlineKeyboardButton("\u2b05 Go back", callback_data="manage_accounts")],
    ])

    await query.edit_message_text(
        f"\u2705 Balance reset!\n\n"
        f"\U0001f464 <b>Info about account:</b>\n"
        f"- Login: <code>{account['login']}</code>\n"
        f"- Password: <code>{account['password']}</code>\n"
        f"- Balance: <code>{account['balance']:.2f}$</code>\n"
        f"- Created: <code>{account['created_at']}</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def view_purchases_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    account_id = int(query.data.split("_")[-1])
    purchases = db.get_purchases_by_account(account_id)

    if not purchases:
        await query.edit_message_text(
            "\u2757 No purchases yet.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2b05 Go back", callback_data=f"view_account_{account_id}")]
            ]),
        )
        return

    text = "\U0001f4e6 <b>Purchases:</b>\n\n"
    for p in purchases[:20]:
        text += (
            f"- <b>{p['key_type_name']}</b> ({p['category_name']})\n"
            f"  Key: <code>{p['key_value']}</code>\n"
            f"  Price: <code>{p['price']:.2f}$</code>\n"
            f"  Date: {p['purchased_at']}\n\n"
        )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2b05 Go back", callback_data=f"view_account_{account_id}")]
        ]),
    )


async def delete_acc_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    account_id = int(query.data.split("_")[-1])
    account = db.get_account_by_id(account_id)
    login = account["login"] if account else "Unknown"
    db.delete_account(account_id)

    await query.edit_message_text(
        f"\U0001f5d1 Account <code>{login}</code> deleted!",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2b05 Back to accounts", callback_data="manage_accounts")]
        ]),
    )


# ─────────────────── Add Account (Conversation) ───────────────────

async def add_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return ConversationHandler.END

    await query.edit_message_text(
        "\U0001f512 <b>Type login for new account:</b>",
        parse_mode="HTML",
    )
    return ADD_ACCOUNT_LOGIN


async def add_account_login_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    login = update.message.text.strip()
    existing = db.get_account_by_login(login)
    if existing:
        await update.message.reply_text(
            "\u274c <b>Account with this login already exists!</b>",
            parse_mode="HTML",
        )
        return ADD_ACCOUNT_LOGIN

    context.user_data["new_account_login"] = login
    await update.message.reply_text(
        "\U0001f512 <b>Type password for account:</b>",
        parse_mode="HTML",
    )
    return ADD_ACCOUNT_PASSWORD


async def add_account_password_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text.strip()

    if len(password) < 8 or len(password) > 14:
        await update.message.reply_text(
            "\u274c <b>The password must be between 8 and 14 characters long! "
            "Please try again.</b>",
            parse_mode="HTML",
        )
        return ADD_ACCOUNT_PASSWORD

    login = context.user_data.get("new_account_login")
    account = db.create_account(login, password)

    if not account:
        await update.message.reply_text("\u274c Failed to create account.")
        return ConversationHandler.END

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\u2709 Send credentials", callback_data=f"send_creds_{account['id']}")],
        [InlineKeyboardButton("\u2b05 Back to accounts", callback_data="manage_accounts")],
    ])

    await update.message.reply_text(
        f"\u2705 <b>Account</b> <code>{login}:{password}</code> <b>added!</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    context.user_data.pop("new_account_login", None)
    return ConversationHandler.END


async def send_creds_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    account_id = int(query.data.split("_")[-1])
    account = db.get_account_by_id(account_id)
    if not account:
        await query.edit_message_text("\u274c Account not found.")
        return

    await query.edit_message_text(
        f"\U0001f4e9 <b>Credentials:</b>\n"
        f"Login: <code>{account['login']}</code>\n"
        f"Password: <code>{account['password']}</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2b05 Back to accounts", callback_data="manage_accounts")]
        ]),
    )


# ─────────────────── Add Balance (Conversation) ───────────────────

async def add_bal_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return ConversationHandler.END

    account_id = int(query.data.split("_")[-1])
    context.user_data["topup_account_id"] = account_id

    await query.edit_message_text(
        "\u270f <b>Type sum to top up:</b>",
        parse_mode="HTML",
    )
    return TOPUP_AMOUNT


async def topup_amount_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        amount = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("\u274c Please enter a valid number.")
        return TOPUP_AMOUNT

    if amount <= 0:
        await update.message.reply_text("\u274c Amount must be positive.")
        return TOPUP_AMOUNT

    account_id = context.user_data.get("topup_account_id")
    admin_login = context.user_data.get("login", "admin")

    new_balance = db.add_balance(account_id, amount)
    db.record_topup(account_id, amount, admin_login)

    account = db.get_account_by_id(account_id)

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2795 Add balance", callback_data=f"add_bal_{account_id}"),
            InlineKeyboardButton("\u274c Reset balance", callback_data=f"reset_bal_{account_id}"),
        ],
        [InlineKeyboardButton("\U0001f4e6 View purchases", callback_data=f"view_purchases_{account_id}")],
        [InlineKeyboardButton("\U0001f5d1 Delete account", callback_data=f"delete_acc_{account_id}")],
        [InlineKeyboardButton("\u2b05 Go back", callback_data="manage_accounts")],
    ])

    await update.message.reply_text(
        f"\u2705 Topped up <code>{amount:.2f}$</code>!\n\n"
        f"\U0001f464 <b>Info about account:</b>\n"
        f"- Login: <code>{account['login']}</code>\n"
        f"- Password: <code>{account['password']}</code>\n"
        f"- Balance: <code>{account['balance']:.2f}$</code>\n"
        f"- Created: <code>{account['created_at']}</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    context.user_data.pop("topup_account_id", None)
    return ConversationHandler.END


# ─────────────────── Look at Purchases ───────────────────

async def look_purchases_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    purchases = db.get_all_purchases()
    if not purchases:
        await query.edit_message_text(
            "\u2757 No purchases yet.",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2b05 Go back", callback_data="go_back_manage")]
            ]),
        )
        return

    text = "\U0001f50e <b>All Purchases:</b>\n\n"
    for p in purchases[:20]:
        text += (
            f"- <b>{p.get('login', '?')}</b>: {p['key_type_name']} ({p['category_name']})\n"
            f"  Price: <code>{p['price']:.2f}$</code> | Date: {p['purchased_at']}\n\n"
        )

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2b05 Go back", callback_data="go_back_manage")]
        ]),
    )


# ─────────────────── Buy Keys ───────────────────

async def buy_keys_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_logged_in(context):
        await update.message.reply_text(access_denied_text(), parse_mode="HTML")
        return

    categories = db.get_all_categories()

    if not categories and not is_admin(context):
        await update.message.reply_text("\u2757 No categories available.")
        return

    buttons = []
    if is_admin(context):
        buttons.append([InlineKeyboardButton("\u2795 Add category", callback_data="add_category")])

    for cat in categories:
        buttons.append([InlineKeyboardButton(cat["name"], callback_data=f"cat_{cat['id']}")])

    await update.message.reply_text(
        "\U0001f4cb <b>Choose a category:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    cat_id = int(query.data.split("_")[-1])
    await category_callback_like(query, context, cat_id)


async def go_back_categories_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    categories = db.get_all_categories()
    buttons = []

    if is_admin(context):
        buttons.append([InlineKeyboardButton("\u2795 Add category", callback_data="add_category")])

    for cat in categories:
        buttons.append([InlineKeyboardButton(cat["name"], callback_data=f"cat_{cat['id']}")])

    await query.edit_message_text(
        "\U0001f4cb <b>Choose a category:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def position_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    pos_id = int(query.data.split("_")[-1])
    context.user_data["current_position_id"] = pos_id
    await show_position_menu(query, context, pos_id)


async def show_position_menu(query, context: ContextTypes.DEFAULT_TYPE, pos_id: int) -> None:
    pos = db.get_position_by_id(pos_id)
    if not pos:
        await query.edit_message_text("\u274c Position not found.")
        return

    context.user_data["current_position_id"] = pos_id
    context.user_data["current_category_id"] = pos["category_id"]

    key_types = db.get_key_types_by_position(pos_id)
    buttons = []

    if is_admin(context):
        buttons.extend([
            [
                InlineKeyboardButton("\U0001f4c1 Add files", callback_data=f"add_files_{pos_id}"),
                InlineKeyboardButton("\u2699 Edit status", callback_data=f"edit_status_{pos_id}"),
            ],
            [
                InlineKeyboardButton("\u2795 Add key type", callback_data=f"add_key_type_{pos_id}"),
                InlineKeyboardButton("\U0001f5d1 Delete position", callback_data=f"delete_pos_{pos_id}"),
            ],
            [
                InlineKeyboardButton("\U0001f4c1 Get files", callback_data=f"get_files_{pos_id}"),
                InlineKeyboardButton("\U0001f6e1 Check status", callback_data=f"check_status_{pos_id}"),
            ],
        ])

    for kt in key_types:
        buttons.append([InlineKeyboardButton(f"{kt['name']} - {kt['price']:.1f}$", callback_data=f"kt_{kt['id']}")])

    buttons.append([InlineKeyboardButton("\u2b05 Go back", callback_data=f"cat_{pos['category_id']}")])

    if not key_types:
        text = f"\u274c <b>No key types for {pos['name']}!</b>"
    else:
        text = f"\U0001f4cb <b>Choose a key type for {pos['name']}:</b>"

    await query.edit_message_text(
        text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def key_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    kt_id = int(query.data.split("_")[-1])
    kt = db.get_key_type_by_id(kt_id)
    if not kt:
        await query.edit_message_text("\u274c Key type not found.")
        return

    await show_key_type(query, context, kt)


async def show_key_type(query, context: ContextTypes.DEFAULT_TYPE, kt: dict) -> None:
    pos = db.get_position_by_id(kt["position_id"])
    cat = db.get_category_by_id(pos["category_id"]) if pos else None
    cat_name = cat["name"] if cat else "Unknown"

    stock = db.get_available_keys_count(kt["id"])

    buttons = [
        [InlineKeyboardButton("\U0001f511 Buy", callback_data=f"buy_key_{kt['id']}")],
    ]

    if is_admin(context):
        buttons.append(
            [InlineKeyboardButton("\U0001f5d1 Delete key type", callback_data=f"del_kt_{kt['id']}")]
        )
        buttons.append([
            InlineKeyboardButton("\u2795 Add keys", callback_data=f"add_keys_{kt['id']}"),
            InlineKeyboardButton("\u274c Clear keys", callback_data=f"clear_keys_{kt['id']}"),
        ])
        buttons.append([
            InlineKeyboardButton("\U0001f4b0 Manage price", callback_data=f"manage_price_{kt['id']}"),
            InlineKeyboardButton("\u270f Edit prices", callback_data=f"edit_price_{kt['id']}"),
        ])
        buttons.append(
            [InlineKeyboardButton("\U0001f4bc Init price", callback_data=f"init_price_{kt['id']}")]
        )

    buttons.append(
        [InlineKeyboardButton("\u2b05 Go back", callback_data=f"pos_{kt['position_id']}")]
    )

    await query.edit_message_text(
        f"\U0001f511 <b>Key {kt['name']} ({cat_name}):</b>\n"
        f"- Category: {cat_name}\n"
        f"- Price: <code>{kt['price']:.1f}$</code>\n"
        f"- Keys in stock: <code>{stock}</code>\n"
        f"- Initial price: <code>{kt['init_price']:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


async def buy_key_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not is_logged_in(context):
        return

    kt_id = int(query.data.split("_")[-1])
    kt = db.get_key_type_by_id(kt_id)
    if not kt:
        await query.edit_message_text("\u274c Key type not found.")
        return

    account = db.get_account_by_id(context.user_data["account_id"])
    if not account:
        await query.edit_message_text("\u274c Account not found.")
        return

    if account["balance"] < kt["price"]:
        await query.edit_message_text(
            "\u274c <b>Not enough balance!</b>\n"
            f"Required: <code>{kt['price']:.2f}$</code>\n"
            f"Your balance: <code>{account['balance']:.2f}$</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2b05 Go back", callback_data=f"pos_{kt['position_id']}")]
            ]),
        )
        return

    cat_id = context.user_data.get("current_category_id", 0)
    cat = db.get_category_by_id(cat_id)
    cat_name = cat["name"] if cat else "Unknown"

    result = db.purchase_key_atomic(
        kt_id, account["id"], kt["name"], cat_name, kt["price"], kt["init_price"]
    )
    if not result:
        await query.edit_message_text(
            "\u274c <b>No keys in stock!</b>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2b05 Go back", callback_data=f"pos_{kt['position_id']}")]
            ]),
        )
        return

    key_value, new_balance = result

    await query.edit_message_text(
        f"\u2705 <b>Purchase successful!</b>\n\n"
        f"\U0001f511 Key: <code>{key_value}</code>\n"
        f"Type: {kt['name']}\n"
        f"Price: <code>{kt['price']:.2f}$</code>\n"
        f"Remaining balance: <code>{new_balance:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2b05 Go back", callback_data=f"pos_{kt['position_id']}")]
        ]),
    )


async def clear_keys_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    kt_id = int(query.data.split("_")[-1])
    cleared = db.clear_keys(kt_id)
    kt = db.get_key_type_by_id(kt_id)

    if kt:
        await show_key_type(query, context, kt)
    else:
        await query.edit_message_text(f"\u2705 Cleared {cleared} keys.")


async def del_kt_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    kt_id = int(query.data.split("_")[-1])
    db.delete_key_type(kt_id)

    cat_id = context.user_data.get("current_category_id", 0)
    await query.edit_message_text(
        "\U0001f5d1 Key type deleted!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2b05 Go back", callback_data=f"cat_{cat_id}")]
        ]),
    )


async def delete_cat_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    cat_id = int(query.data.split("_")[-1])
    db.delete_category(cat_id)

    await query.edit_message_text(
        "\U0001f5d1 Category deleted!",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("\u2b05 Go back", callback_data="go_back_categories")]
        ]),
    )


# ─────────────────── Add Category (Conversation) ───────────────────

async def add_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("\u274c Cancel", callback_data="cancel_add_category")]]
    )
    await query.edit_message_text(
        "\U0001f4dd <b>New name for category:</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return ADD_CATEGORY_NAME


async def add_category_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    cat = db.create_category(name)
    if not cat:
        await update.message.reply_text("\u274c Category already exists or error.")
        return ConversationHandler.END

    context.user_data["current_category_id"] = cat["id"]

    categories = db.get_all_categories()
    buttons = []
    if is_admin(context):
        buttons.append([InlineKeyboardButton("\u2795 Add category", callback_data="add_category")])
    for c in categories:
        buttons.append([InlineKeyboardButton(c["name"], callback_data=f"cat_{c['id']}")])

    await update.message.reply_text(
        "\U0001f4cb <b>Choose a category:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    return ConversationHandler.END


async def cancel_add_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("\U0001f4cd Canceled")
    return ConversationHandler.END


# ─────────────────── Add Position (Conversation) ───────────────────

async def add_position_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    cat_id = int(query.data.split("_")[-1])
    context.user_data["current_category_id"] = cat_id

    await query.edit_message_text(
        "\U0001f4dd <b>Type position name:</b>",
        parse_mode="HTML",
    )
    return ADD_POSITION_NAME


async def add_position_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    cat_id = context.user_data.get("current_category_id")

    pos = db.create_position(name, cat_id)
    if not pos:
        await update.message.reply_text("\u274c Failed to create position.")
        return ConversationHandler.END

    context.user_data["current_position_id"] = pos["id"]
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("\u274c Cancel", callback_data="cancel_add_key_type")]]
    )

    await update.message.reply_text(
        "\U0001f4dd <b>Type key type name:</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return ADD_KEY_TYPE_NAME


# ─────────────────── Add Key Type (Conversation) ───────────────────

async def add_key_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    pos_id = int(query.data.split("_")[-1])
    context.user_data["current_position_id"] = pos_id
    keyboard = InlineKeyboardMarkup(
        [[InlineKeyboardButton("\u274c Cancel", callback_data="cancel_add_key_type")]]
    )

    await query.edit_message_text(
        "\U0001f4dd <b>Type key type name:</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return ADD_KEY_TYPE_NAME


async def add_key_type_name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()
    context.user_data["new_key_type_name"] = name

    await update.message.reply_text(
        "\U0001f4dd <b>Type price for key:</b>",
        parse_mode="HTML",
    )
    return ADD_KEY_TYPE_PRICE


async def add_key_type_price_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("\u274c Please enter a valid number.")
        return ADD_KEY_TYPE_PRICE

    name = context.user_data.get("new_key_type_name")
    pos_id = context.user_data.get("current_position_id")

    kt = db.create_key_type(name, pos_id, price)
    if not kt:
        await update.message.reply_text("\u274c Failed to create key type.")
        return ConversationHandler.END

    pos = db.get_position_by_id(pos_id)
    buttons = [
        [
            InlineKeyboardButton("\U0001f4c1 Add files", callback_data=f"add_files_{pos_id}"),
            InlineKeyboardButton("\u2699 Edit status", callback_data=f"edit_status_{pos_id}"),
        ],
        [
            InlineKeyboardButton("\u2795 Add key type", callback_data=f"add_key_type_{pos_id}"),
            InlineKeyboardButton("\U0001f5d1 Delete position", callback_data=f"delete_pos_{pos_id}"),
        ],
        [
            InlineKeyboardButton("\U0001f4c1 Get files", callback_data=f"get_files_{pos_id}"),
            InlineKeyboardButton("\U0001f6e1 Check status", callback_data=f"check_status_{pos_id}"),
        ],
        [InlineKeyboardButton(f"{kt['name']} - {kt['price']:.1f}$", callback_data=f"kt_{kt['id']}")],
        [InlineKeyboardButton("\u2b05 Go back", callback_data=f"cat_{pos['category_id'] if pos else 0}")],
    ]

    await update.message.reply_text(
        f"\U0001f4cb <b>Choose a key type for {pos['name'] if pos else 'position'}:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    context.user_data.pop("new_key_type_name", None)
    return ConversationHandler.END


async def cancel_add_key_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    pos_id = context.user_data.get("current_position_id")
    if pos_id:
        await show_position_menu(query, context, pos_id)
    else:
        await query.edit_message_text("\U0001f4cd Canceled")
    context.user_data.pop("new_key_type_name", None)
    return ConversationHandler.END


async def feature_disabled_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("\u2757 This feature is disabled.")


async def delete_position_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    pos_id = int(query.data.split("_")[-1])
    pos = db.get_position_by_id(pos_id)
    db.delete_position(pos_id)

    cat_id = pos["category_id"] if pos else context.user_data.get("current_category_id", 0)
    await category_callback_like(query, context, cat_id)


async def category_callback_like(query, context: ContextTypes.DEFAULT_TYPE, cat_id: int) -> None:
    category = db.get_category_by_id(cat_id)
    if not category:
        await query.edit_message_text("\u274c Category not found.")
        return

    context.user_data["current_category_id"] = cat_id

    positions = db.get_positions_by_category(cat_id)
    buttons = []
    if is_admin(context):
        buttons.append([
            InlineKeyboardButton("\u2795 Add position", callback_data=f"add_position_{cat_id}"),
            InlineKeyboardButton("\U0001f5d1 Delete category", callback_data=f"delete_cat_{cat_id}"),
        ])
    for pos in positions:
        buttons.append([InlineKeyboardButton(pos["name"], callback_data=f"pos_{pos['id']}")])
    buttons.append([InlineKeyboardButton("\u2b05 Go back", callback_data="go_back_categories")])

    await query.edit_message_text(
        f"\U0001f4cb <b>Choose a product in category {category['name']}:</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ─────────────────── Add Keys (Conversation) ───────────────────

async def add_keys_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    kt_id = int(query.data.split("_")[-1])
    context.user_data["adding_keys_kt_id"] = kt_id

    await query.edit_message_text(
        "\U0001f4dd <b>Send keys (one per line):</b>",
        parse_mode="HTML",
    )
    return ADD_KEYS_VALUE


async def add_keys_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    kt_id = context.user_data.get("adding_keys_kt_id")
    values = update.message.text.strip().split("\n")
    added = db.add_keys(kt_id, values)

    kt = db.get_key_type_by_id(kt_id)

    await update.message.reply_text(
        f"\u2705 Added <b>{added}</b> keys!",
        parse_mode="HTML",
    )

    if kt:
        stock = db.get_available_keys_count(kt["id"])
        cat_id = context.user_data.get("current_category_id", 0)

        await update.message.reply_text(
            f"\U0001f511 <b>Key {kt['name']}:</b>\n"
            f"- Keys in stock: <code>{stock}</code>",
            parse_mode="HTML",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("\u2b05 Go back", callback_data=f"pos_{kt['position_id']}")]
            ]),
        )

    context.user_data.pop("adding_keys_kt_id", None)
    return ConversationHandler.END


# ─────────────────── Edit Price (Conversation) ───────────────────

async def edit_price_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    kt_id = int(query.data.split("_")[-1])
    context.user_data["editing_price_kt_id"] = kt_id

    await query.edit_message_text(
        "\u270f <b>Type new price:</b>",
        parse_mode="HTML",
    )
    return EDIT_PRICE_VALUE


async def edit_price_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("\u274c Please enter a valid number.")
        return EDIT_PRICE_VALUE

    kt_id = context.user_data.get("editing_price_kt_id")
    db.update_key_type_price(kt_id, price)

    kt = db.get_key_type_by_id(kt_id)
    if kt:
        await show_key_type_message(update, context, kt)

    context.user_data.pop("editing_price_kt_id", None)
    return ConversationHandler.END


# ─────────────────── Init Price (Conversation) ───────────────────

async def init_price_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    kt_id = int(query.data.split("_")[-1])
    context.user_data["init_price_kt_id"] = kt_id

    await query.edit_message_text(
        "\U0001f4bc <b>Type initial price:</b>",
        parse_mode="HTML",
    )
    return INIT_PRICE_VALUE


async def init_price_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("\u274c Please enter a valid number.")
        return INIT_PRICE_VALUE

    kt_id = context.user_data.get("init_price_kt_id")
    db.update_key_type_init_price(kt_id, price)

    kt = db.get_key_type_by_id(kt_id)
    if kt:
        await show_key_type_message(update, context, kt)

    context.user_data.pop("init_price_kt_id", None)
    return ConversationHandler.END


# ─────────────────── Manage Price (Conversation) ───────────────────

async def manage_price_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    kt_id = int(query.data.split("_")[-1])
    context.user_data["manage_price_kt_id"] = kt_id

    await query.edit_message_text(
        "\U0001f4b0 <b>Type new sell price:</b>",
        parse_mode="HTML",
    )
    return MANAGE_PRICE_VALUE


async def manage_price_value_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    try:
        price = float(update.message.text.strip())
    except ValueError:
        await update.message.reply_text("\u274c Please enter a valid number.")
        return MANAGE_PRICE_VALUE

    kt_id = context.user_data.get("manage_price_kt_id")
    db.update_key_type_price(kt_id, price)

    kt = db.get_key_type_by_id(kt_id)
    if kt:
        await show_key_type_message(update, context, kt)

    context.user_data.pop("manage_price_kt_id", None)
    return ConversationHandler.END


async def show_key_type_message(update: Update, context: ContextTypes.DEFAULT_TYPE, kt: dict) -> None:
    pos = db.get_position_by_id(kt["position_id"])
    cat = db.get_category_by_id(pos["category_id"]) if pos else None
    cat_name = cat["name"] if cat else "Unknown"
    stock = db.get_available_keys_count(kt["id"])

    buttons = [
        [InlineKeyboardButton("\U0001f511 Buy", callback_data=f"buy_key_{kt['id']}")],
    ]
    if is_admin(context):
        buttons.append(
            [InlineKeyboardButton("\U0001f5d1 Delete key type", callback_data=f"del_kt_{kt['id']}")]
        )
        buttons.append([
            InlineKeyboardButton("\u2795 Add keys", callback_data=f"add_keys_{kt['id']}"),
            InlineKeyboardButton("\u274c Clear keys", callback_data=f"clear_keys_{kt['id']}"),
        ])
        buttons.append([
            InlineKeyboardButton("\U0001f4b0 Manage price", callback_data=f"manage_price_{kt['id']}"),
            InlineKeyboardButton("\u270f Edit prices", callback_data=f"edit_price_{kt['id']}"),
        ])
        buttons.append(
            [InlineKeyboardButton("\U0001f4bc Init price", callback_data=f"init_price_{kt['id']}")]
        )
    buttons.append(
        [InlineKeyboardButton("\u2b05 Go back", callback_data=f"pos_{kt['position_id']}")]
    )

    await update.message.reply_text(
        f"\U0001f511 <b>Key {kt['name']} ({cat_name}):</b>\n"
        f"- Category: {cat_name}\n"
        f"- Price: <code>{kt['price']:.1f}$</code>\n"
        f"- Keys in stock: <code>{stock}</code>\n"
        f"- Initial price: <code>{kt['init_price']:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(buttons),
    )


# ─────────────────── Broadcast (Conversation) ───────────────────

async def broadcast_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return ConversationHandler.END

    context.user_data["broadcast_items"] = []

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2795 Add more", callback_data="broadcast_add"),
            InlineKeyboardButton("\U0001f440 Preview", callback_data="broadcast_preview"),
        ],
        [
            InlineKeyboardButton("\U0001f680 Send now", callback_data="broadcast_send"),
            InlineKeyboardButton("\u274c Cancel", callback_data="broadcast_cancel"),
        ],
        [InlineKeyboardButton(
            f"\U0001f9fa Items: {len(context.user_data.get('broadcast_items', []))}",
            callback_data="broadcast_count",
        )],
    ])

    await query.edit_message_text(
        "\U0001f4ac <b>Broadcast</b>\n"
        "Send a message (text / photo / document / video)."
        "After each item I'll ask if you're ready to send.",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return BROADCAST_CONTENT


async def broadcast_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    items = context.user_data.get("broadcast_items", [])

    await query.edit_message_text(
        f"\U0001f4ac <b>Add more</b>\n"
        f"Send the next message."
        f"Items in queue: <b>{len(items)}</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("\u2795 Add more", callback_data="broadcast_add"),
                InlineKeyboardButton("\U0001f440 Preview", callback_data="broadcast_preview"),
            ],
            [
                InlineKeyboardButton("\U0001f680 Send now", callback_data="broadcast_send"),
                InlineKeyboardButton("\u274c Cancel", callback_data="broadcast_cancel"),
            ],
            [InlineKeyboardButton(
                f"\U0001f9fa Items: {len(items)}",
                callback_data="broadcast_count",
            )],
        ]),
    )
    return BROADCAST_CONTENT


async def broadcast_content_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    items = context.user_data.setdefault("broadcast_items", [])

    if update.message.photo:
        items.append({"type": "photo", "file_id": update.message.photo[-1].file_id, "caption": update.message.caption})
    elif update.message.document:
        items.append({"type": "document", "file_id": update.message.document.file_id, "caption": update.message.caption})
    elif update.message.video:
        items.append({"type": "video", "file_id": update.message.video.file_id, "caption": update.message.caption})
    elif update.message.text:
        items.append({"type": "text", "text": update.message.text})

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2795 Add more", callback_data="broadcast_add"),
            InlineKeyboardButton("\U0001f440 Preview", callback_data="broadcast_preview"),
        ],
        [
            InlineKeyboardButton("\U0001f680 Send now", callback_data="broadcast_send"),
            InlineKeyboardButton("\u274c Cancel", callback_data="broadcast_cancel"),
        ],
        [InlineKeyboardButton(
            f"\U0001f9fa Items: {len(items)}",
            callback_data="broadcast_count",
        )],
    ])

    await update.message.reply_text(
        f"\u2705 Added to broadcast. Items in queue: <b>{len(items)}</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return BROADCAST_CONTENT


async def broadcast_preview_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    items = context.user_data.get("broadcast_items", [])
    if not items:
        await query.edit_message_text("\u2757 No items to preview.")
        return BROADCAST_CONTENT

    await query.edit_message_text(
        "\U0001f440 <b>Preview:</b>",
        parse_mode="HTML",
    )

    for item in items:
        if item["type"] == "text":
            await query.message.reply_text(item["text"])
        elif item["type"] == "photo":
            await query.message.reply_photo(item["file_id"], caption=item.get("caption"))
        elif item["type"] == "document":
            await query.message.reply_document(item["file_id"], caption=item.get("caption"))
        elif item["type"] == "video":
            await query.message.reply_video(item["file_id"], caption=item.get("caption"))

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\u2795 Add more", callback_data="broadcast_add"),
            InlineKeyboardButton("\U0001f440 Preview", callback_data="broadcast_preview"),
        ],
        [
            InlineKeyboardButton("\U0001f680 Send now", callback_data="broadcast_send"),
            InlineKeyboardButton("\u274c Cancel", callback_data="broadcast_cancel"),
        ],
        [InlineKeyboardButton(
            f"\U0001f9fa Items: {len(items)}",
            callback_data="broadcast_count",
        )],
    ])

    await query.message.reply_text(
        "Ready to send?",
        reply_markup=keyboard,
    )
    return BROADCAST_CONTENT


async def broadcast_send_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    items = context.user_data.get("broadcast_items", [])
    if not items:
        await query.edit_message_text("\u2757 No items to send.")
        return ConversationHandler.END

    sessions = db.get_all_sessions()
    user_count = len(sessions)

    await query.edit_message_text(
        f"\U0001f4e4 Starting broadcast to <b>{user_count}</b> authorized users..."
        f"Items: <b>{len(items)}</b>",
        parse_mode="HTML",
    )

    sent = 0
    for session in sessions:
        tid = session["telegram_id"]
        try:
            for item in items:
                if item["type"] == "text":
                    await context.bot.send_message(tid, item["text"])
                elif item["type"] == "photo":
                    await context.bot.send_photo(tid, item["file_id"], caption=item.get("caption"))
                elif item["type"] == "document":
                    await context.bot.send_document(tid, item["file_id"], caption=item.get("caption"))
                elif item["type"] == "video":
                    await context.bot.send_video(tid, item["file_id"], caption=item.get("caption"))
            sent += 1
        except Exception:
            logger.warning("Failed to send broadcast to %s", tid)

    await query.message.reply_text(
        f"\u2705 Broadcast sent to <b>{sent}/{user_count}</b> users.",
        parse_mode="HTML",
        reply_markup=get_keyboard(context),
    )

    context.user_data.pop("broadcast_items", None)
    return ConversationHandler.END


async def broadcast_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()

    context.user_data.pop("broadcast_items", None)

    await query.edit_message_text("\U0001f4cd Canceled")

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("\U0001f512 Manage accounts", callback_data="manage_accounts")],
        [InlineKeyboardButton("\U0001f50e Look at purchases", callback_data="look_purchases")],
        [InlineKeyboardButton("\U0001f4e2 Broadcast", callback_data="broadcast_start")],
    ])

    await query.message.reply_text(
        "\U0001f527 <b>Admin Panel</b>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )
    return ConversationHandler.END


async def broadcast_count_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()
    return BROADCAST_CONTENT


# ─────────────────── Statistics ───────────────────

async def statistics_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not await require_admin(query, context):
        return

    total = db.get_total_sales()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4c5 Daily", callback_data="stats_daily"),
            InlineKeyboardButton("\U0001f4c6 Week", callback_data="stats_week"),
            InlineKeyboardButton("\U0001f5d3 Month", callback_data="stats_month"),
        ],
        [
            InlineKeyboardButton("TOP", callback_data="stats_top"),
            InlineKeyboardButton("\U0001f4b0 Net Profit", callback_data="stats_net_profit"),
        ],
    ])

    await query.edit_message_text(
        f"\U0001f4ca <b>All time statistics:</b>\n"
        f"\U0001f4b0 Total sum of sells: <code>{total:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def stats_daily_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    now = datetime.now(timezone.utc)
    start = now.replace(hour=0, minute=0, second=0)
    total = db.get_sales_in_period(
        start.strftime("%d/%m/%Y, %H:%M"),
        now.strftime("%d/%m/%Y, %H:%M"),
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4c5 Daily", callback_data="stats_daily"),
            InlineKeyboardButton("\U0001f4c6 Week", callback_data="stats_week"),
            InlineKeyboardButton("\U0001f5d3 Month", callback_data="stats_month"),
        ],
        [
            InlineKeyboardButton("TOP", callback_data="stats_top"),
            InlineKeyboardButton("\U0001f4b0 Net Profit", callback_data="stats_net_profit"),
        ],
    ])

    await query.edit_message_text(
        f"\U0001f4c5 <b>Daily statistics:</b>\n"
        f"\U0001f4b0 Total sells today: <code>{total:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def stats_week_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=7)
    total = db.get_sales_in_period(
        start.strftime("%d/%m/%Y, %H:%M"),
        now.strftime("%d/%m/%Y, %H:%M"),
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4c5 Daily", callback_data="stats_daily"),
            InlineKeyboardButton("\U0001f4c6 Week", callback_data="stats_week"),
            InlineKeyboardButton("\U0001f5d3 Month", callback_data="stats_month"),
        ],
        [
            InlineKeyboardButton("TOP", callback_data="stats_top"),
            InlineKeyboardButton("\U0001f4b0 Net Profit", callback_data="stats_net_profit"),
        ],
    ])

    await query.edit_message_text(
        f"\U0001f4c6 <b>Weekly statistics:</b>\n"
        f"\U0001f4b0 Total sells this week: <code>{total:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def stats_month_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    now = datetime.now(timezone.utc)
    start = now - timedelta(days=30)
    total = db.get_sales_in_period(
        start.strftime("%d/%m/%Y, %H:%M"),
        now.strftime("%d/%m/%Y, %H:%M"),
    )

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4c5 Daily", callback_data="stats_daily"),
            InlineKeyboardButton("\U0001f4c6 Week", callback_data="stats_week"),
            InlineKeyboardButton("\U0001f5d3 Month", callback_data="stats_month"),
        ],
        [
            InlineKeyboardButton("TOP", callback_data="stats_top"),
            InlineKeyboardButton("\U0001f4b0 Net Profit", callback_data="stats_net_profit"),
        ],
    ])

    await query.edit_message_text(
        f"\U0001f5d3 <b>Monthly statistics:</b>\n"
        f"\U0001f4b0 Total sells this month: <code>{total:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


async def stats_top_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    top = db.get_top_buyers(10)

    text = "\U0001f3c6 <b>TOP Buyers:</b>\n\n"
    for i, buyer in enumerate(top, 1):
        text += (
            f"{i}. <b>{buyer['login']}</b> - "
            f"<code>{buyer['total_spent']:.2f}$</code> "
            f"({buyer['purchase_count']} purchases)\n"
        )

    if not top:
        text += "No data yet."

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4c5 Daily", callback_data="stats_daily"),
            InlineKeyboardButton("\U0001f4c6 Week", callback_data="stats_week"),
            InlineKeyboardButton("\U0001f5d3 Month", callback_data="stats_month"),
        ],
        [
            InlineKeyboardButton("TOP", callback_data="stats_top"),
            InlineKeyboardButton("\U0001f4b0 Net Profit", callback_data="stats_net_profit"),
        ],
    ])

    await query.edit_message_text(text, parse_mode="HTML", reply_markup=keyboard)


async def stats_net_profit_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    profit = db.get_net_profit()

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("\U0001f4c5 Daily", callback_data="stats_daily"),
            InlineKeyboardButton("\U0001f4c6 Week", callback_data="stats_week"),
            InlineKeyboardButton("\U0001f5d3 Month", callback_data="stats_month"),
        ],
        [
            InlineKeyboardButton("TOP", callback_data="stats_top"),
            InlineKeyboardButton("\U0001f4b0 Net Profit", callback_data="stats_net_profit"),
        ],
    ])

    await query.edit_message_text(
        f"\U0001f4b0 <b>Net Profit:</b>\n"
        f"Profit: <code>{profit:.2f}$</code>",
        parse_mode="HTML",
        reply_markup=keyboard,
    )


# ─────────────────── Fallback for unknown text ───────────────────

async def unknown_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not is_logged_in(context):
        await update.message.reply_text(access_denied_text(), parse_mode="HTML")


# ─────────────────── Main ───────────────────

def main() -> None:
    db.init_db()

    app = Application.builder().token(BOT_TOKEN).build()

    # Login conversation
    login_conv = ConversationHandler(
        entry_points=[
            CommandHandler("login", login_command),
            MessageHandler(filters.Regex(r"^\U0001f512 Login$"), login_button_handler),
        ],
        states={
            LOGIN_WAITING: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, login_credentials),
                CallbackQueryHandler(cancel_login_callback, pattern="^cancel_login$"),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        per_user=True,
        per_chat=True,
    )

    # Add account conversation
    add_account_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_account_callback, pattern="^add_account$")],
        states={
            ADD_ACCOUNT_LOGIN: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_login_handler),
            ],
            ADD_ACCOUNT_PASSWORD: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_account_password_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        per_user=True,
        per_chat=True,
    )

    # Add category conversation
    add_category_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_category_callback, pattern="^add_category$")],
        states={
            ADD_CATEGORY_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_category_name_handler),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_category_callback, pattern="^cancel_add_category$"),
            CommandHandler("start", start_command),
        ],
        per_user=True,
        per_chat=True,
    )

    # Add position conversation
    add_position_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_position_callback, pattern=r"^add_position_\d+$")],
        states={
            ADD_POSITION_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_position_name_handler),
            ],
            ADD_KEY_TYPE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_key_type_name_handler),
            ],
            ADD_KEY_TYPE_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_key_type_price_handler),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_key_type_callback, pattern="^cancel_add_key_type$"),
            CommandHandler("start", start_command),
        ],
        per_user=True,
        per_chat=True,
    )

    # Add key type conversation
    add_key_type_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_key_type_callback, pattern=r"^add_key_type_\d+$")],
        states={
            ADD_KEY_TYPE_NAME: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_key_type_name_handler),
            ],
            ADD_KEY_TYPE_PRICE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_key_type_price_handler),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(cancel_add_key_type_callback, pattern="^cancel_add_key_type$"),
            CommandHandler("start", start_command),
        ],
        per_user=True,
        per_chat=True,
    )

    # Add keys conversation
    add_keys_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_keys_callback, pattern=r"^add_keys_\d+$")],
        states={
            ADD_KEYS_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, add_keys_value_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        per_user=True,
        per_chat=True,
    )

    # Topup conversation
    topup_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(add_bal_callback, pattern=r"^add_bal_\d+$")],
        states={
            TOPUP_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, topup_amount_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        per_user=True,
        per_chat=True,
    )

    # Edit price conversation
    edit_price_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(edit_price_callback, pattern=r"^edit_price_\d+$")],
        states={
            EDIT_PRICE_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, edit_price_value_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        per_user=True,
        per_chat=True,
    )

    # Init price conversation
    init_price_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(init_price_callback, pattern=r"^init_price_\d+$")],
        states={
            INIT_PRICE_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, init_price_value_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        per_user=True,
        per_chat=True,
    )

    # Manage price conversation
    manage_price_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(manage_price_callback, pattern=r"^manage_price_\d+$")],
        states={
            MANAGE_PRICE_VALUE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, manage_price_value_handler),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        per_user=True,
        per_chat=True,
    )

    # Broadcast conversation
    broadcast_conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(broadcast_start_callback, pattern="^broadcast_start$")],
        states={
            BROADCAST_CONTENT: [
                CallbackQueryHandler(broadcast_add_callback, pattern="^broadcast_add$"),
                CallbackQueryHandler(broadcast_preview_callback, pattern="^broadcast_preview$"),
                CallbackQueryHandler(broadcast_send_callback, pattern="^broadcast_send$"),
                CallbackQueryHandler(broadcast_cancel_callback, pattern="^broadcast_cancel$"),
                CallbackQueryHandler(broadcast_count_callback, pattern="^broadcast_count$"),
                MessageHandler(
                    filters.TEXT | filters.PHOTO | filters.Document.ALL | filters.VIDEO,
                    broadcast_content_handler,
                ),
            ],
        },
        fallbacks=[CommandHandler("start", start_command)],
        per_user=True,
        per_chat=True,
    )

    # Add all conversation handlers first (order matters)
    app.add_handler(login_conv)
    app.add_handler(broadcast_conv)
    app.add_handler(add_account_conv)
    app.add_handler(add_category_conv)
    app.add_handler(add_position_conv)
    app.add_handler(add_key_type_conv)
    app.add_handler(add_keys_conv)
    app.add_handler(topup_conv)
    app.add_handler(edit_price_conv)
    app.add_handler(init_price_conv)
    app.add_handler(manage_price_conv)

    # Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("reset", reset_command))

    # Reply keyboard handlers
    app.add_handler(MessageHandler(filters.Regex(r"^\U0001f680 Log out$"), logout_handler))
    app.add_handler(MessageHandler(filters.Regex(r"^\U0001f3db Account$"), account_handler))
    app.add_handler(MessageHandler(filters.Regex(r"^\U0001f527 Manage$"), manage_handler))
    app.add_handler(MessageHandler(filters.Regex(r"^\U0001f6cd Buy keys$"), buy_keys_handler))
    app.add_handler(MessageHandler(filters.Regex(r"^\U0001f4e6 Stock$"), stock_handler))
    app.add_handler(MessageHandler(filters.Regex(r"^\U0001f4ca Statistics$"), statistics_keyboard_handler))

    # Inline callback handlers
    app.add_handler(CallbackQueryHandler(manage_accounts_callback, pattern="^manage_accounts$"))
    app.add_handler(CallbackQueryHandler(go_back_manage_callback, pattern="^go_back_manage$"))
    app.add_handler(CallbackQueryHandler(view_account_callback, pattern=r"^view_account_\d+$"))
    app.add_handler(CallbackQueryHandler(reset_bal_callback, pattern=r"^reset_bal_\d+$"))
    app.add_handler(CallbackQueryHandler(view_purchases_callback, pattern=r"^view_purchases_\d+$"))
    app.add_handler(CallbackQueryHandler(delete_acc_callback, pattern=r"^delete_acc_\d+$"))
    app.add_handler(CallbackQueryHandler(send_creds_callback, pattern=r"^send_creds_\d+$"))
    app.add_handler(CallbackQueryHandler(look_purchases_callback, pattern="^look_purchases$"))
    app.add_handler(CallbackQueryHandler(statistics_callback, pattern="^statistics$"))
    app.add_handler(CallbackQueryHandler(stats_daily_callback, pattern="^stats_daily$"))
    app.add_handler(CallbackQueryHandler(stats_week_callback, pattern="^stats_week$"))
    app.add_handler(CallbackQueryHandler(stats_month_callback, pattern="^stats_month$"))
    app.add_handler(CallbackQueryHandler(stats_top_callback, pattern="^stats_top$"))
    app.add_handler(CallbackQueryHandler(stats_net_profit_callback, pattern="^stats_net_profit$"))
    app.add_handler(CallbackQueryHandler(category_callback, pattern=r"^cat_\d+$"))
    app.add_handler(CallbackQueryHandler(go_back_categories_callback, pattern="^go_back_categories$"))
    app.add_handler(CallbackQueryHandler(position_callback, pattern=r"^pos_\d+$"))
    app.add_handler(CallbackQueryHandler(key_type_callback, pattern=r"^kt_\d+$"))
    app.add_handler(CallbackQueryHandler(feature_disabled_callback, pattern=r"^(add_files|edit_status|get_files|check_status)_\d+$"))
    app.add_handler(CallbackQueryHandler(delete_position_callback, pattern=r"^delete_pos_\d+$"))
    app.add_handler(CallbackQueryHandler(buy_key_callback, pattern=r"^buy_key_\d+$"))
    app.add_handler(CallbackQueryHandler(clear_keys_callback, pattern=r"^clear_keys_\d+$"))
    app.add_handler(CallbackQueryHandler(del_kt_callback, pattern=r"^del_kt_\d+$"))
    app.add_handler(CallbackQueryHandler(delete_cat_callback, pattern=r"^delete_cat_\d+$"))
    app.add_handler(CallbackQueryHandler(my_purchase_history_callback, pattern="^my_purchase_history$"))
    app.add_handler(CallbackQueryHandler(my_topup_history_callback, pattern="^my_topup_history$"))

    # Fallback
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, unknown_text))

    logger.info("Bot started!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
