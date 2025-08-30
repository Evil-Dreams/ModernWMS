from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel
from pydantic import AliasChoices
from typing import Any, Optional

class ResultModel(BaseModel):
    isSuccess: bool = Field(..., alias="isSuccess")
    code: int
    errorMessage: str
    data: Any | None = None

    class Config:
        populate_by_name = True

# Auth schemas
class LoginInput(BaseModel):
    user_name: str
    password: str
    remember: bool = False

class TokenData(BaseModel):
    user_id: int
    user_name: str
    user_role: str
    tenant_id: int

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str

class LoginResponse(BaseModel):
    user_id: int
    user_name: str
    user_num: str
    user_role: str
    userrole_id: int
    tenant_id: int
    token: Token

# Product schemas
class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    barcode: Optional[str] = None
    category: Optional[str] = None
    weight: float = 0.0
    weight_unit: str = "kg"
    length: float = 0.0
    width: float = 0.0
    height: float = 0.0
    dimension_unit: str = "cm"
    is_active: bool = True

class ProductCreate(ProductBase):
    pass

class ProductUpdate(ProductBase):
    pass

class ProductInDB(ProductBase):
    id: int
    create_time: datetime
    last_update_time: datetime

    class Config:
        orm_mode = True

# Warehouse schemas
class WarehouseBase(BaseModel):
    code: str
    name: str
    address: Optional[str] = None
    contact_person: Optional[str] = None
    contact_phone: Optional[str] = None
    is_active: bool = True

class WarehouseCreate(WarehouseBase):
    pass

class WarehouseUpdate(WarehouseBase):
    pass

class WarehouseInDB(WarehouseBase):
    id: int
    create_time: datetime
    last_update_time: datetime

    class Config:
        orm_mode = True

# Location schemas
class LocationBase(BaseModel):
    warehouse_id: int
    location_code: str
    location_name: Optional[str] = None
    zone: Optional[str] = None
    aisle: Optional[str] = None
    rack: Optional[str] = None
    level: Optional[str] = None
    position: Optional[str] = None
    location_type: Optional[str] = None
    max_volume: Optional[float] = None
    max_weight: Optional[float] = None
    is_active: bool = True

class LocationCreate(LocationBase):
    pass

class LocationUpdate(LocationBase):
    pass

class LocationInDB(LocationBase):
    id: int
    create_time: datetime
    last_update_time: datetime

    class Config:
        orm_mode = True

# Inventory schemas
class InventoryBase(BaseModel):
    product_id: int
    warehouse_id: int
    location_id: int
    quantity: float
    allocated_quantity: float = 0
    available_quantity: float = 0
    lot_number: Optional[str] = None
    serial_number: Optional[str] = None
    expiry_date: Optional[datetime] = None

class InventoryCreate(InventoryBase):
    pass

class InventoryUpdate(InventoryBase):
    pass

class InventoryInDB(InventoryBase):
    id: int
    create_time: datetime
    last_update_time: datetime

    class Config:
        orm_mode = True

# Response schemas
class PaginatedResponse(BaseResponse):
    data: Dict[str, Any] = Field(default_factory=dict)
    pagination: Optional[Pagination] = None

def success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    return {
        "code": 0,
        "message": message,
        "data": data
    }

def error_response(message: str, code: int = 1, data: Any = None) -> Dict[str, Any]:
    return {
        "code": code,
        "message": message,
        "data": data
    }

def result_success(data: Any, errMsg: str = "") -> dict:
    return {"isSuccess": True, "code": 200, "errorMessage": errMsg, "data": data}

def result_error(msg: str, code: int = 400, data: Any | None = None) -> dict:
    return {"isSuccess": False, "code": code, "errorMessage": msg, "data": data}
