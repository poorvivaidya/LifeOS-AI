import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "lifeos.db")

def check_db():
    print(f"Connecting to database: {DB_PATH}")
    if not os.path.exists(DB_PATH):
        print("Database file does not exist yet.")
        return
        
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get table list
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = [t[0] for t in cursor.fetchall()]
    print("Tables in database:", tables)
    
    for table in tables:
        print(f"\n--- Table: {table} ---")
        cursor.execute(f"SELECT * FROM {table}")
        rows = cursor.fetchall()
        print(f"Total rows: {len(rows)}")
        for r in rows[:10]: # print first 10 rows
            print(r)
            
    conn.close()

if __name__ == "__main__":
    check_db()
