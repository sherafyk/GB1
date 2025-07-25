"""Lightweight SQLite database helpers used by the application."""

import os
import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict

from passlib.hash import bcrypt

# Determine absolute path to the SQLite database. This avoids issues where the
# working directory differs from the application root (e.g. when running under
# Docker or tests).
BASE_DIR = Path(__file__).resolve().parent.parent
DB_PATH = os.getenv("DB_PATH", str(BASE_DIR / "app.db"))

# Ensure the directory for the database exists. When the DB_PATH is a file in a
# mounted volume (e.g. Docker), the parent directory may not exist at container
# start which would lead to "unable to open database file" errors. Creating the
# directory here allows SQLite to create the file automatically if it does not
# already exist.
db_file = Path(DB_PATH)
db_file.parent.mkdir(parents=True, exist_ok=True)

def init_db():
    """Create database tables if they do not already exist."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            data TEXT,
            report TEXT,
            score REAL
        )
        """
    )
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE,
            password_hash TEXT,
            role TEXT
        )
        """
    )
    conn.commit()
    conn.close()


def log_submission(data: dict, report: str, score: float) -> None:
    """Persist an analysis submission to the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO submissions (timestamp, data, report, score) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), json.dumps(data), report, score),
    )
    conn.commit()
    conn.close()


def create_user(username: str, password: str, role: str = "user") -> None:
    """Add a new user with ``username`` and ``role``."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
        (username, bcrypt.hash(password), role),
    )
    conn.commit()
    conn.close()


def get_user(username: str) -> Optional[Dict]:
    """Retrieve a user record or ``None`` if it doesn't exist."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT username, password_hash, role FROM users WHERE username = ?",
        (username,),
    )
    row = cur.fetchone()
    conn.close()
    if row:
        return {"username": row[0], "password_hash": row[1], "role": row[2]}
    return None


def list_users() -> List[Dict]:
    """Return all users ordered by username."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute("SELECT username, role FROM users ORDER BY username")
    rows = cur.fetchall()
    conn.close()
    return [{"username": r[0], "role": r[1]} for r in rows]


def delete_user(username: str) -> None:
    """Remove a user from the database."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("DELETE FROM users WHERE username = ?", (username,))
    conn.commit()
    conn.close()


def verify_user(username: str, password: str) -> Optional[Dict]:
    """Validate a username/password pair and return the user info on success."""
    user = get_user(username)
    if user and bcrypt.verify(password, user["password_hash"]):
        return {"username": user["username"], "role": user["role"]}
    return None


def get_logs(limit: int = 100) -> List[Dict]:
    """Return the ``limit`` most recent submission records."""
    conn = sqlite3.connect(DB_PATH)
    cur = conn.execute(
        "SELECT id, timestamp, score FROM submissions ORDER BY id DESC LIMIT ?",
        (limit,),
    )
    rows = cur.fetchall()
    conn.close()
    return [
        {"id": r[0], "timestamp": r[1], "score": r[2]} for r in rows
    ]


init_db()
