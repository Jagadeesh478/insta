# utils/twitter_client.py (refined)
import os, time
from datetime import datetime, timezone
from typing import Dict, Any, Optional
import tweepy
from dotenv import load_dotenv
from tweepy.errors import BadRequest, Unauthorized, Forbidden, TooManyRequests, NotFound

load_dotenv()

class TwitterClient:
    def __init__(self) -> None:
        bearer = os.getenv("TWITTER_BEARER_TOKEN")
        if not bearer:
            raise ValueError("Twitter Bearer Token not found. Set TWITTER_BEARER_TOKEN in environment")
        # Auto-sleep on 15-min bucket limits
        self.client = tweepy.Client(bearer_token=bearer, wait_on_rate_limit=True)

    def _retry_after(self, headers: Optional[dict]) -> int:
        if not headers:
            return 60  # safe default
        reset = headers.get("x-rate-limit-reset")
        if not reset:
            return 60
        try:
            reset_ts = int(reset)
            now = int(time.time())
            return max(1, reset_ts - now)
        except Exception:
            return 60

    def get_user_profile(self, username: str) -> Dict[str, Any]:
        handle = username.lstrip("@").strip()
        try:
            resp = self.client.get_user(
                username=handle,
                user_fields=[
                    "created_at","public_metrics","verified",
                    "description","location","profile_image_url"
                ],
            )
            user = resp.data
            if not user:
                return {"error": "User not found or no data returned."}

            created_at = user.created_at
            age_days = (datetime.now(timezone.utc) - created_at).days if created_at else 0
            pm = user.public_metrics or {}
            return {
                "id": user.id,
                "username": user.username,
                "name": getattr(user, "name", "") or "",
                "description": getattr(user, "description", "") or "",
                "location": getattr(user, "location", "") or "",
                "verified": bool(getattr(user, "verified", False)),
                "created_at": created_at,
                "account_age_days": age_days,
                "followers_count": int(pm.get("followers_count", 0)),
                "following_count": int(pm.get("following_count", 0)),
                "tweet_count": int(pm.get("tweet_count", 0)),
                "listed_count": int(pm.get("listed_count", 0)),
                "profile_image_url": getattr(user, "profile_image_url", "") or "",
            }

        except TooManyRequests as e:
            headers = getattr(e, "response", None)
            headers = getattr(headers, "headers", None)
            wait_s = self._retry_after(headers)
            reset_epoch = headers.get("x-rate-limit-reset") if headers else None
            return {"error": f"429 Rate limit exceeded; retry after {wait_s}s", "retry_after_seconds": wait_s, "reset_epoch": reset_epoch}
        except BadRequest as e:
            body = getattr(e, "response", None)
            return {"error": f"400 Bad Request: {getattr(body, 'text', str(e))[:300]}"}
        except Unauthorized as e:
            body = getattr(e, "response", None)
            return {"error": f"401 Unauthorized: {getattr(body, 'text', str(e))[:300]} — check Bearer token"}
        except Forbidden as e:
            body = getattr(e, "response", None)
            return {"error": f"403 Forbidden: {getattr(body, 'text', str(e))[:300]} — check app plan/permissions"}
        except NotFound:
            return {"error": "404 Not Found: user does not exist"}
        except Exception as e:
            return {"error": f"Unexpected error: {str(e)}"}
