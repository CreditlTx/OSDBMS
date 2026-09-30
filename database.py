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
        )
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
        )
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
        )
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
        )
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

def get_account_balance(account_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT balance FROM accounts WHERE id = ?", (account_id,))
    row = cursor.fetchone()
    return row["balance"] if row else None

def update_account_balance(account_id, new_balance):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "UPDATE accounts SET balance = ? WHERE id = ?",
            (new_balance, account_id)
        )
        return cursor.rowcount > 0
    except sqlite3.IntegrityError as e:
        print(f"[DATABASE] Integrity error: {e}")
        return False

def get_all_accounts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT a.id, a.user_id, u.name AS user_name, a.account_type, a.balance
        FROM accounts a
        JOIN users u ON a.user_id = u.id
        ORDER BY a.id
    """)
    return [dict(row) for row in cursor.fetchall()]

def get_all_users():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users ORDER BY id")
    return [dict(row) for row in cursor.fetchall()]

def record_transaction(txn_id, operation, source_acc_id=None, dest_acc_id=None,
                       amount=None, status="PENDING", details=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO transactions (txn_id, operation, source_acc_id, dest_acc_id,
                                  amount, status, details)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (txn_id, operation, source_acc_id, dest_acc_id, amount, status, details))
    conn.commit()

def update_transaction_status(txn_id, new_status):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE transactions SET status = ? WHERE txn_id = ?",
        (new_status, txn_id)
    )
    conn.commit()

def get_recent_transactions(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM transactions
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    return [dict(row) for row in cursor.fetchall()]
def log_security_event(user_id=None, txn_id=None, operation="", resource=None,
                       result="FLAGGED", event_type="SUSPICIOUS", reason=""):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO security_logs (user_id, txn_id, operation, resource,
                                   result, event_type, reason)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, txn_id, operation, resource, result, event_type, reason))
    conn.commit()

def get_security_logs(limit=30):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM security_logs
        ORDER BY id DESC
        LIMIT ?
    """, (limit,))
    return [dict(row) for row in cursor.fetchall()]

def reset_database():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS security_logs")
    cursor.execute("DROP TABLE IF EXISTS transactions")
    cursor.execute("DROP TABLE IF EXISTS accounts")
    cursor.execute("DROP TABLE IF EXISTS users")
    conn.commit()

    print("[DATABASE] All tables dropped.")

    create_tables()
    seed_data()
    print("[DATABASE] Database reset complete.")


def init_database():
    os.makedirs(DATABASE_DIR, exist_ok=True)

    create_tables()
    seed_data()


if __name__ == "__main__":
    
    print("=" * 60)
    print("DATABASE MODULE TEST")
    print("=" * 60)

    init_database()

    print("\n--- All Accounts ---")
    accounts = get_all_accounts()
    for acc in accounts:
        print(f"  Account {acc['id']}: {acc['user_name']} "
              f"({acc['account_type']}) - Rs.{acc['balance']:,.2f}")

    balance = get_account_balance(1)
    print(f"\nAlice's balance (Account 1): Rs.{balance:,.2f}")

    total = sum(acc["balance"] for acc in accounts)
    print(f"\nTotal money in system: Rs.{total:,.2f}")
    assert total == 80000.0, f"Expected Rs.80,000 but got Rs.{total:,.2f}"
    print("[OK] Conservation check passed!")

    close_connection()
    print("\n[TEST] Database module test completed successfully.")