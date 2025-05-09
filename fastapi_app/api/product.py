from fastapi import APIRouter, FastAPI, Depends, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi_app.common.constants import PRODUCTS
from fastapi_app.models.connect_db import SessionLocal
from fastapi_app.models.models import Product
from fastapi_app.common.schema import PaginatedResponse, ProductResponse, Product
from fastapi_app.services.product import ProductService

router = APIRouter()
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
@router.get(PRODUCTS, response_model=ProductResponse)
def fetch_products(
    skip: int,
    limit: int,
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    total, products = product_service.get_paginated_products(skip, limit)
    
    product_items = [Product.from_orm(p) for p in products]
    paginated= PaginatedResponse(total=total, items=product_items)
    return ProductResponse(
        success=True,
        status_code=200,
        message="Fetched products successfully",
        data=paginated
    )