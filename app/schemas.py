from pydantic import BaseModel
from typing import Optional
import datetime

class WarehouseBase(BaseModel):
    name: str
    location: str

class WarehouseCreate(WarehouseBase):
    pass

class Warehouse(WarehouseBase):
    id: int
    created_at: datetime.datetime
    class Config:
        orm_mode = True

class ProductBase(BaseModel):
    name: str
    sku: str
    quantity: int
    warehouse_id: int

class ProductCreate(ProductBase):
    pass

class Product(ProductBase):
    id: int
    class Config:
        orm_mode = True
