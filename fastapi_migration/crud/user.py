from sqlalchemy.orm import Session
from models.user import User, UserProfile, AuditLog
from schemas.user import UserCreate
from core.security import get_password_hash
from typing import Optional


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user by ID."""
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_profile_uuid(db: Session, uuid: str) -> Optional[User]:
    """Get user by profile UUID."""
    return db.query(User).join(UserProfile).filter(UserProfile.uuid == uuid).first()


def create_user(db: Session, user: UserCreate) -> User:
    """Create new user with profile."""
    # Create user
    hashed_password = get_password_hash(user.password)
    db_user = User(
        email=user.email,
        hashed_password=hashed_password,
        is_active=True
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # Create profile
    db_profile = UserProfile(
        user_id=db_user.id,
        role=user.role,
        name=user.name,
        phone_number=user.phone_number,
        latitude=user.latitude,
        longitude=user.longitude
    )
    db.add(db_profile)
    db.commit()
    db.refresh(db_profile)
    
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    """Authenticate user."""
    from core.security import verify_password
    user = get_user_by_email(db, email)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def get_users(db: Session, skip: int = 0, limit: int = 100, role: Optional[str] = None):
    """Get users with optional role filter."""
    query = db.query(User).join(UserProfile)
    if role:
        query = query.filter(UserProfile.role == role)
    return query.offset(skip).limit(limit).all()


def update_user_password(db: Session, user: User, new_password: str):
    """Update user password."""
    user.hashed_password = get_password_hash(new_password)
    db.commit()
    db.refresh(user)
    return user


def block_user(db: Session, user: User):
    """Block user."""
    if user.profile:
        user.profile.blocked = True
        db.commit()
        db.refresh(user.profile)
    return user


def unblock_user(db: Session, user: User):
    """Unblock user."""
    if user.profile:
        user.profile.blocked = False
        db.commit()
        db.refresh(user.profile)
    return user


def create_audit_log(db: Session, user_id: int, action: str, details: str = None):
    """Create audit log entry."""
    audit_log = AuditLog(
        user_id=user_id,
        action=action,
        details=details
    )
    db.add(audit_log)
    db.commit()
    return audit_log