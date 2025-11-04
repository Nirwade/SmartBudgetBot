import sqlite3
import pandas as pd


from pathlib import Path
from pathlib import Path

DB_PATH = Path(__file__).parent / "smartbudget.db"

def ensure_table():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
    CREATE TABLE IF NOT EXISTS expenses (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      date TEXT,
      category TEXT,
      amount REAL,
      note TEXT
    );
    """)
    conn.commit()
    conn.close()

def add_expense(date_str, category, amount, note):
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO expenses (date, category, amount, note) VALUES (?, ?, ?, ?)",
                (date_str, category, float(amount), note))
    conn.commit()
    conn.close()

def get_expenses():
    ensure_table()
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql_query("SELECT id, date, category, amount, note FROM expenses ORDER BY date DESC", conn)
    conn.close()
    return df