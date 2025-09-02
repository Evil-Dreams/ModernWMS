# ModernWMS_Python

A Python-based Warehouse Management System backend using FastAPI and PostgreSQL.

## Features
- Inventory management
- Warehouse operations
- Product, location, and user management
- RESTful API

## Tech Stack
- FastAPI
- SQLAlchemy
- PostgreSQL
- Alembic
- Pydantic

## Setup
1. Create a Python virtual environment:
   ```powershell
   python -m venv venv
   .\venv\Scripts\activate
   ```
2. Install dependencies:
   ```powershell
   pip install -r requirements.txt
   ```
3. Configure your PostgreSQL connection in `app/config.py`.
4. Run the server:
   ```powershell
   uvicorn app.main:app --reload
   ```

## Database
- PostgreSQL 17
- Default port: 5432
- Superuser: postgres

## API Docs
- Swagger UI: `/docs`
- Redoc: `/redoc`
