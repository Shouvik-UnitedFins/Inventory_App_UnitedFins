from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from schemas.user import UserLogin, Token, UserCreate
from crud.user import authenticate_user, create_user, create_audit_log
from database import get_db
from core.security import create_access_token, create_refresh_token, verify_token

router = APIRouter()
security = HTTPBearer()


@router.post("/login", response_model=dict)
async def login(user_credentials: UserLogin, db: Session = Depends(get_db)):
    """User login endpoint."""
    user = authenticate_user(db, user_credentials.email, user_credentials.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive"
        )
    
    if user.profile and user.profile.blocked:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is blocked"
        )
    
    # Create tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})
    
    # Create audit log
    create_audit_log(db, user.id, "login", "User logged in")
    
    return {
        "message": "Login successful",
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "user": {
            "uuid": user.profile.uuid if user.profile else None,
            "email": user.email,
            "role": user.profile.role if user.profile else None,
            "is_active": user.is_active,
        }
    }


@router.post("/register", response_model=dict)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    """User registration endpoint."""
    # Check if user exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    from models.user import User
    user = create_user(db, user_data)
    
    # Create audit log
    create_audit_log(db, user.id, "register", "User registered")
    
    return {
        "message": "User registered successfully",
        "data": {
            "email": user.email,
            "uuid": user.profile.uuid if user.profile else None,
            "role": user.profile.role if user.profile else None
        }
    }


@router.post("/logout")
async def logout():
    """User logout endpoint."""
    # Note: In JWT, logout is handled on the client side by removing the token
    # Optionally implement token blacklisting here
    return {"message": "Logout successful"}