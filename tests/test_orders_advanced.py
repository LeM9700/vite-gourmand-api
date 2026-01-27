"""
Tests avancés pour le module Orders:
- Calcul de prix (livraison, réduction)
- Transitions de statut
- Validation de stock
- Gestion des erreurs
"""
import pytest
from datetime import date, time, timedelta
from decimal import Decimal
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.main import app
from app.modules.menus.models import Menu
from app.modules.orders.models import Order, OrderStatusHistory
from app.modules.orders.service import DELIVERY_BASE_FEE, DELIVERY_PER_KM


@pytest.fixture
def test_menu(db_session):
    """Crée un menu de test actif avec stock"""
    menu = Menu(
        title="Menu Test Avancé",
        description="Un menu test pour les commandes avancées",
        theme="GASTRONOMIQUE",
        regime="CLASSIQUE",
        base_price=Decimal("50.00"),
        min_people=10,
        stock=5,
        is_active=True,
        conditions_text="Conditions de test"
    )
    db_session.add(menu)
    db_session.commit()
    db_session.refresh(menu)
    return menu


@pytest.fixture
def low_stock_menu(db_session):
    """Crée un menu avec stock limité"""
    menu = Menu(
        title="Menu Stock Limité",
        description="Menu avec très peu de stock disponible",
        theme="VEGETARIEN",
        regime="SANS_GLUTEN",
        base_price=Decimal("45.00"),
        min_people=8,
        stock=1,
        is_active=True,
        conditions_text="Stock limité"
    )
    db_session.add(menu)
    db_session.commit()
    db_session.refresh(menu)
    return menu


@pytest.fixture
def inactive_menu(db_session):
    """Crée un menu inactif"""
    menu = Menu(
        title="Menu Inactif",
        description="Menu temporairement désactivé",
        theme="ASIATIQUE",
        regime="CLASSIQUE",
        base_price=Decimal("40.00"),
        min_people=10,
        stock=10,
        is_active=False,
        conditions_text="Menu désactivé"
    )
    db_session.add(menu)
    db_session.commit()
    db_session.refresh(menu)
    return menu


def test_order_price_calculation_no_discount(client: TestClient, test_menu, user_token):
    """Test du calcul de prix sans réduction (< min_people + 5)"""
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 10,
        "people_count": 12,  # min_people=10, donc 12 < 10+5 = pas de réduction
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    
    data = response.json()
    
    # Vérifications des calculs
    expected_delivery_fee = float(DELIVERY_BASE_FEE + (Decimal("10") * DELIVERY_PER_KM))
    expected_menu_price = float(test_menu.base_price)
    expected_total = (expected_menu_price * 12) + expected_delivery_fee
    
    assert float(data["delivery_fee"]) == pytest.approx(expected_delivery_fee, rel=0.01)
    assert float(data["menu_price"]) == pytest.approx(expected_menu_price, rel=0.01)
    assert float(data["discount"]) == 0.0
    assert float(data["total_price"]) == pytest.approx(expected_total, rel=0.01)


def test_order_price_calculation_with_discount(client: TestClient, test_menu, user_token):
    """Test du calcul de prix avec réduction -10% (>= min_people + 5)"""
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 15,  # min_people=10, donc 15 >= 10+5 = réduction -10%
        "has_loaned_equipment": True
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    
    data = response.json()
    
    # Vérifications des calculs avec réduction
    expected_delivery_fee = float(DELIVERY_BASE_FEE + (Decimal("5") * DELIVERY_PER_KM))
    expected_menu_price = float(test_menu.base_price)
    menu_subtotal = expected_menu_price * 15
    expected_discount = menu_subtotal * 0.10  # -10%
    expected_total = menu_subtotal + expected_delivery_fee - expected_discount
    
    assert float(data["delivery_fee"]) == pytest.approx(expected_delivery_fee, rel=0.01)
    assert float(data["menu_price"]) == pytest.approx(expected_menu_price, rel=0.01)
    assert float(data["discount"]) == pytest.approx(expected_discount, rel=0.01)
    assert float(data["total_price"]) == pytest.approx(expected_total, rel=0.01)
    assert data["has_loaned_equipment"] is True


def test_order_creation_decrements_stock(db_session, client: TestClient, test_menu, user_token):
    """Test que la création d'une commande décrémente le stock"""
    initial_stock = test_menu.stock
    
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    
    # Vérifier que le stock a diminué
    db_session.refresh(test_menu)
    assert test_menu.stock == initial_stock - 1


def test_order_fails_when_stock_zero(db_session, client: TestClient, low_stock_menu, user_token):
    """Test qu'on ne peut pas commander si stock = 0"""
    # Mettre le stock à zéro
    low_stock_menu.stock = 0
    db_session.commit()
    
    payload = {
        "menu_id": low_stock_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 400
    assert "stock" in response.text.lower()


def test_order_fails_for_inactive_menu(client: TestClient, inactive_menu, user_token):
    """Test qu'on ne peut pas commander un menu inactif"""
    payload = {
        "menu_id": inactive_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 400
    assert "menu" in response.text.lower() or "désactivé" in response.text.lower() or "inactif" in response.text.lower()


def test_order_fails_for_past_date(client: TestClient, test_menu, user_token):
    """Test qu'on ne peut pas commander pour une date passée"""
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() - timedelta(days=1)),  # Date passée
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 400
    assert "date" in response.text.lower()


def test_order_fails_below_min_people(client: TestClient, test_menu, user_token):
    """Test qu'on ne peut pas commander moins que min_people"""
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 5,  # min_people=10, donc erreur
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 400
    assert "minimum" in response.text.lower() or "min_people" in response.text.lower()


def test_order_status_transition_placed_to_accepted(db_session, client: TestClient, test_menu, user_token, admin_token):
    """Test transition PLACED -> ACCEPTED"""
    # Créer une commande
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    order_id = response.json()["id"]
    
    # Changer le statut en ACCEPTED
    patch_payload = {"status": "ACCEPTED", "note": "Commande acceptée par l'admin"}
    response = client.patch(
        f"/orders/{order_id}/status",
        json=patch_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ACCEPTED"
    
    # Vérifier l'historique
    history = db_session.execute(
        select(OrderStatusHistory).where(OrderStatusHistory.order_id == order_id)
    ).scalars().all()
    
    assert len(history) >= 2  # PLACED + ACCEPTED
    statuses = [h.status for h in history]
    assert "PLACED" in statuses
    assert "ACCEPTED" in statuses


def test_order_status_invalid_transition(client: TestClient, test_menu, user_token, admin_token):
    """Test qu'on ne peut pas faire une transition invalide (PLACED -> DELIVERING)"""
    # Créer une commande
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    order_id = response.json()["id"]
    
    # Essayer de passer directement à DELIVERING (invalide depuis PLACED)
    patch_payload = {"status": "DELIVERING"}
    response = client.patch(
        f"/orders/{order_id}/status",
        json=patch_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 400
    assert "transition" in response.text.lower()


def test_order_update_people_count(db_session, client: TestClient, test_menu, user_token):
    """Test modification du nombre de personnes (recalcul du prix)"""
    # Créer une commande
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    order_id = response.json()["id"]
    original_price = response.json()["total_price"]
    
    # Modifier le nombre de personnes à 15 (avec réduction -10%)
    update_payload = {"people_count": 15}
    response = client.put(
        f"/orders/{order_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 200
    data = response.json()
    
    assert data["people_count"] == 15
    assert float(data["discount"]) > 0  # Maintenant avec réduction
    assert float(data["total_price"]) != original_price  # Prix a changé


def test_order_update_fails_after_accepted(db_session, client: TestClient, test_menu, user_token, admin_token):
    """Test qu'on ne peut pas modifier une commande déjà acceptée"""
    # Créer une commande
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    order_id = response.json()["id"]
    
    # Changer le statut en ACCEPTED
    patch_payload = {"status": "ACCEPTED"}
    response = client.patch(
        f"/orders/{order_id}/status",
        json=patch_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    
    # Essayer de modifier la commande
    update_payload = {"people_count": 15}
    response = client.put(
        f"/orders/{order_id}",
        json=update_payload,
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 400
    assert "PLACED" in response.text or "modifiable" in response.text.lower()


def test_order_cancel_by_admin(db_session, client: TestClient, test_menu, user_token, admin_token):
    """Test annulation d'une commande par un admin"""
    # Créer une commande
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    order_id = response.json()["id"]
    
    # Annuler la commande
    cancel_payload = {
        "contact_mode": "EMAIL",
        "reason": "Client a demandé l'annulation"
    }
    response = client.post(
        f"/orders/{order_id}/cancel",
        json=cancel_payload,
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"


def test_list_orders_filter_by_status(db_session, client: TestClient, test_menu, user_token, admin_token):
    """Test filtrage des commandes par statut"""
    # Créer 2 commandes
    for i in range(2):
        payload = {
            "menu_id": test_menu.id,
            "event_address": f"{i} Rue de Test",
            "event_city": "Paris",
            "event_date": str(date.today() + timedelta(days=10+i)),
            "event_time": "19:00:00",
            "delivery_km": 5,
            "people_count": 10,
            "has_loaned_equipment": False
        }
        client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    
    # Accepter la première commande
    response = client.get("/orders", headers={"Authorization": f"Bearer {admin_token}"})
    orders = response.json()["items"]
    first_order_id = orders[0]["id"]
    
    client.patch(
        f"/orders/{first_order_id}/status",
        json={"status": "ACCEPTED"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    
    # Filtrer par statut ACCEPTED
    response = client.get(
        "/orders?status=ACCEPTED",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    filtered_orders = response.json()["items"]
    assert len(filtered_orders) >= 1
    assert all(order["status"] == "ACCEPTED" for order in filtered_orders)


def test_user_can_only_see_own_orders(db_session, client: TestClient, test_menu, user_token):
    """Test qu'un utilisateur ne voit que ses propres commandes"""
    # Créer une commande
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 201
    order_id = response.json()["id"]
    
    # Lister ses commandes
    response = client.get("/orders/me", headers={"Authorization": f"Bearer {user_token}"})
    assert response.status_code == 200
    orders = response.json()["items"]
    assert len(orders) >= 1
    assert any(order["id"] == order_id for order in orders)


def test_employee_cannot_create_order(client: TestClient, test_menu, employee_token):
    """Test qu'un employé ne peut pas passer commande"""
    payload = {
        "menu_id": test_menu.id,
        "event_address": "10 Rue de Test",
        "event_city": "Paris",
        "event_date": str(date.today() + timedelta(days=10)),
        "event_time": "19:00:00",
        "delivery_km": 5,
        "people_count": 10,
        "has_loaned_equipment": False
    }
    
    response = client.post("/orders", json=payload, headers={"Authorization": f"Bearer {employee_token}"})
    assert response.status_code == 403  # Seuls les USER peuvent commander
