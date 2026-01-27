"""Tests for schedules module"""
from fastapi import status


def test_get_all_schedules_public(client):
    """Test getting all schedules without authentication"""
    response = client.get("/schedules")
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_create_schedule_success(client, auth_headers):
    """Test creating a schedule as employee/admin"""
    response = client.post(
        "/schedules",
        headers=auth_headers,
        json={
            "day_of_week": 1,  # Monday
            "open_time": "09:00",
            "close_time": "18:00",
            "is_closed": False
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["day_of_week"] == 1
    assert data["open_time"] == "09:00"
    assert data["close_time"] == "18:00"


def test_create_schedule_unauthorized(client):
    """Test creating schedule without authentication fails"""
    response = client.post(
        "/schedules",
        json={
            "day_of_week": 1,
            "open_time": "09:00",
            "close_time": "18:00",
            "is_closed": False
        }
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_schedule_success(client, auth_headers, db_session):
    """Test updating a schedule"""
    from app.modules.schedules.models import Schedule
    from datetime import time
    
    schedule = Schedule(
        day_of_week=1,
        open_time=time(9, 0),
        close_time=time(18, 0),
        is_closed=False
    )
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    
    response = client.put(
        f"/schedules/{schedule.id}",
        headers=auth_headers,
        json={
            "day_of_week": 1,
            "open_time": "10:00",
            "close_time": "19:00",
            "is_closed": False
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["open_time"] == "10:00"
    assert data["close_time"] == "19:00"


def test_update_schedule_not_found(client, auth_headers):
    """Test updating non-existent schedule fails"""
    response = client.put(
        "/schedules/9999",
        headers=auth_headers,
        json={
            "day_of_week": 1,
            "open_time": "10:00",
            "close_time": "19:00",
            "is_closed": False
        }
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_delete_schedule_success(client, auth_headers, db_session):
    """Test deleting a schedule"""
    from app.modules.schedules.models import Schedule
    from datetime import time
    
    schedule = Schedule(
        day_of_week=2,
        open_time=time(9, 0),
        close_time=time(18, 0),
        is_closed=False
    )
    db_session.add(schedule)
    db_session.commit()
    db_session.refresh(schedule)
    
    response = client.delete(f"/schedules/{schedule.id}", headers=auth_headers)
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "message" in data


def test_delete_schedule_not_found(client, auth_headers):
    """Test deleting non-existent schedule fails"""
    response = client.delete("/schedules/9999", headers=auth_headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND


def test_create_schedule_closed_day(client, auth_headers):
    """Test creating a closed day schedule"""
    response = client.post(
        "/schedules",
        headers=auth_headers,
        json={
            "day_of_week": 0,  # Sunday
            "open_time": None,
            "close_time": None,
            "is_closed": True
        }
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["is_closed"] is True
