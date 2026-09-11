from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal

from database import get_connection


router = APIRouter(
    prefix="/api/coupons",
    tags=["Coupons"]
)


class CouponRequest(BaseModel):
    code: str
    discount_percentage: Decimal


# =====================================================
# CREATE COUPON
# =====================================================

@router.post("/")
def create_coupon(coupon: CouponRequest):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT coupon_id
        FROM coupons
        WHERE code = %s;
    """, (coupon.code,))

    if cursor.fetchone():

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=400,
            detail="Coupon code already exists"
        )

    cursor.execute("""
        INSERT INTO coupons
            (code, discount_percentage)
        VALUES
            (%s, %s)
        RETURNING coupon_id;
    """, (
        coupon.code,
        coupon.discount_percentage
    ))

    coupon_id = cursor.fetchone()[0]

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "coupon_id": coupon_id,
        "code": coupon.code,
        "discount_percentage": coupon.discount_percentage
    }


# =====================================================
# GET ALL COUPONS
# =====================================================

@router.get("/")
def get_coupons():

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            coupon_id,
            code,
            discount_percentage
        FROM coupons
        ORDER BY coupon_id;
    """)

    coupons = cursor.fetchall()

    cursor.close()
    connection.close()

    return [
        {
            "coupon_id": coupon[0],
            "code": coupon[1],
            "discount_percentage": coupon[2]
        }
        for coupon in coupons
    ]


# =====================================================
# GET COUPON
# =====================================================

@router.get("/{coupon_id}")
def get_coupon(coupon_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            coupon_id,
            code,
            discount_percentage
        FROM coupons
        WHERE coupon_id = %s;
    """, (coupon_id,))

    coupon = cursor.fetchone()

    cursor.close()
    connection.close()

    if coupon is None:

        raise HTTPException(
            status_code=404,
            detail="Coupon not found"
        )

    return {
        "coupon_id": coupon[0],
        "code": coupon[1],
        "discount_percentage": coupon[2]
    }


# =====================================================
# UPDATE COUPON
# =====================================================

@router.put("/{coupon_id}")
def update_coupon(
    coupon_id: int,
    coupon: CouponRequest
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE coupons
        SET
            code = %s,
            discount_percentage = %s
        WHERE coupon_id = %s;
    """, (
        coupon.code,
        coupon.discount_percentage,
        coupon_id
    ))

    if cursor.rowcount == 0:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Coupon not found"
        )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "coupon_id": coupon_id,
        "code": coupon.code,
        "discount_percentage": coupon.discount_percentage
    }


# =====================================================
# DELETE COUPON
# =====================================================

@router.delete("/{coupon_id}")
def delete_coupon(coupon_id: int):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM coupons
        WHERE coupon_id = %s;
    """, (coupon_id,))

    if cursor.rowcount == 0:

        cursor.close()
        connection.close()

        raise HTTPException(
            status_code=404,
            detail="Coupon not found"
        )

    connection.commit()

    cursor.close()
    connection.close()

    return {
        "message": "Coupon deleted successfully"
    }