import sqlite3, os, json, time

DB_PATH = os.getenv("CLAUSELENS_DB", "clauselens.db")

def _conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    con = _conn()
    cur = con.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS analyses(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      created_at INTEGER,
      doc_sig TEXT,
      file_name TEXT,
      persona TEXT,
      lang TEXT,
      sections_json TEXT,
      flags_json TEXT,
      summary TEXT
    )
    """)
    con.commit()
    con.close()

def save_analysis(doc_sig, file_name, persona, lang, sections, flags, summary):
    con = _conn()
    cur = con.cursor()
    cur.execute("""
      INSERT INTO analyses(created_at, doc_sig, file_name, persona, lang, sections_json, flags_json, summary)
      VALUES(?,?,?,?,?,?,?,?)
    """, (int(time.time()), doc_sig, file_name, persona, lang, json.dumps(sections), json.dumps(flags), summary))
    con.commit()
    con.close()

def clear_all():
    con = _conn()
    cur = con.cursor()
    cur.execute("DELETE FROM analyses")
    con.commit()
    con.close()

def list_recent(limit=25):
    con = _conn()
    cur = con.cursor()
    cur.execute("SELECT id, created_at, file_name, persona, lang FROM analyses ORDER BY id DESC LIMIT ?", (limit,))
    rows = cur.fetchall()
    con.close()
    return rows
