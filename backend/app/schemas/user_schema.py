from pydantic import (
    BaseModel,
    EmailStr,
    field_validator
)

import re


class UserCreate(BaseModel):

    username: str
    email: EmailStr
    password: str
    role: str = "user"

    @field_validator("password")
    @classmethod
    def validate_password(
        cls,
        value
    ):

        if len(value) < 8:
            raise ValueError(
                "Password must be at least 8 characters"
            )

        if not re.search(r"[A-Z]", value):
            raise ValueError(
                "Password must contain uppercase letter"
            )

        if not re.search(r"[a-z]", value):
            raise ValueError(
                "Password must contain lowercase letter"
            )

        if not re.search(r"[0-9]", value):
            raise ValueError(
                "Password must contain a number"
            )

        if not re.search(
            r"[!@#$%^&*()]",
            value
        ):
            raise ValueError(
                "Password must contain special character"
            )

        return value


class UserLogin(BaseModel):

    email: EmailStr
    password: str