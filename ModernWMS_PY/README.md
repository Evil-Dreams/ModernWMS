# ModernWMS_PY

A modern Warehouse Management System (WMS) built with FastAPI and PostgreSQL. This system provides comprehensive inventory management, warehouse operations, and reporting capabilities.

## Features

- **User Authentication & Authorization**
  - JWT-based authentication
  - Role-based access control
  - User management

- **Product Management**
  - SKU and barcode support
  - Product categories and attributes
  - Unit of measure management

- **Warehouse Management**
  - Multiple warehouse support
  - Location management with zone/aisle/rack/level/position
  - Storage capacity tracking

- **Inventory Management**
  - Real-time inventory tracking
  - Lot and serial number tracking
  - Expiration date tracking
  - Stock movements and adjustments

- **API Documentation**
  - Interactive API docs with Swagger UI
  - ReDoc documentation
  - OpenAPI 3.0 specification

## Prerequisites

- Python 3.9+
- PostgreSQL 13+
- Redis (for caching and background tasks)
- Git

## Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ModernWMS_PY.git
cd ModernWMS_PY
```

### 2. Set up a virtual environment

```bash
# Windows
python -m venv venv
.\venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root with the following content:

```env
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=modernwms
POSTGRES_USER=postgres
POSTGRES_PASSWORD=your_password

# JWT
JWT_SECRET=your_jwt_secret_key
JWT_ISSUER=ModernWMS.Py
JWT_AUDIENCE=ModernWMS.Client
JWT_EXPIRE_MINUTES=1440  # 24 hours

# App
APP_PORT=8000
ENVIRONMENT=development

# Redis (for caching)
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 5. Set up the database

1. Create a new PostgreSQL database named `modernwms`
2. Run migrations:

```bash
alembic upgrade head
```

### 6. Run the application

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## API Documentation

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

## Default Admin User

- **Username**: admin
- **Password**: 1

## Project Structure

```
ModernWMS_PY/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI application
│   ├── config.py            # Application configuration
│   ├── database.py          # Database configuration
│   ├── models.py            # SQLAlchemy models
│   ├── schemas.py           # Pydantic models
│   ├── security.py          # Authentication utilities
│   ├── cache.py             # Caching utilities
│   ├── utils/               # Utility modules
│   └── routers/             # API route handlers
│       ├── __init__.py
│       ├── auth.py          # Authentication routes
│       ├── products.py      # Product management
│       ├── warehouses.py    # Warehouse management
│       ├── locations.py     # Location management
│       └── inventory.py     # Inventory management
├── alembic/                 # Database migrations
├── tests/                   # Test files
├── .env.example             # Example environment variables
├── requirements.txt         # Python dependencies
└── README.md                # This file
```

## Development

### Running Tests

```bash
pytest
```

### Code Formatting

```bash
# Auto-format code
black .

# Sort imports
isort .

# Type checking
mypy .
```

### Creating Migrations

```bash
alembic revision --autogenerate -m "Your migration message"
alembic upgrade head
```

## Deployment

For production deployment, consider using:

- **Web Server**: Nginx or Apache
- **ASGI Server**: Uvicorn with Gunicorn
- **Process Manager**: Systemd, Supervisor, or Docker
- **Database**: PostgreSQL with connection pooling (PgBouncer)
- **Caching**: Redis

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For support, please open an issue on the GitHub repository.

A Python backend mirroring the ModernWMS .NET flow with the same endpoints and response shapes.

## Features
- Endpoints: POST /login, POST /refresh-token, POST /hello-world
- Response shape: `{ isSuccess, code, errorMessage, data }`
- Login response mirrors C# `LoginOutputViewModel`
- JWT auth with refresh token (in-memory)
- PostgreSQL via SQLAlchemy, auto-creates tables and seeds `admin` user (password `1`, MD5 hashed)
- CORS open (same behavior as existing .NET middleware)

## Configure PostgreSQL
Ensure PostgreSQL is running locally (default install paths are fine).
- Host: 127.0.0.1
- Port: 5432
- DB: modernwms (create this database before running)
- User: postgres
- Password: set in `.env` (default provided)

Create DB via psql:
```
psql -U postgres -h 127.0.0.1 -p 5432 -c "CREATE DATABASE modernwms;"
```

## Setup
```
python -m venv .venv
. .venv/Scripts/activate  # PowerShell: .\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python start.py
```

Server runs on http://127.0.0.1:5555 (from `.env`).

## API
- POST /login
  - body: `{ "user_name": "admin", "password": "1" }` (plain `1` is accepted; it will be MD5-ed)
  - response: `ResultModel<LoginOutputViewModel>`
- POST /refresh-token
  - body: `{ "accessToken": "...", "refreshToken": "..." }` (or `AccessToken`/`RefreshToken`)
  - response: `ResultModel<string>` (data is the new access token)
- POST /hello-world
  - response: `ResultModel<string>`

## Notes
- Refresh tokens are kept in memory (process-local). Restarting the app clears them.
- For production, use a persistent store (Redis) and secure JWT secret.
