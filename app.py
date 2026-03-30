import os
import sys

from flask import Flask

# ── add sub-module roots to PYTHONPATH ──────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(BASE_DIR, "modules", "phishing"))
sys.path.insert(0, os.path.join(BASE_DIR, "modules", "xfake"))
sys.path.insert(0, os.path.join(BASE_DIR, "modules", "insta"))

from blueprints.insta_bp   import insta_bp
from blueprints.phishing_bp import phishing_bp
from blueprints.xfake_bp   import xfake_bp
from blueprints.home_bp    import home_bp

app = Flask(__name__, template_folder="templates", static_folder="static")
app.secret_key = "unified-detector-secret-2024"

app.register_blueprint(home_bp)
app.register_blueprint(insta_bp,    url_prefix="/instagram")
app.register_blueprint(phishing_bp, url_prefix="/phishing")
app.register_blueprint(xfake_bp,    url_prefix="/xfake")

if __name__ == "__main__":
    print("\n" + "="*60)
    print("  🛡️  Unified Threat Detector — running on http://127.0.0.1:5000")
    print("="*60 + "\n")
    app.run(debug=True, host="0.0.0.0", port=5000)
