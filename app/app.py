from fastapi import FastAPI, HTTPException, File, UploadFile, Form, Depends
from app.schemas import PostCreate, PostResponse, UserRead, UserCreate, UserUpdate
from app.db import Post, create_db_and_tables, get_async_session, User
from sqlalchemy.ext.asyncio import AsyncSession
from contextlib import asynccontextmanager
from sqlalchemy import select
from app.images import imagekit
from app.users import auth_backend, current_active_user, fastapi_users

import shutil
import os
import uuid
import tempfile

from pathlib import Path


# --------------------------------------------------
# Database Lifespan
# --------------------------------------------------

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


# --------------------------------------------------
# Authentication Routes
# --------------------------------------------------

app.include_router(
    fastapi_users.get_auth_router(auth_backend),
    prefix="/auth/jwt",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_reset_password_router(),
    prefix="/auth",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_verify_router(UserRead),
    prefix="/auth",
    tags=["auth"]
)

app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/users",
    tags=["users"]
)


# --------------------------------------------------
# Upload File Route
# --------------------------------------------------

@app.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    caption: str = Form(""),
    user: User = Depends(current_active_user),
    session: AsyncSession = Depends(get_async_session)
):

    temp_file_path = None

    try:

        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=os.path.splitext(file.filename or "")[1]
        ) as temp_file:

            temp_file_path = temp_file.name

            shutil.copyfileobj(file.file, temp_file)

        # Upload file to ImageKit
        upload = imagekit.files.upload(
            file=Path(temp_file_path),
            file_name=file.filename or "uploaded_file"
        )

        # Save uploaded file information in database
        post = Post(
            user_id=user.id,
            caption=caption,
            url=upload.url,
            file_type="video" if (file.content_type or "").startswith("video/") else "image",
            file_name=upload.name
        )

        session.add(post)

        await session.commit()

        await session.refresh(post)

        return post

    except Exception as e:

        await session.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )

    finally:

        # Delete temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            os.unlink(temp_file_path)

        file.file.close()


# --------------------------------------------------
# Feed Route
# --------------------------------------------------

@app.get("/feed")
async def get_feed(
    session: AsyncSession = Depends(get_async_session),
    user: User = Depends(current_active_user)
):

    try:
        # Fetch all posts
        result = await session.execute(
            select(Post).order_by(Post.created_at.desc())
        )

        posts = result.scalars().all()

        # Fetch all users
        result = await session.execute(select(User))

        users = result.scalars().all()

        # Create user dictionary
        user_dict = {
            u.id: u.email for u in users
        }

        posts_data = []

        # Prepare post information
        for post in posts:

            posts_data.append({
                "id": str(post.id),
                "user_id": str(post.user_id),
                "caption": post.caption,
                "url": post.url,
                "file_type": post.file_type,
                "file_name": post.file_name,
                "created_at": post.created_at.isoformat(),
                "is_owner": post.user_id == user.id,
                "email": user_dict.get(post.user_id, "Unknown")
            })

        # IMPORTANT: Return the response
        return {
            "posts": posts_data
        }

    except Exception as e:

        print(f"Feed Error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail=str(e)
        )