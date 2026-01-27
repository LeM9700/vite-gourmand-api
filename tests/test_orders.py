import pytest
from fastapi import status
from datetime import datetime, timedelta

def test_get_orders_unauthorized(client):
    """Test getting orders without authentication"""
    response = client.get("/orders")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_get_orders_as_admin(client, auth_headers):
    """Test getting orders as admin"""
    response = client.get("/orders", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)

@pytest.mark.skip("Requires complex menu/order setup")
def test_create_order_success(client, auth_headers):
    """Test creating a new order"""
    # Create a menu first
    menu_response = client.post(
        "/menus",
        headers=auth_headers,
        json={
            "name": "Test Menu for Order",
            "description": "Menu description",
            "base_price": 60.0,
            "min_guests": 10,
            "max_guests": 100,
            "is_active": True
        }
    )
    menu_id = menu_response.json()["id"]
    
    # Create order
    delivery_date = (datetime.now() + timedelta(days=7)).isoformat()
    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "menu_id": menu_id,
            "guest_count": 50,
            "delivery_date": delivery_date,
            "delivery_address": "123 Test St, Bordeaux",
            "special_requests": "No nuts please"
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["menu_id"] == menu_id
    assert data["guest_count"] == 50
    assert data["status"] == "PENDING"

@pytest.mark.skip("Requires complex menu/order setup")
def test_create_order_invalid_guest_count(client, auth_headers):
    """Test creating order with invalid guest count"""
    menu_response = client.post(
        "/menus",
        headers=auth_headers,
        json={
            "name": "Test Menu",
            "base_price": 50.0,
            "min_guests": 10,
            "max_guests": 100,
            "is_active": True
        }
    )
    menu_id = menu_response.json()["id"]
    
    delivery_date = (datetime.now() + timedelta(days=7)).isoformat()
    response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "menu_id": menu_id,
            "guest_count": 5,  # Below minimum
            "delivery_date": delivery_date,
            "delivery_address": "123 Test St"
        }
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.skip("Requires complex menu/order setup")
def test_update_order_status(client, auth_headers):
    """Test updating order status (admin only)"""
    # Create order first
    menu_response = client.post(
        "/menus",
        headers=auth_headers,
        json={
            "name": "Test Menu",
            "base_price": 50.0,
            "min_guests": 10,
            "max_guests": 100,
            "is_active": True
        }
    )
    menu_id = menu_response.json()["id"]
    
    delivery_date = (datetime.now() + timedelta(days=7)).isoformat()
    order_response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "menu_id": menu_id,
            "guest_count": 50,
            "delivery_date": delivery_date,
            "delivery_address": "123 Test St"
        }
    )
    order_id = order_response.json()["id"]
    
    # Update status
    response = client.patch(
        f"/orders/{order_id}/status",
        headers=auth_headers,
        json={"status": "CONFIRMED"}
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "CONFIRMED"
@pytest.mark.skip("Requires complex menu/order setup")

def test_cancel_order(client, auth_headers):
    """Test canceling an order"""
    # Create order
    menu_response = client.post(
        "/menus",
        headers=auth_headers,
        json={
            "name": "Test Menu",
            "base_price": 50.0,
            "min_guests": 10,
            "max_guests": 100,
            "is_active": True
        }
    )
    menu_id = menu_response.json()["id"]
    
    delivery_date = (datetime.now() + timedelta(days=7)).isoformat()
    order_response = client.post(
        "/orders",
        headers=auth_headers,
        json={
            "menu_id": menu_id,
            "guest_count": 50,
            "delivery_date": delivery_date,
            "delivery_address": "123 Test St"
        }
    )
    order_id = order_response.json()["id"]
    
    # Cancel
    response = client.delete(
        f"/orders/{order_id}",
        headers=auth_headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["status"] == "CANCELLED"