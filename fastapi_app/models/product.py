
from typing import List, Tuple
from sqlalchemy.orm import Session
from fastapi import HTTPException
from fastapi_app.models.models import Product
from fastapi_app.models.connect_db import connect_to_postgres

def get_all_products(db: Session, page_no: int = 1, limit: int = 20) -> Tuple[int, List[Product]]:
    try:
        offset = (page_no - 1) * limit
        total = db.query(Product).count()
        products = db.query(Product).order_by(Product.product_id.asc()).offset(offset).limit(limit).all()
        return total, products
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{e}")



def fetch_products():
    """Fetches distinct product information from the database.
    
    This method connects to a PostgreSQL database, executes a query to retrieve
    distinct product details including product ID, name, tax, price, weight,
    unit, brand, and vegan status, and returns the results.
    
    Returns:
        list: A list of tuples, where each tuple contains the product ID,
        product name, tax, price, weight, unit, brand, and vegan status.
    
    Raises:
        Exception: If there is an error during the database connection or query execution.
    """

    try:
        conn = connect_to_postgres()
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT ON (product_name) product_id, product_name, tax, price, weight, unit, brand, is_vegan
            FROM ai.products;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        raise Exception(f"Product fetch error: {e}")

