import os
import uuid
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool
from app.config import settings
from app.db import engine, Base
from app.main import app


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


@pytest.mark.asyncio
async def test_health_and_root():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["app"] == "sidaz-meet API"
        assert data["status"] == "online"

        health = await client.get("/health")
        assert health.status_code == 200
        assert health.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_auth_flow():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Signup
        email = f"test_user_{uuid.uuid4().hex[:6]}@example.com"
        signup_res = await client.post("/auth/signup", json={
            "email": email,
            "password": "password123",
            "display_name": "Test User"
        })
        assert signup_res.status_code == 201
        data = signup_res.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == email

        access_token = data["access_token"]
        refresh_token = data["refresh_token"]

        # Get me
        me_res = await client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
        assert me_res.status_code == 200
        assert me_res.json()["display_name"] == "Test User"

        # Refresh
        ref_res = await client.post("/auth/refresh", json={"refresh_token": refresh_token})
        assert ref_res.status_code == 200
        assert "access_token" in ref_res.json()


@pytest.mark.asyncio
async def test_meeting_creation_and_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Create instant meeting
        create_res = await client.post("/meetings", json={
            "title": "Daily Standup",
            "lobby_enabled": False
        })
        assert create_res.status_code == 201
        meeting = create_res.json()
        assert "code" in meeting
        code = meeting["code"]
        assert len(code.split("-")) == 3

        # Fetch meeting metadata
        get_res = await client.get(f"/meetings/{code}")
        assert get_res.status_code == 200
        assert get_res.json()["code"] == code

        # Mint LiveKit token
        token_res = await client.post(f"/meetings/{code}/token", json={
            "display_name": "Alice In Wonderland",
            "is_host": True
        })
        assert token_res.status_code == 200
        token_data = token_res.json()
        assert "token" in token_data
        assert token_data["room_name"] == code
        assert len(token_data["token"]) > 20

        # Post chat message
        chat_post = await client.post(f"/meetings/{code}/chat", json={
            "sender_name": "Alice",
            "content": "Hello everyone!"
        })
        assert chat_post.status_code == 201
        assert chat_post.json()["content"] == "Hello everyone!"

        # Get chat messages
        chat_get = await client.get(f"/meetings/{code}/chat")
        assert chat_get.status_code == 200
        msgs = chat_get.json()
        assert len(msgs) >= 1
        assert msgs[0]["sender_name"] == "Alice"


@pytest.mark.asyncio
async def test_lobby_and_host_controls():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Host signs up & creates meeting with lobby enabled
        host_email = f"host_{uuid.uuid4().hex[:6]}@example.com"
        host_signup = await client.post("/auth/signup", json={
            "email": host_email,
            "password": "password123",
            "display_name": "Meeting Host"
        })
        host_token = host_signup.json()["access_token"]
        host_headers = {"Authorization": f"Bearer {host_token}"}

        create_res = await client.post(
            "/meetings",
            json={"title": "Private Team Sync", "lobby_enabled": True},
            headers=host_headers
        )
        assert create_res.status_code == 201
        code = create_res.json()["code"]

        # 2. Guest joins -> gets 'waiting' status
        guest_join = await client.post(f"/meetings/{code}/join", json={
            "display_name": "Guest Bob"
        })
        assert guest_join.status_code == 200
        guest_data = guest_join.json()
        assert guest_data["status"] == "waiting"
        guest_p_id = guest_data["participant_id"]

        # 3. Host lists participants -> sees Guest Bob
        parts_res = await client.get(f"/meetings/{code}/participants", headers=host_headers)
        assert parts_res.status_code == 200
        parts = parts_res.json()
        assert any(p["id"] == guest_p_id and p["status"] == "waiting" for p in parts)

        # 4. Host admits Guest Bob
        admit_res = await client.post(
            f"/meetings/{code}/admit",
            json={"participant_id": guest_p_id, "admit": True},
            headers=host_headers
        )
        assert admit_res.status_code == 200
        assert admit_res.json()["status"] == "admitted"

        # 5. Guest rejoins/checks status with participant_id -> now 'admitted' with token
        guest_rejoin = await client.post(f"/meetings/{code}/join", json={
            "display_name": "Guest Bob",
            "participant_id": guest_p_id
        })
        assert guest_rejoin.status_code == 200
        assert guest_rejoin.json()["status"] == "admitted"
        assert guest_rejoin.json()["livekit_token"] is not None

        # 6. Host ends meeting
        end_res = await client.post(f"/meetings/{code}/end", headers=host_headers)
        assert end_res.status_code == 200
        assert end_res.json()["success"] is True
