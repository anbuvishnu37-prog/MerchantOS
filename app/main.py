from fastapi import FastAPI, HTTPException
from app.products import products
from app.agent import router as agent_router
from app.cart import router as cart_router
from app.database import engine, Base
from app import models
from app.orders import router as orders_router
from app import audit
from app.audit import router as audit_router
from app.payment.routes import router as payment_router
from fastapi.middleware.cors import CORSMiddleware
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MerchantOS API",
    description="AI-native Merchant Commerce Gateway",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(agent_router)
app.include_router(cart_router)
app.include_router(orders_router)
app.include_router(audit_router)
app.include_router(payment_router)

@app.get("/")
def root():
    return {
        "message": "MerchantOS API is running",
        "status": "healthy"
    }


@app.get("/products")
def get_products():
    return products


@app.get("/products/{product_id}")
def get_product(product_id: int):

    for product in products:
        if product["id"] == product_id:
            return product

    raise HTTPException(
        status_code=404,
        detail="Product not found"
    )