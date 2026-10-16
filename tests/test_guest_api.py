import pytest


@pytest.mark.asyncio
async def test_create_guest_api(client):
    response = await client.post(
        "/guests",
        json={
            "name": "Nikita Shestakov",
            "category": "guest",
            "telegram_id": 123456789,
            "username": "MrMops",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == "Nikita Shestakov"
    assert data["category"] == "guest"
    assert data["telegram_id"] == 123456789
    assert data["username"] == "MrMops"
    assert data["points"] == 0
    assert "id" in data


@pytest.mark.asyncio
async def test_duplicate_guest_returns_409(client):
    guest_data = {
        "name": "First Guest",
        "category": "guest",
        "telegram_id": 123456789,
    }

    first_response = await client.post(
        "/guests",
        json=guest_data,
    )

    assert first_response.status_code == 201

    second_response = await client.post(
        "/guests",
        json={
            "name": "Second Guest",
            "category": "vip",
            "telegram_id": 123456789,
        },
    )

    assert second_response.status_code == 409
    assert second_response.json()["detail"] == (
        "Guest with this Telegram ID already exists"
    )


@pytest.mark.asyncio
async def test_create_guest_validation(client):
    response = await client.post(
        "/guests",
        json={
            "name": "",
            "category": "",
            "telegram_id": 123456789,
        },
    )

    assert response.status_code == 422