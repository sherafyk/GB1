import sqlite3
import json
from datetime import datetime

DB_PATH = "app.db"

def init_db():
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
    conn.commit()
    conn.close()


def log_submission(data: dict, report: str, score: float) -> None:
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO submissions (timestamp, data, report, score) VALUES (?, ?, ?, ?)",
        (datetime.utcnow().isoformat(), json.dumps(data), report, score),
    )
    conn.commit()
    conn.close()


init_db()
