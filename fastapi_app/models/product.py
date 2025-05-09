from typing import List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi_app.models.models import Product

def get_all_products(db: Session, skip: int = 0, limit: int = 10) -> Tuple[int, List[Product]]:
    try:
        total = db.query(Product).count()
        products = db.query(Product).order_by(Product.product_id.asc()).offset(skip).limit(limit).all()
        return total, products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")
