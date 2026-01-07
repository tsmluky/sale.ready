from datetime import timedelta, datetime
from typing import Annotated
import json
from marketplace_config import SYSTEM_PERSONAS
from models_db import StrategyConfig, User
from pydantic import BaseModel
import fastapi
from fastapi import APIRouter, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database import get_db
from core.schemas import UserCreate, UserResponse
from core.security import (
    verify_password,
    create_access_token,
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    SECRET_KEY,
    ALGORITHM,
)
from core.limiter import limiter

# Entitlements Endpoint
from database import SessionLocal
from core.entitlements import get_user_entitlements

router = APIRouter(prefix="/auth", tags=["Auth"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")


async def get_current_user(
    token: Annotated[str, fastapi.Depends(oauth2_scheme)],
    db: Session = fastapi.Depends(get_db),
):
    """Verifica el token JWT y retorna el usuario actual."""
    from jose import JWTError, jwt

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decode and Verify Token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            print("[AUTH] Token missing 'sub' claim")
            raise credentials_exception
    except JWTError as e:
        print(f"[AUTH] JWT Decode Error: {e}")
        raise credentials_exception

    # Get User from DB
    result = db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    if user is None:
        print(f"[AUTH] User {email} not found in DB")
        raise credentials_exception

    return user


@router.post("/token")
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request,  # Required for SlowAPI
    form_data: Annotated[OAuth2PasswordRequestForm, fastapi.Depends()],
    db: Session = fastapi.Depends(get_db),
):
    """Endpoint estandar OAuth2 para login (email/password)."""
    # En OAuth2 'username' es el campo estándar, lo usamos para el email
    result = db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()

    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )

    # Logic for entitlements
    plan_upper = user.plan.upper() if user.plan else "FREE"
    is_premium = plan_upper in ["TRADER", "PRO", "OWNER"]

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "role": user.role,
            "plan": user.plan.capitalize() if user.plan else "Free",
            "plan_status": user.plan_status,
            "allowed_tokens": (
                [
                    "BTC",
                    "ETH",
                    "SOL",
                    "XRP",
                    "BNB",
                    "DOGE",
                    "ADA",
                    "AVAX",
                    "DOT",
                    "LINK",
                ]
                if is_premium
                else ["BTC", "ETH", "SOL"]
            ),
            "created_at": user.created_at,
        },
    }


@router.post(
    "/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED
)
async def register_user(request: Request, db: Session = fastapi.Depends(get_db)):
    """
    Registra un nuevo usuario en la plataforma.
    """
    try:
        data = await request.json()
        user_data = UserCreate(**data)
    except Exception as e:
        raise HTTPException(status_code=422, detail=str(e))

    # 1. Normalizar email
    email_norm = user_data.email.strip().lower()

    # 2. Verificar duplicado
    result = db.execute(select(User).where(User.email == email_norm))
    existing_user = result.scalars().first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email already registered"
        )

    # 3. Hash Password
    hashed_pwd = get_password_hash(user_data.password)

    # 4. Crear Usuario
    new_user = User(
        email=email_norm,
        hashed_password=hashed_pwd,
        name=user_data.name,
        role="user",
        plan="free",
        plan_status="active",
        created_at=datetime.utcnow(),
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        # Capture ID safely while session is fresh and attached
        user_id_created = new_user.id
        
        try:
            # [ISO-STRAT] Seed Private Strategies
            seed_default_strategies(db, new_user)
        except Exception as seed_err:
            print(f"⚠️ [AUTH WARNING] Strategy seeding failed for {new_user.email}: {seed_err}")
            # Rollback clears the failed transaction but expires the 'new_user' instance.
            db.rollback()
            # Re-fetch using the safe ID
            new_user = db.query(User).filter(User.id == user_id_created).first()
            if not new_user:
                raise HTTPException(status_code=500, detail="User lost after rollback.")
            pass

        # FIX 500: UserResponse schema requires 'allowed_tokens', which is missing on DB model
        from core.entitlements import TokenCatalog
        allowed = TokenCatalog.get_allowed_tokens("FREE") 

        return {
            "id": new_user.id,
            "email": new_user.email,
            "name": new_user.name,
            "role": new_user.role,
            "plan": new_user.plan,
            "allowed_tokens": allowed,
            "telegram_chat_id": new_user.telegram_chat_id,
            "timezone": new_user.timezone,
            "created_at": new_user.created_at
        }

    except IntegrityError:
        # If user commit failed
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )
    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        print(f"[AUTH ERROR] Register failed: {e}")
        # Re-raise nicely
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}",
        )


def seed_default_strategies(db: Session, user: User):
    """
    Crea copias privadas de las estrategias del sistema para un nuevo usuario.
    Esto permite toggling independiente (isolation).
    """
    print(f"[AUTH] Seeding strategies for user {user.email}...")
    try:
        for p in SYSTEM_PERSONAS:
            # Create a unique ID for this user's instance
            # Suffixing ensures uniqueness in the DB constraint
            # e.g. "eth_breaker_105"
            private_id = f"{p['id']}_{user.id}"
            
            # Check exist (idempotent)
            exists = db.query(StrategyConfig).filter(StrategyConfig.persona_id == private_id).first()
            if exists:
                continue

            new_conf = StrategyConfig(
                persona_id=private_id,
                strategy_id=p["strategy_id"],
                name=p["name"],
                description=p["description"],
                tokens=json.dumps([p["symbol"]]),
                timeframes=json.dumps([p["timeframe"]]),
                risk_profile=p["risk_level"],
                expected_roi=p["expected_roi"],
                color=p["color"],
                icon=p.get("icon", "Cpu"),
                is_public=0, # Private now
                user_id=user.id,
                enabled=1, # Default ACTIVE
                total_signals=0,
                win_rate=0.0
            )
            db.add(new_conf)
        
        db.commit()
        print(f"[AUTH] Seeded {len(SYSTEM_PERSONAS)} system strategies for user {user.id}")
    except Exception as e:
        db.rollback()
        print(f"[AUTH ERROR] Failed to seed strategies: {e}")


def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("/me/entitlements")
def read_my_entitlements(
    current_user: User = fastapi.Depends(get_current_user),
    db: Session = fastapi.Depends(get_sync_db),
):
    """
    Diagnóstico de límites y cuotas.
    """
    return get_user_entitlements(db, current_user)


@router.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: User = fastapi.Depends(get_current_user)):
    """
    Get current user profile (synced with frontend requirements).
    """
    from core.entitlements import TokenCatalog

    plan = current_user.plan or "FREE"
    allowed_tokens = TokenCatalog.get_allowed_tokens(plan)

    user_dict = {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "plan": current_user.plan,
        "allowed_tokens": allowed_tokens,
        "telegram_chat_id": current_user.telegram_chat_id,
        "timezone": current_user.timezone,
        "created_at": current_user.created_at,  # PnL Fix: Critical for Dashboard
        # filtering
    }
    return user_dict


class TelegramUpdate(BaseModel):
    chat_id: str


@router.patch("/users/me/plan")
async def update_my_plan(
    new_plan: str,
    db: Session = fastapi.Depends(get_db),
    current_user: User = fastapi.Depends(get_current_user),
):
    """
    Self-service plan update (for subscription upgrades/downgrades).
    Users can update their own plan without admin approval.
    """
    # Validate plan
    valid_plans = ["FREE", "TRADER", "PRO"]
    plan_upper = new_plan.upper()

    if plan_upper not in valid_plans:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid plan. Must be one of: {', '.join(valid_plans)}",
        )

    # Update user plan
    current_user.plan = plan_upper
    db.commit()
    db.refresh(current_user)

    return {"message": f"Plan updated to {plan_upper}", "plan": plan_upper}


@router.patch("/users/me/telegram")
async def update_telegram_id(
    payload: TelegramUpdate,
    current_user: User = fastapi.Depends(get_current_user),
    db: Session = fastapi.Depends(get_db),
):
    """
    Updates the connected Telegram Chat ID for the current user.
    """
    current_user.telegram_chat_id = payload.chat_id
    db.commit()
    return {"status": "ok", "telegram_chat_id": current_user.telegram_chat_id}


class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str


@router.patch("/users/me/password")
async def update_password(
    payload: PasswordUpdate,
    current_user: User = fastapi.Depends(get_current_user),
    db: Session = fastapi.Depends(get_db),
):
    """
    Secure password change.
    """
    if not verify_password(payload.old_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Incorrect old password"
        )

    current_user.hashed_password = get_password_hash(payload.new_password)
    db.commit()
    return {"status": "ok", "message": "Password updated successfully"}


class TimezoneUpdate(BaseModel):
    timezone: str


@router.patch("/users/me/timezone")
async def update_timezone(
    payload: TimezoneUpdate,
    current_user: User = fastapi.Depends(get_current_user),
    db: Session = fastapi.Depends(get_db),
):
    """
    Updates the preferred Timezone for the current user.
    """
    current_user.timezone = payload.timezone
    db.commit()
    return {"status": "ok", "timezone": current_user.timezone}
