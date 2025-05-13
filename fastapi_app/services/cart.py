import logging
import re

from fastapi_app.common.schema import AddToCartRequest, EroorRespone, GetCartRequest
from fastapi_app.models import cart

logger = logging.getLogger(__name__)


def get_cart_data(user_id: str, session_id: str):
    """Retrieve the shopping cart for a specific user.

    This function fetches the cart items associated with a given user ID and session ID.
    It processes the cart items to calculate the total amount and total number of items,
    and returns a structured response containing the cart details.

    Args:
        user_id (str): The unique identifier for the user whose cart is being retrieved.
        session_id (str): The session identifier associated with the user's cart.

    Returns:
        dict: A dictionary containing the user's ID, total number of items, total amount,
              and a list of cart items. Each cart item includes details such as
              cart item ID, product ID, product name, price, quantity, subtotal,
              creation timestamp, and last updated timestamp.

    Raises:
        EroorRespone: If no items are found in the cart, if there is an invalid price format,
                       or if the quantity of any cart item is invalid.
    """

    cart_items = cart.fetch_cart_items(user_id, session_id)

    if not cart_items:
        return EroorRespone(
            success=False,
            status_code=404,
            message=f"No items found in cart for user_id: {user_id} and session_id: {session_id}",
        )

    cart_data = []
    for item in cart_items:
        (
            cart_item_id,
            product_id,
            product_name,
            price_raw,
            quantity,
            created_at,
            updated_at,
        ) = item

        price_clean = re.sub(r"[^\d.]", "", str(price_raw))
        if not price_clean.replace(".", "", 1).isdigit():
            return EroorRespone(
                success=False,
                status_code=500,
                message=f"Invalid price format for product ID {product_id}: {price_raw}",
            )
        price = float(price_clean)

        if not isinstance(quantity, int) or quantity <= 0:
            logger.error(f"Invalid quantity in cart item ID: {cart_item_id}")
            return EroorRespone(
                success=False,
                status_code=400,
                message=f"Invalid quantity for cart item ID {cart_item_id}: {quantity}",
            )

        subtotal = price * quantity

        cart_data.append(
            {
                "cart_item_id": cart_item_id,
                "product_id": product_id,
                "product_name": product_name,
                "price": price,
                "quantity": quantity,
                "subtotal": subtotal,
                "created_at": created_at,
                "updated_at": updated_at,
            }
        )

    total_amount = sum(item["subtotal"] for item in cart_data)
    total_items = sum(item["quantity"] for item in cart_data)

    return {
        "user_id": user_id,
        "total_items": total_items,
        "total_amount": total_amount,
        "cart": cart_data,
    }


def add_item_to_cart(product_id: str, payload: AddToCartRequest):
    """Adds an item to the shopping cart.

    This function checks if the provided quantity is a positive integer. If the item already exists in the cart, it updates the quantity. If the item does not exist, it inserts a new item into the cart.

    Args:
        product_id (str): The ID of the product to be added to the cart.
        payload (AddToCartRequest): An object containing the user ID, session ID, and quantity of the product to be added.

    Returns:
        dict or EroorRespone:
            - If the operation is successful, returns a dictionary containing the cart item ID and the new quantity.
            - If there is an error (e.g., invalid quantity, failure to update or insert), returns an EroorRespone object with the error details.
    """

    if not isinstance(payload.quantity, int) or payload.quantity <= 0:
        return EroorRespone(
            success=False,
            status_code=400,
            message="Quantity must be a positive integer",
        )

    existing_item = cart.get_existing_cart_item(
        product_id, payload.user_id, payload.session_id
    )

    if existing_item:
        cart_item_id, existing_quantity = existing_item
        new_quantity = existing_quantity + payload.quantity

        update_id = cart.update_cart_quantity(cart_item_id, new_quantity)
        if not update_id:
            return EroorRespone(
                success=False,
                status_code=500,
                message="Failed to update existing cart item",
            )

        return {"update_id": update_id}
    else:
        insert_id = cart.insert_cart_item(
            payload.user_id, payload.session_id, product_id, payload.quantity
        )
        if not insert_id:
            return EroorRespone(
                success=False,
                status_code=500,
                message="Failed to insert new item into cart",
            )

        return {"insert_id": insert_id}


def delete_cart_item(cart_item_id: int):
    """Deletes an item from the shopping cart.

    This function retrieves the cart item using the provided cart item ID. If the item is not found, it returns an error response. If the item is found, it deletes the item from the cart and returns the deleted item's ID along with the associated user ID and session ID.

    Args:
        cart_item_id (int): The ID of the cart item to be deleted.

    Returns:
        dict: A dictionary containing the deleted cart item ID, user ID, and session ID if the deletion is successful.

    Raises:
        ErrorResponse: If the cart item is not found, an error response is returned with a success status of False and a message indicating that the data was not found for the given cart item ID.
    """

    cart_data = cart.get_cart_item(cart_item_id)
    if not cart_data:
        return EroorRespone(
            success=False,
            status_code=500,
            message="data not found for  cart id{cart_item_id}",
        )
    cart.delete_cart_item(cart_item_id)
    user_id, session_id = cart_data

    return {
        "deleted_cart_item_id": cart_item_id,
        "user_id": user_id,
        "session_id": session_id,
    }


def get_cart(payload: GetCartRequest):
    """Retrieve the shopping cart data for a user.

    This function fetches the cart data based on the provided user ID and session ID from the payload.
    If no cart data is found, it returns an error response indicating that no cart data is available.

    Args:
        payload (GetCartRequest): An object containing the user ID and session ID.

    Returns:
        dict or ErrorResponse: The cart data if found, otherwise an ErrorResponse indicating failure.
    """

    cart_data = get_cart_data(payload.user_id, payload.session_id)
    if not cart_data:
        return EroorRespone(
            success=False, status_code=404, message="no cart data found"
        )
    return cart_data
