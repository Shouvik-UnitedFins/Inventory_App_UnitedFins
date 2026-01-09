from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text, Boolean, Numeric
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=True)
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    quantity_available = Column(Integer, nullable=False, default=0)
    location = Column(String(100), nullable=True)
    warehouse = Column(String(100), nullable=True)
    shelf = Column(String(50), nullable=True)
    batch_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    cost_per_unit = Column(Numeric(10, 2), nullable=True)
    notes = Column(Text, nullable=True)
    last_counted = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    product = relationship("Product")
    vendor = relationship("Vendor")

    def __str__(self):
        return f"Inventory for {self.product.name if self.product else 'Unknown'} - Qty: {self.quantity_on_hand}"