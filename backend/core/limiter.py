from slowapi import Limiter
from slowapi.util import get_remote_address
import os

def get_limiter_storage_uri():
    redis_url = os.getenv("REDIS_URL")
    if redis_url:
        print(f"[LIMITER] Using Redis storage: {redis_url.split('@')[-1] if '@' in redis_url else 'redacted'}")
        return redis_url
    print("[LIMITER] WARNING: Using MemoryStorage (Not suitable for multi-worker production).")
    return "memory://"

# Initialize Limiter with explicit storage configuration
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri=get_limiter_storage_uri(),
    strategy="fixed-window" # Fixed window is cheaper and standard for basic protections
)
