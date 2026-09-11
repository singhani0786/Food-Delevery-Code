from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt

from database import get_connection


SECRET_KEY = "food-delivery-secret-key"
ALGORITHM = "HS256"

security = HTTPBearer()


# =====================================================
# GET CURRENT USER
# =====================================================

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )

        user_id = payload.get("user_id")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

    except jwt.InvalidTokenError:

        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            user_id,
            name,
            email,
            role,
            is_blocked
        FROM users
        WHERE user_id = %s;
    """, (user_id,))

    user = cursor.fetchone()

    cursor.close()
    connection.close()

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )

    if user[4]:
        raise HTTPException(
            status_code=403,
            detail="User is blocked"
        )

    return {
        "user_id": user[0],
        "name": user[1],
        "email": user[2],
        "role": user[3],
        "is_blocked": user[4]
    }


# =====================================================
# ADMIN CHECK
# =====================================================

def get_current_admin(
    current_user: dict = Depends(get_current_user)
):

    if current_user["role"].upper() != "ADMIN":

        raise HTTPException(
            status_code=403,
            detail="Admin access required"
        )

    return current_user