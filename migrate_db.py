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
    
    if 'subscription_expiry' not in columns:
        print("Adding subscription_expiry column to users table...")
        cursor.execute("ALTER TABLE users ADD COLUMN subscription_expiry DATETIME;")
        conn.commit()

    # Check webhook_logs table
    cursor.execute("PRAGMA table_info(webhook_logs)")
    logs_columns = [col[1] for col in cursor.fetchall()]

    if 'message_id' not in logs_columns:
        print("Adding message_id column to webhook_logs...")
        cursor.execute("ALTER TABLE webhook_logs ADD COLUMN message_id VARCHAR;")
        conn.commit()

    # Check analyses table
    try:
        cursor.execute("PRAGMA table_info(analyses)")
        analyses_columns = [col[1] for col in cursor.fetchall()]
        if 'deadline_date' not in analyses_columns:
            print("Adding deadline_date to analyses...")
            cursor.execute("ALTER TABLE analyses ADD COLUMN deadline_date DATETIME;")
            conn.commit()
    except Exception:
        pass
        
    print("Database migration complete.")

except Exception as e:
    print(f"Error: {e}")
finally:
    if 'conn' in locals():
        conn.close()
