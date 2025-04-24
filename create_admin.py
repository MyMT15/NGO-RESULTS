from app import app, db, User
from dotenv import load_dotenv
import os

def create_admin_user():
    load_dotenv()
    
    # Create database tables
    with app.app_context():
        # Drop all tables first to ensure clean state
        db.drop_all()
        # Create all tables
        db.create_all()
        
        # Create admin user
        admin = User(
            username='admin',
            email=os.getenv('EMAIL_USER', 'admin@example.com')
        )
        admin.set_password('ABS123@')  # Set the new password
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
        print("Username: admin")
        print("Password: ABS123@")
        print(f"Email: {admin.email}")

if __name__ == '__main__':
    create_admin_user() 