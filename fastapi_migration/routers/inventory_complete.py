from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from schemas.complete import InventoryCreate, InventoryUpdate, InventoryResponse, APIResponse
from core.security import get_current_user, require_roles
from models.user import User
from models.inventory import Inventory
from models.product import Product
from crud.user import create_audit_log

router = APIRouter()


@router.get("/", response_model=dict)
async def list_inventory(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    product_search: Optional[str] = Query(None, description="Search products by name"),
    location: Optional[str] = Query(None, description="Filter by location"),
    low_stock_only: bool = Query(False, description="Show only low stock items"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all inventory items with pagination and filtering."""
    query = db.query(Inventory).join(Product)
    
    # Apply filters
    if product_id:
        query = query.filter(Inventory.product_id == product_id)
    if product_search:
        query = query.filter(Product.name.ilike(f"%{product_search}%"))
    if location:
        query = query.filter(Inventory.location.ilike(f"%{location}%"))
    if low_stock_only:
        query = query.filter(
            (Inventory.quantity <= Inventory.reorder_level) | 
            (Inventory.quantity <= 0)
        )
    
    # Get total count
    total = query.count()
    
    # Apply pagination and order by product name
    inventory_items = query.order_by(Product.name).offset(skip).limit(limit).all()
    
    return {
        "message": "Inventory items fetched successfully",
        "data": {
            "inventory": inventory_items,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }


@router.get("/low-stock", response_model=dict)
async def get_low_stock_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all low stock items."""
    low_stock_items = db.query(Inventory).join(Product).filter(
        (Inventory.quantity <= Inventory.reorder_level) | 
        (Inventory.quantity <= 0)
    ).order_by(Inventory.quantity.asc()).all()
    
    return {
        "message": "Low stock items fetched successfully",
        "data": {
            "low_stock_items": low_stock_items,
            "count": len(low_stock_items)
        }
    }


@router.get("/locations", response_model=dict)
async def get_all_locations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all unique inventory locations."""
    locations = db.query(Inventory.location).distinct().filter(
        Inventory.location.isnot(None)
    ).all()
    
    location_list = [loc[0] for loc in locations if loc[0]]
    
    return {
        "message": "Locations fetched successfully",
        "data": {"locations": location_list}
    }


@router.get("/{inventory_id}", response_model=dict)
async def get_inventory_item(
    inventory_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get inventory item by ID."""
    inventory_item = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    return {
        "message": "Inventory item fetched successfully",
        "data": {"inventory_item": inventory_item}
    }


@router.post("/", response_model=dict)
async def create_inventory_item(
    inventory_data: InventoryCreate,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Create new inventory item (admin, super_admin, inventorymanager only)."""
    # Check if product exists
    product = db.query(Product).filter(Product.id == inventory_data.product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    # Check if inventory for this product and location already exists
    existing_inventory = db.query(Inventory).filter(
        Inventory.product_id == inventory_data.product_id,
        Inventory.location == inventory_data.location
    ).first()
    
    if existing_inventory:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inventory for this product and location already exists"
        )
    
    # Create inventory item
    inventory_item = Inventory(**inventory_data.dict())
    db.add(inventory_item)
    db.commit()
    db.refresh(inventory_item)
    
    # Create audit log
    create_audit_log(
        db, current_user.id, "create_inventory", 
        f"Created inventory for product {product.name} at {inventory_item.location}"
    )
    
    return {
        "message": "Inventory item created successfully",
        "data": {"inventory_item": inventory_item}
    }


@router.put("/{inventory_id}", response_model=dict)
async def update_inventory_item(
    inventory_id: int,
    inventory_data: InventoryUpdate,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Update inventory item (admin, super_admin, inventorymanager only)."""
    inventory_item = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    # Update inventory fields
    update_data = inventory_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inventory_item, field, value)
    
    db.commit()
    db.refresh(inventory_item)
    
    # Create audit log
    create_audit_log(
        db, current_user.id, "update_inventory", 
        f"Updated inventory item ID {inventory_id}"
    )
    
    return {
        "message": "Inventory item updated successfully",
        "data": {"inventory_item": inventory_item}
    }


@router.delete("/{inventory_id}", response_model=dict)
async def delete_inventory_item(
    inventory_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Delete inventory item (admin, super_admin only)."""
    inventory_item = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    inventory_info = f"ID {inventory_item.id} - Product ID {inventory_item.product_id}"
    db.delete(inventory_item)
    db.commit()
    
    # Create audit log
    create_audit_log(
        db, current_user.id, "delete_inventory", 
        f"Deleted inventory item: {inventory_info}"
    )
    
    return {
        "message": "Inventory item deleted successfully",
        "data": None
    }


@router.post("/{inventory_id}/adjust-stock", response_model=dict)
async def adjust_stock(
    inventory_id: int,
    adjustment: int = Query(..., description="Stock adjustment amount (positive to add, negative to subtract)"),
    reason: Optional[str] = Query(None, description="Reason for stock adjustment"),
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Adjust inventory stock level."""
    inventory_item = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inventory_item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Inventory item not found"
        )
    
    old_quantity = inventory_item.quantity
    new_quantity = old_quantity + adjustment
    
    if new_quantity < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock quantity cannot be negative"
        )
    
    inventory_item.quantity = new_quantity
    db.commit()
    db.refresh(inventory_item)
    
    # Create audit log
    reason_text = f" - Reason: {reason}" if reason else ""
    create_audit_log(
        db, current_user.id, "adjust_stock", 
        f"Adjusted stock for inventory ID {inventory_id}: {old_quantity} → {new_quantity} (adjustment: {adjustment:+d}){reason_text}"
    )
    
    return {
        "message": "Stock adjusted successfully",
        "data": {
            "inventory_item": inventory_item,
            "old_quantity": old_quantity,
            "adjustment": adjustment,
            "new_quantity": new_quantity
        }
    }


@router.get("/product/{product_id}", response_model=dict)
async def get_product_inventory(
    product_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all inventory records for a specific product."""
    # Check if product exists
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Product not found"
        )
    
    inventory_items = db.query(Inventory).filter(Inventory.product_id == product_id).all()
    
    total_quantity = sum(item.quantity for item in inventory_items)
    
    return {
        "message": "Product inventory fetched successfully",
        "data": {
            "product": product,
            "inventory_items": inventory_items,
            "total_quantity": total_quantity,
            "locations_count": len(inventory_items)
        }
    }