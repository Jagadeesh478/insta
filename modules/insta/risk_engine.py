"""
Advanced Risk Scoring Engine for Instagram Account Analysis
"""
from typing import Dict, List, Any


def calculate_risk_score(account_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate comprehensive risk score (0-100) based on multiple factors
    """
    risk_score = 0
    confidence = 100  # Start with full confidence
    
    # Factor 1: Account Verification (-20 risk if verified, +20 if not)
    if account_data.get("verified") is True:
        risk_score -= 20  # Verified accounts are safer
    elif account_data.get("verified") is False:
        risk_score += 20
    else:
        confidence -= 10  # Unknown verification status reduces confidence
    
    # Factor 2: Account Age (newer accounts are riskier)
    account_age = account_data.get("account_age_days")
    if account_age is not None:
        if account_age < 30:
            risk_score += 25  # Very new account
        elif account_age < 90:
            risk_score += 15  # Relatively new
        elif account_age < 180:
            risk_score += 5   # Moderately new
        # Older accounts get no penalty
    else:
        confidence -= 15
    
    # Factor 3: Follower/Following Ratio (suspicious patterns)
    followers = account_data.get("followers")
    following = account_data.get("following")
    
    if followers is not None and following is not None:
        if followers < 50:
            risk_score += 10  # Very low followers
        
        if following > 1000:
            risk_score += 15  # Following too many
        
        # Suspicious ratio: following way more than followers
        if followers > 0 and following > 0:
            ratio = following / max(followers, 1)
            if ratio > 10:
                risk_score += 20  # Highly suspicious
            elif ratio > 5:
                risk_score += 10
    else:
        confidence -= 10
    
    # Factor 4: Profile Picture
    has_profile_pic = account_data.get("has_profile_pic")
    if has_profile_pic == "no" or has_profile_pic == "suspicious":
        risk_score += 15
    elif has_profile_pic is None:
        confidence -= 5
    
    # Factor 5: Bio Analysis
    bio_text = account_data.get("bio_text")
    if bio_text:
        bio_lower = bio_text.lower()
        # Check for suspicious keywords
        suspicious_keywords = [
            "dm for", "click link", "free", "prize", "winner", 
            "cash", "money", "investment", "crypto", "bitcoin",
            "urgent", "limited time", "act now", "verify account"
        ]
        for keyword in suspicious_keywords:
            if keyword in bio_lower:
                risk_score += 5
    
    # Factor 6: External Links in Bio
    bio_links = account_data.get("bio_links")
    if bio_links == "suspicious" or bio_links == "multiple":
        risk_score += 20
    elif bio_links == "yes":
        risk_score += 5
    
    # Factor 7: DM Activity (most critical factor)
    dm_activity = account_data.get("dm_activity")
    if dm_activity == "suspicious":
        risk_score += 30  # Highest risk factor
    elif dm_activity == "unsolicited":
        risk_score += 20
    
    # Factor 8: Post Count
    posts = account_data.get("posts")
    if posts is not None:
        if posts == 0:
            risk_score += 15  # No posts is suspicious
        elif posts < 5:
            risk_score += 10  # Very few posts
    else:
        confidence -= 5
    
    # Factor 9: Account Visibility
    visibility = account_data.get("visibility")
    if visibility == "private":
        confidence -= 20  # Can't see much, lower confidence
    
    # Normalize risk score to 0-100 range
    risk_score = max(0, min(100, risk_score))
    confidence = max(0, min(100, confidence))
    
    # Determine risk level
    if risk_score >= 65:
        risk_level = "High Risk"
    elif risk_score >= 40:
        risk_level = "Moderate Risk"
    else:
        risk_level = "Low Risk"
    
    # Determine confidence label
    if confidence >= 70:
        confidence_label = "High"
    elif confidence >= 40:
        confidence_label = "Medium"
    else:
        confidence_label = "Low"
    
    return {
        "risk_score": risk_score,
        "risk_level": risk_level,
        "confidence": confidence,
        "confidence_label": confidence_label
    }


def get_risk_reasons(account_data: Dict[str, Any], risk_data: Dict[str, Any]) -> List[str]:
    """
    Generate detailed list of reasons for the risk assessment
    """
    reasons = []
    
    # Verification status
    if account_data.get("verified") is False:
        reasons.append("❌ Account is not verified by Instagram")
    elif account_data.get("verified") is True:
        reasons.append("✅ Account is verified by Instagram (lower risk)")
    
    # Account age
    account_age = account_data.get("account_age_days")
    if account_age is not None:
        if account_age < 30:
            reasons.append(f"⚠️ Very new account (only {account_age} days old)")
        elif account_age < 90:
            reasons.append(f"⚡ Relatively new account ({account_age} days old)")
    
    # Follower analysis
    followers = account_data.get("followers")
    following = account_data.get("following")
    
    if followers is not None and followers < 50:
        reasons.append(f"📉 Very low follower count ({followers} followers)")
    
    if following is not None and following > 1000:
        reasons.append(f"📈 Following unusually high number of accounts ({following})")
    
    if followers is not None and following is not None and followers > 0:
        ratio = following / max(followers, 1)
        if ratio > 5:
            reasons.append(f"⚖️ Suspicious follower ratio (following {ratio:.1f}x more than followers)")
    
    # Profile picture
    if account_data.get("has_profile_pic") in ["no", "suspicious"]:
        reasons.append("🖼️ Missing or suspicious profile picture")
    
    # Bio links
    bio_links = account_data.get("bio_links")
    if bio_links in ["suspicious", "multiple"]:
        reasons.append("🔗 Bio contains suspicious external links")
    
    # DM activity
    dm_activity = account_data.get("dm_activity")
    if dm_activity == "suspicious":
        reasons.append("🚨 Reported suspicious direct message activity")
    elif dm_activity == "unsolicited":
        reasons.append("📬 Sends unsolicited direct messages")
    
    # Posts
    posts = account_data.get("posts")
    if posts is not None:
        if posts == 0:
            reasons.append("📭 Account has no posts")
        elif posts < 5:
            reasons.append(f"📊 Very few posts ({posts} posts)")
    
    # Bio analysis
    bio_text = account_data.get("bio_text")
    if bio_text:
        bio_lower = bio_text.lower()
        suspicious_found = []
        if any(word in bio_lower for word in ["dm for", "click link"]):
            suspicious_found.append("promotional language")
        if any(word in bio_lower for word in ["free", "prize", "winner", "cash", "money"]):
            suspicious_found.append("financial incentives")
        if any(word in bio_lower for word in ["crypto", "bitcoin", "investment"]):
            suspicious_found.append("cryptocurrency/investment")
        if any(word in bio_lower for word in ["urgent", "limited time", "act now"]):
            suspicious_found.append("urgency tactics")
        
        if suspicious_found:
            reasons.append(f"⚠️ Bio contains suspicious keywords: {', '.join(suspicious_found)}")
    
    # Visibility
    if account_data.get("visibility") == "private":
        reasons.append("🔒 Private account limits visibility into activity")
    
    # If no specific reasons found but risk is high
    if not reasons and risk_data["risk_score"] >= 40:
        reasons.append("⚠️ Multiple minor risk indicators detected")
    
    # If low risk
    if risk_data["risk_score"] < 40 and not reasons:
        reasons.append("✅ No significant scam indicators detected")
        reasons.append("👍 Account appears to follow normal usage patterns")
    
    return reasons
