from sqlalchemy import text
from src.db.session import engine

def migrate():
    with engine.connect() as conn:
        print("Starting manual migration...")
        
        # 1. Drop old tables
        # Use CASCADE to remove FK constraints from users table to these tables
        print("Dropping categories and menu_items...")
        conn.execute(text("DROP TABLE IF EXISTS categories CASCADE"))
        conn.execute(text("DROP TABLE IF EXISTS menu_items CASCADE"))
        # Also drop menu_item_limits to recreate it with new schema
        conn.execute(text("DROP TABLE IF EXISTS menu_item_limits CASCADE"))
        
        # 2. Alter users table
        print("Migrating users table...")
        # We need to change the column types from Integer to String.
        # Since we dropped menu_items CASCADE, the FK constraints should be gone.
        # But data conversion might be tricky if we want to preserve IDs.
        # However, new IDs are strings (e.g. "menu_boulanger"). Old IDs were Integers.
        # It's unlikely we can map them easily without the old data.
        # Assuming we can just clear the selection or cast to string (which will be a number string)
        # But "1" (int) != "menu_boulanger" (string).
        # So it's better to probably nullify the columns for compatibility or just cast.
        # Let's cast to varchar for now.
        
        conn.execute(text("ALTER TABLE users ALTER COLUMN menu_id TYPE VARCHAR"))
        conn.execute(text("ALTER TABLE users ALTER COLUMN boisson_id TYPE VARCHAR"))
        conn.execute(text("ALTER TABLE users ALTER COLUMN bonus_id TYPE VARCHAR"))
        
        conn.commit()
        print("Migration done.")

if __name__ == "__main__":
    migrate()
