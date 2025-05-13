import logging

from fastapi import APIRouter, Body, Path

from fastapi_app.common.constants import (
    ADD_TO_CART,
    CART_SUMMARY,
    REMOVE_FROM_CART,
)
from fastapi_app.common.schema import (
    AddToCartRequest,
    AddToCartResponse,
    CartSummaryResponse,
    EroorRespone,
    GetCartRequest,
    RemoveToCartResponse,
)
from fastapi_app.services.cart import (
    add_item_to_cart,
    delete_cart_item,
    get_cart,
)

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post(ADD_TO_CART, response_model=AddToCartResponse)
def add_product_to_cart(product_id: int, payload: AddToCartRequest = Body(...)):
    """Adds a product to the shopping cart.

    This function attempts to add a specified product to the user's cart using the provided product ID and payload. If the addition is successful, it retrieves the updated cart data and returns a response indicating success. In case of an error during the process, it logs the error and raises an exception.

    Args:
        product_id (int): The ID of the product to be added to the cart.
        payload (AddToCartRequest, optional): The request payload containing details for adding the product to the cart. Defaults to Body(...).

    Returns:
        AddToCartResponse: A response object containing the success status, status code, message, and updated cart data.

    Raises:
        Exception: If there is an error during the process of adding the product to the cart.
    """

    try:
        response = add_item_to_cart(product_id, payload)

        if isinstance(response, EroorRespone):
            return response

        # Handle insert/update success
        cart_data = get_cart(payload)
        if "update_id" in response:
            return AddToCartResponse(
            success=True,
            status_code=200,
            message="Product updated to cart",
            cart=cart_data,
        )

        return AddToCartResponse(
            success=True,
            status_code=200,
            message="Product added to cart",
            cart=cart_data,
        )

    except Exception as e:
        logger.error(f"Failed to add product to cart: {e}")
        raise


@router.delete(REMOVE_FROM_CART, response_model=RemoveToCartResponse)
def delete_cart_item_api(cart_id: int = Path(..., description="Cart item ID")):
    """Deletes an item from the shopping cart.

    This function attempts to remove a specified item from the cart using the provided cart ID.
    If the operation is successful, it returns a response indicating the success of the removal.
    In case of an error, it logs the error and raises an exception.

    Args:
        cart_id (int): The ID of the cart item to be deleted. This is a required parameter.

    Returns:
        RemoveToCartResponse: A response object indicating the success of the operation,
        including a success flag, status code, message, and the cart ID.

    Raises:
        Exception: If an error occurs during the deletion process, an exception is raised
        after logging the error.
    """

    try:
        response = delete_cart_item(cart_id)
        if isinstance(response, EroorRespone):
            return response
        return RemoveToCartResponse(
            success=True,
            status_code=200,
            message="Product removed from cart",
            cart_id=cart_id,
        )

    except Exception as e:
        logger.error(f"Failed to add product to cart: {e}")
        raise


@router.get(CART_SUMMARY, response_model=CartSummaryResponse)
def get_cart_details(payload: GetCartRequest):
    """Retrieves the details of a shopping cart based on the provided request payload.

    Args:
        payload (GetCartRequest): The request object containing the necessary information to fetch the cart details.

    Returns:
        CartSummaryResponse or EroorRespone: Returns a CartSummaryResponse object if the cart details are successfully retrieved.
        If an error occurs during the retrieval process, an EroorRespone object is returned.

    Raises:
        Exception: Logs an error message and raises the exception if an unexpected error occurs during the process.
    """

    try:
        response = get_cart(payload)
        if isinstance(response, EroorRespone):
            return response
        return CartSummaryResponse(**response)

    except Exception as e:
        logger.error(f"Failed to add product to cart: {e}")
        raise
