"""
worker.py — Background worker for file metadata processing & checksum validation.
"""

import hashlib
import json
import sqlite3
import time
from pathlib import Path


class StorageWorker:
    def __init__(self, db_path: Path | str, blob_store_dir: Path | str):
        self.db_path = str(db_path)
        self.blob_store_dir = Path(blob_store_dir)
        self.blob_store_dir.mkdir(parents=True, exist_ok=True)

    def process_file_blob(self, file_id: str, content_bytes: bytes) -> dict:
        """Process an uploaded blob: compute SHA-256, store CAS blob, and update DB."""
        checksum = hashlib.sha256(content_bytes).hexdigest()
        blob_path = self.blob_store_dir / checksum[:2] / checksum[2:4] / checksum
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        blob_path.write_bytes(content_bytes)

        # Update file in DB
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                UPDATE files
                SET checksum_sha256 = ?, storage_path = ?, status = 'READY'
                WHERE file_id = ?
                """,
                (checksum, str(blob_path), file_id)
            )
            # Create completed async task record
            task_id = f"task_{checksum[:12]}"
            payload = json.dumps({
                "checksum": checksum,
                "size_bytes": len(content_bytes),
                "thumbnail_ref": f"thumb_{checksum[:16]}"
            })
            cursor.execute(
                """
                INSERT INTO async_tasks (task_id, file_id, action, status, result_payload, created_at, completed_at)
                VALUES (?, ?, 'PROCESS_THUMBNAIL', 'COMPLETED', ?, ?, ?)
                """,
                (task_id, file_id, payload, int(time.time()), int(time.time()))
            )
            conn.commit()
            return {
                "file_id": file_id,
                "checksum": checksum,
                "storage_path": str(blob_path),
                "status": "READY"
            }
        finally:
            conn.close()
