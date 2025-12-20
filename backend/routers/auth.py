from datetime import timedelta, datetime
from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from database import get_db
from models_db import User
from core.schemas import UserCreate, UserResponse
from core.security import verify_password, create_access_token, get_password_hash, ACCESS_TOKEN_EXPIRE_MINUTES, SECRET_KEY, ALGORITHM

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.get("/probe_deployment")
def probe_deployment():
    """Probe to verify if deployment is updated"""
    return {
        "status": "active", 
        "version_tag": "fix_register_json_v1",
        "timestamp": datetime.utcnow()
    }


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: Session = Depends(get_db)):
    """Verifica el token JWT y retorna el usuario actual."""
    from jose import JWTError, jwt
    from fastapi import status
    
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
from core.limiter import limiter

@router.post("/token")
@limiter.limit("5/minute")
async def login_for_access_token(
    request: Request, # Required for SlowAPI
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Session = Depends(get_db)
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
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "user": {
            "id": user.id,
            "email": user.email,
            "name": user.name,
            "name": user.name,
            "role": user.role,
            "plan": user.plan,
            "plan_status": user.plan_status
        }
    }

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Registra un nuevo usuario en la plataforma.
    (Debug Mode: Reads raw JSON to debug validation errors)
    """
    try:
        data = await request.json()
        print(f"[DEBUG REGISTER] Raw Payload: {data}")
        # Manually validate to trigger Pydantic
        user_data = UserCreate(**data)
    except Exception as e:
        print(f"[DEBUG REGISTER] JSON Parse/Validation Error: {e}")
        raise HTTPException(status_code=422, detail=str(e))

    # 1. Normalizar email
    email_norm = user_data.email.strip().lower()
    
    # 2. Verificar duplicado
    result = db.execute(select(User).where(User.email == email_norm))
    existing_user = result.scalars().first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
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
        created_at=datetime.utcnow() # Ensure model has this or defaults
    )
    
    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        return new_user
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Error creating user (Integrity)"
        )
    except Exception as e:
        db.rollback()
        print(f"[AUTH ERROR] Register failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during registration"
        )

# Entitlements Endpoint (Sync DB required for core logic)
from database import SessionLocal
from sqlalchemy.orm import Session
from core.entitlements import get_user_entitlements

def get_sync_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/me/entitlements")
def read_my_entitlements(
    current_user: User = Depends(get_current_user), 
    db: Session = Depends(get_sync_db)
):
    """
    Diagnóstico de límites y cuotas.
    """
    return get_user_entitlements(db, current_user)

