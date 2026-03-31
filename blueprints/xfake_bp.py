import os, sys
from flask import Blueprint, render_template, request, jsonify

XFAKE_DIR = os.path.join(os.path.dirname(__file__), "..", "modules", "xfake")
sys.path.insert(0, XFAKE_DIR)

from utils.twitter_client import TwitterClient
from utils.detector import FakeAccountDetector

xfake_bp = Blueprint("xfake", __name__,
                     template_folder="../templates",
                     static_folder="../static")

try:
    twitter_client = TwitterClient()
    detector       = FakeAccountDetector()
    _twitter_ready = True
except Exception as e:
    _twitter_ready = False
    _twitter_error = str(e)

@xfake_bp.route("/")
def index():
    return render_template("xfake.html")

@xfake_bp.route("/analyze", methods=["POST"])
def analyze():
    if not _twitter_ready:
        return jsonify({"error": f"Twitter API not configured: {_twitter_error}", "result": None})

    username = request.form.get("username", "").strip()
    if not username:
        return jsonify({"error": "Please enter a username", "result": None})

    profile_data = twitter_client.get_user_profile(username)
    if "error" in profile_data:
        return jsonify({"error": profile_data["error"], "result": None})

    features = detector.extract_features(profile_data)
    result, score, signals = detector.rule_based_detection(features)

    return jsonify({
        "error": None,
        "result": {
            "username":          profile_data["username"],
            "name":              profile_data["name"],
            "classification":    result,
            "suspicion_score":   round(score * 100, 1),
            "suspicious_signals": signals,
            "profile_stats": {
                "followers":      profile_data["followers_count"],
                "following":      profile_data["following_count"],
                "tweets":         profile_data["tweet_count"],
                "account_age_days": profile_data["account_age_days"],
                "verified":       profile_data["verified"],
            },
            "is_simulated":       profile_data.get("is_simulated", False),
            "simulation_reason":  profile_data.get("simulation_reason", "")
        },
    })
