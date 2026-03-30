import requests
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import socket
import ssl
import datetime
import whois

# -----------------------------------------------------
# Helper: Check if string is IP-based URL
# -----------------------------------------------------
def is_ip_address(host):
    try:
        socket.inet_aton(host)
        return True
    except:
        return False


# -----------------------------------------------------
# Helper: Check domain age using python-whois
# -----------------------------------------------------
def get_domain_age(host):
    try:
        info = whois.whois(host)
        created = info.creation_date

        if isinstance(created, list):
            created = created[0]

        if created is None:
            return None

        today = datetime.datetime.now()
        age_days = (today - created).days
        return age_days
    except:
        return None


# -----------------------------------------------------
# Check HTTPS TLS certificate
# -----------------------------------------------------
def check_tls(host):
    details = {"valid": False, "issuer": None, "expires_in_days": None}

    try:
        ctx = ssl.create_default_context()
        with ctx.wrap_socket(socket.socket(), server_hostname=host) as s:
            s.settimeout(4)
            s.connect((host, 443))
            cert = s.getpeercert()

        details["valid"] = True

        issuer = cert.get("issuer", [["N/A"]])[0][0][1]
        details["issuer"] = issuer

        exp_date = datetime.datetime.strptime(cert['notAfter'], "%b %d %H:%M:%S %Y %Z")
        remaining = (exp_date - datetime.datetime.utcnow()).days
        details["expires_in_days"] = remaining

    except:
        pass

    return details


# -----------------------------------------------------
# Main Analysis Function
# -----------------------------------------------------
def analyze(url):
    reasons = []
    score = 0.0

    parsed = urlparse(url)
    host = parsed.netloc

    # A) IP Address URL
    if is_ip_address(host):
        score += 0.25
        reasons.append("URL uses IP address instead of domain (high risk)")

    # B) Check domain exists
    try:
        socket.gethostbyname(host)
        domain_exists = True
    except:
        domain_exists = False
        reasons.append("Domain does not resolve")
        return {
            "url": url,
            "verdict": "High Risk / Phishing",
            "safe_percent": 0,
            "score": 1,
            "domain_exists": False,
            "online": False,
            "http_status": None,
            "tls": {},
            "title": None,
            "reasons": reasons
        }

    # C) Get domain age
    age_days = get_domain_age(host)
    if age_days is None:
        score += 0.10
        reasons.append("Domain age unavailable (possible privacy hiding)")
    elif age_days < 30:
        score += 0.20
        reasons.append(f"Domain is very new ({age_days} days old) — common for phishing")

    # D) Very long URL
    if len(url) > 75:
        score += 0.10
        reasons.append("URL is unusually long")

    # E) Suspicious subdomain patterns
    if url.count('.') >= 4:
        score += 0.10
        reasons.append("Too many subdomains (likely deceptive)")

    # F) Suspicious keywords
    keywords = ["login", "verify", "secure", "update", "unlock", "bank", "offer"]
    if any(w in url.lower() for w in keywords):
        score += 0.15
        reasons.append("Suspicious phishing keywords found in URL")

    # G) HEAD request
    try:
        r = requests.head(url, timeout=5, allow_redirects=True)
        http_status = r.status_code
        redirects = len(r.history)

        if redirects >= 3:
            score += 0.10
            reasons.append("Website has multiple redirects (phish evasion)")
    except:
        http_status = None
        reasons.append("Website not reachable")
        return {
            "url": url,
            "verdict": "High Risk / Phishing",
            "safe_percent": 10,
            "score": 0.9,
            "domain_exists": True,
            "online": False,
            "http_status": None,
            "tls": {},
            "title": None,
            "reasons": reasons
        }

    # H) TLS Certificate
    tls = {"valid": False}
    if url.startswith("https://"):
        tls = check_tls(host)

        if tls["valid"]:
            reasons.append("Valid SSL certificate detected")
        else:
            score += 0.20
            reasons.append("Invalid or missing SSL certificate")

        if tls.get("expires_in_days") is not None and tls["expires_in_days"] < 10:
            score += 0.10
            reasons.append("SSL certificate expiring soon")

    # I) GET page
    title = None
    try:
        r = requests.get(url, timeout=6)
        if r.status_code == 200 and "text/html" in (r.headers.get("Content-Type", "")):
            soup = BeautifulSoup(r.text, "html.parser")

            # Page title
            if soup.title and soup.title.string:
                title = soup.title.string.strip()

            # Detect password fields
            if soup.find("input", {"type": "password"}):
                score += 0.20
                reasons.append("Password field found — often used in phishing pages")

            # Detect fake forms
            if soup.find("form"):
                score += 0.15
                reasons.append("Form detected — possible credential harvesting")

    except:
        pass

    # Normalize Score
    score = max(0, min(1, score))
    safe_percent = round((1 - score) * 100, 1)

    # Final Verdict
    if safe_percent >= 85:
        verdict = "Safe & Verified"
    elif safe_percent >= 60:
        verdict = "Suspicious"
    else:
        verdict = "High Risk / Phishing"

    return {
        "url": url,
        "score": score,
        "safe_percent": safe_percent,
        "verrett": verdict,
        "verdict": verdict,
        "domain_exists": domain_exists,
        "online": True,
        "http_status": http_status,
        "tls": tls,
        "title": title,
        "reasons": reasons
    }
