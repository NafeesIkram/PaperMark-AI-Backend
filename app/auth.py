import os
from datetime import datetime, timedelta

import bcrypt
from dotenv import load_dotenv

from fastapi import (
    Depends,
    HTTPException,
    Request,
)

from jose import JWTError, jwt

from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User


load_dotenv()


JWT_SECRET = os.getenv("JWT_SECRET")

if not JWT_SECRET:
    raise RuntimeError(
        "JWT_SECRET is not configured."
    )


ALGORITHM = "HS256"

TOKEN_EXPIRE_DAYS = 7


# =========================================================
# PASSWORD
# =========================================================

def hash_password(password: str) -> str:

    password_bytes = password.encode(
        "utf-8"
    )

    if len(password_bytes) > 72:
        raise ValueError(
            "Password must be 72 bytes or fewer."
        )

    hashed = bcrypt.hashpw(
        password_bytes,
        bcrypt.gensalt()
    )

    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:

    password_bytes = plain_password.encode(
        "utf-8"
    )

    if len(password_bytes) > 72:
        return False

    return bcrypt.checkpw(
        password_bytes,
        hashed_password.encode("utf-8"),
    )


# =========================================================
# JWT
# =========================================================

def create_token(user_id: int) -> str:

    expire = (
        datetime.utcnow()
        + timedelta(
            days=TOKEN_EXPIRE_DAYS
        )
    )

    payload = {
        "sub": str(user_id),
        "exp": expire,
    }

    return jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=ALGORITHM,
    )


# =========================================================
# CURRENT USER
# =========================================================

def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
):

    token = request.cookies.get(
        "papermark_token"
    )

    if not token:
        raise HTTPException(
            status_code=401,
            detail="Authentication required.",
        )

    try:

        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[ALGORITHM],
        )

        user_id = payload.get("sub")

        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token.",
            )

    except JWTError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired authentication token.",
        )

    user = (
        db.query(User)
        .filter(
            User.id == int(user_id)
        )
        .first()
    )

    if not user:

        raise HTTPException(
            status_code=401,
            detail="User not found.",
        )

    return user