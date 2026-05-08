import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager

DB_PATH = os.path.join("data", "arthiai.db")
os.makedirs("data", exist_ok=True)

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:

        conn.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id          TEXT PRIMARY KEY,        -- user_id e.g. "user_123"
                name        TEXT,
                email       TEXT UNIQUE,
                created_at  TEXT DEFAULT (datetime('now'))
            )
            CREATE TABLE IF NOT EXISTS portfolios (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         TEXT NOT NULL,
                portfolio_name  TEXT NOT NULL,
                created_at      TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, portfolio_name),    -- same user can't have two same-named portfolios
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
            CREATE TABLE IF NOT EXISTS holdings (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                portfolio_id    INTEGER NOT NULL,
                asset_type      TEXT NOT NULL,      -- stock, crypto, mutual_fund, bond, fd
                symbol          TEXT NOT NULL,      -- RELIANCE, bitcoin, 120716
                name            TEXT,
                quantity        REAL NOT NULL,
                buy_price       REAL NOT NULL,      -- Price paid per unit in Rs.
                buy_date        TEXT,               -- YYYY-MM-DD
                exchange        TEXT DEFAULT 'NSE',
                notes           TEXT DEFAULT '',
                added_at        TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (portfolio_id) REFERENCES portfolios(id)
            )
            CREATE TABLE IF NOT EXISTS alerts (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id         TEXT NOT NULL,
                asset_type      TEXT NOT NULL,      -- stock, crypto, mutual_fund
                symbol          TEXT NOT NULL,
                alert_type      TEXT NOT NULL,      -- above, below
                target_value    REAL NOT NULL,      -- Price threshold in Rs.
                exchange        TEXT DEFAULT 'NSE',
                email           TEXT,               -- Where to send notification
                note            TEXT DEFAULT '',
                status          TEXT DEFAULT 'active',  -- active, triggered, cancelled
                created_at      TEXT DEFAULT (datetime('now')),
                triggered_at    TEXT,               -- When it fired
                triggered_price REAL                -- Price when it fired
            )
            CREATE TABLE IF NOT EXISTS chat_history (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                role        TEXT NOT NULL,          -- user or assistant
                content     TEXT NOT NULL,
                model_used  TEXT,                   -- which AI model replied
                created_at  TEXT DEFAULT (datetime('now'))
            )
            CREATE TABLE IF NOT EXISTS watchlist (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     TEXT NOT NULL,
                asset_type  TEXT NOT NULL,
                symbol      TEXT NOT NULL,
                name        TEXT,
                added_at    TEXT DEFAULT (datetime('now')),
                UNIQUE(user_id, symbol, asset_type)
            """)
def get_portfolios(user_id: str):
    """Creates a new portfolio. Returns the portfolio's database ID.
    Also creates the user record if they don't exist yet."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM portfolios WHERE user_id=? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]

def add_holding(portfolio_id: int, holding: Dict) -> int:
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO holdings
                (portfolio_id, asset_type, symbol, name, quantity,
                 buy_price, buy_date, exchange, notes)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM holdings WHERE portfolio_id=? ORDER BY added_at DESC",
            (portfolio_id,)
        ).fetchall()
        return [dict(r) for r in rows]

def remove_holding(holding_id: int, portfolio_id: int) -> bool:
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM holdings WHERE id=? AND portfolio_id=?",
            (holding_id, portfolio_id)
        )
        return cursor.rowcount > 0

def create_alert(alert: Dict) -> int:
    with get_db() as conn:
        cursor = conn.execute("""
            INSERT INTO alerts
                (user_id, asset_type, symbol, alert_type, target_value,
                 exchange, email, note)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """)
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE status='active'"
        ).fetchall()
        return [dict(r) for r in rows]

def get_user_alerts(user_id: str) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM alerts WHERE user_id=? ORDER BY created_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]

def trigger_alert(alert_id: int, triggered_price: float):
    with get_db() as conn:
        conn.execute("""
            UPDATE alerts
            SET status='triggered',
                triggered_at=datetime('now'),
                triggered_price=?
            WHERE id=?
            """)
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM alerts WHERE id=? AND user_id=?",
            (alert_id, user_id)
        )
        return cursor.rowcount > 0

def save_chat_message(user_id: str, role: str, content: str, model: str = None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO chat_history (user_id, role, content, model_used) VALUES (?, ?, ?, ?)",
            (user_id, role, content, model)
        )

def get_chat_history(user_id: str, limit: int = 20) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute("""
            SELECT role, content, model_used, created_at
            FROM chat_history
            WHERE user_id=?
            ORDER BY created_at DESC
            LIMIT ?""")
    with get_db() as conn:
        conn.execute("DELETE FROM chat_history WHERE user_id=?", (user_id,))

def add_to_watchlist(user_id: str, asset_type: str, symbol: str, name: str = None):
    with get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO watchlist (user_id, asset_type, symbol, name) VALUES (?, ?, ?, ?)",
            (user_id, asset_type, symbol, name or symbol)
        )

def get_watchlist(user_id: str) -> List[Dict]:
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM watchlist WHERE user_id=? ORDER BY added_at DESC",
            (user_id,)
        ).fetchall()
        return [dict(r) for r in rows]

def remove_from_watchlist(user_id: str, symbol: str, asset_type: str):
    with get_db() as conn:
        conn.execute(
            "DELETE FROM watchlist WHERE user_id=? AND symbol=? AND asset_type=?",
            (user_id, symbol, asset_type)
        )

def get_db_stats() -> Dict:
    with get_db() as conn:
        tables = ["users", "portfolios", "holdings", "alerts", "chat_history", "watchlist"]
        stats = {}
        for table in tables:
            count = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            stats[table] = count
        stats["db_file"] = DB_PATH
        stats["db_size_kb"] = round(os.path.getsize(DB_PATH) / 1024, 2) if os.path.exists(DB_PATH) else 0
        return stats
