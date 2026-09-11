from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from database import get_connection


router = APIRouter(
    prefix="/api/restro",
    tags=["Restaurants"]
)


class RestaurantCreate(BaseModel):
    owner_id: int
    name: str
    description: str | None = None


# --------------------------------
# GET ALL RESTAURANTS
# --------------------------------

@router.get("/")
def get_all_restaurants():

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

    result = []

    for restaurant in restaurants:
        result.append({
            "restro_id": restaurant[0],
            "name": restaurant[1],
            "description": restaurant[2],
            "owner_id": restaurant[3]
        })

    return result


# --------------------------------
# CREATE RESTAURANT
# --------------------------------

@router.post("/")
def create_restaurant(restaurant: RestaurantCreate):

    connection = get_connection()
    cursor = connection.cursor()

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


# --------------------------------
# GET RESTAURANT BY ID
# --------------------------------

@router.get("/{restro_id}")
def get_restaurant(restro_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            restaurant_id,
            name,
            description,
            owner_id
        FROM restaurants
        WHERE restaurant_id = %s;
    """, (restro_id,))

    restaurant = cursor.fetchone()

    cursor.close()
    connection.close()

    if restaurant is None:
        raise HTTPException(
            status_code=404,
            detail="Restaurant not found"
        )

    return {
        "restro_id": restaurant[0],
        "name": restaurant[1],
        "description": restaurant[2],
        "owner_id": restaurant[3]
    }


# --------------------------------
# UPDATE RESTAURANT
# --------------------------------

@router.put("/{restro_id}")
def update_restaurant(
    restro_id: int,
    restaurant: RestaurantCreate
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


# --------------------------------
# DELETE RESTAURANT
# --------------------------------

@router.delete("/{restro_id}")
def delete_restaurant(restro_id: int):

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