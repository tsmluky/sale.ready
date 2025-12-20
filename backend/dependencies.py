# backend/dependencies.py
from fastapi import Depends, HTTPException, status
from models_db import User
from routers.auth import get_current_user

def require_plan(required_plan: str):
    """
    Closure to enforce plan requirements.
    Hierarchy: OWNER > PRO > FREE.
    """
    def plan_checker(current_user: User = Depends(get_current_user)) -> User:
        user_plan = current_user.plan.upper() if current_user.plan else "FREE"
        
        # Hierarchy Definition
        levels = {"FREE": 0, "TRADER": 1, "PRO": 2, "OWNER": 3}
        
        user_level = levels.get(user_plan, 0)
        req_level = levels.get(required_plan.upper(), 0)
        
        if user_level < req_level:
            # 403 with specific payload for Frontend Interceptor
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PLAN_REQUIRED",
                    "message": f"Upgrade to {required_plan} to access this feature.",
                    "upgrade_url": "/pricing"
                }
            )
        return current_user
    return plan_checker

# Shortcuts
require_pro = require_plan("PRO")
require_owner = require_plan("OWNER")
