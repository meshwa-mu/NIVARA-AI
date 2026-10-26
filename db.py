"""SQLite storage for Nivara: every analysis and chat message is saved."""
import sqlite3
from dataclasses import asdict
from datetime import datetime

DB_PATH = "nivara.db"


def _conn():
    return sqlite3.connect(DB_PATH)


def init():
    with _conn() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS entries(
            id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, village TEXT, district TEXT,
            business TEXT, competition TEXT, capital REAL, project_cost REAL, loan REAL,
            scheme TEXT, emi REAL, surplus REAL, coverage REAL, verdict TEXT, session TEXT)""")
        try:  # upgrade older local databases
            c.execute("ALTER TABLE entries ADD COLUMN session TEXT")
        except sqlite3.OperationalError:
            pass
        c.execute("""CREATE TABLE IF NOT EXISTS chats(
            id INTEGER PRIMARY KEY AUTOINCREMENT, created TEXT, entry_id INTEGER,
            role TEXT, message TEXT, sources TEXT)""")


def save_entry(r, village, district, competition, session="") -> int:
    with _conn() as c:
        cur = c.execute(
            "INSERT INTO entries(created,village,district,business,competition,capital,project_cost,loan,"
            "scheme,emi,surplus,coverage,verdict,session) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
            (datetime.now().isoformat(timespec="seconds"), village, district, r.business, competition,
             r.capital, r.project_cost, r.loan, r.scheme, r.emi, r.surplus, r.coverage, r.verdict, session))
        return cur.lastrowid


def save_chat(entry_id, role, message, sources=""):
    with _conn() as c:
        c.execute("INSERT INTO chats(created,entry_id,role,message,sources) VALUES(?,?,?,?,?)",
                  (datetime.now().isoformat(timespec="seconds"), entry_id, role, message, sources))


def list_entries(session, limit=50):
    with _conn() as c:
        c.row_factory = sqlite3.Row
        return [dict(x) for x in c.execute("SELECT * FROM entries WHERE session=? ORDER BY id DESC LIMIT ?", (session, limit))]
