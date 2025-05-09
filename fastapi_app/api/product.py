from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi_app.models.connect_db import SessionLocal
from fastapi_app.models.models import Product
from fastapi_app.common.schema import PaginatedResponse, ProductListResponse, Product
from fastapi_app.services.product import ProductService



from fastapi_app.common.schema import ProductResponse
from fastapi_app.services.product import ProductFinderAgent
from fastapi_app.common.constants import FIND_PRODUCT,PRODUCTS_LIST
from fastapi import APIRouter, Depends, HTTPException, Query
router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get(PRODUCTS_LIST, response_model=ProductListResponse)
def fetch_products(
    skip: int,
    limit: int,
    db: Session = Depends(get_db)
):
    product_service = ProductService(db)
    total, products = product_service.get_paginated_products(skip, limit)
    
    product_items = [Product.from_orm(p) for p in products]
    paginated= PaginatedResponse(total=total, items=product_items)
    return ProductListResponse(
        success=True,
        status_code=200,
        message="Fetched products successfully",
        data=paginated
    )


@router.get(FIND_PRODUCT, response_model=ProductResponse)
def find_products(
    language: str = Query("English"),
    session_id: Optional[str] = Query(""),
    ingredients: List[str] = Query(...), 
    db: Session = Depends(get_db)
):
    """Finds products based on the provided ingredients and language.
    
    Args:
        language (str, optional): The language in which to fetch product information. Defaults to "English".
        session_id (Optional[str], optional): An optional session identifier. Defaults to an empty string.
        ingredients (List[str], required): A list of ingredients to search for products.
        db (Session, optional): Database session dependency. Defaults to the result of `get_db()`.
    
    Returns:
        ProductResponse: A response object containing the success status, status code, message, and matched products.
    
    Raises:
        HTTPException: If an error occurs during the product fetching process, a 500 error is raised with the error detail.
    """
    try:
        product_agent = ProductFinderAgent()
        matched_products = product_agent.get_available_ingredients(ingredients, language)

        return ProductResponse(
            success=True,
            status_code=200,
            message="products fetched successfully",
            data={"products": matched_products}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

