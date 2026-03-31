import os, sys, json, sqlite3
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify, g

# ── add insta backend to path ──────────────────────────────────────────────
INSTA_DIR = os.path.join(os.path.dirname(__file__), "..", "modules", "insta")
sys.path.insert(0, INSTA_DIR)

from risk_engine import calculate_risk_score, get_risk_reasons

insta_bp = Blueprint("insta", __name__,
                     template_folder="../templates",
                     static_folder="../static")

# ── Database (Use /tmp on Vercel for write access) ─────────────────────────
IS_VERCEL = os.environ.get("VERCEL") == "1"
if IS_VERCEL:
    DB_PATH = "/tmp/insta_history.db"
else:
    DB_PATH = os.path.join(INSTA_DIR, "insta_history.db")
    os.makedirs(INSTA_DIR, exist_ok=True)

def _get_db():
    db = getattr(g, "_insta_db", None)
    if db is None:
        db = g._insta_db = sqlite3.connect(DB_PATH)
        db.execute("""
            CREATE TABLE IF NOT EXISTS analyses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT, risk_score INTEGER, risk_level TEXT,
                confidence INTEGER, confidence_label TEXT,
                reasons TEXT, recommendations TEXT,
                timestamp TEXT, created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.commit()
    return db

@insta_bp.teardown_app_request
def _close_db(exc):
    db = getattr(g, "_insta_db", None)
    if db:
        db.close()

# ── helpers ────────────────────────────────────────────────────────────────
def _recommendations(risk_level, reasons):
    recs = []
    if risk_level == "High Risk":
        recs += ["⚠️ DO NOT interact or click any links",
                 "🚫 Block this account immediately",
                 "📢 Report to Instagram for suspicious activity",
                 "🔒 Never share personal or payment details"]
    elif risk_level == "Moderate Risk":
        recs += ["⚡ Exercise extreme caution",
                 "🔍 Verify authenticity via official channels",
                 "❌ Avoid clicking bio/message links",
                 "👥 Check if mutual friends follow this account"]
    else:
        recs += ["✅ Account appears relatively safe",
                 "🛡️ Still verify identity before sharing sensitive info",
                 "📱 Be cautious of unsolicited messages"]

    if any("profile picture" in r.lower() for r in reasons):
        recs.append("🖼️ Missing profile picture is a common scam indicator")
    if any("external link" in r.lower() for r in reasons):
        recs.append("🔗 Never click suspicious links — may be phishing attempts")
    if any("follower" in r.lower() for r in reasons):
        recs.append("📊 Unusual follower patterns suggest automated/fake account")
    return recs

# ── Routes ─────────────────────────────────────────────────────────────────
@insta_bp.route("/")
def index():
    return render_template("insta.html")

@insta_bp.route("/analyze", methods=["POST"])
def analyze():
    data = request.get_json(silent=True) or {}
    username = data.get("username", "").strip()
    if not username:
        return jsonify({"error": "Username is required"}), 400

    # ── Simulate Live Fetching if data is missing ───────────────────────────
    # If all fields are missing, we simulate a "Live Fetch" for the demo
    has_any_manual = any(data.get(k) is not None for k in ["followers", "following", "posts", "account_age_days", "has_profile_pic"])
    is_live_fetch = data.get("is_live_fetch", False) or not has_any_manual

    if is_live_fetch:
        import random, zlib
        # Seed the random number generator with the username for consistent mock results per username
        seed = zlib.adler32(username.encode())
        random.seed(seed)

        # Heuristics: if username looks like a scammer name, give it scammer stats
        scam_leads = ["official", "verify", "support", "help", "claim", "prize", "winner", "reward", "meta"]
        is_scam_pattern = any(x in username.lower() for x in scam_leads)

        
        if is_scam_pattern:
            followers = random.randint(10, 80)
            following = random.randint(1500, 4500)
            posts     = random.randint(0, 3)
            age       = random.randint(2, 25)
            verified  = False
            pic       = "no" if random.random() > 0.4 else "suspicious"
            bio_links = "suspicious"
            dm_act    = "suspicious"
            bio_text  = "DM for prize claim! 🎁 Click link below to verify identity."
        else:
            # Looks like a normal user
            followers = random.randint(200, 1500)
            following = random.randint(150, 800)
            posts     = random.randint(50, 300)
            age       = random.randint(300, 2000)
            verified  = random.random() < 0.1
            pic       = "yes"
            bio_links = "none"
            dm_act    = "normal"
            bio_text  = "Living life one photo at a time. ✨"

        account = {
            "username":        username,
            "followers":       followers,
            "following":       following,
            "posts":           posts,
            "account_age_days":age,
            "verified":        verified,
            "visibility":      "public",
            "has_profile_pic": pic,
            "bio_text":        bio_text,
            "bio_links":       bio_links,
            "dm_activity":     dm_act,
            "is_simulated":    True
        }
    else:
        account = {
            "username":        username,
            "followers":       data.get("followers"),
            "following":       data.get("following"),
            "posts":           data.get("posts"),
            "account_age_days":data.get("account_age_days"),
            "verified":        data.get("verified"),
            "visibility":      data.get("visibility", "public"),
            "has_profile_pic": data.get("has_profile_pic"),
            "bio_text":        data.get("bio_text", ""),
            "bio_links":       data.get("bio_links"),
            "dm_activity":     data.get("dm_activity"),
            "is_simulated":    False
        }

    risk_data = calculate_risk_score(account)
    reasons   = get_risk_reasons(account, risk_data)
    recs      = _recommendations(risk_data["risk_level"], reasons)

    result = {
        "username":        username,
        "risk_score":      risk_data["risk_score"],
        "risk_level":      risk_data["risk_level"],
        "confidence":      risk_data["confidence"],
        "confidence_label":risk_data["confidence_label"],
        "reasons":         reasons,
        "recommendations": recs,
        "details":         account if account.get("is_simulated") else None,
        "timestamp":       datetime.now().isoformat(),
    }

    db = _get_db()
    db.execute("""
        INSERT INTO analyses
        (username,risk_score,risk_level,confidence,confidence_label,reasons,recommendations,timestamp)
        VALUES (?,?,?,?,?,?,?,?)
    """, (
        result["username"], result["risk_score"], result["risk_level"],
        result["confidence"], result["confidence_label"],
        json.dumps(result["reasons"]), json.dumps(result["recommendations"]),
        result["timestamp"],
    ))
    db.commit()

    return jsonify(result)

@insta_bp.route("/history")
def history():
    db = _get_db()
    rows = db.execute(
        "SELECT username,risk_score,risk_level,confidence,confidence_label,timestamp "
        "FROM analyses ORDER BY id DESC LIMIT 50"
    ).fetchall()
    return render_template("insta_history.html", rows=rows)
