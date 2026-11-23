"""SQLite persistence for tickets, traces, conversations and chat messages."""
import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from config import settings


@contextmanager
def connect():
    path = Path(settings.database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def initialize_database():
    with connect() as conn:
        conn.execute("""CREATE TABLE IF NOT EXISTS tickets (
            ticket_id TEXT PRIMARY KEY, customer_id TEXT, issue TEXT, diagnosis TEXT,
            reason TEXT, status TEXT DEFAULT 'OPEN', created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS execution_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT, run_id TEXT, agent TEXT,
            event TEXT, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS conversations (
            conversation_id TEXT PRIMARY KEY, customer_id TEXT, state_json TEXT NOT NULL,
            status TEXT DEFAULT 'OPEN', attempts INTEGER DEFAULT 0,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )""")
        conn.execute("""CREATE TABLE IF NOT EXISTS conversation_messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT, conversation_id TEXT NOT NULL,
            role TEXT NOT NULL, content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(conversation_id) REFERENCES conversations(conversation_id)
        )""")
        conn.commit()


def save_log(run_id, agent, event, details):
    with connect() as conn:
        conn.execute("INSERT INTO execution_logs(run_id,agent,event,details) VALUES(?,?,?,?)",
                     (run_id, agent, event, json.dumps(details, default=str)))


def create_ticket(ticket):
    with connect() as conn:
        conn.execute("INSERT OR IGNORE INTO tickets(ticket_id,customer_id,issue,diagnosis,reason,status) VALUES(?,?,?,?,?,?)",
                     (ticket['ticket_id'], ticket.get('customer_id'), ticket.get('issue'),
                      ticket.get('diagnosis'), ticket.get('reason'), 'OPEN'))
    return ticket


def recent_tickets(limit=20):
    with connect() as conn:
        return [dict(r) for r in conn.execute("SELECT * FROM tickets ORDER BY created_at DESC LIMIT ?", (limit,)).fetchall()]


def save_conversation(conversation_id, state, status="OPEN", attempts=0):
    customer_id = state.get("customer_id")
    payload = json.dumps(state, default=str)
    with connect() as conn:
        conn.execute("""INSERT INTO conversations(conversation_id,customer_id,state_json,status,attempts)
            VALUES(?,?,?,?,?) ON CONFLICT(conversation_id) DO UPDATE SET
            customer_id=excluded.customer_id,state_json=excluded.state_json,status=excluded.status,
            attempts=excluded.attempts,updated_at=CURRENT_TIMESTAMP""",
            (conversation_id, customer_id, payload, status, attempts))


def load_conversation(conversation_id):
    with connect() as conn:
        row = conn.execute("SELECT * FROM conversations WHERE conversation_id=?", (conversation_id,)).fetchone()
    if not row:
        return None
    item = dict(row)
    item["state"] = json.loads(item.pop("state_json"))
    return item


def add_message(conversation_id, role, content):
    with connect() as conn:
        conn.execute("INSERT INTO conversation_messages(conversation_id,role,content) VALUES(?,?,?)",
                     (conversation_id, role, content))


def get_messages(conversation_id, limit=100):
    with connect() as conn:
        rows = conn.execute("SELECT role,content,created_at FROM conversation_messages WHERE conversation_id=? ORDER BY id LIMIT ?",
                            (conversation_id, limit)).fetchall()
    return [dict(row) for row in rows]
