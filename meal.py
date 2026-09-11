from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from decimal import Decimal

from database import get_connection


router = APIRouter(
    tags=["Meals"]
)


class MealCreate(BaseModel):
    name: str
    description: str | None = None
    price: Decimal


# =====================================================
# GET ALL MEALS OF A RESTAURANT
# =====================================================

@router.get("/api/restro/{restro_id}/meals")
def get_restaurant_meals(restro_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    # First check restaurant exists
    cursor.execute("""
        SELECT restaurant_id
        FROM restaurants
        WHERE restaurant_id = %s;
    """, (restro_id,))

    restaurant = cursor.fetchone()

    if restaurant is None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    cursor.execute("""
        SELECT
            meal_id,
            restaurant_id,
            name,
            description,
            price
        FROM meals
        WHERE restaurant_id = %s
        ORDER BY meal_id;
    """, (restro_id,))

    meals = cursor.fetchall()

    cursor.close()
    connection.close()

    result = []

    for meal in meals:
        result.append({
            "meal_id": meal[0],
            "restaurant_id": meal[1],
            "name": meal[2],
            "description": meal[3],
            "price": meal[4]
        })

    return result


# =====================================================
# CREATE MEAL
# =====================================================

@router.post("/api/restro/{restro_id}/meals")
def create_meal(
    restro_id: int,
    meal: MealCreate
):

    connection = get_connection()
    cursor = connection.cursor()

    # Check restaurant exists
    cursor.execute("""
        SELECT restaurant_id
        FROM restaurants
        WHERE restaurant_id = %s;
    """, (restro_id,))

    restaurant = cursor.fetchone()

    if restaurant is None:
        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    cursor.execute("""
        INSERT INTO meals
            (restaurant_id, name, description, price)
        VALUES
            (%s, %s, %s, %s)
        RETURNING meal_id;
    """, (
        restro_id,
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
        "restaurant_id": restro_id,
        "name": meal.name,
        "description": meal.description,
        "price": meal.price
    }


# =====================================================
# GET MEAL BY ID
# =====================================================

@router.get("/api/meals/{meal_id}")
def get_meal(meal_id: int):

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
        WHERE meal_id = %s;
    """, (meal_id,))

    meal = cursor.fetchone()

    cursor.close()
    connection.close()

    if meal is None:
        raise HTTPException(
            status_code=404,
            detail="Meal not found"
        )

    return {
        "meal_id": meal[0],
        "restaurant_id": meal[1],
        "name": meal[2],
        "description": meal[3],
        "price": meal[4]
    }


# =====================================================
# UPDATE MEAL
# =====================================================

@router.put("/api/meals/{meal_id}")
def update_meal(
    meal_id: int,
    meal: MealCreate
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE meals
        SET
            name = %s,
            description = %s,
            price = %s
        WHERE meal_id = %s;
    """, (
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

    # Get restaurant_id after update
    cursor.execute("""
        SELECT
            meal_id,
            restaurant_id,
            name,
            description,
            price
        FROM meals
        WHERE meal_id = %s;
    """, (meal_id,))

    updated_meal = cursor.fetchone()

    cursor.close()
    connection.close()

    return {
        "meal_id": updated_meal[0],
        "restaurant_id": updated_meal[1],
        "name": updated_meal[2],
        "description": updated_meal[3],
        "price": updated_meal[4]
    }


# =====================================================
# DELETE MEAL
# =====================================================

@router.delete("/api/meals/{meal_id}")
def delete_meal(meal_id: int):

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