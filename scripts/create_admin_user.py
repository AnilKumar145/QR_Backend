import sys
from getpass import getpass
from sqlalchemy.orm import Session
from app.db.base import SessionLocal, engine, Base
from app.models.admin_user import AdminUser
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def create_admin_user(username: str, password: str):
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        existing_user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if existing_user:
            print(f"User '{username}' already exists.")
            return
        hashed_password = pwd_context.hash(password)
        admin_user = AdminUser(
            username=username,
            hashed_password=hashed_password,
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print(f"Admin user '{username}' created successfully.")
    except Exception as e:
        print(f"Error creating admin user: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) >= 2:
        username = sys.argv[1]
    else:
        username = input("Enter admin username: ")
    password = getpass("Enter admin password: ")
    confirm_password = getpass("Confirm admin password: ")
    if password != confirm_password:
        print("Passwords do not match. Exiting.")
        sys.exit(1)
    create_admin_user(username, password)
