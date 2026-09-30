"""
db_migrations.py — Real SQL Schema Migrations for PolyFlow Cloud Drive.
"""

import sqlite3
from pathlib import Path

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'user',
    created_at INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    file_id TEXT PRIMARY KEY,
    owner_id TEXT NOT NULL,
    name TEXT NOT NULL,
    size_bytes INTEGER NOT NULL,
    mime_type TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    checksum_sha256 TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'PENDING_PROCESSING',
    created_at INTEGER NOT NULL,
    FOREIGN KEY(owner_id) REFERENCES users(user_id)
);

CREATE TABLE IF NOT EXISTS shares (
    share_id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    granter_id TEXT NOT NULL,
    grantee_email TEXT NOT NULL,
    permission TEXT NOT NULL DEFAULT 'READ',
    is_public_link INTEGER NOT NULL DEFAULT 0,
    expires_at INTEGER NOT NULL,
    FOREIGN KEY(file_id) REFERENCES files(file_id)
);

CREATE TABLE IF NOT EXISTS async_tasks (
    task_id TEXT PRIMARY KEY,
    file_id TEXT NOT NULL,
    action TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'QUEUED',
    result_payload TEXT,
    created_at INTEGER NOT NULL,
    completed_at INTEGER
);
"""


def apply_migrations(db_path: Path | str) -> None:
    conn = sqlite3.connect(str(db_path))
    try:
        cursor = conn.cursor()
        cursor.executescript(SCHEMA_SQL)
        conn.commit()
    finally:
        conn.close()


if __name__ == "__main__":
    db_file = Path(__file__).parent / "cloud_drive.db"
    apply_migrations(db_file)
    print(f"[OK] Migrations applied successfully to {db_file}")
