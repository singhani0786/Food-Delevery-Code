from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

from database import get_connection
from dependencies import get_current_admin
from auth import hash_password


router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"]
)


# =====================================================
# MODELS
# =====================================================

class AdminUserCreate(BaseModel):
    name: str
    email: str
    password: str
    role: str


class AdminUserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None


class BlockUserRequest(BaseModel):
    is_blocked: bool


class AdminRestaurantCreate(BaseModel):
    owner_id: int
    name: str
    description: Optional[str] = None


class AdminMealCreate(BaseModel):
    restaurant_id: int
    name: str
    description: Optional[str] = None
    price: Decimal


# =====================================================
# ADMIN USERS
# =====================================================

@router.get("/users/")
def get_all_users(
    admin: dict = Depends(get_current_admin)
):

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
        ORDER BY user_id;
    """)

    users = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "user_id": user[0],
            "name": user[1],
            "email": user[2],
            "role": user[3],
            "is_blocked": user[4]
        }
        for user in users
    ]


# =====================================================
# ADMIN CREATE USER
# =====================================================

@router.post("/users/")
def create_user(
    user: AdminUserCreate,
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE email = %s;
    """, (user.email,))

    if cursor.fetchone():

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Email already exists"
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
# ADMIN GET USER
# =====================================================

@router.get("/users/{user_id}")
def admin_get_user(
    user_id: int,
    admin: dict = Depends(get_current_admin)
):

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
# ADMIN UPDATE USER
# =====================================================

@router.put("/users/{user_id}")
def admin_update_user(
    user_id: int,
    user: AdminUserUpdate,
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            name,
            email,
            role
        FROM users
        WHERE user_id = %s;
    """, (user_id,))

    existing = cursor.fetchone()

    if existing is None:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="User not found"
        )

    name = user.name if user.name else existing[0]
    email = user.email if user.email else existing[1]
    role = user.role.upper() if user.role else existing[2]

    cursor.execute("""
        UPDATE users
        SET
            name = %s,
            email = %s,
            role = %s
        WHERE user_id = %s;
    """, (
        name,
        email,
        role,
        user_id
    ))

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "user_id": user_id,
        "name": name,
        "email": email,
        "role": role
    }


# =====================================================
# ADMIN DELETE USER
# =====================================================

@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: int,
    admin: dict = Depends(get_current_admin)
):

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


# =====================================================
# BLOCK / UNBLOCK USER
# =====================================================

@router.patch("/users/{user_id}/block")
def block_user(
    user_id: int,
    request: BlockUserRequest,
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE users
        SET is_blocked = %s
        WHERE user_id = %s;
    """, (
        request.is_blocked,
        user_id
    ))

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

    message = (
        "User blocked successfully"
        if request.is_blocked
        else
        "User unblocked successfully"
    )

    return {
        "user_id": user_id,
        "is_blocked": request.is_blocked,
        "message": message
    }


# =====================================================
# ADMIN RESTAURANTS
# =====================================================

@router.get("/restaurants/")
def get_all_restaurants(
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            restaurant_id,
            name,
            description,
            owner_id
        FROM restaurants
        ORDER BY restaurant_id;
    """)

    restaurants = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "restro_id": restaurant[0],
            "name": restaurant[1],
            "description": restaurant[2],
            "owner_id": restaurant[3]
        }
        for restaurant in restaurants
    ]


# =====================================================
# ADMIN CREATE RESTAURANT
# =====================================================

@router.post("/restaurants/")
def admin_create_restaurant(
    restaurant: AdminRestaurantCreate,
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT user_id
        FROM users
        WHERE user_id = %s;
    """, (restaurant.owner_id,))

    if cursor.fetchone() is None:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Restaurant owner not found"
        )

    cursor.execute("""
        INSERT INTO restaurants
            (owner_id, name, description)
        VALUES
            (%s, %s, %s)
        RETURNING restaurant_id;
    """, (
        restaurant.owner_id,
        restaurant.name,
        restaurant.description
    ))

    restaurant_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "restro_id": restaurant_id,
        "name": restaurant.name,
        "description": restaurant.description,
        "owner_id": restaurant.owner_id
    }


# =====================================================
# ADMIN UPDATE RESTAURANT
# =====================================================

@router.put("/restaurants/{restro_id}")
def admin_update_restaurant(
    restro_id: int,
    restaurant: AdminRestaurantCreate,
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE restaurants
        SET
            owner_id = %s,
            name = %s,
            description = %s
        WHERE restaurant_id = %s;
    """, (
        restaurant.owner_id,
        restaurant.name,
        restaurant.description,
        restro_id
    ))

    if cursor.rowcount == 0:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "restro_id": restro_id,
        "name": restaurant.name,
        "description": restaurant.description,
        "owner_id": restaurant.owner_id
    }


# =====================================================
# ADMIN DELETE RESTAURANT
# =====================================================

@router.delete("/restaurants/{restro_id}")
def admin_delete_restaurant(
    restro_id: int,
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM restaurants
        WHERE restaurant_id = %s;
    """, (restro_id,))

    if cursor.rowcount == 0:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Restaurant deleted successfully"
    }


# =====================================================
# ADMIN MEALS
# =====================================================

@router.get("/meals/")
def get_all_meals(
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            meal_id,
            restaurant_id,
            name,
            description,
            price
        FROM meals
        ORDER BY meal_id;
    """)

    meals = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "meal_id": meal[0],
            "restaurant_id": meal[1],
            "name": meal[2],
            "description": meal[3],
            "price": meal[4]
        }
        for meal in meals
    ]


# =====================================================
# ADMIN CREATE MEAL
# =====================================================

@router.post("/meals/")
def admin_create_meal(
    meal: AdminMealCreate,
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT restaurant_id
        FROM restaurants
        WHERE restaurant_id = %s;
    """, (meal.restaurant_id,))

    if cursor.fetchone() is None:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    cursor.execute("""
        INSERT INTO meals
            (
                restaurant_id,
                name,
                description,
                price
            )
        VALUES
            (%s, %s, %s, %s)
        RETURNING meal_id;
    """, (
        meal.restaurant_id,
        meal.name,
        meal.description,
        meal.price
    ))

    meal_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "meal_id": meal_id,
        "restaurant_id": meal.restaurant_id,
        "name": meal.name,
        "description": meal.description,
        "price": meal.price
    }


# =====================================================
# ADMIN UPDATE MEAL
# =====================================================

@router.put("/meals/{meal_id}")
def admin_update_meal(
    meal_id: int,
    meal: AdminMealCreate,
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE meals
        SET
            restaurant_id = %s,
            name = %s,
            description = %s,
            price = %s
        WHERE meal_id = %s;
    """, (
        meal.restaurant_id,
        meal.name,
        meal.description,
        meal.price,
        meal_id
    ))

    if cursor.rowcount == 0:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Meal not found"
        )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "meal_id": meal_id,
        "restaurant_id": meal.restaurant_id,
        "name": meal.name,
        "description": meal.description,
        "price": meal.price
    }


# =====================================================
# ADMIN DELETE MEAL
# =====================================================

@router.delete("/meals/{meal_id}")
def admin_delete_meal(
    meal_id: int,
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM meals
        WHERE meal_id = %s;
    """, (meal_id,))

    if cursor.rowcount == 0:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Meal not found"
        )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Meal deleted successfully"
    }
# =====================================================
# TOP 3 CUSTOMERS BY NUMBER OF ORDERS
# =====================================================

@router.get("/customers/top")
def get_top_customers(
    admin: dict = Depends(get_current_admin)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            u.user_id,
            u.name,
            u.email,
            COUNT(o.order_id) AS total_orders
        FROM users u
        JOIN orders o
            ON u.user_id = o.customer_id
        WHERE u.role = 'CUSTOMER'
        GROUP BY
            u.user_id,
            u.name,
            u.email
        ORDER BY total_orders DESC
        LIMIT 3;
    """)

    customers = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "user_id": customer[0],
            "name": customer[1],
            "email": customer[2],
            "total_orders": customer[3]
        }
        for customer in customers
    ]
