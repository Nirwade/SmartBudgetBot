import sqlite3
import pandas as pd
from pathlib import Path
from datetime import date, datetime, timedelta  # Added datetime & timedelta

DB_PATH = "smartbudget.db"

# ==================================================
# INITIALIZATION
# ==================================================
def ensure_table():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # 1. Expenses Table (Existing)
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

    # 2. Memory Facts Table (Existing)
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

    # 3. NEW: Reminders Table (For the "Passive Check")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            message TEXT,
            remind_at TEXT,
            created_at TEXT,
            status TEXT DEFAULT 'pending'
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

    # Default remaining_amount to amount if not provided
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
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, entity, remaining_amount, memory_type
        FROM memory_facts
        WHERE user_id = ?
          AND status = 'active'
          AND memory_type IN ('loan_given', 'loan_received')
    """, (user_id,))

    loans = [dict(row) for row in cur.fetchall()]
    conn.close()
    return loans


# ==================================================
# UPDATES & CLOSING
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


def get_loan_by_entity(user_id, entity_name):
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT id, entity, remaining_amount, amount
        FROM memory_facts
        WHERE user_id = ?
          AND memory_type IN ('loan_given', 'loan_received')
          AND status = 'active'
          AND lower(entity) = ?
        ORDER BY created_at ASC
        LIMIT 1
    """, (user_id, entity_name.lower()))

    row = cur.fetchone()
    conn.close()
    return dict(row) if row else None


# ==================================================
# NEW: PASSIVE REMINDERS
# ==================================================
def add_reminder(user_id, message, remind_at):
    """Stores a new reminder."""
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    created_at = datetime.now().isoformat()
    c.execute("INSERT INTO reminders (user_id, message, remind_at, created_at) VALUES (?, ?, ?, ?)",
              (user_id, message, remind_at, created_at))
    conn.commit()
    conn.close()

def get_due_reminders(user_id):
    """
    Checks if any reminders are due right now.
    Returns a list of formatted strings and marks them as 'sent'.
    """
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    now = datetime.now().isoformat()
    
    # Find pending reminders where time <= now
    c.execute("SELECT id, message, created_at FROM reminders WHERE user_id=? AND status='pending' AND remind_at <= ?", 
              (user_id, now))
    rows = c.fetchall()
    
    messages = []
    for r in rows:
        rem_id, msg, created_at_str = r
        # Calculate human-friendly "Time ago"
        try:
            created_dt = datetime.fromisoformat(created_at_str)
            delta = datetime.now() - created_dt
            
            if delta.days == 0:
                time_str = "earlier today"
            elif delta.days == 1:
                time_str = "yesterday"
            else:
                time_str = f"{delta.days} days ago"
                
            formatted_msg = f"🔔 **Reminder:** {time_str} you asked me to remind you: _{msg}_"
            messages.append(formatted_msg)
            
            # Mark as sent
            c.execute("UPDATE reminders SET status='sent' WHERE id=?", (rem_id,))
        except Exception as e:
            print(f"Error processing reminder {rem_id}: {e}")
            continue
            
    conn.commit()
    conn.close()
    return messages