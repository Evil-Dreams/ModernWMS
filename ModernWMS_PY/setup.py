from app.database import init_db, clear_data, get_db
from app.models import User
from app.utils.hash import get_password_hash
from sqlalchemy.orm import Session
import sys

def setup_database():
    print("Initializing database...")
    try:
        # Initialize database tables
        init_db()
        
        # Create admin user if not exists
        db = next(get_db())
        admin = db.query(User).filter(User.user_name == "admin").first()
        
        if not admin:
            admin = User(
                user_name="admin",
                password=get_password_hash("admin123"),
                user_role="admin",
                email="admin@example.com"
            )
            db.add(admin)
            db.commit()
            print("Created admin user")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("Admin user already exists")
            
        print("\nDatabase setup complete!")
        print("You can now start the application with: uvicorn app.main:app --reload")
        
    except Exception as e:
        print(f"Error setting up database: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    setup_database()
