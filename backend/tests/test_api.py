"""Basic API tests."""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "name" in data
    assert "version" in data
    assert "status" in data


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_create_player(client: AsyncClient):
    """Test player creation."""
    player_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "testpass123",
        "character_name": "Test Hero",
        "character_class": "Warrior"
    }
    
    response = await client.post("/api/players/", json=player_data)
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == player_data["username"]
    assert data["character_name"] == player_data["character_name"]
    assert "id" in data


@pytest.mark.asyncio
async def test_get_player(client: AsyncClient):
    """Test getting player details."""
    # Create player first
    player_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "testpass123",
        "character_name": "Test Hero 2",
    }
    
    create_response = await client.post("/api/players/", json=player_data)
    player_id = create_response.json()["id"]
    
    # Get player
    response = await client.get(f"/api/players/{player_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == player_id
    assert data["username"] == player_data["username"]
