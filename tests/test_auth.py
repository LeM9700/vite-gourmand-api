import pytest
from fastapi import status
import uuid
from app.modules.users.models import User
from passlib.context import CryptContext

def test_login_success(client, db_session):
    """Test successful login"""
    
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # ✅ Email unique avec UUID
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
    
    user = User(
        email=unique_email,
        password_hash=pwd_context.hash("TestPass123!"),
        firstname="Test",
        lastname="User",
        phone="0601020304",
        address="123 Test St",
        role="USER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Login
    response = client.post(
        "/auth/login",
        data={
            "username": unique_email,
            "password": "TestPass123!"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_credentials(client, db_session):
    """Test login with invalid credentials"""
    
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # ✅ Email unique
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@test.com"
    
    user = User(
        email=unique_email,
        password_hash=pwd_context.hash("CorrectPass123!"),
        firstname="Test",
        lastname="User",
        phone="0601020304",
        address="123 Test St",
        role="USER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    response = client.post(
        "/auth/login",
        data={
            "username": unique_email,
            "password": "WrongPassword"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_login_missing_fields(client):
    """Test login with missing fields"""
    response = client.post(
        "/auth/login",
        data={"username": "test@test.com"}
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

def test_register_success(client):
    """Test successful registration"""
    unique_email = f"newuser_{uuid.uuid4().hex[:8]}@test.com"
    
    response = client.post(
        "/auth/register",
        json={
            "email": unique_email,
            "password": "NewPass123!",
            "firstname": "New",
            "lastname": "User",
            "phone": "0601020304",
            "address": "123 Test St"
        }
    )
    assert response.status_code in [status.HTTP_200_OK, status.HTTP_201_CREATED]

def test_register_duplicate_email(client, db_session):
    """Test registration with existing email"""
    
    
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    # Create user in DB
    duplicate_email = f"duplicate_{uuid.uuid4().hex[:8]}@test.com"
    user = User(
        email=duplicate_email,
        password_hash=pwd_context.hash("Pass123!"),
        firstname="First",
        lastname="User",
        phone="0601020304",
        address="123 Test St",
        role="USER",
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # Try to register again
    response = client.post(
        "/auth/register",
        json={
            "email": duplicate_email,
            "password": "Pass123!",
            "firstname": "Second",
            "lastname": "User",
            "phone": "0601020305",
            "address": "456 Test St"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

def test_get_current_user(client, auth_headers):
    """Test getting current authenticated user"""
    response = client.get("/auth/me", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["email"] == "admin@test.com"
    assert data["role"] == "ADMIN"


def test_update_current_user_success(client, auth_headers):
    """Test updating current user profile"""
    response = client.patch(
        "/auth/me",
        headers=auth_headers,
        json={
            "firstname": "UpdatedFirstName",
            "phone": "0611111111"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # API capitalizes/normalizes firstname
    assert data["firstname"] == "Updatedfirstname"
    assert data["phone"] == "0611111111"


def test_register_weak_password(client):
    """Test registration with weak password fails"""
    response = client.post(
        "/auth/register",
        json={
            "email": f"user_{uuid.uuid4().hex[:8]}@test.com",
            "password": "weak",  # Too weak
            "firstname": "Test",
            "lastname": "User",
            "phone": "0601020304",
            "address": "123 Test St"
        }
    )
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_create_employee_as_admin(client, auth_headers):
    """Test creating an employee as admin"""
    response = client.post(
        "/auth/create-employee",
        headers=auth_headers,
        json={
            "email": f"employee_{uuid.uuid4().hex[:8]}@test.com",
            "password": "EmployeePass123!",
            "firstname": "New",
            "lastname": "Employee",
            "phone": "0601020305",
            "address": "456 Employee St"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["role"] == "EMPLOYEE"
    assert data["firstname"] == "New"


def test_create_employee_unauthorized(client):
    """Test creating employee without authentication fails"""
    response = client.post(
        "/auth/create-employee",
        json={
            "email": "employee@test.com",
            "password": "EmpPass123!",
            "firstname": "Test",
            "lastname": "Employee",
            "phone": "0601020304",
            "address": "123 Test St"
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED