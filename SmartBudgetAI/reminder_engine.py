from datetime import date, timedelta
import sqlite3
from SmartBudgetAI.db import DB_PATH


# ==================================================
# DUE REMINDERS
# ==================================================
def get_due_reminders(user_id=1, days_ahead=7):
    today = date.today()
    upcoming_limit = today + timedelta(days=days_ahead)

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, entity, remaining_amount, currency, due_date, description
        FROM memory_facts
        WHERE user_id = ?
          AND status = 'active'
          AND remaining_amount > 0
          AND due_date IS NOT NULL
          AND due_date <= ?
        ORDER BY due_date ASC
    """, (user_id, upcoming_limit.isoformat()))

    rows = cur.fetchall()
    conn.close()

    reminders = []
    for r in rows:
        reminders.append({
            "id": r[0],
            "entity": r[1],
            "amount": r[2],
            "currency": r[3],
            "due_date": r[4],
            "description": r[5]
        })

    return reminders


def format_reminder_message(reminder):
    due = date.fromisoformat(reminder["due_date"])
    today = date.today()
    days_left = (due - today).days

    if days_left < 0:
        timing = "was due earlier"
    elif days_left == 0:
        timing = "is due today"
    elif days_left == 1:
        timing = "is due tomorrow"
    else:
        timing = f"is due in {days_left} days"

    return (
        f"🔔 Reminder: {reminder['entity']} still owes you "
        f"${reminder['amount']:.0f}. It {timing}."
    )


# ==================================================
# ACTIVE LOAN SUMMARY (AGGREGATED)
# ==================================================
def get_active_loans_summary(user_id=1):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT entity, SUM(remaining_amount)
        FROM memory_facts
        WHERE user_id = ?
          AND memory_type = 'loan'
          AND status = 'active'
          AND remaining_amount > 0
        GROUP BY entity
        ORDER BY SUM(remaining_amount) DESC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    summary = []
    total_amount = 0.0

    for entity, amount in rows:
        summary.append({
            "entity": entity,
            "amount": amount
        })
        total_amount += amount

    return summary, total_amount


# ==================================================
# INDIVIDUAL ACTIVE LOANS (FOR CLOSING)
# ==================================================
def get_active_loan_items(user_id=1):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute("""
        SELECT id, entity, remaining_amount, currency, due_date, description
        FROM memory_facts
        WHERE user_id = ?
          AND memory_type = 'loan'
          AND status = 'active'
          AND remaining_amount > 0
        ORDER BY created_at ASC
    """, (user_id,))

    rows = cur.fetchall()
    conn.close()

    loans = []
    for r in rows:
        loans.append({
            "id": r[0],
            "entity": r[1],
            "remaining_amount": r[2],
            "currency": r[3],
            "due_date": r[4],
            "description": r[5]
        })

    return loans
