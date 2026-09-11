from fastapi import FastAPI

from restaurant import router as restaurant_router
from meal import router as meal_router
from auth import router as auth_router
from users import router as users_router
from coupon import router as coupon_router
from order import router as order_router
from admin import router as admin_router


app = FastAPI(
    title="Food Delivery API",
    description="REST API for Food Delivery Application",
    version="1.0.0"
)


# =====================================================
# ROUTERS
# =====================================================

app.include_router(restaurant_router)

app.include_router(meal_router)

app.include_router(auth_router)

app.include_router(users_router)

app.include_router(coupon_router)

app.include_router(order_router)

app.include_router(admin_router)


# =====================================================
# ROOT
# =====================================================

@app.get("/")
def root():

    return {
        "message": "Food Delivery API is running"
    }