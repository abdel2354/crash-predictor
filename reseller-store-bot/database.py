import sqlite3
from datetime import datetime, timezone
from typing import Optional

from config import DB_PATH


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    conn = get_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            balance REAL DEFAULT 0.0,
            telegram_id INTEGER,
            is_admin INTEGER DEFAULT 0,
            created_at TEXT NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category_id INTEGER NOT NULL,
            FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS key_types (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            position_id INTEGER NOT NULL,
            price REAL DEFAULT 0.0,
            init_price REAL DEFAULT 0.0,
            FOREIGN KEY (position_id) REFERENCES positions(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS keys (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            key_type_id INTEGER NOT NULL,
            value TEXT NOT NULL,
            sold INTEGER DEFAULT 0,
            FOREIGN KEY (key_type_id) REFERENCES key_types(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            key_type_name TEXT NOT NULL,
            category_name TEXT NOT NULL,
            key_value TEXT NOT NULL,
            price REAL NOT NULL,
            init_price REAL DEFAULT 0.0,
            purchased_at TEXT NOT NULL,
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS topups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            account_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            topped_up_at TEXT NOT NULL,
            admin_login TEXT,
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
        )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            telegram_id INTEGER PRIMARY KEY,
            account_id INTEGER,
            FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE SET NULL
        )
    """)

    conn.commit()
    conn.close()


# --------------- Account Operations ---------------

def create_account(login: str, password: str, is_admin: int = 0) -> Optional[dict]:
    conn = get_connection()
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y, %H:%M")
    try:
        conn.execute(
            "INSERT INTO accounts (login, password, is_admin, created_at) VALUES (?, ?, ?, ?)",
            (login, password, is_admin, now),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM accounts WHERE login = ?", (login,)
        ).fetchone()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_account_by_login(login: str) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM accounts WHERE login = ?", (login,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_account_by_id(account_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM accounts WHERE id = ?", (account_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_accounts() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM accounts ORDER BY login").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def delete_account(account_id: int) -> bool:
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE account_id = ?", (account_id,))
    result = conn.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    conn.commit()
    deleted = result.rowcount > 0
    conn.close()
    return deleted


def update_balance(account_id: int, new_balance: float) -> None:
    conn = get_connection()
    conn.execute("UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id))
    conn.commit()
    conn.close()


def add_balance(account_id: int, amount: float) -> float:
    acc = get_account_by_id(account_id)
    if not acc:
        return 0.0
    new_bal = acc["balance"] + amount
    update_balance(account_id, new_bal)
    return new_bal


def reset_balance(account_id: int) -> None:
    update_balance(account_id, 0.0)


# --------------- Session Operations ---------------

def login_session(telegram_id: int, account_id: int) -> None:
    conn = get_connection()
    conn.execute(
        "INSERT OR REPLACE INTO sessions (telegram_id, account_id) VALUES (?, ?)",
        (telegram_id, account_id),
    )
    conn.commit()
    conn.close()


def logout_session(telegram_id: int) -> None:
    conn = get_connection()
    conn.execute("DELETE FROM sessions WHERE telegram_id = ?", (telegram_id,))
    conn.commit()
    conn.close()


def get_session(telegram_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute(
        "SELECT s.*, a.login, a.balance, a.is_admin FROM sessions s "
        "JOIN accounts a ON s.account_id = a.id WHERE s.telegram_id = ?",
        (telegram_id,),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_all_sessions() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT s.telegram_id FROM sessions s JOIN accounts a ON s.account_id = a.id"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --------------- Category Operations ---------------

def create_category(name: str) -> Optional[dict]:
    conn = get_connection()
    try:
        conn.execute("INSERT INTO categories (name) VALUES (?)", (name,))
        conn.commit()
        row = conn.execute("SELECT * FROM categories WHERE name = ?", (name,)).fetchone()
        return dict(row) if row else None
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()


def get_all_categories() -> list[dict]:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM categories ORDER BY name").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_category_by_id(cat_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM categories WHERE id = ?", (cat_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_category(cat_id: int) -> bool:
    conn = get_connection()
    result = conn.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    conn.commit()
    deleted = result.rowcount > 0
    conn.close()
    return deleted


# --------------- Position Operations ---------------

def create_position(name: str, category_id: int) -> Optional[dict]:
    conn = get_connection()
    conn.execute(
        "INSERT INTO positions (name, category_id) VALUES (?, ?)", (name, category_id)
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM positions WHERE name = ? AND category_id = ?",
        (name, category_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_positions_by_category(category_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM positions WHERE category_id = ? ORDER BY name", (category_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_position_by_id(pos_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM positions WHERE id = ?", (pos_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def delete_position(pos_id: int) -> bool:
    conn = get_connection()
    result = conn.execute("DELETE FROM positions WHERE id = ?", (pos_id,))
    conn.commit()
    deleted = result.rowcount > 0
    conn.close()
    return deleted


# --------------- Key Type Operations ---------------

def create_key_type(name: str, position_id: int, price: float) -> Optional[dict]:
    conn = get_connection()
    conn.execute(
        "INSERT INTO key_types (name, position_id, price) VALUES (?, ?, ?)",
        (name, position_id, price),
    )
    conn.commit()
    row = conn.execute(
        "SELECT * FROM key_types WHERE name = ? AND position_id = ?",
        (name, position_id),
    ).fetchone()
    conn.close()
    return dict(row) if row else None


def get_key_types_by_position(position_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM key_types WHERE position_id = ? ORDER BY name", (position_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_key_type_by_id(kt_id: int) -> Optional[dict]:
    conn = get_connection()
    row = conn.execute("SELECT * FROM key_types WHERE id = ?", (kt_id,)).fetchone()
    conn.close()
    return dict(row) if row else None


def update_key_type_price(kt_id: int, price: float) -> None:
    conn = get_connection()
    conn.execute("UPDATE key_types SET price = ? WHERE id = ?", (price, kt_id))
    conn.commit()
    conn.close()


def update_key_type_init_price(kt_id: int, init_price: float) -> None:
    conn = get_connection()
    conn.execute("UPDATE key_types SET init_price = ? WHERE id = ?", (init_price, kt_id))
    conn.commit()
    conn.close()


def delete_key_type(kt_id: int) -> bool:
    conn = get_connection()
    result = conn.execute("DELETE FROM key_types WHERE id = ?", (kt_id,))
    conn.commit()
    deleted = result.rowcount > 0
    conn.close()
    return deleted


# --------------- Key Operations ---------------

def add_keys(key_type_id: int, values: list[str]) -> int:
    conn = get_connection()
    added = 0
    for v in values:
        v = v.strip()
        if v:
            conn.execute(
                "INSERT INTO keys (key_type_id, value) VALUES (?, ?)",
                (key_type_id, v),
            )
            added += 1
    conn.commit()
    conn.close()
    return added


def get_available_keys_count(key_type_id: int) -> int:
    conn = get_connection()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM keys WHERE key_type_id = ? AND sold = 0",
        (key_type_id,),
    ).fetchone()
    conn.close()
    return row["cnt"] if row else 0


def get_stock_summary() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT c.name AS category_name, kt.name AS key_type_name,
               COUNT(CASE WHEN k.sold = 0 THEN 1 END) AS available
        FROM categories c
        JOIN positions p ON p.category_id = c.id
        JOIN key_types kt ON kt.position_id = p.id
        LEFT JOIN keys k ON k.key_type_id = kt.id
        GROUP BY c.name, kt.name
        ORDER BY c.name, kt.name
        """
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def buy_key(key_type_id: int) -> Optional[str]:
    conn = get_connection()
    row = conn.execute(
        "SELECT * FROM keys WHERE key_type_id = ? AND sold = 0 LIMIT 1",
        (key_type_id,),
    ).fetchone()
    if row:
        conn.execute("UPDATE keys SET sold = 1 WHERE id = ?", (row["id"],))
        conn.commit()
        conn.close()
        return row["value"]
    conn.close()
    return None


def purchase_key_atomic(
    key_type_id: int,
    account_id: int,
    key_type_name: str,
    category_name: str,
    price: float,
    init_price: float = 0.0,
) -> Optional[tuple[str, float]]:
    conn = get_connection()
    try:
        row = conn.execute(
            "SELECT * FROM keys WHERE key_type_id = ? AND sold = 0 LIMIT 1",
            (key_type_id,),
        ).fetchone()
        if not row:
            conn.close()
            return None

        conn.execute("UPDATE keys SET sold = 1 WHERE id = ?", (row["id"],))

        acc = conn.execute(
            "SELECT balance FROM accounts WHERE id = ?", (account_id,)
        ).fetchone()
        new_balance = acc["balance"] - price
        conn.execute(
            "UPDATE accounts SET balance = ? WHERE id = ?", (new_balance, account_id)
        )

        now = datetime.now(timezone.utc).strftime("%d/%m/%Y, %H:%M")
        conn.execute(
            "INSERT INTO purchases (account_id, key_type_name, category_name, key_value, price, init_price, purchased_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (account_id, key_type_name, category_name, row["value"], price, init_price, now),
        )

        conn.commit()
        conn.close()
        return (row["value"], new_balance)
    except Exception:
        conn.rollback()
        conn.close()
        raise


def clear_keys(key_type_id: int) -> int:
    conn = get_connection()
    result = conn.execute(
        "DELETE FROM keys WHERE key_type_id = ? AND sold = 0", (key_type_id,)
    )
    conn.commit()
    cleared = result.rowcount
    conn.close()
    return cleared


# --------------- Purchase Operations ---------------

def record_purchase(
    account_id: int,
    key_type_name: str,
    category_name: str,
    key_value: str,
    price: float,
    init_price: float = 0.0,
) -> None:
    conn = get_connection()
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y, %H:%M")
    conn.execute(
        "INSERT INTO purchases (account_id, key_type_name, category_name, key_value, price, init_price, purchased_at) "
        "VALUES (?, ?, ?, ?, ?, ?, ?)",
        (account_id, key_type_name, category_name, key_value, price, init_price, now),
    )
    conn.commit()
    conn.close()


def get_purchases_by_account(account_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM purchases WHERE account_id = ? ORDER BY id DESC", (account_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_all_purchases() -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT p.*, a.login FROM purchases p JOIN accounts a ON p.account_id = a.id ORDER BY p.id DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --------------- Top-up Operations ---------------

def record_topup(account_id: int, amount: float, admin_login: str) -> None:
    conn = get_connection()
    now = datetime.now(timezone.utc).strftime("%d/%m/%Y, %H:%M")
    conn.execute(
        "INSERT INTO topups (account_id, amount, topped_up_at, admin_login) VALUES (?, ?, ?, ?)",
        (account_id, amount, now, admin_login),
    )
    conn.commit()
    conn.close()


def get_topups_by_account(account_id: int) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM topups WHERE account_id = ? ORDER BY id DESC", (account_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


# --------------- Statistics Operations ---------------

def get_total_sales() -> float:
    conn = get_connection()
    row = conn.execute("SELECT COALESCE(SUM(price), 0) as total FROM purchases").fetchone()
    conn.close()
    return row["total"] if row else 0.0


def get_sales_in_period(start_date: str, end_date: str) -> float:
    conn = get_connection()
    rows = conn.execute("SELECT * FROM purchases").fetchall()
    conn.close()
    total = 0.0
    for r in rows:
        try:
            pdate = datetime.strptime(r["purchased_at"], "%d/%m/%Y, %H:%M")
            sdate = datetime.strptime(start_date, "%d/%m/%Y, %H:%M")
            edate = datetime.strptime(end_date, "%d/%m/%Y, %H:%M")
            if sdate <= pdate <= edate:
                total += r["price"]
        except (ValueError, TypeError):
            continue
    return total


def get_top_buyers(limit: int = 10) -> list[dict]:
    conn = get_connection()
    rows = conn.execute(
        "SELECT a.login, COALESCE(SUM(p.price), 0) as total_spent, COUNT(p.id) as purchase_count "
        "FROM accounts a LEFT JOIN purchases p ON a.id = p.account_id "
        "GROUP BY a.id ORDER BY total_spent DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_net_profit() -> float:
    conn = get_connection()
    row = conn.execute(
        "SELECT COALESCE(SUM(price), 0) as revenue, COALESCE(SUM(init_price), 0) as cost FROM purchases"
    ).fetchone()
    conn.close()
    revenue = row["revenue"] if row else 0.0
    cost = row["cost"] if row else 0.0
    return revenue - cost
