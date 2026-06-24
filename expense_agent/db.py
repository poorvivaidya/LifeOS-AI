import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lifeos.db")

def init_db():
    """Initializes the SQLite database with tables for LifeOS AI."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create goals table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS goals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        goal_text TEXT NOT NULL,
        roadmap TEXT,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create schedule table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS schedule (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_name TEXT NOT NULL,
        time_block TEXT NOT NULL,
        priority TEXT NOT NULL,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create habits table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS habits (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        habit_name TEXT NOT NULL,
        streak INTEGER DEFAULT 0,
        risk_level TEXT DEFAULT 'Low',
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create learning table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS learning (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        skill_gap TEXT NOT NULL,
        resource_name TEXT NOT NULL,
        activity_type TEXT NOT NULL,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create accountability table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS accountability (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        progress_status TEXT NOT NULL,
        missed_milestones TEXT,
        recovery_plan TEXT,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    # Create reflections table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS reflections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        review_period TEXT NOT NULL,
        performance_summary TEXT NOT NULL,
        insights TEXT,
        date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()

def execute_query(query: str, params: tuple = ()) -> list:
    """Executes a query and returns results."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(query, params)
    res = cursor.fetchall()
    conn.commit()
    conn.close()
    return res

# Initialize database on module load
init_db()
