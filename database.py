import sqlite3
import os
import threading
from datetime import datetime


DATABASE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "database")
DATABASE_PATH = os.path.join(DATABASE_DIR, "database.db")


_thread_local = threading.local()


def get_connection():
    if not hasattr(_thread_local, "connection") or _thread_local.connection is None:
        _thread_local.connection = sqlite3.connect(DATABASE_PATH, timeout=10)
        _thread_local.connection.row_factory = sqlite3.Row
        _thread_local.connection.execute("PRAGMA foreign_keys = ON")
    return _thread_local.connection


def close_connection():
    if hasattr(_thread_local, "connection") and _thread_local.connection is not None:
        _thread_local.connection.close()
        _thread_local.connection = None
def create_tables():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            name        TEXT NOT NULL,
            role        TEXT NOT NULL DEFAULT 'customer' 
                        CHECK(role IN ('customer', 'admin', 'system')),
            created_at  TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id      INTEGER NOT NULL,
            account_type TEXT NOT NULL DEFAULT 'savings'
                         CHECK(account_type IN ('savings', 'current', 'system')),
            balance      REAL NOT NULL DEFAULT 0.0
                         CHECK(balance >= 0),
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            txn_id        TEXT NOT NULL,
            operation     TEXT NOT NULL,
            source_acc_id INTEGER,
            dest_acc_id   INTEGER,
            amount        REAL,
            status        TEXT NOT NULL DEFAULT 'PENDING'
                          CHECK(status IN ('PENDING', 'COMMITTED', 'ABORTED', 'ROLLED_BACK')),
            timestamp     TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            details       TEXT,
            FOREIGN KEY (source_acc_id) REFERENCES accounts(id),
            FOREIGN KEY (dest_acc_id)   REFERENCES accounts(id)
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS security_logs (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp   TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
            user_id     INTEGER,
            txn_id      TEXT,
            operation   TEXT NOT NULL,
            resource    TEXT,
            result      TEXT NOT NULL 
                        CHECK(result IN ('ALLOWED', 'BLOCKED', 'FLAGGED', 'REJECTED')),
            event_type  TEXT NOT NULL
                        CHECK(event_type IN (
                            'NORMAL', 'UNAUTHORIZED_ACCESS', 'SQL_INJECTION',
                            'RATE_LIMIT_EXCEEDED', 'REPEATED_FAILURE',
                            'RESTRICTED_ACCESS', 'DEADLOCK', 'SUSPICIOUS'
                        )),
            reason      TEXT
    """)

    conn.commit()
    print("[DATABASE] All tables created successfully.")
def seed_data():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM users")
    if cursor.fetchone()[0] > 0:
        print("[DATABASE] Seed data already exists. Skipping.")
        return

    users = [
        ("Alice", "customer"),
        ("Bob", "customer"),
        ("Charlie", "customer"),
        ("Admin", "admin"),
    ]
    cursor.executemany("INSERT INTO users (name, role) VALUES (?, ?)", users)

    accounts = [
        (1, "savings", 10000.0),
        (2, "savings", 10000.0),
        (3, "current", 10000.0),
        (4, "system",  50000.0),
    ]
    cursor.executemany(
        "INSERT INTO accounts (user_id, account_type, balance) VALUES (?, ?, ?)",
        accounts
    )

    conn.commit()
    print("[DATABASE] Seed data inserted successfully.")
    print("           Alice  (Account 1): Rs.10,000")
    print("           Bob    (Account 2): Rs.10,000")
    print("           Charlie(Account 3): Rs.10,000")
    print("           Admin  (Account 4): Rs.50,000 (restricted)")
    print("           Total: Rs.80,000")