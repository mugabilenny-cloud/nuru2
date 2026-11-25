"""SQLite storage for Nuru (listings, users, applications)."""
import hashlib, hmac, os, secrets, sqlite3, uuid
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
import pandas as pd

BASE = Path(__file__).parent
DB_PATH = Path(os.environ.get("NURU_DB", BASE / "data" / "nuru.db"))
SEED_FILE = BASE / "data" / "hub_repo.xlsx"

SCHEMA = """
CREATE TABLE IF NOT EXISTS listings(
  id INTEGER PRIMARY KEY AUTOINCREMENT, kind TEXT, title TEXT NOT NULL, company TEXT,
  category TEXT, job_type TEXT, work_mode TEXT, location TEXT,
  salary_min REAL, salary_max REAL, currency TEXT, deadline TEXT,
  description TEXT, url TEXT, apply_email TEXT, status TEXT DEFAULT 'active',
  source TEXT, owner_email TEXT, created_at TEXT, dedupe_key TEXT UNIQUE);
CREATE TABLE IF NOT EXISTS users(
  email TEXT PRIMARY KEY, name TEXT, phone TEXT, pw_hash TEXT, salt TEXT, role TEXT, created_at TEXT);
CREATE TABLE IF NOT EXISTS applications(
  id INTEGER PRIMARY KEY AUTOINCREMENT, listing_id INTEGER, name TEXT, email TEXT,
  phone TEXT, message TEXT, created_at TEXT);
"""
COLS = ["kind", "title", "company", "category", "job_type", "work_mode", "location", "salary_min",
        "salary_max", "currency", "deadline", "description", "url", "apply_email"]


@contextmanager
def conn():
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    try:
        yield c
        c.commit()
    finally:
        c.close()


def now():
    return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")


def init():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with conn() as c:
        c.executescript(SCHEMA)
        n = c.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
    if n == 0 and SEED_FILE.exists():
        import importer
        bulk_add(importer.parse_dataframe(pd.read_excel(SEED_FILE)), source="excel", owner="")


# ---------- listings ----------
def _key(d, source):
    if d.get("url"):
        return "url:" + d["url"].strip().lower()
    return "t:" + "|".join([d.get("title", "").lower(), d.get("company", "").lower(), source])


def add_listing(d, source="form", owner="", key=None):
    key = key or _key(d, source)
    vals = [d.get(k) for k in COLS]
    with conn() as c:
        try:
            c.execute(f"INSERT INTO listings({','.join(COLS)},status,source,owner_email,created_at,dedupe_key) "
                      f"VALUES({','.join('?'*len(COLS))},'active',?,?,?,?)",
                      vals + [source, owner, now(), key])
            return True
        except sqlite3.IntegrityError:
            return False


def post_job(d, owner):
    return add_listing(d, source="form", owner=owner, key="form:" + uuid.uuid4().hex)


def bulk_add(items, source="excel", owner=""):
    added = sum(add_listing(d, source, owner) for d in items)
    return added, len(items) - added


def listings_df(owner=None):
    q = ("SELECT l.*, (SELECT COUNT(*) FROM applications a WHERE a.listing_id=l.id) AS applicants "
         "FROM listings l")
    args = []
    if owner:
        q += " WHERE owner_email=?"
        args.append(owner)
    q += " ORDER BY created_at DESC, id ASC"
    with conn() as c:
        return pd.read_sql_query(q, c, params=args)


def get_listing(lid):
    with conn() as c:
        r = c.execute("SELECT * FROM listings WHERE id=?", (lid,)).fetchone()
    return dict(r) if r else None


def set_status(lid, status):
    with conn() as c:
        c.execute("UPDATE listings SET status=? WHERE id=?", (status, lid))


def delete_listing(lid):
    with conn() as c:
        c.execute("DELETE FROM applications WHERE listing_id=?", (lid,))
        c.execute("DELETE FROM listings WHERE id=?", (lid,))


# ---------- applications ----------
def add_application(lid, name, email, phone, message):
    with conn() as c:
        c.execute("INSERT INTO applications(listing_id,name,email,phone,message,created_at) VALUES(?,?,?,?,?,?)",
                  (lid, name, email, phone, message, now()))


def applications_df(owner=None):
    q = ("SELECT a.id, a.created_at, l.title AS job, l.company, a.name, a.email, a.phone, a.message "
         "FROM applications a JOIN listings l ON l.id=a.listing_id")
    args = []
    if owner:
        q += " WHERE l.owner_email=?"
        args.append(owner)
    q += " ORDER BY a.created_at DESC"
    with conn() as c:
        return pd.read_sql_query(q, c, params=args)


# ---------- users ----------
def _hash(pw, salt):
    return hashlib.pbkdf2_hmac("sha256", pw.encode(), bytes.fromhex(salt), 200_000).hex()


def create_user(email, name, phone, pw, role):
    email = email.strip().lower()
    salt = secrets.token_hex(16)
    with conn() as c:
        try:
            c.execute("INSERT INTO users VALUES(?,?,?,?,?,?,?)",
                      (email, name.strip(), phone.strip(), _hash(pw, salt), salt, role, now()))
            return True
        except sqlite3.IntegrityError:
            return False


def verify_user(email, pw):
    with conn() as c:
        r = c.execute("SELECT * FROM users WHERE email=?", (email.strip().lower(),)).fetchone()
    if r and hmac.compare_digest(r["pw_hash"], _hash(pw, r["salt"])):
        return dict(r)
    return None


def set_role(email, role):
    with conn() as c:
        c.execute("UPDATE users SET role=? WHERE email=?", (role, email))
