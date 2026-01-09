from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from schemas.complete import CategoryCreate, CategoryUpdate, CategoryResponse, APIResponse
from core.security import get_current_user, require_roles
from models.user import User
from models.category import Category
from crud.user import create_audit_log

router = APIRouter()


@router.get("/", response_model=dict)
async def list_categories(
    skip: int = Query(0, ge=0, description="Number of categories to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of categories to return"),
    search: Optional[str] = Query(None, description="Search categories by name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    parent_only: bool = Query(False, description="Get only parent categories"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all categories with pagination and filtering."""
    query = db.query(Category)
    
    # Apply filters
    if search:
        query = query.filter(Category.name.ilike(f"%{search}%"))
    if is_active is not None:
        query = query.filter(Category.is_active == is_active)
    if parent_only:
        query = query.filter(Category.parent_id.is_(None))
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    categories = query.offset(skip).limit(limit).all()
    
    return {
        "message": "Categories fetched successfully",
        "data": {
            "categories": categories,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }


@router.get("/{category_id}", response_model=dict)
async def get_category(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get category by ID with its children."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    return {
        "message": "Category fetched successfully",
        "data": {"category": category}
    }


@router.post("/", response_model=dict)
async def create_category(
    category_data: CategoryCreate,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Create new category (admin, super_admin, inventorymanager only)."""
    # Check if category with same name exists
    existing_category = db.query(Category).filter(Category.name == category_data.name).first()
    if existing_category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category with this name already exists"
        )
    
    # If parent_id is provided, check if parent exists
    if category_data.parent_id:
        parent = db.query(Category).filter(Category.id == category_data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )
    
    # Create category
    category = Category(**category_data.dict())
    db.add(category)
    db.commit()
    db.refresh(category)
    
    # Create audit log
    create_audit_log(db, current_user.id, "create_category", f"Created category: {category.name}")
    
    return {
        "message": "Category created successfully",
        "data": {"category": category}
    }


@router.put("/{category_id}", response_model=dict)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Update category (admin, super_admin, inventorymanager only)."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # If parent_id is being updated, check if parent exists
    if category_data.parent_id and category_data.parent_id != category.parent_id:
        if category_data.parent_id == category_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category cannot be its own parent"
            )
        parent = db.query(Category).filter(Category.id == category_data.parent_id).first()
        if not parent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Parent category not found"
            )
    
    # Update category fields
    update_data = category_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(category, field, value)
    
    db.commit()
    db.refresh(category)
    
    # Create audit log
    create_audit_log(db, current_user.id, "update_category", f"Updated category: {category.name}")
    
    return {
        "message": "Category updated successfully",
        "data": {"category": category}
    }


@router.delete("/{category_id}", response_model=dict)
async def delete_category(
    category_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Delete category (admin, super_admin only)."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    # Check if category has children
    children = db.query(Category).filter(Category.parent_id == category_id).count()
    if children > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category with subcategories. Delete subcategories first."
        )
    
    category_name = category.name
    db.delete(category)
    db.commit()
    
    # Create audit log
    create_audit_log(db, current_user.id, "delete_category", f"Deleted category: {category_name}")
    
    return {
        "message": "Category deleted successfully",
        "data": None
    }


@router.get("/{category_id}/children", response_model=dict)
async def get_category_children(
    category_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all child categories of a parent category."""
    parent = db.query(Category).filter(Category.id == category_id).first()
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent category not found"
        )
    
    children = db.query(Category).filter(Category.parent_id == category_id).all()
    
    return {
        "message": "Child categories fetched successfully",
        "data": {
            "parent": parent,
            "children": children
        }
    }


@router.patch("/{category_id}/toggle-status", response_model=dict)
async def toggle_category_status(
    category_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Toggle category active/inactive status."""
    category = db.query(Category).filter(Category.id == category_id).first()
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Category not found"
        )
    
    category.is_active = not category.is_active
    db.commit()
    db.refresh(category)
    
    status_text = "activated" if category.is_active else "deactivated"
    create_audit_log(db, current_user.id, "toggle_category_status", f"Category {category.name} {status_text}")
    
    return {
        "message": f"Category {status_text} successfully",
        "data": {"category": category}
    }