from fastapi import APIRouter, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from database import get_db
from schemas.complete import UserCreate, UserResponse, Token, APIResponse
from core.security import (
    authenticate_user, 
    create_access_token, 
    get_current_user, 
    get_password_hash,
    ACCESS_TOKEN_EXPIRE_MINUTES
)
from models.user import User, UserProfile
from crud.user import create_audit_log

router = APIRouter()


@router.post("/register", response_model=dict)
async def register(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    first_name: str = Form(None),
    last_name: str = Form(None),
    phone: str = Form(None),
    db: Session = Depends(get_db)
):
    """Register a new user."""
    # Check if user with same username exists
    existing_user = db.query(User).filter(User.username == username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if user with same email exists
    existing_email = db.query(User).filter(User.email == email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user with default role as viewer
    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password,
        role="viewer",  # Default role for new registrations
        is_active=True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create user profile
    profile = UserProfile(
        user_id=user.id,
        first_name=first_name,
        last_name=last_name,
        phone=phone
    )
    
    db.add(profile)
    db.commit()
    
    # Create audit log
    create_audit_log(db, user.id, "register", f"New user registered: {user.username}")
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    return {
        "message": "User registered successfully",
        "data": {
            "user": user,
            "access_token": access_token,
            "token_type": "bearer"
        }
    }


@router.post("/login", response_model=dict)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Login user and return access token."""
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if user.is_blocked:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is blocked. Please contact administrator."
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive. Please contact administrator."
        )
    
    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Create audit log
    create_audit_log(db, user.id, "login", f"User logged in: {user.username}")
    
    return {
        "message": "Login successful",
        "data": {
            "user": user,
            "access_token": access_token,
            "token_type": "bearer",
            "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60  # in seconds
        }
    }


@router.post("/logout", response_model=dict)
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Logout current user."""
    # Create audit log
    create_audit_log(db, current_user.id, "logout", f"User logged out: {current_user.username}")
    
    return {
        "message": "Logout successful",
        "data": None
    }


@router.get("/verify-token", response_model=dict)
async def verify_token(
    current_user: User = Depends(get_current_user)
):
    """Verify if the current token is valid."""
    return {
        "message": "Token is valid",
        "data": {
            "user": current_user,
            "token_valid": True
        }
    }