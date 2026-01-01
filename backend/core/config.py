import os
from dotenv import load_dotenv

def load_env_if_needed():
    """
    Loads environment variables from .env if not already loaded or if explicitly requested.
    This ensures a single, deterministic source of configuration.
    """
    # Check if a critical env var is already present (proxy for "already loaded")
    # However, for robustness in dev, we force load from the standard location
    # if we are in the backend context.
    
    current_dir = os.path.dirname(os.path.abspath(__file__)) # backend/core
    backend_dir = os.path.dirname(current_dir) # backend
    env_path = os.path.join(backend_dir, ".env")
    
    if os.path.exists(env_path):
        print(f"[CONFIG] Loading environment from: {env_path}")
        load_dotenv(env_path, override=True) # Force override to fix stale keys
    else:
        # Fallback or production scenarios where env vars are injected directly
        print(f"[CONFIG] No .env found at {env_path}, assuming environment variables are set.")
