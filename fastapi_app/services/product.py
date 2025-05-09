# services.py

from sqlalchemy.orm import Session
from fastapi_app.models.models import Product
from typing import List, Tuple

from fastapi_app.models.product import get_all_products
class ProductService:
    def __init__(self, db: Session):
        self.db = db

    def get_paginated_products(self, skip: int, limit: int) -> Tuple[int, List[Product]]:
        """
        Fetch paginated products from the database.

        Returns:
            total: total count of products
            products: list of products (subset based on pagination)
        """
        return get_all_products(self.db, skip=skip, limit=limit)

