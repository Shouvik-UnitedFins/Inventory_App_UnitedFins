from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime
from decimal import Decimal


# Vendor Schemas
class VendorBase(BaseModel):
    name: str
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None


class VendorCreate(VendorBase):
    pass


class VendorUpdate(BaseModel):
    name: Optional[str] = None
    contact_person: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    postal_code: Optional[str] = None
    website: Optional[str] = None
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    is_active: Optional[bool] = None


class VendorResponse(VendorBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Product Schemas  
class ProductBase(BaseModel):
    name: str
    description: Optional[str] = None
    sku: str
    price: Decimal
    category: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    min_stock_level: Optional[int] = 0


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    price: Optional[Decimal] = None
    category: Optional[str] = None
    brand: Optional[str] = None
    unit: Optional[str] = None
    min_stock_level: Optional[int] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Category Schemas
class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    children: Optional[List["CategoryResponse"]] = []

    class Config:
        from_attributes = True


# Inventory Schemas
class InventoryBase(BaseModel):
    product_id: int
    vendor_id: Optional[int] = None
    quantity_on_hand: int = 0
    quantity_reserved: int = 0
    quantity_available: int = 0
    location: Optional[str] = None
    warehouse: Optional[str] = None
    shelf: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    cost_per_unit: Optional[Decimal] = None
    notes: Optional[str] = None


class InventoryCreate(InventoryBase):
    pass


class InventoryUpdate(BaseModel):
    vendor_id: Optional[int] = None
    quantity_on_hand: Optional[int] = None
    quantity_reserved: Optional[int] = None
    quantity_available: Optional[int] = None
    location: Optional[str] = None
    warehouse: Optional[str] = None
    shelf: Optional[str] = None
    batch_number: Optional[str] = None
    expiry_date: Optional[datetime] = None
    cost_per_unit: Optional[Decimal] = None
    notes: Optional[str] = None
    is_active: Optional[bool] = None


class InventoryResponse(InventoryBase):
    id: int
    last_counted: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    last_updated: datetime

    class Config:
        from_attributes = True


# API Response wrapper
class APIResponse(BaseModel):
    message: str
    data: Optional[dict] = None
    error: Optional[str] = None