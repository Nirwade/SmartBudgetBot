import sqlite3
import pandas as pd
from pathlib import Path
from datetime import date

DB_PATH = "smartbudget.db"


# ==================================================
# INITIALIZATION
# ==================================================
def ensure_table():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            date TEXT,
            category TEXT,
            amount REAL,
            note TEXT
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory_facts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            memory_type TEXT,
            entity TEXT,
            amount REAL,
            remaining_amount REAL,
            currency TEXT,
            event_date TEXT,
            due_date TEXT,
            description TEXT,
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closed_at TEXT
        );
    """)

    conn.commit()
    conn.close()


# ==================================================
# EXPENSES
# ==================================================
def add_expense(user_id, date_str, category, amount, note):
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO expenses (user_id, date, category, amount, note)
        VALUES (?, ?, ?, ?, ?)
        """,
        (user_id, date_str, category, float(amount), note)
    )

    conn.commit()
    conn.close()


def get_expenses(user_id):
    ensure_table()
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query(
        """
        SELECT id, date, category, amount, note
        FROM expenses
        WHERE user_id = ?
        ORDER BY date DESC
        """,
        conn,
        params=(user_id,)
    )

    conn.close()
    return df


# ==================================================
# MEMORY FACTS (LOW LEVEL)
# ==================================================
def add_memory_fact(
    user_id,
    memory_type,
    entity,
    amount,
    currency="USD",
    event_date=None,
    due_date=None,
    description=None
):
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO memory_facts (
            user_id,
            memory_type,
            entity,
            amount,
            remaining_amount,
            currency,
            event_date,
            due_date,
            description
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        user_id,
        memory_type,
        entity,
        amount,
        amount,
        currency,
        event_date,
        due_date,
        description
    ))

    conn.commit()
    conn.close()


def get_memory_facts(user_id, memory_type=None, active_only=False):
    """
    Core fetcher used by memory.py
    """
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = "SELECT * FROM memory_facts WHERE user_id = ?"
    params = [user_id]

    if memory_type:
        query += " AND memory_type = ?"
        params.append(memory_type)

    if active_only:
        query += " AND status = 'active'"

    cur.execute(query, params)
    rows = [dict(r) for r in cur.fetchall()]

    conn.close()
    return rows


# ==================================================
# LOANS (HIGH LEVEL)
# ==================================================
def get_active_loans(user_id):
    """
    Used by executor.py (pandas)
    """
    ensure_table()
    conn = sqlite3.connect(DB_PATH)

    df = pd.read_sql_query("""
        SELECT id, memory_type, entity, remaining_amount, currency, due_date
        FROM memory_facts
        WHERE user_id = ?
          AND status = 'active'
          AND memory_type IN ('loan_given', 'loan_received')
    """, conn, params=(user_id,))

    conn.close()
    return df


def get_active_loan_items(user_id):
    """
    Used by chat_engine + tests (list[dict])
    """
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, entity, remaining_amount
        FROM memory_facts
        WHERE user_id = ?
          AND status = 'active'
          AND memory_type IN ('loan_given', 'loan_received')
    """, (user_id,))

    loans = [dict(row) for row in cur.fetchall()]
    conn.close()
    return loans


# ==================================================
# UPDATES
# ==================================================
def close_memory_fact(memory_id):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE memory_facts
        SET status = 'closed',
            remaining_amount = 0,
            closed_at = ?
        WHERE id = ?
    """, (date.today().isoformat(), memory_id))

    conn.commit()
    conn.close()


def update_remaining(memory_id, new_amount):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        UPDATE memory_facts
        SET remaining_amount = ?
        WHERE id = ?
    """, (new_amount, memory_id))

    conn.commit()
    conn.close()



# ... existing imports ...

# SmartBudgetAI/db.py
# (Add this new function at the bottom)

def get_loan_by_entity(user_id, entity_name):
    """Find the oldest active loan for a specific person (case-insensitive)"""
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, entity, remaining_amount, amount
        FROM memory_facts
        WHERE user_id = ?
          AND memory_type = 'loan'
          AND status = 'active'
          AND lower(entity) = ?
        ORDER BY created_at ASC
        LIMIT 1
    """, (user_id, entity_name.lower()))

    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None