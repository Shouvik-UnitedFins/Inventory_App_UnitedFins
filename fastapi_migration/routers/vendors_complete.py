from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from database import get_db
from schemas.complete import VendorCreate, VendorUpdate, VendorResponse, APIResponse
from core.security import get_current_user, require_roles
from models.user import User
from models.vendor_complete import Vendor
from crud.user import create_audit_log

router = APIRouter()


@router.get("/", response_model=dict)
async def list_vendors(
    skip: int = Query(0, ge=0, description="Number of vendors to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of vendors to return"),
    search: Optional[str] = Query(None, description="Search vendors by name"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all vendors with pagination and filtering."""
    query = db.query(Vendor)
    
    # Apply filters
    if search:
        query = query.filter(Vendor.name.ilike(f"%{search}%"))
    if is_active is not None:
        query = query.filter(Vendor.is_active == is_active)
    
    # Get total count
    total = query.count()
    
    # Apply pagination
    vendors = query.offset(skip).limit(limit).all()
    
    return {
        "message": "Vendors fetched successfully",
        "data": {
            "vendors": vendors,
            "total": total,
            "skip": skip,
            "limit": limit
        }
    }


@router.get("/{vendor_id}", response_model=dict)
async def get_vendor(
    vendor_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get vendor by ID."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    return {
        "message": "Vendor fetched successfully",
        "data": {"vendor": vendor}
    }


@router.post("/", response_model=dict)
async def create_vendor(
    vendor_data: VendorCreate,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Create new vendor (admin, super_admin, inventorymanager only)."""
    # Check if vendor with same name exists
    existing_vendor = db.query(Vendor).filter(Vendor.name == vendor_data.name).first()
    if existing_vendor:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Vendor with this name already exists"
        )
    
    # Create vendor
    vendor = Vendor(**vendor_data.dict())
    db.add(vendor)
    db.commit()
    db.refresh(vendor)
    
    # Create audit log
    create_audit_log(db, current_user.id, "create_vendor", f"Created vendor: {vendor.name}")
    
    return {
        "message": "Vendor created successfully",
        "data": {"vendor": vendor}
    }


@router.put("/{vendor_id}", response_model=dict)
async def update_vendor(
    vendor_id: int,
    vendor_data: VendorUpdate,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Update vendor (admin, super_admin, inventorymanager only)."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    # Update vendor fields
    update_data = vendor_data.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(vendor, field, value)
    
    db.commit()
    db.refresh(vendor)
    
    # Create audit log
    create_audit_log(db, current_user.id, "update_vendor", f"Updated vendor: {vendor.name}")
    
    return {
        "message": "Vendor updated successfully",
        "data": {"vendor": vendor}
    }


@router.delete("/{vendor_id}", response_model=dict)
async def delete_vendor(
    vendor_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin"])),
    db: Session = Depends(get_db)
):
    """Delete vendor (admin, super_admin only)."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    vendor_name = vendor.name
    db.delete(vendor)
    db.commit()
    
    # Create audit log
    create_audit_log(db, current_user.id, "delete_vendor", f"Deleted vendor: {vendor_name}")
    
    return {
        "message": "Vendor deleted successfully",
        "data": None
    }


@router.patch("/{vendor_id}/toggle-status", response_model=dict)
async def toggle_vendor_status(
    vendor_id: int,
    current_user: User = Depends(require_roles(["admin", "super_admin", "inventorymanager"])),
    db: Session = Depends(get_db)
):
    """Toggle vendor active/inactive status."""
    vendor = db.query(Vendor).filter(Vendor.id == vendor_id).first()
    if not vendor:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Vendor not found"
        )
    
    vendor.is_active = not vendor.is_active
    db.commit()
    db.refresh(vendor)
    
    status_text = "activated" if vendor.is_active else "deactivated"
    create_audit_log(db, current_user.id, "toggle_vendor_status", f"Vendor {vendor.name} {status_text}")
    
    return {
        "message": f"Vendor {status_text} successfully",
        "data": {"vendor": vendor}
    }