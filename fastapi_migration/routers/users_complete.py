from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from schemas.complete import UserCreate, UserUpdate, UserResponse, ChangePasswordSchema, APIResponse
from core.security import get_current_user, require_roles, get_password_hash, verify_password
from models.user import User, UserProfile
from crud.user import create_audit_log
from datetime import datetime

router = APIRouter()


@router.get("/", response_model=dict)
async def list_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of users to return"),
    search: Optional[str] = Query(None, description="Search users by username or email"),
    role: Optional[str] = Query(None, description="Filter by role"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    is_blocked: Optional[bool] = Query(None, description="Filter by blocked status"),
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """List all users with pagination and filtering (admin, super_admin only)."""
    query = db.query(User)
    
    # Apply filters
    if search:
        query = query.filter(
            (User.username.ilike(f"%{search}%")) | 
            (User.email.ilike(f"%{search}%"))
        )
    if role:
        query = query.filter(User.role == role)
    if is_active is not None:
        query = query.filter(User.is_active == is_active)
    if is_blocked is not None:
        query = query.filter(User.is_blocked == is_blocked)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    users = query.offset(skip).limit(limit).all()
    
    return {
        "message": "Users fetched successfully",
        "data": {
            "users": users,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }


@router.get("/me", response_model=dict)
async def get_current_user_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's profile."""
    return {
        "message": "User profile fetched successfully",
        "data": {"user": current_user}
    }


@router.get("/{user_id}", response_model=dict)
async def get_user(
    user_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Get user by ID (admin, super_admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return {
        "message": "User fetched successfully",
        "data": {"user": user}
    }


@router.post("/", response_model=dict)
async def create_user(
    user_data: UserCreate,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Create new user (admin, super_admin only)."""
    # Check if user with same username exists
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if user with same email exists
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        is_active=user_data.is_active if hasattr(user_data, 'is_active') else True
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Create user profile
    profile = UserProfile(
        user_id=user.id,
        first_name=user_data.first_name if hasattr(user_data, 'first_name') else None,
        last_name=user_data.last_name if hasattr(user_data, 'last_name') else None,
        phone=user_data.phone if hasattr(user_data, 'phone') else None
    )
    
    db.add(profile)
    db.commit()
    
    # Create audit log
    create_audit_log(db, current_user.id, "create_user", f"Created user: {user.username}")
    
    return {
        "message": "User created successfully",
        "data": {"user": user}
    }


@router.put("/{user_id}", response_model=dict)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Update user (admin, super_admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update user fields
    update_data = user_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(user, field):
            setattr(user, field, value)
    
    db.commit()
    db.refresh(user)
    
    # Create audit log
    create_audit_log(db, current_user.id, "update_user", f"Updated user: {user.username}")
    
    return {
        "message": "User updated successfully",
        "data": {"user": user}
    }


@router.delete("/{user_id}", response_model=dict)
async def delete_user(
    user_id: int,
    current_user: User = Depends(require_roles(["super_admin"])),
    db: Session = Depends(get_db)
):
    """Delete user (super_admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    username = user.username
    db.delete(user)
    db.commit()
    
    # Create audit log
    create_audit_log(db, current_user.id, "delete_user", f"Deleted user: {username}")
    
    return {
        "message": "User deleted successfully",
        "data": None
    }


@router.patch("/{user_id}/block", response_model=dict)
async def block_user(
    user_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Block user (admin, super_admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot block your own account"
        )
    
    user.is_blocked = True
    db.commit()
    db.refresh(user)
    
    # Create audit log
    create_audit_log(db, current_user.id, "block_user", f"Blocked user: {user.username}")
    
    return {
        "message": "User blocked successfully",
        "data": {"user": user}
    }


@router.patch("/{user_id}/unblock", response_model=dict)
async def unblock_user(
    user_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Unblock user (admin, super_admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    user.is_blocked = False
    db.commit()
    db.refresh(user)
    
    # Create audit log
    create_audit_log(db, current_user.id, "unblock_user", f"Unblocked user: {user.username}")
    
    return {
        "message": "User unblocked successfully",
        "data": {"user": user}
    }


@router.post("/change-password", response_model=dict)
async def change_password(
    password_data: ChangePasswordSchema,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Change current user's password."""
    # Verify current password
    if not verify_password(password_data.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    current_user.hashed_password = get_password_hash(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()
    
    # Create audit log
    create_audit_log(db, current_user.id, "change_password", f"Password changed for user: {current_user.username}")
    
    return {
        "message": "Password changed successfully",
        "data": None
    }


@router.post("/{user_id}/reset-password", response_model=dict)
async def reset_user_password(
    user_id: int,
    new_password: str = Query(..., min_length=8, description="New password for the user"),
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Reset user password (admin, super_admin only)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Update password
    user.hashed_password = get_password_hash(new_password)
    user.updated_at = datetime.utcnow()
    db.commit()
    
    # Create audit log
    create_audit_log(db, current_user.id, "reset_password", f"Reset password for user: {user.username}")
    
    return {
        "message": "Password reset successfully",
        "data": None
    }


@router.get("/roles/available", response_model=dict)
async def get_available_roles(
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Get all available user roles."""
    roles = ["super_admin", "admin", "inventorymanager", "viewer"]
    
    return {
        "message": "Available roles fetched successfully",
        "data": {"roles": roles}
    }