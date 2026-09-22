import os
import sqlite3
from pathlib import Path

import psycopg
from psycopg.rows import dict_row


BASE_DIR = Path(__file__).resolve().parent
SQLITE_DATABASE = BASE_DIR / "users.db"

DATABASE_URL = os.environ.get("DATABASE_URL")


# --------------------------------------------------
# PostgreSQL compatibility wrappers
# --------------------------------------------------

class PostgresCursor:
    def __init__(self, cursor):
        self.cursor = cursor

    def execute(self, query, params=None):
        # Convert SQLite ? placeholders to PostgreSQL %s
        query = query.replace("?", "%s")

        if params is None:
            self.cursor.execute(query)
        else:
            self.cursor.execute(query, params)

        return self

    def fetchone(self):
        return self.cursor.fetchone()

    def fetchall(self):
        return self.cursor.fetchall()

    @property
    def rowcount(self):
        return self.cursor.rowcount


class PostgresConnection:
    def __init__(self, connection):
        self.connection = connection

    def execute(self, query, params=None):
        cursor = self.connection.cursor()
        wrapper = PostgresCursor(cursor)
        return wrapper.execute(query, params)

    def cursor(self):
        return PostgresCursor(self.connection.cursor())

    def commit(self):
        self.connection.commit()

    def rollback(self):
        self.connection.rollback()

    def close(self):
        self.connection.close()


# --------------------------------------------------
# Database connection
# --------------------------------------------------

def create_connection():
    if DATABASE_URL:
        conn = psycopg.connect(
            DATABASE_URL,
            row_factory=dict_row
        )
        return PostgresConnection(conn)

    conn = sqlite3.connect(SQLITE_DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# --------------------------------------------------
# SQLite migration helpers
# --------------------------------------------------

def column_exists(cursor, table, column):
    return any(
        row[1] == column
        for row in cursor.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    )


def ensure_column(cursor, table, column, definition):
    if not column_exists(cursor, table, column):
        cursor.execute(
            f"ALTER TABLE {table} ADD COLUMN {column} {definition}"
        )


# --------------------------------------------------
# PostgreSQL tables
# --------------------------------------------------

def create_postgres_tables():
    conn = create_connection()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password BYTEA NOT NULL,
            is_blocked INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS driver_requests (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            license TEXT NOT NULL,
            vehicle TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,
            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id SERIAL PRIMARY KEY,
            user_id INTEGER NOT NULL,
            driver_id INTEGER,

            pickup_location TEXT NOT NULL,
            destination TEXT NOT NULL,

            passengers INTEGER NOT NULL DEFAULT 1,
            notes TEXT,

            status TEXT NOT NULL DEFAULT 'requested',
            fare DOUBLE PRECISION NOT NULL DEFAULT 85.00,

            payment_method TEXT NOT NULL DEFAULT 'cash',
            payment_status TEXT NOT NULL DEFAULT 'pending',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at TIMESTAMP,
            completed_at TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id),

            FOREIGN KEY (driver_id)
                REFERENCES users(id)
        )
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# SQLite tables
# --------------------------------------------------

def create_sqlite_tables():
    conn = create_connection()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password BLOB NOT NULL,
            is_blocked INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    ensure_column(
        c,
        "users",
        "is_blocked",
        "INTEGER NOT NULL DEFAULT 0"
    )

    ensure_column(
        c,
        "users",
        "created_at",
        "TIMESTAMP"
    )

    c.execute("""
        UPDATE users
        SET created_at = CURRENT_TIMESTAMP
        WHERE created_at IS NULL
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS driver_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            license TEXT NOT NULL,
            vehicle TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id)
                ON DELETE CASCADE
        )
    """)

    ensure_column(
        c,
        "driver_requests",
        "submitted_at",
        "TIMESTAMP"
    )

    ensure_column(
        c,
        "driver_requests",
        "reviewed_at",
        "TIMESTAMP"
    )

    c.execute("""
        UPDATE driver_requests
        SET
            status = LOWER(status),
            submitted_at = COALESCE(
                submitted_at,
                CURRENT_TIMESTAMP
            )
    """)

    c.execute("""
        CREATE TABLE IF NOT EXISTS rides (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            user_id INTEGER NOT NULL,
            driver_id INTEGER,

            pickup_location TEXT NOT NULL,
            destination TEXT NOT NULL,

            passengers INTEGER NOT NULL DEFAULT 1,
            notes TEXT,

            status TEXT NOT NULL DEFAULT 'requested',
            fare REAL NOT NULL DEFAULT 85.00,

            payment_method TEXT NOT NULL DEFAULT 'cash',
            payment_status TEXT NOT NULL DEFAULT 'pending',

            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accepted_at TIMESTAMP,
            completed_at TIMESTAMP,

            FOREIGN KEY(user_id)
                REFERENCES users(id),

            FOREIGN KEY(driver_id)
                REFERENCES users(id)
        )
    """)

    for col, definition in [
        ("driver_id", "INTEGER"),
        ("passengers", "INTEGER NOT NULL DEFAULT 1"),
        ("notes", "TEXT"),
        ("fare", "REAL NOT NULL DEFAULT 85.00"),
        (
            "payment_method",
            "TEXT NOT NULL DEFAULT 'cash'"
        ),
        (
            "payment_status",
            "TEXT NOT NULL DEFAULT 'pending'"
        ),
        ("accepted_at", "TIMESTAMP"),
        ("completed_at", "TIMESTAMP")
    ]:
        ensure_column(
            c,
            "rides",
            col,
            definition
        )

    c.execute("""
        UPDATE rides
        SET
            status = LOWER(status),
            payment_status = LOWER(payment_status)
    """)

    conn.commit()
    conn.close()


# --------------------------------------------------
# Initialise correct database
# --------------------------------------------------

def create_tables():
    if DATABASE_URL:
        create_postgres_tables()
    else:
        create_sqlite_tables()