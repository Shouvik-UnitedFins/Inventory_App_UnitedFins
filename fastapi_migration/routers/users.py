from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import List, Optional
from models.user import User, UserProfile
from schemas.user import User as UserSchema, UserUpdate, UserPasswordChange, UserResponse
from crud.user import (
    get_users, get_user_by_profile_uuid, update_user_password, 
    block_user, unblock_user, create_audit_log
)
from database import get_db
from core.security import verify_token

router = APIRouter()
security = HTTPBearer()


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)):
    """Get current authenticated user."""
    token = credentials.credentials
    email = verify_token(token)
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    from crud.user import get_user_by_email
    user = get_user_by_email(db, email)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    return user


def require_admin(current_user: User = Depends(get_current_user)):
    """Require admin role."""
    if not current_user.profile or current_user.profile.role not in ['admin', 'super_admin']:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin or super_admin can perform this action"
        )
    return current_user


@router.get("/", response_model=dict)
async def list_users(
    role: Optional[str] = Query(None, description="Filter by role"),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """List all users (admin only)."""
    # Permission-based filtering
    users = get_users(db, role=role)
    
    if current_user.profile.role == 'admin':
        # Admins can't see super_admins
        users = [u for u in users if not (u.profile and u.profile.role == 'super_admin')]
    
    return {
        "message": "Users fetched successfully",
        "data": users
    }


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information."""
    return {
        "message": "User fetched successfully",
        "data": current_user
    }


@router.get("/{user_uuid}", response_model=UserResponse)
async def get_user(
    user_uuid: str, 
    current_user: User = Depends(require_admin), 
    db: Session = Depends(get_db)
):
    """Get user by UUID (admin only)."""
    user = get_user_by_profile_uuid(db, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": "User fetched successfully",
        "data": user
    }


@router.delete("/{user_uuid}", response_model=dict)
async def delete_user(
    user_uuid: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete user by UUID (admin only)."""
    if not current_user.profile or current_user.profile.role != 'admin':
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only admin can delete users"
        )
    
    user = get_user_by_profile_uuid(db, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Delete user
    db.delete(user)
    db.commit()
    
    # Create audit log
    create_audit_log(db, current_user.id, "delete", f"Deleted user {user.email}")
    
    return {
        "message": "User deleted successfully",
        "data": None
    }


@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: UserPasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change own password."""
    update_user_password(db, current_user, password_data.password)
    
    # Create audit log
    create_audit_log(db, current_user.id, "change_password", "User changed their password")
    
    return {"message": "Password changed successfully"}


@router.patch("/{user_uuid}/password", response_model=dict)
async def set_user_password(
    user_uuid: str,
    password_data: UserPasswordChange,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Set password for a user (admin only)."""
    user = get_user_by_profile_uuid(db, user_uuid)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    update_user_password(db, user, password_data.password)
    
    # Create audit log
    create_audit_log(db, current_user.id, "change_password", f"Admin changed password for user {user.email}")
    
    return {"message": "Password set successfully", "data": None}


@router.patch("/block", response_model=dict)
async def block_user_endpoint(
    email: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Block a user by email (admin only)."""
    from crud.user import get_user_by_email
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    block_user(db, user)
    
    # Create audit log
    create_audit_log(db, current_user.id, "block", f"Blocked user {user.email}")
    
    return {"message": "User blocked successfully", "data": None}


@router.patch("/unblock", response_model=dict)
async def unblock_user_endpoint(
    email: str,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db)
):
    """Unblock a user by email (admin only)."""
    from crud.user import get_user_by_email
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    unblock_user(db, user)
    
    # Create audit log
    create_audit_log(db, current_user.id, "unblock", f"Unblocked user {user.email}")
    
    return {"message": "User unblocked successfully", "data": None}