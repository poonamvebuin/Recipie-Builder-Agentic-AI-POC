import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = os.getenv("PORT")

def connect_to_postgres():
    try:
        conn = psycopg2.connect(
            dbname=db_name,
            user=db_user,
            password=db_password,
            host=db_host,
            port=port
        )
        return conn
    except Exception as e:
        raise Exception(f"Database connection error: {e}")

def search_products():
    try:
        conn = connect_to_postgres()
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT ON (product_name) product_name, tax, price, stock_quantity, category,
                   weight, unit, brand, expiry_date, is_vegan
            FROM ai.products;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        raise Exception(f"Product fetch error: {e}")
