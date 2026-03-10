import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'tenderbot.db')

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if column exists first
    cursor.execute("PRAGMA table_info(users)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if 'referred_by' not in columns:
        print("Adding referred_by column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN referred_by VARCHAR;")
        conn.commit()
        print("Successfully added referred_by column.")
    else:
        print("referred_by column already exists.")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
