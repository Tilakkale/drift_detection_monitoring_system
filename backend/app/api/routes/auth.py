from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
)

from sqlalchemy.orm import Session

from backend.app.database.connection import SessionLocal
from backend.app.models.user import User

from backend.app.schemas.user_schema import (
    UserCreate,
    UserLogin,
)

from backend.app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
)

from backend.app.core.logger import logger
from backend.app.core.dependencies import get_current_user

router = APIRouter()


def get_db():

    db = SessionLocal()

    try:
        yield db

    finally:
        db.close()


@router.post("/signup")
def signup(
    user: UserCreate,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if existing_user:

        logger.warning(
            f"Signup failed - Email already exists: {user.email}"
        )

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
        )

    new_user = User(
    username=user.username,
    email=user.email,
    password=hash_password(
        user.password
    ),
    role=user.role
)

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    logger.info(
        f"New user registered: {user.email}"
    )

    return {
        "message": "User created successfully"
    }


@router.post("/login")
def login(
    user: UserLogin,
    db: Session = Depends(get_db)
):

    db_user = db.query(User).filter(
        User.email == user.email
    ).first()

    if not db_user:

        logger.warning(
            f"Login failed - User not found: {user.email}"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    if not verify_password(
        user.password,
        db_user.password
    ):

        logger.warning(
            f"Login failed - Wrong password: {user.email}"
        )

        raise HTTPException(
            status_code=401,
            detail="Invalid credentials"
        )

    logger.info(
        f"User logged in successfully: {user.email}"
    )

    token = create_access_token(
        {
            "sub": db_user.email
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer"
    }


@router.get("/profile")
def profile(
    current_user=Depends(get_current_user)
):

    return {
        "message": "Protected Route",
        "user": current_user
    }