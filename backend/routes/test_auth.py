from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
from backend.main import app
from backend.routes import auth as auth_routes
from backend.helpers import helper_auth
from datetime import datetime, timezone


@pytest.fixture(scope="module", autouse=True)
def test_db():
    # In-memory MongoDB for testing
    mock_client = AsyncMongoMockClient()
    test_database = mock_client.get_database("testdb")

    # Override the database client in auth_routes and helper_auth
    auth_routes._db = test_database
    auth_routes.users_coll = test_database["users"]
    auth_routes.password_reset_coll = test_database["password_reset"]
    auth_routes.email_verification_coll = test_database["email_verification"]

    helper_auth._db = test_database
    helper_auth.users_coll = test_database["users"]
    helper_auth.password_reset_coll = test_database["password_reset"]
    helper_auth.email_verification_coll = test_database["email_verification"]

    yield test_database

    # Clean up the database after tests
    mock_client.close()


@pytest.fixture(scope="function")
def client():
    with TestClient(app) as c:
        yield c


@pytest.mark.asyncio
async def test_register_user_username_already_taken(client, test_db):
    # Pre-populate a user
    await test_db["users"].insert_one({
        "username": "existinguser",
        "hashed_password": "somehashedpassword",
        "email": "existing@example.com",
        "full_name": "Existing User",
        "email_verified": False,
        "profile_picture_url": None,
        "group_ids": []
    })

    response = client.post(
        "/auth/register",
        data={
            "username": "existinguser",
            "password": "StrongPassword123",
            "email": "new@example.com",
            "full_name": "New User"
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already taken"}


@pytest.mark.asyncio
async def test_register_user_email_already_taken(client, test_db):
    # Pre-populate a user
    await test_db["users"].insert_one({
        "username": "anotheruser",
        "hashed_password": "somehashedpassword",
        "email": "taken@example.com",
        "full_name": "Another User",
        "email_verified": False,
        "profile_picture_url": None,
        "group_ids": []
    })

    response = client.post(
        "/auth/register",
        data={
            "username": "newuser",
            "password": "StrongPassword123",
            "email": "taken@example.com",
            "full_name": "New User"
        }
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already taken"}


@pytest.mark.asyncio
async def test_verify_email_success(client, test_db):
    # Pre-populate a user and an email verification token
    await test_db["users"].insert_one({
        "username": "unverifieduser",
        "hashed_password": "somehashedpassword",
        "email": "unverified@example.com",
        "full_name": "Unverified User",
        "email_verified": False,
        "profile_picture_url": None,
        "group_ids": []
    })
    await test_db["email_verification"].insert_one({
        "email": "unverified@example.com",
        "email_verification_url": "valid_token",
        "created_at": datetime.now(timezone.utc)
    })

    response = client.post(
        "/auth/verify-email",
        data={"email_verification_token": "valid_token"}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Email successfully verified."}

    # Verify that the user's email_verified field is updated
    user_in_db = await test_db["users"].find_one({"username": "unverifieduser"})
    assert user_in_db["email_verified"] is True

    # Verify that the verification token is deleted
    token_in_db = await test_db["email_verification"].find_one({"email_verification_url": "valid_token"})
    assert token_in_db is None


@pytest.mark.asyncio
async def test_verify_email_invalid_token(client, test_db):
    response = client.post(
        "/auth/verify-email",
        data={"email_verification_token": "invalid_token"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid email verification token"}


@pytest.mark.asyncio
@patch('backend.routes.auth.verify_email_helper_task.delay', new_callable=AsyncMock)
async def test_resend_verify_email_already_verified(mock_celery_task, client, test_db):
    # Pre-populate a user
    await test_db["users"].insert_one({
        "username": "verifieduser",
        "hashed_password": "somehashedpassword",
        "email": "verified@example.com",
        "full_name": "Verified User",
        "email_verified": True,
        "profile_picture_url": None,
        "group_ids": []
    })

    response = client.post(
        "/auth/resend-verify-email",
        data={"email": "verified@example.com"}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "If your email is registered and unverified, a new verification link has been sent."}
    mock_celery_task.assert_not_called()


@pytest.mark.asyncio
@patch('backend.routes.auth.verify_email_helper_task.delay', new_callable=AsyncMock)
async def test_resend_verify_email_unregistered_email(mock_celery_task, client):
    response = client.post(
        "/auth/resend-verify-email",
        data={"email": "unregistered@example.com"}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "If your email is registered and unverified, a new verification link has been sent."}
    mock_celery_task.assert_not_called()


@pytest.mark.asyncio
async def test_login_for_access_token_success(client, test_db):
    # Pre-populate a user
    from backend.helpers.helper_auth import get_password_hash
    await test_db["users"].insert_one({
        "username": "loginuser",
        "hashed_password": get_password_hash("StrongPassword123"),
        "email": "loginuser@example.com",
        "full_name": "Login User",
        "email_verified": True,
        "profile_picture_url": None,
        "group_ids": []
    })

    response = client.post(
        "/auth/login",
        data={"username": "loginuser", "password": "StrongPassword123"}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Login successful"}
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_login_for_access_token_incorrect_password(client, test_db):
    # Pre-populate a user
    from backend.helpers.helper_auth import get_password_hash
    await test_db["users"].insert_one({
        "username": "loginuser2",
        "hashed_password": get_password_hash("StrongPassword123"),
        "email": "loginuser2@example.com",
        "full_name": "Login User 2",
        "email_verified": True,
        "profile_picture_url": None,
        "group_ids": []
    })

    response = client.post(
        "/auth/login",
        data={"username": "loginuser2", "password": "WrongPassword"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Incorrect username or password"}


@pytest.mark.asyncio
async def test_login_for_access_token_unverified_email(client, test_db):
    # Pre-populate a user
    from backend.helpers.helper_auth import get_password_hash
    await test_db["users"].insert_one({
        "username": "loginuser3",
        "hashed_password": get_password_hash("StrongPassword123"),
        "email": "loginuser3@example.com",
        "full_name": "Login User 3",
        "email_verified": False,
        "profile_picture_url": None,
        "group_ids": []
    })

    response = client.post(
        "/auth/login",
        data={"username": "loginuser3", "password": "StrongPassword123"}
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Please verify your email address."}


@pytest.mark.asyncio
async def test_read_users_me_success(client, test_db):
    # Pre-populate a user
    from backend.helpers.helper_auth import create_access_token
    from datetime import timedelta

    username = "mydetailsuser"
    await test_db["users"].insert_one({
        "username": username,
        "hashed_password": "somehashedpassword",
        "email": "mydetails@example.com",
        "full_name": "My Details User",
        "email_verified": True,
        "profile_picture_url": None,
        "group_ids": []
    })

    # Create an access token for the user
    access_token = create_access_token(
        data={"sub": username},
        expires_delta_in_min=timedelta(minutes=30)
    )

    # Set the access token as a cookie
    client.cookies.set("access_token", f"Bearer {access_token}")

    response = client.get("/auth/my-details")
    assert response.status_code == 200
    response_data = response.json()
    assert response_data["username"] == username
    assert response_data["email"] == "mydetails@example.com"
    assert response_data["full_name"] == "My Details User"


@pytest.mark.asyncio
async def test_read_users_me_no_token(client):
    response = client.get("/auth/my-details")
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}


@pytest.mark.asyncio
async def test_logout(client):
    # Set a dummy cookie
    client.cookies.set("access_token", "dummy_token")

    response = client.post("/auth/logout")
    assert response.status_code == 200
    assert response.json() == {"msg": "Logged out successfully"}
    assert "access_token" not in response.cookies


@pytest.mark.asyncio
async def test_reset_password_success(client, test_db):
    # Pre-populate a user and a password reset token
    from backend.helpers.helper_auth import get_password_hash, verify_password
    email = "resetpassword@example.com"
    await test_db["users"].insert_one({
        "username": "resetpassworduser",
        "hashed_password": get_password_hash("OldPassword"),
        "email": email,
        "full_name": "Reset Password User",
        "email_verified": True,
        "profile_picture_url": None,
        "group_ids": []
    })
    await test_db["password_reset"].insert_one({
        "email": email,
        "password_reset_url": "valid_reset_token",
        "created_at": datetime.now(timezone.utc)
    })

    response = client.post(
        "/auth/reset-password",
        data={"reset_token": "valid_reset_token", "new_password": "NewStrongPassword123"}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Password successfully reset."}

    # Verify that the user's password is updated
    user_in_db = await test_db["users"].find_one({"email": email})
    assert verify_password("NewStrongPassword123", user_in_db["hashed_password"])

    # Verify that the reset token is deleted
    token_in_db = await test_db["password_reset"].find_one({"password_reset_url": "valid_reset_token"})
    assert token_in_db is None


@pytest.mark.asyncio
async def test_reset_password_invalid_token(client, test_db):
    response = client.post(
        "/auth/reset-password",
        data={"reset_token": "invalid_reset_token", "new_password": "NewStrongPassword123"}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Invalid password reset token"}


@pytest.mark.asyncio
async def test_change_username_success(client, test_db):
    # Pre-populate a user
    from backend.helpers.helper_auth import create_access_token
    from datetime import timedelta

    username = "changeusernameuser"
    await test_db["users"].insert_one({
        "username": username,
        "hashed_password": "somehashedpassword",
        "email": "changeusername@example.com",
        "full_name": "Change Username User",
        "email_verified": True,
        "profile_picture_url": None,
        "group_ids": []
    })

    # Create an access token for the user
    access_token = create_access_token(
        data={"sub": username},
        expires_delta_in_min=timedelta(minutes=30)
    )

    # Set the access token as a cookie
    client.cookies.set("access_token", f"Bearer {access_token}")

    new_username = "newusername"
    response = client.post(
        "/auth/change-username",
        data={"new_username": new_username}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Username successfully updated."}

    # Verify that the username is updated in the database
    user_in_db = await test_db["users"].find_one({"username": new_username})
    assert user_in_db is not None

    # Verify that the old username no longer exists
    old_user_in_db = await test_db["users"].find_one({"username": username})
    assert old_user_in_db is None

    # Verify that the new access token is set in the cookie
    assert "access_token" in response.cookies


@pytest.mark.asyncio
async def test_change_username_taken(client, test_db):
    # Pre-populate two users
    from backend.helpers.helper_auth import create_access_token
    from datetime import timedelta

    username1 = "changeusernameuser1"
    username2 = "changeusernameuser2"
    await test_db["users"].insert_many([
        {
            "username": username1,
            "hashed_password": "somehashedpassword",
            "email": "changeusername1@example.com",
            "full_name": "Change Username User 1",
            "email_verified": True,
            "profile_picture_url": None,
            "group_ids": []
        },
        {
            "username": username2,
            "hashed_password": "somehashedpassword",
            "email": "changeusername2@example.com",
            "full_name": "Change Username User 2",
            "email_verified": True,
            "profile_picture_url": None,
            "group_ids": []
        }
    ])

    # Create an access token for the first user
    access_token = create_access_token(
        data={"sub": username1},
        expires_delta_in_min=timedelta(minutes=30)
    )

    # Set the access token as a cookie
    client.cookies.set("access_token", f"Bearer {access_token}")

    response = client.post(
        "/auth/change-username",
        data={"new_username": username2}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already taken"}


@pytest.mark.asyncio
async def test_change_password_success(client, test_db):
    # Pre-populate a user
    from backend.helpers.helper_auth import get_password_hash, create_access_token, verify_password
    from datetime import timedelta

    username = "changepassworduser"
    old_password = "OldPassword123"
    new_password = "NewStrongPassword123"

    await test_db["users"].insert_one({
        "username": username,
        "hashed_password": get_password_hash(old_password),
        "email": "changepassword@example.com",
        "full_name": "Change Password User",
        "email_verified": True,
        "profile_picture_url": None,
        "group_ids": []
    })

    # Create an access token for the user
    access_token = create_access_token(
        data={"sub": username},
        expires_delta_in_min=timedelta(minutes=30)
    )

    # Set the access token as a cookie
    client.cookies.set("access_token", f"Bearer {access_token}")

    response = client.post(
        "/auth/change-password",
        data={"old_password": old_password, "new_password": new_password}
    )
    assert response.status_code == 200
    assert response.json() == {"msg": "Password successfully changed."}

    # Verify that the password is updated in the database
    user_in_db = await test_db["users"].find_one({"username": username})
    assert verify_password(new_password, user_in_db["hashed_password"])


@pytest.mark.asyncio
async def test_change_password_incorrect_old_password(client, test_db):
    # Pre-populate a user
    from backend.helpers.helper_auth import get_password_hash, create_access_token
    from datetime import timedelta

    username = "changepassworduser2"
    old_password = "OldPassword123"
    new_password = "NewStrongPassword123"

    await test_db["users"].insert_one({
        "username": username,
        "hashed_password": get_password_hash(old_password),
        "email": "changepassword2@example.com",
        "full_name": "Change Password User 2",
        "email_verified": True,
        "profile_picture_url": None,
        "group_ids": []
    })

    # Create an access token for the user
    access_token = create_access_token(
        data={"sub": username},
        expires_delta_in_min=timedelta(minutes=30)
    )

    # Set the access token as a cookie
    client.cookies.set("access_token", f"Bearer {access_token}")

    response = client.post(
        "/auth/change-password",
        data={"old_password": "WrongOldPassword", "new_password": new_password}
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Old password is incorrect"}
