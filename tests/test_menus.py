import pytest
from fastapi import status

def test_get_menus(client):
    """Test getting all menus"""
    response = client.get("/menus")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    # ✅ Votre API retourne {'items': [], 'total': 0}
    assert "items" in data
    assert isinstance(data["items"], list)

def test_get_menu_by_id(client, auth_headers):
    """Test getting a specific menu"""
    # Create a menu first
    create_response = client.post(
        "/menus",
        headers=auth_headers,
        json={
            "title": "Test Menu",
            "description": "Test description for menu",
            "theme": "classique",
            "regime": "classique",
            "min_people": 10,
            "base_price": 50.0,
            "conditions_text": "Conditions de livraison standard",
            "stock": 10,
            "is_active": True,
            "dish_ids": [],
            "image_urls": []
        }
    )
    assert create_response.status_code == status.HTTP_201_CREATED
    menu_id = create_response.json()["id"]
    
    # Get the menu
    response = client.get(f"/menus/{menu_id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["title"] == "Test Menu"
    assert float(data["base_price"]) == 50.0

def test_create_menu_unauthorized(client):
    """Test creating menu without authentication"""
    response = client.post(
        "/menus",
        json={
            "title": "Unauthorized Menu",
            "base_price": 50.0
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

def test_create_menu_success(client, auth_headers):
    """Test successful menu creation"""
    response = client.post(
        "/menus",
        headers=auth_headers,
        json={
            "title": "New Test Menu",
            "description": "Delicious menu for testing",
            "theme": "vegetarien",
            "regime": "vegetarien",
            "min_people": 15,
            "base_price": 75.0,
            "conditions_text": "Livraison gratuite au-dessus de 100€",
            "stock": 20,
            "is_active": True,
            "dish_ids": [],
            "image_urls": []
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["title"] == "New Test Menu"
    assert float(data["base_price"]) == 75.0
    assert data["theme"] == "vegetarien"