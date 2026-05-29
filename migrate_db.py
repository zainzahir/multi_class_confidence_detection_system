import os
import sqlite3

def migrate():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'instance', 'confidence_detector.db')
    
    if not os.path.exists(db_path):
        print(f"[INFO] Database file not found at {db_path}. It will be created automatically on run.")
        return
        
    print(f"[INFO] Found database at {db_path}. Checking columns...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get columns of the users table
    cursor.execute("PRAGMA table_info(users)")
    columns = [row[1] for row in cursor.fetchall()]
    
    # Check reset_token column
    if 'reset_token' not in columns:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token VARCHAR(100)")
            conn.commit()
            print("[SUCCESS] Added column 'reset_token' to 'users' table.")
        except Exception as e:
            print(f"[ERROR] Failed to add 'reset_token': {str(e)}")
    else:
        print("[INFO] Column 'reset_token' already exists.")
        
    # Check reset_token_expiry column
    if 'reset_token_expiry' not in columns:
        try:
            cursor.execute("ALTER TABLE users ADD COLUMN reset_token_expiry DATETIME")
            conn.commit()
            print("[SUCCESS] Added column 'reset_token_expiry' to 'users' table.")
        except Exception as e:
            print(f"[ERROR] Failed to add 'reset_token_expiry': {str(e)}")
    else:
        print("[INFO] Column 'reset_token_expiry' already exists.")
        
    conn.close()
    print("[INFO] Migration complete.")

if __name__ == '__main__':
    migrate()
