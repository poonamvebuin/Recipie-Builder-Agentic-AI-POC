import os
import psycopg
from dotenv import load_dotenv
import streamlit as st

load_dotenv()


db_host = st.secrets["database"]["host"]
db_user = st.secrets["database"]["user"]
db_password = st.secrets["database"]["password"]
db_name = st.secrets["database"]["dbname"]
port = st.secrets["database"]["port"]



def connect_to_postgres():
    try:
        conn = psycopg.connect(
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
