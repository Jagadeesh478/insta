import os, sqlite3
from datetime import datetime
from flask import Blueprint, render_template, request, g

import sys
PHISHING_DIR = os.path.join(os.path.dirname(__file__), "..", "modules", "phishing")
sys.path.insert(0, PHISHING_DIR)

from detector import analyze

phishing_bp = Blueprint("phishing", __name__,
                        template_folder="../templates",
                        static_folder="../static")

DB_PATH = os.path.join(PHISHING_DIR, "phish_logs.sqlite3")
os.makedirs(PHISHING_DIR, exist_ok=True)

def _get_db():
    db = getattr(g, "_phish_db", None)
    if db is None:
        db = g._phish_db = sqlite3.connect(DB_PATH)
        db.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                url TEXT, verdict TEXT, score REAL, safe_percent REAL,
                http_status INTEGER, domain_exists INTEGER, online INTEGER,
                tls_valid INTEGER, title TEXT, created_at TEXT
            )
        """)
        db.commit()
    return db

@phishing_bp.teardown_app_request
def _close_db(exc):
    db = getattr(g, "_phish_db", None)
    if db:
        db.close()

@phishing_bp.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if url:
            result = analyze(url)
            db = _get_db()
            db.execute("""
                INSERT INTO logs (url,verdict,score,safe_percent,http_status,
                                  domain_exists,online,tls_valid,title,created_at)
                VALUES (?,?,?,?,?,?,?,?,?,?)
            """, (
                result["url"], result["verdict"], result["score"],
                result["safe_percent"], result["http_status"],
                int(result["domain_exists"]), int(result["online"]),
                int(result["tls"].get("valid", False)), result["title"],
                datetime.utcnow().isoformat(),
            ))
            db.commit()
    return render_template("phishing.html", result=result)

@phishing_bp.route("/history")
def history():
    db = _get_db()
    rows = db.execute("SELECT * FROM logs ORDER BY id DESC LIMIT 200").fetchall()
    return render_template("phishing_history.html", rows=rows)
