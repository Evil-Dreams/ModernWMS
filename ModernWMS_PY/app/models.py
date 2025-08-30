from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, BigInteger, Boolean, Numeric
from sqlalchemy.orm import relationship, Mapped, mapped_column
from .database import Base

class BaseMixin:
    create_time = Column(DateTime, default=datetime.utcnow)
    last_update_time = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_valid = Column(Boolean, default=True)
    is_deleted = Column(Boolean, default=False)

class User(Base, BaseMixin):
    __tablename__ = "users"

    user_id: Mapped[int] = mapped_column("user_id", Integer, primary_key=True, index=True, autoincrement=True)
    user_num: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    user_name: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    password: Mapped[str] = mapped_column(String(64))  # MD5 hex
    user_role: Mapped[str] = mapped_column(String(128), default="admin")
    userrole_id: Mapped[int] = mapped_column(Integer, default=1)
    tenant_id: Mapped[int] = mapped_column(BigInteger, default=1)
    email: Mapped[str] = mapped_column(String(255), nullable=True)
    phone: Mapped[str] = mapped_column(String(50), nullable=True)
    avatar: Mapped[str] = mapped_column(String(500), nullable=True)

class Product(Base, BaseMixin):
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    sku = Column(String(100), unique=True, index=True, nullable=False)
    name = Column(String(200), nullable=False)
    description = Column(String(1000), nullable=True)
    barcode = Column(String(100), unique=True, nullable=True)
    category = Column(String(100), nullable=True)
    weight = Column(Float, default=0.0)
    weight_unit = Column(String(10), default='kg')
    length = Column(Float, default=0.0)
    width = Column(Float, default=0.0)
    height = Column(Float, default=0.0)
    dimension_unit = Column(String(10), default='cm')
    is_active = Column(Boolean, default=True)
    
    # Relationships
    inventory_items = relationship("Inventory", back_populates="product")

class Warehouse(Base, BaseMixin):
    __tablename__ = "warehouses"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(200), nullable=False)
    address = Column(String(500), nullable=True)
    contact_person = Column(String(100), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    locations = relationship("Location", back_populates="warehouse")
    inventory_items = relationship("Inventory", back_populates="warehouse")

class Location(Base, BaseMixin):
    __tablename__ = "locations"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    location_code = Column(String(50), nullable=False)
    location_name = Column(String(200), nullable=True)
    zone = Column(String(100), nullable=True)
    aisle = Column(String(50), nullable=True)
    rack = Column(String(50), nullable=True)
    level = Column(String(50), nullable=True)
    position = Column(String(50), nullable=True)
    location_type = Column(String(50), nullable=True)  # e.g., 'PICKING', 'STORAGE', 'RECEIVING', 'SHIPPING'
    max_volume = Column(Float, nullable=True)
    max_weight = Column(Float, nullable=True)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    warehouse = relationship("Warehouse", back_populates="locations")
    inventory_items = relationship("Inventory", back_populates="location")

class Inventory(Base, BaseMixin):
    __tablename__ = "inventory"
    
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)
    warehouse_id = Column(Integer, ForeignKey("warehouses.id"), nullable=False)
    location_id = Column(Integer, ForeignKey("locations.id"), nullable=False)
    quantity = Column(Numeric(12, 4), default=0, nullable=False)
    allocated_quantity = Column(Numeric(12, 4), default=0, nullable=False)
    available_quantity = Column(Numeric(12, 4), default=0, nullable=False)
    lot_number = Column(String(100), nullable=True)
    serial_number = Column(String(100), nullable=True)
    expiry_date = Column(DateTime, nullable=True)
    
    # Relationships
    product = relationship("Product", back_populates="inventory_items")
    warehouse = relationship("Warehouse", back_populates="inventory_items")
    location = relationship("Location", back_populates="inventory_items")
