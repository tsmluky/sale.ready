from datetime import datetime
from typing import List
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from models_db import User, DailyUsage

# === 1. CONFIGURATION & DATA ===

# Aliases: Input -> Canonical
TOKEN_ALIASES = {
    "MATIC": "POL",
    "RNDR": "RENDER",
    "LUNA": "LUNC",
}

# Stablecoins (Blocked)
STABLECOINS = {"USDT", "USDC", "DAI", "FDUSD", "TUSD", "USDD", "BUSD", "USDE", "PYUSD"}

# Allow-lists (Canonical Symbols) imported from CENTRAL SOURCE
from data.supported_tokens import VALID_TOKENS_FREE, VALID_TOKENS_FULL

TOKENS_FREE = set(VALID_TOKENS_FREE)

# Trader gets access to everything PRO gets for now, or a subset if desired.
# For simplicity in this codebase, we equate TRADER/PRO access to the FULL list.
TOKENS_TRADER = set(VALID_TOKENS_FULL)

# Full Pro List (Set for O(1) lookup)
TOKENS_PRO = set(VALID_TOKENS_FULL)

# Feature Quotas (Daily)
QUOTAS = {
    "FREE": {"ai_analysis": 2, "advisor_chat": 0},
    "TRADER": {"ai_analysis": 10, "advisor_chat": 20},
    "PRO": {"ai_analysis": 200, "advisor_chat": 500},  # Hard-Cap  # Hard-Cap
    "OWNER": {"ai_analysis": 9999, "advisor_chat": 9999},
}

# === 2. TOKEN CATALOG SERVICE ===


class TokenCatalog:
    @staticmethod
    def normalize(token: str) -> str:
        """
        Normaliza entrada: Trim, Upper, Resolve Alias.
        """
        if not token:
            return ""

        t = token.strip().upper()

        # 1. Alias Resolution
        if t in TOKEN_ALIASES:
            t = TOKEN_ALIASES[t]

        return t

    @staticmethod
    def is_stablecoin(token: str) -> bool:
        return token in STABLECOINS

    @staticmethod
    def get_allowed_tokens(plan: str) -> List[str]:
        p = plan.upper()
        # Fallback for old/weird plans
        if p not in ["FREE", "TRADER", "PRO", "OWNER"]:
            p = "FREE"

        if p == "FREE":
            return sorted(list(TOKENS_FREE))
        elif p == "TRADER":
            return sorted(list(TOKENS_TRADER))
        # PRO / OWNER
        return sorted(list(TOKENS_PRO))

    @staticmethod
    def check_access(plan: str, token: str) -> bool:
        """
        Verifica si el plan tiene acceso al token (CANONICAL).
        """
        p = plan.upper()

        # Owner bypass
        if p == "OWNER":
            return True

        if p == "FREE":
            return token in TOKENS_FREE
        if p == "TRADER":
            return token in TOKENS_TRADER
        if p == "PRO" or p == "INSTITUTIONAL":
            return token in TOKENS_PRO

        return False  # Unknown plan -> Block


# === 3. ENFORCEMENT FUNCTIONS ===


def assert_token_allowed(user: User, raw_token: str):
    """
    Validación estricta de token por tier.
    Lanza 403 con JSON estructurado si falla.
    """
    # 0. Normalize
    token = TokenCatalog.normalize(raw_token)

    # 1. Stablecoin Check
    if TokenCatalog.is_stablecoin(token):
        raise HTTPException(
            status_code=403,
            detail={
                "code": "STABLECOIN_NOT_SUPPORTED",
                "message": (
                    f"Stablecoins like {token} are not supported for analysis targets."
                ),
                "tier": user.plan,
            },
        )

    # 2. Tier Access Check
    plan = (user.plan or "FREE").upper()
    if not TokenCatalog.check_access(plan, token):
        # Prepare standard response
        allowed = TokenCatalog.get_allowed_tokens(plan)

        raise HTTPException(
            status_code=403,
            detail={
                "code": "TOKEN_NOT_ALLOWED",
                "message": (
                    f"Your {plan} plan does not include access to {token}."
                ),
                "tier": plan,
                "token_requested": token,
                "allowed_sample": allowed[:5],
                "upgrade_required": True,
            },
        )

    # Return normalized token
    return token


def can_use_advisor(user: User):
    """
    Verifica acceso base al Advisor Chat.
    """
    plan = (user.plan or "FREE").upper()

    limits = QUOTAS.get(plan, QUOTAS["FREE"])
    chat_limit = limits.get("advisor_chat", 0)

    if chat_limit <= 0:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FEATURE_LOCKED",
                "message": f"Advisor Chat is not available on the {plan} plan.",
                "tier": plan,
                "upgrade_required": True,
            },
        )


def check_and_increment_quota(db: Session, user: User, feature: str):
    """
    Verifica y consume cuota diaria con atomicidad robusta.
    Maneja condiciones de carrera (Race Conditions) mediante retries y locking.
    Lanza 429 con JSON estructurado si falla.
    """
    plan = (user.plan or "FREE").upper()

    # Get Limits
    limits = QUOTAS.get(plan, QUOTAS["FREE"])
    limit = limits.get(feature, 0)

    # Hard Block if 0
    if limit <= 0:
        raise HTTPException(
            status_code=403,
            detail={
                "code": "FEATURE_LOCKED",
                "message": f"Feature {feature} not enabled for {plan}.",
                "tier": plan,
                "upgrade_required": True,
            },
        )

    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Retry loop to handle Insert Race Conditions (Upsert)
    for attempt in range(3):
        try:
            # 1. Try to Get Record (with Lock if possible)
            usage = None
            try:
                # Intentamos Locking (Postgres)
                usage = (
                    db.query(DailyUsage)
                    .filter(
                        DailyUsage.user_id == user.id,
                        DailyUsage.feature == feature,
                        DailyUsage.date == today_str,
                    )
                    .with_for_update()
                    .first()
                )
            except Exception:
                # Fallback (SQLite u otros drivers sin soporte row-lock simple)
                # En SQLite esto no bloquea de la misma forma. Sin embargo, el
                # commit puede fallar si ocurre un race en variantes serializables.
                # Simplemente leemos standard.
                db.rollback()  # Limpiar estado transacción fallida
                usage = (
                    db.query(DailyUsage)
                    .filter(
                        DailyUsage.user_id == user.id,
                        DailyUsage.feature == feature,
                        DailyUsage.date == today_str,
                    )
                    .first()
                )

            # 2. Si no existe, insertar (Atomic Insert attempt)
            if not usage:
                usage = DailyUsage(
                    user_id=user.id, feature=feature, date=today_str, count=0
                )
                db.add(usage)
                db.commit()
                db.refresh(usage)
                # Ahora tenemos el record, continuamos al check
                # (Podríamos necesitar re-lockear si fuera muy de alto tráfico, pero
                # el Insert fue exitoso)

            # 3. Check Limit
            if usage.count >= limit:
                # Quota Exceeded
                raise HTTPException(
                    status_code=429,
                    detail={
                        "code": "DAILY_QUOTA_EXCEEDED",
                        "message": (
                            f"You have reached your daily limit of {limit} for {feature}."
                        ),
                        "tier": plan,
                        "limit": limit,
                        "used": usage.count,
                        "reset_at": "00:00 UTC",
                        "upgrade_required": plan != "PRO",
                    },
                )

            # 4. Increment & Commit
            usage.count += 1
            db.commit()

            return {
                "used": usage.count,
                "limit": limit,
                "remaining": limit - usage.count,
            }

        except IntegrityError:
            # Race Condition detected: Alguien insertó el registro mientras
            # nosotros intentábamos.
            # Rollback y reintentar (en el siguiente loop encontraremos el
            # registro y haremos update)
            db.rollback()
            continue

        except HTTPException as e:
            # 429/403 normal, propagar
            raise e

        except Exception as e:
            # Error desconocido
            db.rollback()
            raise HTTPException(status_code=500, detail=f"Quota check failed: {str(e)}")

    # Si agotamos retries
    raise HTTPException(
        status_code=500, detail="System busy: Unable to lock quota record."
    )


def get_user_entitlements(db: Session, user: User):
    """
    Retorna estado completo para UI.
    """
    plan = (user.plan or "FREE").upper()
    today_str = datetime.utcnow().strftime("%Y-%m-%d")

    # Get usage from DB
    usages = (
        db.query(DailyUsage)
        .filter(DailyUsage.user_id == user.id, DailyUsage.date == today_str)
        .all()
    )

    usage_map = {u.feature: u.count for u in usages}
    limits = QUOTAS.get(plan, QUOTAS["FREE"])

    return {
        "tier": plan,
        "features": {
            "ai_analysis": {
                "limit": limits.get("ai_analysis", 0),
                "used": usage_map.get("ai_analysis", 0),
                "remaining": max(
                    0, limits.get("ai_analysis", 0) - usage_map.get("ai_analysis", 0)
                ),
            },
            "advisor_chat": {
                "limit": limits.get("advisor_chat", 0),
                "used": usage_map.get("advisor_chat", 0),
                "remaining": max(
                    0, limits.get("advisor_chat", 0) - usage_map.get("advisor_chat", 0)
                ),
            },
        },
        "allowed_tokens": TokenCatalog.get_allowed_tokens(plan),
        "server_time": datetime.utcnow().isoformat() + "Z",
    }
