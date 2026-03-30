import numpy as np
from typing import Dict, Tuple
import re

class FakeAccountDetector:
    def __init__(self):
        # These thresholds are based on research on fake account patterns
        self.suspicious_patterns = {
            'min_account_age': 30,  # accounts younger than 30 days
            'max_following_ratio': 10,  # following more than 10x followers
            'min_tweets_per_day': 50,   # more than 50 tweets per day
            'suspicious_username_patterns': [
                r'^\w+\d{4,}$',  # username ending with 4+ digits
                r'^\w+_\w+_\w+$',  # multiple underscores
            ]
        }
    
    def extract_features(self, profile_data: Dict) -> Dict:
        """Extract features for fake account detection"""
        if 'error' in profile_data:
            return profile_data
            
        features = {}
        
        # Basic metrics
        features['followers_count'] = profile_data['followers_count']
        features['following_count'] = profile_data['following_count'] 
        features['tweet_count'] = profile_data['tweet_count']
        features['listed_count'] = profile_data['listed_count']
        features['account_age_days'] = profile_data['account_age_days']
        features['verified'] = int(profile_data['verified'])
        
        # Calculated ratios and patterns
        features['followers_following_ratio'] = (
            profile_data['followers_count'] / max(profile_data['following_count'], 1)
        )
        features['following_followers_ratio'] = (
            profile_data['following_count'] / max(profile_data['followers_count'], 1)
        )
        
        # Tweet activity rate
        features['tweets_per_day'] = (
            profile_data['tweet_count'] / max(profile_data['account_age_days'], 1)
        )
        
        # Profile completeness
        features['has_description'] = int(bool(profile_data['description']))
        features['has_location'] = int(bool(profile_data['location']))
        features['has_profile_image'] = int(
            'default_profile_image' not in profile_data.get('profile_image_url', '')
        )
        features['description_length'] = len(profile_data['description'])
        
        # Username patterns (suspicious indicators)
        username = profile_data['username']
        features['username_has_numbers'] = int(bool(re.search(r'\d', username)))
        features['username_length'] = len(username)
        features['name_username_similarity'] = self._calculate_similarity(
            profile_data['name'], username
        )
        
        return features
    
    def _calculate_similarity(self, name: str, username: str) -> float:
        """Simple similarity calculation between name and username"""
        if not name or not username:
            return 0.0
        
        name = name.lower().replace(' ', '')
        username = username.lower()
        
        # Basic Jaccard similarity
        set1 = set(name)
        set2 = set(username)
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0
    
    def rule_based_detection(self, features: Dict) -> Tuple[str, float, list]:
        """Rule-based fake account detection with suspicion reasons"""
        if 'error' in features:
            return 'Error', 0.0, [features['error']]
            
        suspicious_signals = []
        suspicion_score = 0.0
        
        # Check account age
        if features['account_age_days'] < self.suspicious_patterns['min_account_age']:
            suspicious_signals.append(f"Very new account ({features['account_age_days']} days old)")
            suspicion_score += 0.3
            
        # Check following ratio
        if features['following_followers_ratio'] > self.suspicious_patterns['max_following_ratio']:
            suspicious_signals.append(f"Following too many accounts compared to followers (ratio: {features['following_followers_ratio']:.1f})")
            suspicion_score += 0.25
            
        # Check tweet activity
        if features['tweets_per_day'] > self.suspicious_patterns['min_tweets_per_day']:
            suspicious_signals.append(f"Unusually high tweet activity ({features['tweets_per_day']:.1f} tweets/day)")
            suspicion_score += 0.2
            
        # Check profile completeness
        if not features['has_description']:
            suspicious_signals.append("No profile description")
            suspicion_score += 0.1
            
        if not features['has_profile_image']:
            suspicious_signals.append("Using default profile image")
            suspicion_score += 0.1
            
        # Check username patterns
        if features['username_length'] > 15:
            suspicious_signals.append("Unusually long username")
            suspicion_score += 0.05
            
        if features['name_username_similarity'] < 0.3:
            suspicious_signals.append("Name and username are very different")
            suspicion_score += 0.1
            
        # Determine result
        if suspicion_score >= 0.5:
            result = "Likely Fake"
        elif suspicion_score >= 0.3:
            result = "Suspicious" 
        else:
            result = "Likely Genuine"
            
        return result, suspicion_score, suspicious_signals
