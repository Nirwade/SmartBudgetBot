# SmartBudgetAI/conftest.py
import pytest
import sqlite3
from SmartBudgetAI.db import DB_PATH, ensure_table

@pytest.fixture(autouse=True)
def reset_system():
    # 1. Reset Session Context
    from SmartBudgetAI.chat_engine import SESSION_CONTEXT
    SESSION_CONTEXT.clear()
    
    # 2. Reset Database (Truncate tables)
    ensure_table() # Ensure DB exists first
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM expenses")
    cursor.execute("DELETE FROM memory_facts")
    # Reset auto-increment counters so IDs start at 1
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='expenses'")
    cursor.execute("DELETE FROM sqlite_sequence WHERE name='memory_facts'")
    conn.commit()
    conn.close()
    
    yield
    
    SESSION_CONTEXT.clear()