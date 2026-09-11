from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from database import get_connection


router = APIRouter(
    prefix="/api/users",
    tags=["Users"]
)


class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None


# =====================================================
# GET USER
# =====================================================

@router.get("/{user_id}")
def get_user(user_id: int):

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
            status_code=404,
            detail="User not found"
        )

    return {
        "user_id": user[0],
        "name": user[1],
        "email": user[2],
        "role": user[3],
        "is_blocked": user[4]
    }


# =====================================================
# UPDATE USER
# =====================================================

@router.put("/{user_id}")
def update_user(
    user_id: int,
    user: UserUpdate
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id, name, email
        FROM users
        WHERE user_id = %s;
    """, (user_id,))

    existing_user = cursor.fetchone()

    if existing_user is None:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    new_name = (
        user.name
        if user.name is not None
        else existing_user[1]
    )

    new_email = (
        user.email
        if user.email is not None
        else existing_user[2]
    )

    cursor.execute("""
        UPDATE users
        SET
            name = %s,
            email = %s
        WHERE user_id = %s;
    """, (
        new_name,
        new_email,
        user_id
    ))

    connection.commit()

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

    updated_user = cursor.fetchone()

    cursor.close()
    connection.close()

    return {
        "user_id": updated_user[0],
        "name": updated_user[1],
        "email": updated_user[2],
        "role": updated_user[3],
        "is_blocked": updated_user[4]
    }


# =====================================================
# DELETE USER
# =====================================================

@router.delete("/{user_id}")
def delete_user(user_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM users
        WHERE user_id = %s;
    """, (user_id,))

    if cursor.rowcount == 0:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "User deleted successfully"
    }