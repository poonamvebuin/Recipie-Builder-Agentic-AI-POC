import os

import psycopg
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT", 5432))


def connect_to_postgres():
    """Connect to a PostgreSQL database.
    
    This function attempts to establish a connection to a PostgreSQL database using the provided
    database credentials. If the connection is successful, it returns the connection object.
    In case of an error during the connection attempt, it raises an exception with a descriptive
    error message.
    
    Returns:
        psycopg.Connection: A connection object to the PostgreSQL database.
    
    Raises:
        Exception: If there is an error while trying to connect to the database.
    """

    try:
        conn = psycopg.connect(
            dbname=db_name, user=db_user, password=db_password, host=db_host, port=port
        )
        return conn
    except Exception as e:
        raise Exception(f"Database connection error: {e}")


def search_products():
    """Search for products in the database.
    
    This function connects to a PostgreSQL database, executes a query to retrieve distinct product information, 
    and returns the results. The information includes product name, tax, price, stock quantity, category, 
    weight, unit, brand, expiry date, and whether the product is vegan.
    
    Returns:
        list: A list of tuples containing product details.
    
    Raises:
        Exception: If there is an error while fetching products from the database.
    """

    try:
        conn = connect_to_postgres()
        cursor = conn.cursor()
        query = """
            SELECT DISTINCT ON (product_name) product_name, tax, price, weight, unit, brand,is_vegan
            FROM ai.products;
        """
        cursor.execute(query)
        rows = cursor.fetchall()
        conn.close()
        return rows
    except Exception as e:
        raise Exception(f"Product fetch error: {e}")


def save_conversation_to_postgres(
    session_id, chat_history, preferences, cart, product, recipe_choice
):
    """Saves a conversation log to a PostgreSQL database.
    
    This function inserts a new conversation log into the `ai.conversation_logs` table. If a log with the same `session_id` already exists, it updates the existing record with the new values.
    
    Args:
        session_id (str): The unique identifier for the session.
        chat_history (str): The history of the chat in string format.
        preferences (str): User preferences in string format.
        cart (str): The user's cart contents in string format.
        product (Union[str, dict]): The product information, which can be a string or a dictionary. If it's a dictionary, it will be converted to a JSON string.
        recipe_choice (str): The user's choice of recipe.
    
    Raises:
        Exception: If there is an error while saving to PostgreSQL, an error message will be displayed.
    """
    
    try:
        import json

        conn = connect_to_postgres()
        cursor = conn.cursor()

        # Convert product to JSON string if needed
        if not isinstance(product, str):
            product = json.dumps(product)

        insert_query = """
            INSERT INTO ai.conversation_logs (session_id, chat_history, preferences, cart, product, recipe_choice)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (session_id)
            DO UPDATE SET
                chat_history = EXCLUDED.chat_history,
                preferences = EXCLUDED.preferences,
                cart = EXCLUDED.cart,
                product = EXCLUDED.product,
                recipe_choice = EXCLUDED.recipe_choice
        """

        cursor.execute(
            insert_query,
            (session_id, chat_history, preferences, cart, product, recipe_choice),
        )
        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        st.error(f"Error saving to PostgreSQL: {e}")
