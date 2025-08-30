# Warehouse Management System (WMS) - Proof of Concept

A lightweight, fast, and secure backend for a Warehouse Management System built with FastAPI and SQLite.

## Features

- 🔐 JWT-based authentication
- 👥 Role-based access control (User, Manager, Admin)
- 🏭 Warehouse management
- 🗄️ SQLite database (easy to switch to PostgreSQL)
- 📝 Interactive API documentation (Swagger UI & ReDoc)

## Getting Started

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. Clone the repository
2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

### Running the Application

Start the development server:
```bash
uvicorn main:app --reload
```

The API will be available at `http://localhost:8000`

## API Documentation

- Interactive API docs: http://localhost:8000/docs
- Alternative documentation: http://localhost:8000/redoc

## Default Credentials

- **Admin User**
  - Username: `admin`
  - Password: `admin123`

## API Endpoints

### Authentication
- `POST /token` - Get JWT token
- `GET /users/me/` - Get current user info

### Users
- `POST /users/` - Create a new user (Admin only)

### Warehouses
- `GET /warehouses/` - List all warehouses
- `POST /warehouses/` - Create a new warehouse (Admin/Manager only)

## Testing the API

You can use the included `test_api.py` script to test the API endpoints:

```bash
python test_api.py
```

## Project Structure

```
ModernWMS_PoC/
├── main.py           # Main application file
├── requirements.txt  # Dependencies
├── README.md         # This file
├── test_api.py       # API test script
└── wms_poc.db       # SQLite database (created on first run)
```

## License

This project is licensed under the MIT License.
