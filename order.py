from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal

from database import get_connection
from dependencies import get_current_user


router = APIRouter(
    prefix="/api/orders",
    tags=["Orders"]
)


# =====================================================
# MODELS
# =====================================================

class OrderItemRequest(BaseModel):
    meal_id: int
    quantity: int


class OrderCreate(BaseModel):
    restaurant_id: int
    items: List[OrderItemRequest]
    tip: Decimal = Decimal("0")
    coupon_id: Optional[int] = None


class OrderStatusRequest(BaseModel):
    status: str


# =====================================================
# CREATE ORDER
# =====================================================

@router.post("/")
def create_order(
    order: OrderCreate,
    current_user: dict = Depends(get_current_user)
):

    connection = get_connection()
    cursor = connection.cursor()

    try:

        # ---------------------------------------------
        # CHECK RESTAURANT
        # ---------------------------------------------

        cursor.execute("""
            SELECT restaurant_id
            FROM restaurants
            WHERE restaurant_id = %s;
        """, (order.restaurant_id,))

        restaurant = cursor.fetchone()

        if restaurant is None:

            raise HTTPException(
                status_code=404,
                detail="Restaurant not found"
            )

        # ---------------------------------------------
        # CALCULATE SUBTOTAL
        # ---------------------------------------------

        subtotal = Decimal("0")
        order_items = []

        for item in order.items:

            if item.quantity <= 0:

                raise HTTPException(
                    status_code=400,
                    detail="Quantity must be greater than 0"
                )

            cursor.execute("""
                SELECT
                    meal_id,
                    name,
                    price,
                    restaurant_id,
                    is_available
                FROM meals
                WHERE meal_id = %s;
            """, (item.meal_id,))

            meal = cursor.fetchone()

            if meal is None:

                raise HTTPException(
                    status_code=404,
                    detail=f"Meal {item.meal_id} not found"
                )

            if meal[3] != order.restaurant_id:

                raise HTTPException(
                    status_code=400,
                    detail="Meal does not belong to selected restaurant"
                )

            if not meal[4]:

                raise HTTPException(
                    status_code=400,
                    detail=f"Meal {meal[1]} is not available"
                )

            price = Decimal(str(meal[2]))

            subtotal += price * item.quantity

            order_items.append({
                "meal_id": meal[0],
                "meal_name": meal[1],
                "quantity": item.quantity,
                "price": price
            })

        # ---------------------------------------------
        # COUPON
        # ---------------------------------------------

        discount = Decimal("0")

        if order.coupon_id is not None:

            cursor.execute("""
                SELECT
                    coupon_id,
                    discount_percentage,
                    is_active,
                    expiry_date
                FROM coupons
                WHERE coupon_id = %s;
            """, (order.coupon_id,))

            coupon = cursor.fetchone()

            if coupon is None:

                raise HTTPException(
                    status_code=404,
                    detail="Coupon not found"
                )

            if not coupon[2]:

                raise HTTPException(
                    status_code=400,
                    detail="Coupon is inactive"
                )

            if coupon[3] is not None:

                from datetime import datetime

                if coupon[3] < datetime.now():

                    raise HTTPException(
                        status_code=400,
                        detail="Coupon has expired"
                    )

            discount = (
                subtotal
                * Decimal(str(coupon[1]))
                / Decimal("100")
            )

        # ---------------------------------------------
        # TOTAL
        # ---------------------------------------------

        tip = order.tip

        if tip < 0:

            raise HTTPException(
                status_code=400,
                detail="Tip cannot be negative"
            )

        total_amount = (
            subtotal
            - discount
            + tip
        )

        # ---------------------------------------------
        # CREATE ORDER
        # ---------------------------------------------

        cursor.execute("""
            INSERT INTO orders
                (
                    customer_id,
                    restaurant_id,
                    coupon_id,
                    subtotal,
                    discount,
                    tip,
                    total_amount,
                    status
                )
            VALUES
                (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
            RETURNING order_id, created_at;
        """, (
            current_user["user_id"],
            order.restaurant_id,
            order.coupon_id,
            subtotal,
            discount,
            tip,
            total_amount,
            "PLACED"
        ))

        created_order = cursor.fetchone()

        order_id = created_order[0]
        created_at = created_order[1]

        # ---------------------------------------------
        # CREATE ORDER ITEMS
        # ---------------------------------------------

        for item in order_items:

            cursor.execute("""
                INSERT INTO order_items
                    (
                        order_id,
                        meal_id,
                        quantity,
                        price_at_purchase
                    )
                VALUES
                    (%s, %s, %s, %s);
            """, (
                order_id,
                item["meal_id"],
                item["quantity"],
                item["price"]
            ))

        # ---------------------------------------------
        # STATUS HISTORY
        # ---------------------------------------------

        cursor.execute("""
            INSERT INTO order_status_history
                (
                    order_id,
                    old_status,
                    new_status,
                    changed_by
                )
            VALUES
                (%s, %s, %s, %s);
        """, (
            order_id,
            None,
            "PLACED",
            current_user["user_id"]
        ))

        connection.commit()

        return {
            "order_id": order_id,
            "restaurant_id": order.restaurant_id,
            "items": [
                {
                    "meal_id": item["meal_id"],
                    "quantity": item["quantity"],
                    "price": item["price"]
                }
                for item in order_items
            ],
            "subtotal": subtotal,
            "discount": discount,
            "tip": tip,
            "total_amount": total_amount,
            "status": "PLACED",
            "created_at": created_at
        }

    except HTTPException:

        connection.rollback()
        raise

    except Exception as error:

        connection.rollback()

        raise HTTPException(
            status_code=500,
            detail=str(error)
        )

    finally:

        cursor.close()
        connection.close()


# =====================================================
# GET MY ORDERS
# =====================================================

@router.get("/")
def get_orders(
    current_user: dict = Depends(get_current_user)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            order_id,
            restaurant_id,
            total_amount,
            status,
            created_at
        FROM orders
        WHERE customer_id = %s
        ORDER BY created_at DESC;
    """, (
        current_user["user_id"],
    ))

    orders = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "order_id": order[0],
            "restaurant_id": order[1],
            "total_amount": order[2],
            "status": order[3],
            "created_at": order[4]
        }
        for order in orders
    ]


# =====================================================
# GET ORDER BY ID
# =====================================================

@router.get("/{order_id}")
def get_order(
    order_id: int,
    current_user: dict = Depends(get_current_user)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            order_id,
            customer_id,
            restaurant_id,
            subtotal,
            discount,
            tip,
            total_amount,
            status,
            created_at
        FROM orders
        WHERE order_id = %s;
    """, (order_id,))

    order = cursor.fetchone()

    if order is None:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    # User can only see their own order
    if (
        order[1] != current_user["user_id"]
        and current_user["role"].upper() != "ADMIN"
    ):

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to view this order"
        )

    cursor.execute("""
        SELECT
            oi.meal_id,
            m.name,
            oi.quantity,
            oi.price_at_purchase
        FROM order_items oi
        JOIN meals m
            ON m.meal_id = oi.meal_id
        WHERE oi.order_id = %s
        ORDER BY oi.order_item_id;
    """, (order_id,))

    items = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "order_id": order[0],
        "restaurant_id": order[2],
        "items": [
            {
                "meal_id": item[0],
                "meal_name": item[1],
                "quantity": item[2],
                "price": item[3]
            }
            for item in items
        ],
        "subtotal": order[3],
        "discount": order[4],
        "tip": order[5],
        "total_amount": order[6],
        "status": order[7],
        "created_at": order[8]
    }


# =====================================================
# UPDATE ORDER STATUS
# =====================================================

@router.patch("/{order_id}/status")
def update_order_status(
    order_id: int,
    status_request: OrderStatusRequest,
    current_user: dict = Depends(get_current_user)
):

    allowed_statuses = {
        "PLACED",
        "PROCESSING",
        "IN_ROUTE",
        "DELIVERED",
        "RECEIVED",
        "CANCELLED"
    }

    new_status = status_request.status.upper()

    if new_status not in allowed_statuses:

        raise HTTPException(
            status_code=400,
            detail="Invalid order status"
        )

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            order_id,
            customer_id,
            status
        FROM orders
        WHERE order_id = %s;
    """, (order_id,))

    order = cursor.fetchone()

    if order is None:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if (
        order[1] != current_user["user_id"]
        and current_user["role"].upper() != "ADMIN"
    ):

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="You do not have permission to update this order"
        )

    old_status = order[2]

    cursor.execute("""
        UPDATE orders
        SET status = %s
        WHERE order_id = %s;
    """, (
        new_status,
        order_id
    ))

    cursor.execute("""
        INSERT INTO order_status_history
            (
                order_id,
                old_status,
                new_status,
                changed_by
            )
        VALUES
            (%s, %s, %s, %s);
    """, (
        order_id,
        old_status,
        new_status,
        current_user["user_id"]
    ))

    connection.commit()

    cursor.execute("""
        SELECT status
        FROM orders
        WHERE order_id = %s;
    """, (order_id,))

    updated_status = cursor.fetchone()[0]

    cursor.close()
    connection.close()

    return {
        "order_id": order_id,
        "status": updated_status,
        "updated_at": "updated"
    }


# =====================================================
# ORDER HISTORY
# =====================================================

@router.get("/{order_id}/history")
def get_order_history(
    order_id: int,
    current_user: dict = Depends(get_current_user)
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            order_id,
            customer_id
        FROM orders
        WHERE order_id = %s;
    """, (order_id,))

    order = cursor.fetchone()

    if order is None:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Order not found"
        )

    if (
        order[1] != current_user["user_id"]
        and current_user["role"].upper() != "ADMIN"
    ):

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=403,
            detail="You do not have permission"
        )

    cursor.execute("""
        SELECT
            new_status,
            changed_at
        FROM order_status_history
        WHERE order_id = %s
        ORDER BY changed_at;
    """, (order_id,))

    history = cursor.fetchall()

    cursor.close()
    connection.close()

    return {
        "order_id": order_id,
        "history": [
            {
                "status": item[0],
                "changed_at": item[1]
            }
            for item in history
        ]
    }