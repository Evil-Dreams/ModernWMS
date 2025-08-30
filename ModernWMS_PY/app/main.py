import logging
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import select
import uvicorn

from .config import APP_PORT, JWT_SECRET
from .database import Base, engine, get_db
from .models import User, Warehouse, Location, Product
from .routers import (
    auth as auth_router,
    products as products_router,
    warehouses as warehouses_router,
    locations as locations_router,
    inventory as inventory_router
)
from .utils.hash import md5_hex

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ModernWMS_PY",
    description="A modern Warehouse Management System built with FastAPI",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router.router, prefix="/api")
app.include_router(products_router.router, prefix="/api")
app.include_router(warehouses_router.router, prefix="/api")
app.include_router(locations_router.router, prefix="/api")
app.include_router(inventory_router.router, prefix="/api")

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"message": "An unexpected error occurred", "detail": str(exc)},
    )

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    logger.error(f"Validation error: {exc}")
    return JSONResponse(
        status_code=422,
        content={"message": "Validation error", "detail": exc.errors()},
    )

@app.on_event("startup")
async def on_startup():
    try:
        # Create database tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created")
        
        # Seed initial data if needed
        with next(get_db()) as db:
            # Create admin user if not exists
            admin = db.execute(select(User).where(User.user_name == "admin")).scalar_one_or_none()
            if not admin:
                admin_user = User(
                    user_num="admin",
                    user_name="admin",
                    password=md5_hex("1"),  # Default password is '1'
                    user_role="admin",
                    userrole_id=1,
                    tenant_id=1,
                    email="admin@example.com"
                )
                db.add(admin_user)
                logger.info("Created admin user")
            
            # Create default warehouse if not exists
            warehouse = db.execute(select(Warehouse).where(Warehouse.code == "DEFAULT")).scalar_one_or_none()
            if not warehouse:
                default_warehouse = Warehouse(
                    code="DEFAULT",
                    name="Default Warehouse",
                    address="Default address",
                    is_active=True
                )
                db.add(default_warehouse)
                db.flush()  # To get the warehouse ID
                
                # Create a default location
                default_location = Location(
                    warehouse_id=default_warehouse.id,
                    location_code="DEFAULT-001",
                    location_name="Default Location",
                    location_type="STORAGE",
                    is_active=True
                )
                db.add(default_location)
                logger.info("Created default warehouse and location")
            
            db.commit()
            
    except Exception as e:
        logger.error(f"Error during startup: {str(e)}", exc_info=True)
        if 'db' in locals():
            db.rollback()
        raise

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "version": "1.0.0",
        "database": "connected"  # In a real app, you'd check DB connection
    }
