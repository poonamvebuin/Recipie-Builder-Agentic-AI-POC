import streamlit as st

from Agent.product import get_available_ingredients

import streamlit as st
from Agent.product import get_available_ingredients
from streamlit_app.ui_helpers import render_cart, render_matching_products


def get_product_suggestions(language):
    """Get product suggestions based on user input.

    This function allows users to enter a list of products or ingredients and find matching products. It displays the available products along with their details, allows users to add items to their cart, and provides a summary of the cart contents.

    Args:
        language (str): The language in which to display product information.

    Returns:
        None: This function does not return a value but updates the Streamlit session state and UI.

    Raises:
        None: This function does not raise any exceptions.

    Usage:
        Call this function within a Streamlit application to enable product searching and cart management.
    """

    st.title("🛒 Product Finder")
    product_input = st.text_input(
        "Enter comma separated list of products or ingredients:"
    )

    if st.button("Find Products"):
        ingredients = product_input.split(",")
        products = get_available_ingredients(ingredients, language)
        st.session_state.available_ingredients = products
        st.session_state.search_done = True
        print('---------st.session_state.available_ingredients', st.session_state.available_ingredients)

    if st.session_state.search_done and st.session_state.available_ingredients:
        render_matching_products(st.session_state.available_ingredients)
    else:
        st.warning("No matching product found.")
    if st.session_state.cart_items:
        render_cart()