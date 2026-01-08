# backend/dependencies.py
import fastapi
from fastapi import HTTPException, status
from models_db import User
from routers.auth_new import get_current_user


def require_plan(required_plan: str):
    """
    Closure to enforce plan requirements.
    Hierarchy: OWNER > PRO > FREE.
    """

    def plan_checker(current_user: User = fastapi.Depends(get_current_user)) -> User:
        user_plan = current_user.plan.upper() if current_user.plan else "FREE"

        # Hierarchy Definition
        levels = {"FREE": 0, "TRADER": 1, "PRO": 2, "OWNER": 3}

        user_level = levels.get(user_plan, 0)
        req_level = levels.get(required_plan.upper(), 0)

        # Allow explicit "admin" role to bypass plan requirements
        is_admin_role = (current_user.role or "").lower() == "admin"

        if user_level < req_level and not is_admin_role:
            # 403 with specific payload for Frontend Interceptor
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "code": "PLAN_REQUIRED",
                    "message": f"Upgrade to {required_plan} to access this feature.",
                    "upgrade_url": "/pricing",
                },
            )
        return current_user

    return plan_checker


# Shortcuts
require_pro = require_plan("PRO")
require_owner = require_plan("OWNER")


class PaginationParams:
    """
    Common pagination dependency.
    Enforces hard caps to prevent DB overload (Sale-Ready).
    """
    def __init__(self, page: int = 1, limit: int = 20):
        self.page = page if page > 0 else 1
        # Hard Cap: 100 items max per page
        self.limit = min(limit, 100) if limit > 0 else 20
        self.offset = (self.page - 1) * self.limit

