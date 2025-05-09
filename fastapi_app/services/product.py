# services.py

from sqlalchemy.orm import Session
from fastapi_app.models.models import Product
from typing import List, Tuple

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
        total = self.db.query(Product).count()
        query = self.db.query(Product).order_by(Product.product_id.asc()).offset(skip).limit(limit)
        return total, query

