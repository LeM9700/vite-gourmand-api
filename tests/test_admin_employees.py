"""Tests for admin employees module"""
import uuid
from fastapi import status


def test_get_all_employees_as_admin(client, auth_headers, db_session):
    """Test getting all employees as admin"""
    response = client.get("/admin/employees", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    # Should have at least the admin user created in fixtures
    assert len(data) >= 1
    assert any(emp["role"] == "ADMIN" for emp in data)


def test_get_employees_unauthorized(client):
    """Test getting employees without authentication fails"""
    response = client.get("/admin/employees")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_toggle_employee_active_status(client, auth_headers, db_session):
    """Test toggling employee active status"""
    import bcrypt
    from app.modules.users.models import User
    
    hashed = bcrypt.hashpw(b"EmpPass123!", bcrypt.gensalt(rounds=12)).decode("utf-8")
    
    # Create an employee to toggle
    employee = User(
        email=f"employee_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hashed,
        firstname="Test",
        lastname="Employee",
        phone="0600000001",
        address="456 Test St",
        role="EMPLOYEE",
        is_active=True
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    
    # Deactivate the employee
    response = client.patch(
        f"/admin/employees/{employee.id}/toggle-active",
        headers=auth_headers,
        json={"is_active": False}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_active"] is False
    assert data["message"] is not None


def test_toggle_employee_reactivate(client, auth_headers, db_session):
    """Test reactivating a deactivated employee"""
    import bcrypt
    from app.modules.users.models import User
    
    hashed = bcrypt.hashpw(b"EmpPass123!", bcrypt.gensalt(rounds=12)).decode("utf-8")
    
    # Create an inactive employee
    employee = User(
        email=f"inactive_{uuid.uuid4().hex[:8]}@test.com",
        password_hash=hashed,
        firstname="Inactive",
        lastname="Employee",
        phone="0600000002",
        address="789 Test St",
        role="EMPLOYEE",
        is_active=False
    )
    db_session.add(employee)
    db_session.commit()
    db_session.refresh(employee)
    
    # Reactivate
    response = client.patch(
        f"/admin/employees/{employee.id}/toggle-active",
        headers=auth_headers,
        json={"is_active": True}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_active"] is True


def test_toggle_own_account_forbidden(client, admin_user, db_session):
    """Test that admin cannot deactivate their own account"""
    
    # Login as admin
    response = client.post(
        "/auth/login",
        data={
            "username": admin_user.email,
            "password": "TestPass123!"
        }
    )
    token = response.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # Try to deactivate own account
    response = client.patch(
        f"/admin/employees/{admin_user.id}/toggle-active",
        headers=headers,
        json={"is_active": False}
    )
    # Should be forbidden (403) or return error message
    assert response.status_code in [status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST]


def test_toggle_employee_not_found(client, auth_headers):
    """Test toggling non-existent employee fails"""
    response = client.patch(
        "/admin/employees/9999/toggle-active",
        headers=auth_headers,
        json={"is_active": False}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
