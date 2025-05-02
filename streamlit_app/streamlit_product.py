import json

import streamlit as st

from Agent.cart import (add_item_to_cart, display_cart_summary,
                        remove_item_from_cart)
from Agent.product import get_available_ingredients


def product_cart(product_input, language):
    """Product Cart Function.
    
    This function retrieves available products based on the user's input and language preference, updates the session state with the available ingredients, and allows the user to add products to their cart. It also provides feedback on the cart's contents and any actions taken.
    
    Args:
        product_input (str): The input string representing the products to search for.
        language (str): The language in which the product information should be retrieved.
    
    Returns:
        None: This function does not return a value but updates the session state and displays information to the user.
    
    Raises:
        None: This function does not raise any exceptions.
    
    Usage:
        Call this function within a Streamlit application to enable product searching and cart management.
    """
    
    products = get_available_ingredients(product_input, language)
    # print('---------products', products)
    st.session_state.available_ingredients = products
    st.session_state.search_done = True

    # Show matching products if search was done
    if st.session_state.search_done and not st.session_state.available_ingredients:
        st.warning("⚠️ No matching product found.")
    elif st.session_state.search_done:
        st.subheader("Matching Products:")
        product_list = st.session_state.available_ingredients

        for i, product in enumerate(product_list):
            st.subheader(f"{product['Product_name']}")
            st.write(f"Price with Tax: {product['Tax']}")
            st.write(f"Price: {product['Price']}")
            st.write(f"Weight: {product['Weight']}")

            quantity = st.number_input(
                f"Quantity for {product['Product_name']}",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"qty_{i}",
            )

            if st.button(f"Add to Cart", key=f"add_{i}"):
                add_item_to_cart(product, quantity)
                st.session_state.last_added = product["Product_name"]

    if st.session_state.last_added:
        st.success(f"✅ {st.session_state.last_added} added to cart!")
        st.session_state.last_added = None

    if st.session_state.cart_items:
        st.title("🧺 Your Cart:")
        for item_line in display_cart_summary():
            st.write(item_line)


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
        "Enter comma seperated list of products or ingredients:"
    )
    if st.button("Find Products"):
        # Simulate product search
        products = get_available_ingredients(product_input.split(","), language)
        st.session_state.available_ingredients = products
        st.session_state.search_done = True

    # Show matching products if search was done
    if st.session_state.search_done and not st.session_state.available_ingredients:
        st.warning("⚠️ No matching product found.")
    elif st.session_state.search_done:
        st.subheader("Matching Products:")
        product_list = st.session_state.available_ingredients

        for i, product in enumerate(product_list):
            st.subheader(f"{product['Product_name']}")
            st.write(f"Price with Tax: {product['Tax']}")
            st.write(f"Price: {product['Price']}")
            st.write(f"Weight: {product['Weight']}")

            quantity = st.number_input(
                f"Quantity for {product['Product_name']}",
                min_value=1,
                max_value=10,
                value=1,
                step=1,
                key=f"qty_{i}",
            )

            if st.button(f"Add to Cart", key=f"add_{i}"):
                # st.write('🛒 Button clicked for:', product["Product_name"])
                add_item_to_cart(product, quantity)
                st.session_state.last_added = product["Product_name"]
                # st.experimental_rerun()  # Force refresh to show cart update immediately

    if st.session_state.last_added:
        st.success(f"✅ {st.session_state.last_added} added to cart!")
        st.session_state.last_added = None

    if st.session_state.cart_items:
        st.title("🧺 Your Cart:")
        for item_line in display_cart_summary():
            st.write(item_line)

    for item in st.session_state.cart_items:
        if st.button(f'Remove one {item["Product_name"]} from cart'):
            remove_item_from_cart(item["Product_name"])
            break
