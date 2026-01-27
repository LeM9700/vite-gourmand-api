import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.db_base import Base
from app.core.db_postgres import get_db
from app.core.config import Settings
from app.core.rate_limiter import rate_limiter
import os
from app.modules.users.models import User
from passlib.context import CryptContext


# Forcer environnement de test
os.environ["ENVIRONMENT"] = "testing"

# Base de données de test (SQLite en mémoire)
SQLALCHEMY_TEST_DATABASE_URL = "sqlite:///./test.db"


# ✅ Désactiver le rate limiter pour les tests


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment and disable rate limiting"""
    # ✅ Désactiver le rate limiter globalement
    rate_limiter.enabled = False
    
    yield
    
    # ✅ Réactiver après les tests
    rate_limiter.enabled = True

@pytest.fixture(scope="function", autouse=True)
def reset_rate_limiter():
    """Reset rate limiter before each test"""
    rate_limiter.reset()
    yield

@pytest.fixture(scope="session")
def test_settings():
    """Override settings for tests"""
    return Settings(
        postgres_url=SQLALCHEMY_TEST_DATABASE_URL,
        jwt_secret="test_secret_key_for_testing_only",
        jwt_alg="HS256",
        jwt_expire_minutes=30,
        mongo_url="mongodb://localhost:27017",
        mongo_db="test_vg_db",
        environment="testing"
    )

@pytest.fixture(scope="session")
def engine():
    """Create test database engine"""
    engine = create_engine(
        SQLALCHEMY_TEST_DATABASE_URL,
        connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    yield engine
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session(engine):
    """Create a new database session for each test"""
    # ✅ CRUCIAL: Drop and recreate ALL tables before EACH test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    """Create test client with overridden database"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    
    with TestClient(app) as test_client:
        yield test_client
    
    app.dependency_overrides.clear()
    
@pytest.fixture(scope="function")  # ✅ IMPORTANT: scope="function" pas "session"
def admin_user(db_session):
    """Create admin user for the current test"""
    
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # ✅ Créer un nouvel admin pour CE test uniquement
    admin = User(
        email="admin@test.com",
        password_hash=pwd_context.hash("TestPass123!"),
        firstname="Admin",
        lastname="Test",
        phone="0601020304",
        address="123 Test St",
        role="ADMIN",
        is_active=True
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    
    return admin    

@pytest.fixture
def admin_token(client, admin_user):
    """Get admin JWT token for authenticated requests"""
    # Login with admin_user created by admin_user fixture
    response = client.post(
        "/auth/login",
        data={
            "username": admin_user.email,
            "password": "TestPass123!"
        }
    )
    
    if response.status_code != 200:
        print(f"Login failed: {response.json()}")
        pytest.fail(f"Login failed: {response.json()}")
    
    return response.json()["access_token"]

@pytest.fixture
def auth_headers(admin_token):
    """Get authorization headers"""
    return {"Authorization": f"Bearer {admin_token}"}

@pytest.fixture(scope="function")
def employee_user(db_session):
    """Create employee user for the current test"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    employee = User(
        email="employee@test.com",
        password_hash=pwd_context.hash("TestPass123!"),
        firstname="Employee",
        lastname="Test",
        phone="0601020305",
        address="456 Test St",
        role="EMPLOYEE",
        is_active=True
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    
    return employee

@pytest.fixture
def employee_token(client, employee_user):
    """Get employee JWT token for authenticated requests"""
    response = client.post(
        "/auth/login",
        data={
            "username": employee_user.email,
            "password": "TestPass123!"
        }
    )
    
    if response.status_code != 200:
        print(f"Employee login failed: {response.json()}")
        pytest.fail(f"Employee login failed: {response.json()}")
    
    return response.json()["access_token"]

@pytest.fixture(scope="function")
def regular_user(db_session):
    """Create regular user for the current test"""
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    user = User(
        email="user@test.com",
        password_hash=pwd_context.hash("TestPass123!"),
        firstname="Regular",
        lastname="User",
        phone="0601020306",
        address="789 Test St",
        role="USER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    
    return user

@pytest.fixture
def user_token(client, regular_user):
    """Get regular user JWT token for authenticated requests"""
    response = client.post(
        "/auth/login",
        data={
            "username": regular_user.email,
            "password": "TestPass123!"
        }
    )
    
    if response.status_code != 200:
        print(f"User login failed: {response.json()}")
        pytest.fail(f"User login failed: {response.json()}")
    
    return response.json()["access_token"]