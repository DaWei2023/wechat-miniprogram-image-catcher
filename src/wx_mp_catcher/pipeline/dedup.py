"""SHA256 去重与已处理文件索引."""

from __future__ import annotations

import hashlib
import sqlite3
import threading
from datetime import datetime
from pathlib import Path


class DedupStore:
    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._init_schema()

    def _init_schema(self) -> None:
        with self._lock:
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS content_hashes (
                    sha256 TEXT PRIMARY KEY,
                    saved_path TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
                """
            )
            self._conn.execute(
                """
                CREATE TABLE IF NOT EXISTS processed_files (
                    source_path TEXT PRIMARY KEY,
                    mtime REAL NOT NULL,
                    sha256 TEXT,
                    processed_at TEXT NOT NULL
                )
                """
            )
            self._conn.commit()

    @staticmethod
    def hash_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def is_duplicate_content(self, sha256: str) -> bool:
        with self._lock:
            row = self._conn.execute(
                "SELECT 1 FROM content_hashes WHERE sha256 = ?", (sha256,)
            ).fetchone()
        return row is not None

    def was_processed(self, path: Path, mtime: float) -> bool:
        key = str(path.resolve())
        with self._lock:
            row = self._conn.execute(
                "SELECT mtime FROM processed_files WHERE source_path = ?",
                (key,),
            ).fetchone()
        if not row:
            return False
        return abs(row[0] - mtime) < 0.001

    def record(
        self,
        source_path: Path,
        mtime: float,
        sha256: str,
        saved_path: Path,
    ) -> None:
        now = datetime.now().isoformat()
        key = str(source_path.resolve())
        with self._lock:
            self._conn.execute(
                """
                INSERT OR REPLACE INTO processed_files
                (source_path, mtime, sha256, processed_at)
                VALUES (?, ?, ?, ?)
                """,
                (key, mtime, sha256, now),
            )
            self._conn.execute(
                """
                INSERT OR IGNORE INTO content_hashes (sha256, saved_path, created_at)
                VALUES (?, ?, ?)
                """,
                (sha256, str(saved_path), now),
            )
            self._conn.commit()

    def count_saved(self) -> int:
        with self._lock:
            row = self._conn.execute("SELECT COUNT(*) FROM content_hashes").fetchone()
        return row[0] if row else 0

    def close(self) -> None:
        self._conn.close()
