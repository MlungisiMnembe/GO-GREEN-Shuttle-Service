import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "users.db"


def create_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def column_exists(cursor, table, column):
    return any(row[1] == column for row in cursor.execute(f"PRAGMA table_info({table})").fetchall())


def ensure_column(cursor, table, column, definition):
    if not column_exists(cursor, table, column):
        cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


def create_tables():
    conn = create_connection(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL, password BLOB NOT NULL,
        is_blocked INTEGER NOT NULL DEFAULT 0, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    ensure_column(c, 'users', 'is_blocked', 'INTEGER NOT NULL DEFAULT 0')
    ensure_column(c, 'users', 'created_at', 'TIMESTAMP')
    c.execute("UPDATE users SET created_at=CURRENT_TIMESTAMP WHERE created_at IS NULL")

    c.execute("""CREATE TABLE IF NOT EXISTS driver_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
        license TEXT NOT NULL, vehicle TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending',
        submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, reviewed_at TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)""")
    ensure_column(c, 'driver_requests', 'submitted_at', 'TIMESTAMP')
    ensure_column(c, 'driver_requests', 'reviewed_at', 'TIMESTAMP')
    c.execute("UPDATE driver_requests SET status=LOWER(status), submitted_at=COALESCE(submitted_at,CURRENT_TIMESTAMP)")

    c.execute("""CREATE TABLE IF NOT EXISTS rides (
        id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, driver_id INTEGER,
        pickup_location TEXT NOT NULL, destination TEXT NOT NULL,
        passengers INTEGER NOT NULL DEFAULT 1, notes TEXT,
        status TEXT NOT NULL DEFAULT 'requested', fare REAL NOT NULL DEFAULT 85.00,
        payment_method TEXT NOT NULL DEFAULT 'cash', payment_status TEXT NOT NULL DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP, accepted_at TIMESTAMP, completed_at TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id), FOREIGN KEY(driver_id) REFERENCES users(id))""")
    # Upgrade the original rides table safely.
    for col, definition in [
        ('driver_id','INTEGER'), ('passengers','INTEGER NOT NULL DEFAULT 1'), ('notes','TEXT'),
        ('fare','REAL NOT NULL DEFAULT 85.00'), ('payment_method',"TEXT NOT NULL DEFAULT 'cash'"),
        ('payment_status',"TEXT NOT NULL DEFAULT 'pending'"), ('accepted_at','TIMESTAMP'), ('completed_at','TIMESTAMP')]:
        ensure_column(c, 'rides', col, definition)
    # Original schema already has pickup_location, destination, status, created_at.
    c.execute("UPDATE rides SET status=LOWER(status), payment_status=LOWER(payment_status)")
    conn.commit(); conn.close()
