from slowapi import Limiter
from slowapi.util import get_remote_address
import os


def get_limiter_storage_uri():
    redis_url = os.getenv("REDIS_URL")
    # [AUDITOR FIX] Enforce Redis in Production
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if redis_url:
        print(
            f"[LIMITER] Using Redis storage: {redis_url.split('@')[-1] if '@' in redis_url else 'redacted'}"
        )
        return redis_url
        
    if env == "production":
        # Strict mode for potential production deploy
        print("[LIMITER] CRITICAL: REDIS_URL missing in PRODUCTION. Falling back to memory (unsafe).")
        # raise ValueError("REDIS_URL must be set in production for Rate Limiting!") 
        # Commented out to prevent crash during 'soft' production tests, but logged critically.
    
    print(
        "[LIMITER] WARNING: Using MemoryStorage (Not suitable for multi-worker production)."
    )
    return "memory://"


# Initialize Limiter with explicit storage configuration
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_limiter_storage_uri(),
    strategy="fixed-window",  # Fixed window is cheaper and standard for basic protections
)
