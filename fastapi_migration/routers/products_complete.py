from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from schemas.complete import ProductCreate, ProductUpdate, ProductResponse, APIResponse
from core.security import get_current_user, require_roles
from models.user import User
from models.product_complete import Product
from crud.user import create_audit_log

router = APIRouter()


@router.get("/", response_model=dict)
async def list_products(
    skip: int = Query(0, ge=0, description="Number of products to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of products to return"),
    search: Optional[str] = Query(None, description="Search products by name or SKU"),
    category: Optional[str] = Query(None, description="Filter by category"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all products with pagination and filtering."""
    query = db.query(Product)
    
    # Apply filters
    if search:
        query = query.filter(
            (Product.name.ilike(f"%{search}%")) | 
            (Product.sku.ilike(f"%{search}%"))
        )
    if category:
        query = query.filter(Product.category == category)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    products = query.offset(skip).limit(limit).all()
    
    return {
        "message": "Products fetched successfully",
        "data": {
            "products": products,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }


@router.get("/{product_id}", response_model=dict)
async def get_product(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get product by ID."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    return {
        "message": "Product fetched successfully",
        "data": {"product": product}
    }


@router.post("/", response_model=dict)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Create new product (admin, super_admin, inventorymanager only)."""
    # Check if product with same SKU exists
    existing_product = db.query(Product).filter(Product.sku == product_data.sku).first()
    if existing_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product with this SKU already exists"
        )
    
    # Create product
    product = Product(**product_data.dict())
    db.add(product)
    db.commit()
    db.refresh(product)
    
    # Create audit log
    create_audit_log(db, current_user.id, "create_product", f"Created product: {product.name} ({product.sku})")
    
    return {
        "message": "Product created successfully",
        "data": {"product": product}
    }


@router.put("/{product_id}", response_model=dict)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Update product (admin, super_admin, inventorymanager only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Update product fields
    update_data = product_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(product, field, value)
    
    db.commit()
    db.refresh(product)
    
    # Create audit log
    create_audit_log(db, current_user.id, "update_product", f"Updated product: {product.name} ({product.sku})")
    
    return {
        "message": "Product updated successfully",
        "data": {"product": product}
    }


@router.delete("/{product_id}", response_model=dict)
async def delete_product(
    product_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Delete product (admin, super_admin only)."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product_info = f"{product.name} ({product.sku})"
    db.delete(product)
    db.commit()
    
    # Create audit log
    create_audit_log(db, current_user.id, "delete_product", f"Deleted product: {product_info}")
    
    return {
        "message": "Product deleted successfully",
        "data": None
    }


@router.get("/categories/list", response_model=dict)
async def list_product_categories(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of all unique product categories."""
    categories = db.query(Product.category).filter(Product.category.isnot(None)).distinct().all()
    category_list = [cat[0] for cat in categories if cat[0]]
    
    return {
        "message": "Product categories fetched successfully",
        "data": {"categories": category_list}
    }


@router.patch("/{product_id}/toggle-status", response_model=dict)
async def toggle_product_status(
    product_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Toggle product active/inactive status."""
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    product.is_active = not product.is_active
    db.commit()
    db.refresh(product)
    
    status_text = "activated" if product.is_active else "deactivated"
    create_audit_log(db, current_user.id, "toggle_product_status", f"Product {product.name} {status_text}")
    
    return {
        "message": f"Product {status_text} successfully",
        "data": {"product": product}
    }