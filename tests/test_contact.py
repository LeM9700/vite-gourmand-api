"""Tests for contact module"""
from fastapi import status


def test_create_contact_message_success(client):
    """Test creating a contact message"""
    response = client.post(
        "/contact",
        json={
            "email": "user@example.com",
            "title": "Question about menu",
            "description": "I have a question about your vegetarian menu options."
        }
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["email"] == "user@example.com"
    assert data["title"] == "Question about menu"
    assert data["status"] == "SENT"


def test_list_contact_messages_as_admin(client, auth_headers, db_session):
    """Test listing all contact messages as admin"""
    # Create a contact message first
    from app.modules.contact.models import ContactMessage
    
    msg = ContactMessage(
        email="test@example.com",
        title="Test Message",
        description="This is a test message",
        status="SENT"
    )
    db_session.add(msg)
    db_session.commit()
    
    response = client.get("/admin/messages", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1


def test_list_contact_messages_unauthorized(client):
    """Test listing messages without authentication fails"""
    response = client.get("/admin/messages")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_patch_contact_message_status(client, auth_headers, db_session):
    """Test updating contact message status"""
    from app.modules.contact.models import ContactMessage
    
    msg = ContactMessage(
        email="test@example.com",
        title="Test Message",
        description="Test description",
        status="SENT"
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)
    
    response = client.patch(
        f"/admin/messages/{msg.id}/status",
        headers=auth_headers,
        json={"status": "TREATED"}
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["status"] == "TREATED"


def test_patch_contact_invalid_status(client, auth_headers, db_session):
    """Test updating with invalid status fails"""
    from app.modules.contact.models import ContactMessage
    
    msg = ContactMessage(
        email="test@example.com",
        title="Test",
        description="Test",
        status="SENT"
    )
    db_session.add(msg)
    db_session.commit()
    db_session.refresh(msg)
    
    response = client.patch(
        f"/admin/messages/{msg.id}/status",
        headers=auth_headers,
        json={"status": "INVALID"}
    )
    # Pydantic @field_validator renvoie 422 (Unprocessable Entity) et non 400
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


def test_patch_contact_not_found(client, auth_headers):
    """Test updating non-existent message fails"""
    response = client.patch(
        "/admin/messages/9999/status",
        headers=auth_headers,
        json={"status": "TREATED"}
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
