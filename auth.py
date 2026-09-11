from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import hashlib
import os
import jwt
from datetime import datetime, timedelta

from database import get_connection
from dependencies import (
    SECRET_KEY,
    ALGORITHM,
    get_current_user
)


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


# =====================================================
# MODELS
# =====================================================

class RegisterRequest(BaseModel):
    name: str
    email: str
    password: str
    role: str = "CUSTOMER"


class LoginRequest(BaseModel):
    email: str
    password: str


# =====================================================
# PASSWORD HELPERS
# =====================================================

def hash_password(password: str) -> str:

    salt = os.urandom(16)

    password_hash = hashlib.pbkdf2_hmac(
        "sha256",
        password.encode("utf-8"),
        salt,
        100000
    )

    return (
        salt.hex()
        + ":"
        + password_hash.hex()
    )


def verify_password(password: str, stored_password: str) -> bool:

    try:

        salt_hex, hash_hex = stored_password.split(":")

        salt = bytes.fromhex(salt_hex)

        new_hash = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            salt,
            100000
        )

        return new_hash.hex() == hash_hex

    except Exception:

        return False


# =====================================================
# CREATE JWT TOKEN
# =====================================================

def create_access_token(user_id: int):

    payload = {
        "user_id": user_id,
        "exp": datetime.utcnow() + timedelta(hours=24)
    }

    return jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


# =====================================================
# REGISTER
# =====================================================

@router.post("/register")
def register(user: RegisterRequest):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE email = %s;
    """, (user.email,))

    existing_user = cursor.fetchone()

    if existing_user:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    password_hash = hash_password(user.password)

    cursor.execute("""
        INSERT INTO users
            (name, email, password, role)
        VALUES
            (%s, %s, %s, %s)
        RETURNING user_id;
    """, (
        user.name,
        user.email,
        password_hash,
        user.role.upper()
    ))

    user_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "user_id": user_id,
        "name": user.name,
        "email": user.email,
        "role": user.role.upper(),
        "is_blocked": False
    }


# =====================================================
# LOGIN
# =====================================================

@router.post("/login")
def login(user: LoginRequest):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            user_id,
            name,
            email,
            password,
            role,
            is_blocked
        FROM users
        WHERE email = %s;
    """, (user.email,))

    db_user = cursor.fetchone()

    cursor.close()
    connection.close()

    if db_user is None:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    if db_user[5]:

        raise HTTPException(
            status_code=403,
            detail="User is blocked"
        )

    if not verify_password(
        user.password,
        db_user[3]
    ):

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    token = create_access_token(
        db_user[0]
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "user_id": db_user[0],
            "name": db_user[1],
            "email": db_user[2],
            "role": db_user[4]
        }
    }


# =====================================================
# CURRENT USER
# =====================================================

@router.get("/me")
def get_me(
    current_user: dict = Depends(get_current_user)
):

    return current_user