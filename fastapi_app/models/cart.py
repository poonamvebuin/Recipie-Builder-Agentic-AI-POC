import logging

from fastapi_app.models.connect_db import connect_to_postgres

logger = logging.getLogger(__name__)


def fetch_cart_items(user_id: str, session_id: str):
    """Fetches cart items for a specific user and session from the database.

    Args:
        user_id (str): The ID of the user whose cart items are to be fetched.
        session_id (str): The session ID associated with the user's cart.

    Returns:
        list: A list of tuples containing the cart items, where each tuple includes:
            - id (int): The ID of the cart item.
            - product_id (int): The ID of the product.
            - product_name (str): The name of the product.
            - price (float): The price of the product.
            - quantity (int): The quantity of the product in the cart.
            - created_at (datetime): The timestamp when the cart item was created.
            - updated_at (datetime): The timestamp when the cart item was last updated.

    Raises:
        Exception: If there is an error while fetching the cart items from the database.
    """

    try:
        conn = connect_to_postgres()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT 
                c.id,
                c.product_id,
                p.product_name,
                p.price,
                c.quantity,
                c.created_at,
                c.updated_at
            FROM ai.cart_items c
            JOIN ai.products p ON c.product_id = p.product_id
            WHERE c.user_id = %s AND c.session_id = %s
            """,
            (user_id, session_id),
        )
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return rows
    except Exception as error:
        logger.error(f"Error in fetch_cart_items: {error}")
        raise


def get_existing_cart_item(product_id: int, user_id: str, session_id: int):
    """Retrieve an existing cart item from the database.

    This function queries the database for a cart item associated with the specified
    product ID, user ID, and session ID. If found, it returns the item's ID and quantity.

    Args:
        product_id (int): The ID of the product to look for in the cart.
        user_id (int): The ID of the user whose cart is being queried.
        session_id (str): The session ID associated with the user's cart.

    Returns:
        tuple: A tuple containing the ID and quantity of the cart item if it exists,
               or None if the item is not found.

    Raises:
        Exception: If there is an error during the database operation, an exception
                   is raised and logged.
    """

    try:
        conn = connect_to_postgres()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, quantity FROM ai.cart_items
            WHERE product_id = %s AND user_id = %s AND session_id = %s
            """,
            (product_id, user_id, session_id),
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception as error:
        logger.error(f"Error in get_existing_cart_item: {error}")
        raise


def insert_cart_item(user_id: str, session_id: str, product_id: int, quantity: int):
    """Inserts an item into the user's cart in the database.

    Args:
        user_id (int): The ID of the user.
        session_id (str): The session ID associated with the user's cart.
        product_id (int): The ID of the product to be added to the cart.
        quantity (int): The quantity of the product to be added.

    Returns:
        int or None: The ID of the newly inserted cart item if successful, otherwise None.

    Raises:
        Exception: If there is an error during the database operation.
    """

    try:
        conn = connect_to_postgres()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ai.cart_items (user_id, session_id, product_id, quantity)
            VALUES (%s, %s, %s, %s)
            RETURNING id
            """,
            (user_id, session_id, product_id, quantity),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return row[0] if row else None
    except Exception as error:
        logger.error(f"Error in insert_cart_item: {error}")
        raise


def update_cart_quantity(cart_id: int, quantity: int):
    """Update the quantity of a specific item in the shopping cart.

    This function connects to a PostgreSQL database and updates the quantity of an item in the `ai.cart_items` table based on the provided cart ID. It also updates the timestamp of the last modification. If the update is successful, it returns the ID of the updated cart item.

    Args:
        cart_id (int): The ID of the cart item to be updated.
        quantity (int): The new quantity to set for the cart item.

    Returns:
        int or None: The ID of the updated cart item if the update was successful, otherwise None.

    Raises:
        Exception: If there is an error during the database operation, an exception is raised and logged.
    """

    try:
        conn = connect_to_postgres()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE ai.cart_items
            SET quantity = %s, updated_at = CURRENT_TIMESTAMP
            WHERE id = %s
            RETURNING id
            """,
            (quantity, cart_id),
        )
        row = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        return row[0] if row else None
    except Exception as error:
        logger.error(f"Error in update_cart_quantity: {error}")
        raise


def get_cart_item(cart_id: int):
    """Retrieve a cart item from the database based on the provided cart ID.

    Args:
        cart_id (int): The ID of the cart item to retrieve.

    Returns:
        tuple: A tuple containing the user ID and session ID associated with the cart item,
               or None if the cart item does not exist.

    Raises:
        Exception: If there is an error connecting to the database or executing the query.
    """

    try:
        conn = connect_to_postgres()
        cur = conn.cursor()
        cur.execute(
            "SELECT user_id, session_id FROM ai.cart_items WHERE id = %s", (cart_id,)
        )
        row = cur.fetchone()
        cur.close()
        conn.close()
        return row
    except Exception as error:
        logger.error(f"Error in get_cart_item_owner: {error}")
        raise


def delete_cart_item(cart_id: int):
    """Deletes an item from the shopping cart in the database.

    This function connects to a PostgreSQL database and removes a cart item
    identified by the given cart ID. If an error occurs during the operation,
    it logs the error and raises an exception.

    Args:
        cart_id (int): The ID of the cart item to be deleted.

    Raises:
        Exception: If there is an error during the database operation.
    """

    try:
        conn = connect_to_postgres()
        cur = conn.cursor()
        cur.execute("DELETE FROM ai.cart_items WHERE id = %s", (cart_id,))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as error:
        logger.error(f"Error in delete_cart_item: {error}")
        raise
