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


def save_conversation_to_postgres(session_id, chat_history, preferences, cart, product, recipe_choice):
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

        cursor.execute(insert_query, (session_id, chat_history, preferences, cart, product, recipe_choice))
        conn.commit()
        cursor.close()
        conn.close()

        # st.success("✅ Conversation saved or updated in PostgreSQL successfully!")

    except Exception as e:
        st.error(f"❌ Error saving to PostgreSQL: {e}")
