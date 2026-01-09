from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(Integer, primary_key=True, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    quantity = Column(Integer, nullable=False, default=0)
    location = Column(String, nullable=True)
    notes = Column(Text, nullable=True)
    last_updated = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationship to product
    product = relationship("Product")