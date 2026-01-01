from fastapi import APIRouter
import os

router = APIRouter()

# Destructive reset endpoint removed for Security Audit Compliance (Sale-Ready).
# Use 'python backend/reset_db_manual.py' instead.

@router.get("/health")
def health_check():
    return {"status": "ok", "db": "connected"}

@router.get("/config")
def get_system_config():
    """
    White-Label Configuration.
    """
    import json
    
    defaults = {
        "appName": "TraderCopilot",
        "logoUrl": "/logo.png",
        "primaryColor": "#10b981", # Emerald-500
        "supportEmail": "support@tradercopilot.com"
    }
    
    config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "theme_config.json")
    if os.path.exists(config_path):
        try:
            with open(config_path, "r") as f:
                custom = json.load(f)
                defaults.update(custom)
        except Exception as e:
            print(f"Error loading theme_config: {e}")
            
    return defaults
