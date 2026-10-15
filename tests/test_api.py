import pytest


@pytest.mark.asyncio
async def test_create_qr_api(client):
    response = await client.post(
        "/qr",
        params={"points": 100},
    )

    assert response.status_code == 200

    data = response.json()

    assert data["points"] == 100
    assert data["token"]
    assert data["id"] is not None

@pytest.mark.asyncio
async def test_create_qr_rejects_negative_points(client):
    response = await client.post(
        "/qr",
        params={"points": -100},
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_redeem_qr_api(client):
    create_response = await client.post(
        "/qr",
        params={"points": 100},
    )

    token = create_response.json()["token"]

    redeem_response = await client.post(
        f"/qr/{token}/redeem",
        json={
            "telegram_id": 123456789,
            "username": "nikita",
        },
    )

    assert redeem_response.status_code == 200

    data = redeem_response.json()

    assert data["points_added"] == 100
    assert data["balance"] == 100


@pytest.mark.asyncio
async def test_redeem_qr_twice_returns_409(client):
    create_response = await client.post(
        "/qr",
        params={"points": 100},
    )

    token = create_response.json()["token"]

    body = {
        "telegram_id": 123456789,
        "username": "nikita",
    }

    first_response = await client.post(
        f"/qr/{token}/redeem",
        json=body,
    )

    second_response = await client.post(
        f"/qr/{token}/redeem",
        json=body,
    )

    assert first_response.status_code == 200
    assert second_response.status_code == 409

    assert second_response.json() == {
        "detail": "QR code already used"
    }


@pytest.mark.asyncio
async def test_unknown_qr_returns_404(client):
    response = await client.post(
        "/qr/this-token-does-not-exist/redeem",
        json={
            "telegram_id": 123456789,
            "username": "nikita",
        },
    )

    assert response.status_code == 404

    assert response.json() == {
        "detail": "QR code not found"
    }


@pytest.mark.asyncio
async def test_create_qr_image(client):
    response = await client.post(
        "/qr/image",
        params={"points": 100},
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "image/png"
    assert len(response.content) > 0