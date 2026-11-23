import uuid
import os

from typing import Optional
from dotenv import load_dotenv

from fastapi import Depends, Request

from fastapi_users import (
    BaseUserManager,
    FastAPIUsers,
    UUIDIDMixin,
)

from fastapi_users.authentication import (
    AuthenticationBackend,
    BearerTransport,
    JWTStrategy,
)

from fastapi_users.db import SQLAlchemyUserDatabase

from app.db import User, get_user_db


# -----------------------------------------
# LOAD ENVIRONMENT VARIABLES
# -----------------------------------------

load_dotenv()

SECRET = os.getenv("SECRET_KEY")

if not SECRET:
    raise RuntimeError(
        "SECRET_KEY environment variable is not configured."
    )


# -----------------------------------------
# USER MANAGER
# -----------------------------------------

class UserManager(UUIDIDMixin, BaseUserManager[User, uuid.UUID]):

    reset_password_token_secret = SECRET
    verification_token_secret = SECRET

    async def on_after_register(
        self,
        user: User,
        request: Optional[Request] = None
    ):
        print(f"User {user.id} has registered.")

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None
    ):
        print(f"Password reset requested for user {user.id}.")

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional[Request] = None
    ):
        print(f"Verification requested for user {user.id}.")


# -----------------------------------------
# GET USER MANAGER
# -----------------------------------------

async def get_user_manager(
    user_db: SQLAlchemyUserDatabase = Depends(get_user_db)
):
    yield UserManager(user_db)


# -----------------------------------------
# BEARER TRANSPORT
# -----------------------------------------

bearer_transport = BearerTransport(
    tokenUrl="auth/jwt/login"
)


# -----------------------------------------
# JWT STRATEGY
# -----------------------------------------

def get_jwt_strategy():

    return JWTStrategy(
        secret=SECRET,
        lifetime_seconds=3600
    )


# -----------------------------------------
# AUTHENTICATION BACKEND
# -----------------------------------------

auth_backend = AuthenticationBackend(
    name="jwt",
    transport=bearer_transport,
    get_strategy=get_jwt_strategy,
)


# -----------------------------------------
# FASTAPI USERS
# -----------------------------------------

fastapi_users = FastAPIUsers[User, uuid.UUID](
    get_user_manager,
    [auth_backend]
)


current_active_user = fastapi_users.current_user(
    active=True
)