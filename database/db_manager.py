"""
SQLite access layer.

Golden rule: only metadata and COUNTS go into the database.
Raw PII values (actual emails, names, etc.) are NEVER stored —
only categories and how many were found.

This protects privacy and is what the audit trail relies on.
"""
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone

import config


# ---- Schema ----------------------------------------------------------
# Written as a single string so we can execute it in one call.
SCHEMA = """
CREATE TABLE IF NOT EXISTS documents (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    filename_hash  TEXT NOT NULL,       -- sha256 of file contents (for dedupe)
    original_name  TEXT NOT NULL,
    file_type      TEXT NOT NULL,
    size_bytes     INTEGER,
    uploaded_at    TEXT NOT NULL,
    status         TEXT DEFAULT 'uploaded'
);

CREATE TABLE IF NOT EXISTS pii_findings (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id  INTEGER NOT NULL,
    category     TEXT NOT NULL,
    count        INTEGER NOT NULL,
    source       TEXT,                  -- 'regex', 'ner', or 'hybrid'
    detected_at  TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS redactions (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    document_id   INTEGER NOT NULL,
    strategy      TEXT NOT NULL,        -- 'mask' or 'redact'
    redacted_path TEXT,
    created_at    TEXT NOT NULL,
    FOREIGN KEY(document_id) REFERENCES documents(id)
);

CREATE TABLE IF NOT EXISTS qa_results (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    run_at      TEXT NOT NULL,
    precision   REAL,
    recall      REAL,
    f1          REAL,
    tp          INTEGER,
    fp          INTEGER,
    fn          INTEGER,
    report_path TEXT
);

CREATE TABLE IF NOT EXISTS audit_logs (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp     TEXT NOT NULL,
    action        TEXT NOT NULL,
    document_hash TEXT,
    actor         TEXT,
    details       TEXT
);
"""


# ---- Helpers ---------------------------------------------------------
def _now() -> str:
    """ISO timestamp in UTC. Using UTC avoids timezone bugs."""
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def get_conn():
    """
    Context manager for database connections.

    Why a context manager? It guarantees the connection closes
    even if an error happens. Forgetting to close connections
    is the #1 cause of "database is locked" bugs.
    """
    conn = sqlite3.connect(config.DB_PATH)
    conn.row_factory = sqlite3.Row   # lets us access columns by name: row["id"]
    try:
        yield conn
        conn.commit()                # only commit on success
    except Exception:
        conn.rollback()              # undo partial changes on error
        raise
    finally:
        conn.close()


# ---- Initialization --------------------------------------------------
def init_db() -> None:
    """Create all tables. Safe to call on every app start."""
    with get_conn() as conn:
        conn.executescript(SCHEMA)


# ---- Documents -------------------------------------------------------
def add_document(filename_hash: str, original_name: str,
                 file_type: str, size_bytes: int) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO documents "
            "(filename_hash, original_name, file_type, size_bytes, uploaded_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (filename_hash, original_name, file_type, size_bytes, _now()),
        )
        return cur.lastrowid


def list_documents():
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM documents ORDER BY uploaded_at DESC"
        ).fetchall()


# ---- PII findings ----------------------------------------------------
def add_pii_findings(document_id: int, findings: dict, source: str = "hybrid") -> None:
    """
    findings is a dict like {"EMAIL": 3, "PHONE": 1}.
    We store only the COUNT per category — never the actual values.
    """
    with get_conn() as conn:
        for category, count in findings.items():
            if count <= 0:
                continue
            conn.execute(
                "INSERT INTO pii_findings "
                "(document_id, category, count, source, detected_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (document_id, category, count, source, _now()),
            )


def get_pii_totals():
    """Return {category: total_count} across all documents."""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT category, SUM(count) AS total "
            "FROM pii_findings GROUP BY category"
        ).fetchall()
        return {row["category"]: row["total"] for row in rows}


# ---- Redactions ------------------------------------------------------
def add_redaction(document_id: int, strategy: str, redacted_path: str) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO redactions "
            "(document_id, strategy, redacted_path, created_at) "
            "VALUES (?, ?, ?, ?)",
            (document_id, strategy, redacted_path, _now()),
        )


# ---- QA results ------------------------------------------------------
def add_qa_result(precision, recall, f1, tp, fp, fn, report_path=None) -> None:
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO qa_results "
            "(run_at, precision, recall, f1, tp, fp, fn, report_path) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (_now(), precision, recall, f1, tp, fp, fn, report_path),
        )


# ---- Audit logs ------------------------------------------------------
def log_event(action: str, document_hash: str = None,
              actor: str = "system", details: str = None) -> None:
    """
    Record what happened. NEVER put raw PII in `details`.
    Use document_hash, category counts, or other non-sensitive info.
    """
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO audit_logs "
            "(timestamp, action, document_hash, actor, details) "
            "VALUES (?, ?, ?, ?, ?)",
            (_now(), action, document_hash, actor, details),
        )


def get_audit_logs(limit: int = 200):
    with get_conn() as conn:
        return conn.execute(
            "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()


# ---- Dashboard aggregates --------------------------------------------
def dashboard_counts() -> dict:
    """
    One query bundle for the Home dashboard.
    All values come from the DB — nothing is hardcoded.
    """
    with get_conn() as conn:
        documents = conn.execute("SELECT COUNT(*) AS n FROM documents").fetchone()["n"]
        pii_instances = conn.execute(
            "SELECT COALESCE(SUM(count), 0) AS n FROM pii_findings"
        ).fetchone()["n"]
        redactions = conn.execute("SELECT COUNT(*) AS n FROM redactions").fetchone()["n"]
        qa_runs = conn.execute("SELECT COUNT(*) AS n FROM qa_results").fetchone()["n"]
    return {
        "documents": documents,
        "pii_instances": pii_instances,
        "redactions": redactions,
        "qa_runs": qa_runs,
    }