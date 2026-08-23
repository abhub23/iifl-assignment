import json
import sqlite3
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS entries (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    original_text TEXT NOT NULL,
    summary       TEXT NOT NULL,
    tags          TEXT NOT NULL,
    created_at    TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


class EntryStore:
    """Thin wrapper around sqlite3.

    Tags are stored as a JSON array string and decoded on read, so the rest of
    the application only ever sees plain Python values.
    """

    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def init(self) -> None:
        with self._connect() as connection:
            connection.executescript(SCHEMA)

    def create(self, original_text: str, summary: str, tags: list[str]) -> dict:
        with self._connect() as connection:
            cursor = connection.execute(
                "INSERT INTO entries (original_text, summary, tags) VALUES (?, ?, ?)",
                (original_text, summary, json.dumps(tags)),
            )
            row_id = cursor.lastrowid
            row = connection.execute("SELECT * FROM entries WHERE id = ?", (row_id,)).fetchone()
        return self._to_entry(row)

    def list(self, limit: int = 100) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM entries ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._to_entry(row) for row in rows]

    def get(self, entry_id: int) -> dict | None:
        with self._connect() as connection:
            row = connection.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        return self._to_entry(row) if row is not None else None

    @staticmethod
    def _to_entry(row: sqlite3.Row) -> dict:
        return {
            "id": row["id"],
            "original_text": row["original_text"],
            "summary": row["summary"],
            "tags": json.loads(row["tags"]),
            "created_at": row["created_at"],
        }
