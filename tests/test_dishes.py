"""Tests for dishes module"""
import uuid
from fastapi import status


def test_create_dish_success(client, auth_headers):
    """Test creating a dish as employee/admin"""
    response = client.post(
        "/dishes",
        headers=auth_headers,
        json={
            "name": "Salade César",
            "dish_type": "STARTER",
            "description": "Salade romaine avec croûtons et parmesan",
            "allergens": ["gluten", "lait"]
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["name"] == "Salade César"
    assert data["dish_type"] == "STARTER"
    # API capitalizes allergens
    assert "Gluten" in [a["allergen"] for a in data["allergens"]]
    assert "Lait" in [a["allergen"] for a in data["allergens"]]


def test_create_dish_unauthorized(client):
    """Test creating dish without authentication fails"""
    response = client.post(
        "/dishes",
        json={
            "name": "Test Dish",
            "dish_type": "MAIN",
            "description": "Test description",
            "allergens": []
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_list_dishes(client):
    """Test listing all dishes"""
    response = client.get("/dishes")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_list_dishes_filter_by_type(client, auth_headers, db_session):
    """Test filtering dishes by type"""
    # Create dishes of different types
    from app.modules.menus.models_dishes import Dish
    
    entree = Dish(name="Salade", dish_type="STARTER", description="Salade verte")
    plat = Dish(name="Poulet", dish_type="MAIN", description="Poulet rôti")
    
    db_session.add(entree)
    db_session.add(plat)
    db_session.commit()
    
    response = client.get("/dishes?dish_type=STARTER")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert all(d["dish_type"] == "STARTER" for d in data)


def test_get_dish_by_id(client, auth_headers, db_session):
    """Test getting a specific dish"""
    from app.modules.menus.models_dishes import Dish
    
    dish = Dish(
        name="Tarte aux pommes",
        dish_type="DESSERT",
        description="Délicieuse tarte maison"
    )
    db_session.add(dish)
    db_session.commit()
    db_session.refresh(dish)
    
    response = client.get(f"/dishes/{dish.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Tarte aux pommes"


def test_get_dish_not_found(client):
    """Test getting non-existent dish fails"""
    response = client.get("/dishes/9999")
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_update_dish_success(client, auth_headers, db_session):
    """Test updating a dish"""
    from app.modules.menus.models_dishes import Dish
    
    dish = Dish(
        name="Old Name",
        dish_type="MAIN",
        description="Old description"
    )
    db_session.add(dish)
    db_session.commit()
    db_session.refresh(dish)
    
    response = client.patch(
        f"/dishes/{dish.id}",
        headers=auth_headers,
        json={
            "name": "Updated Name",
            "description": "Updated description"
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["name"] == "Updated Name"
    assert data["description"] == "Updated description"


def test_replace_dish_allergens(client, auth_headers, db_session):
    """Test replacing dish allergens"""
    from app.modules.menus.models_dishes import Dish, DishAllergen
    
    dish = Dish(
        name="Test Dish",
        dish_type="MAIN",
        description="Test"
    )
    db_session.add(dish)
    db_session.commit()
    db_session.refresh(dish)
    
    # Add initial allergen
    allergen = DishAllergen(dish_id=dish.id, allergen="gluten")
    db_session.add(allergen)
    db_session.commit()
    
    # Replace with new allergens
    response = client.put(
        f"/dishes/{dish.id}/allergens",
        headers=auth_headers,
        json={"allergens": ["lait", "oeufs"]}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    allergens = [a["allergen"] for a in data["allergens"]]
    # API capitalizes allergens
    assert "Lait" in allergens
    assert "Oeufs" in allergens
    assert "Gluten" not in allergens


def test_delete_dish_success(client, auth_headers, db_session):
    """Test deleting a dish"""
    from app.modules.menus.models_dishes import Dish
    
    dish = Dish(
        name="To Delete",
        dish_type="DESSERT",
        description="Will be deleted"
    )
    db_session.add(dish)
    db_session.commit()
    db_session.refresh(dish)
    
    response = client.delete(f"/dishes/{dish.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_list_dishes_search(client, auth_headers, db_session):
    """Test searching dishes by name"""
    from app.modules.menus.models_dishes import Dish
    
    dish1 = Dish(name="Poulet rôti", dish_type="MAIN", description="Poulet")
    dish2 = Dish(name="Salade", dish_type="STARTER", description="Salade verte")
    
    db_session.add(dish1)
    db_session.add(dish2)
    db_session.commit()
    
    response = client.get("/dishes?search=poulet")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    names = [d["name"] for d in data]
    assert any("Poulet" in n for n in names)
