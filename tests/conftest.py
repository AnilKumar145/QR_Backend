import os
import sys
from pathlib import Path
from sqlalchemy import text

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

from app.main import app
from app.db.base import Base, get_db

# Load environment variables
load_dotenv()

# Use the test database URL directly from environment
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")
if not SQLALCHEMY_DATABASE_URL:
    raise ValueError("DATABASE_URL must be set in .env.test file")

# Create test engine
engine = create_engine(SQLALCHEMY_DATABASE_URL)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def create_test_database():
    """Create test database tables"""
    # Drop all tables
    Base.metadata.drop_all(bind=engine)
    # Create all tables
    Base.metadata.create_all(bind=engine)
    
    yield  # Run the tests
    
    # Clean up after tests
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db():
    """Get database session for each test"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()

@pytest.fixture(scope="function")
def client(db):
    """Get test client with database session"""
    def override_get_db():
        try:
            yield db
        finally:
            db.close()
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c



