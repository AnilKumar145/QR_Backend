import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.admin_user import AdminUser
from app.core.security import pwd_context
from app.core.config import settings

DATABASE_URL = settings.SQLALCHEMY_DATABASE_URI

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_admin_password(username: str, password: str):
    db = SessionLocal()
    try:
        user = db.query(AdminUser).filter(AdminUser.username == username).first()
        if not user:
            print(f"User {username} not found.")
            return False
        if pwd_context.verify(password, user.hashed_password):
            print(f"Password for user {username} is correct.")
            return True
        else:
            print(f"Password for user {username} is incorrect.")
            return False
    finally:
        db.close()

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python check_admin_password.py <username> <password>")
        sys.exit(1)
    username = sys.argv[1]
    password = sys.argv[2]
    check_admin_password(username, password)
