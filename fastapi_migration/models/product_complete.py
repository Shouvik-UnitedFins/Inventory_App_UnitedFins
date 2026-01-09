from sqlalchemy import Column, Integer, String, Text, DateTime, Numeric
from sqlalchemy.sql import func
from database import Base


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(100), nullable=True)
    brand = Column(String(100), nullable=True)
    unit = Column(String(50), nullable=True)  # kg, liter, piece, etc.
    min_stock_level = Column(Integer, default=0)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    is_active = Column(Boolean, default=True)

    def __str__(self):
        return f"{self.name} ({self.sku})"