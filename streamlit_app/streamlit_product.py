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
    st.markdown("### 🔎 Most Popular Searches")

    def run_search(ingredients_text):
        ingredients = [i.strip() for i in ingredients_text.split(",")]
        print(ingredients)
        products = get_available_ingredients(ingredients, language)
        st.session_state.available_ingredients = products
        st.session_state.search_done = True

    cols = st.columns(3)
    with cols[0]:
        if st.button("💧 Water & Milk" if language == "English" else "水 , 牛乳"):
            input_prompt = ("Water , Milk" if language == "English" else "水 , 牛乳")
            run_search(input_prompt)
    with cols[1]:
        if st.button("🍬 Sugar & Tomato" if language == "English" else "砂糖 , トマト"):
            input_prompt = ("Sugar , Tomato" if language == "English" else "砂糖 , トマト")
            run_search(input_prompt)
    with cols[2]:
        if st.button("🧂 Soy Sauce & Mayo" if language == "English" else "醤油 , マヨネーズ"):
            input_prompt = ("Soy Sauce , Mayo" if language == "English" else "醤油 , マヨネーズ")
            run_search(input_prompt)

    product_input = st.text_input("Enter comma separated list of products or ingredients:")
    
    if st.button("Find Products"):
        run_search(product_input)

    if st.session_state.get("search_done") and st.session_state.get("available_ingredients"):
        render_matching_products(st.session_state.available_ingredients)
    elif st.session_state.get("search_done"):
        st.warning("No matching product found.")
    if st.session_state.get("cart_items"):
        render_cart()
