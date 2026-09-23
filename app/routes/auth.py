from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    Response,
)

from sqlalchemy.orm import Session

from app.auth import (
    create_token,
    get_current_user,
    hash_password,
    verify_password,
)

from app.database import get_db

from app.models import User

from app.schemas import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
)


# =========================================================
# ROUTER
# =========================================================

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


# =========================================================
# REGISTER
# =========================================================

@router.post(
    "/register",
    response_model=UserResponse,
)
def register(
    data: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):

    existing = db.query(User).filter(
        User.email == data.email.lower()
    ).first()

    if existing:

        raise HTTPException(
            status_code=400,
            detail="An account with this email already exists.",
        )

    if len(data.password) < 8:

        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters.",
        )

    user = User(
        name=data.name.strip(),
        email=data.email.lower(),
        password_hash=hash_password(
            data.password
        ),
    )

    db.add(user)

    db.commit()

    db.refresh(user)

    token = create_token(user.id)

    # -----------------------------------------------------
    # PRODUCTION AUTH COOKIE
    # -----------------------------------------------------

    response.set_cookie(
        key="papermark_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24 * 7,
    )

    return user


# =========================================================
# LOGIN
# =========================================================

@router.post("/login")
def login(
    data: LoginRequest,
    response: Response,
    db: Session = Depends(get_db),
):

    user = db.query(User).filter(
        User.email == data.email.lower()
    ).first()

    if not user:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    if not verify_password(
        data.password,
        user.password_hash,
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password.",
        )

    token = create_token(user.id)

    # -----------------------------------------------------
    # PRODUCTION AUTH COOKIE
    # -----------------------------------------------------

    response.set_cookie(
        key="papermark_token",
        value=token,
        httponly=True,
        secure=True,
        samesite="none",
        max_age=60 * 60 * 24 * 7,
    )

    return {
        "message": "Login successful."
    }


# =========================================================
# LOGOUT
# =========================================================

@router.post("/logout")
def logout(response: Response):

    response.delete_cookie(
        key="papermark_token",
        secure=True,
        samesite="none",
    )

    return {
        "message": "Logged out."
    }


# =========================================================
# CURRENT USER
# =========================================================

@router.get(
    "/me",
    response_model=UserResponse,
)
def me(
    current_user: User = Depends(
        get_current_user
    ),
):

    return current_user