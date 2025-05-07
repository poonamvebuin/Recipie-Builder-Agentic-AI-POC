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
        if st.button("Cucumber,nori,gohan ,salt , soy sauce , shiso leaves" if language == "English" else "きゅうり, 海苔, ごはん, 塩, しょうゆ, 大葉"):
            input_prompt = ("Cucumber , nori , gohan , salt , soy sauce , shiso leaves" if language == "English" else "きゅうり, 海苔, ごはん, 塩, しょうゆ, 大葉")
            run_search(input_prompt)

    with cols[1]:
        if st.button("Lemon juice, Water ,Matcha ,Walnuts , Potatoes , Broccoli" if language == "English" else "レモン汁, 水, 抹茶, くるみ[ロースト], じゃがいも ,ブロッコリー"):
            input_prompt = ("Lemon juice, Water ,Matcha ,Walnuts , Potatoes , Broccoli" if language == "English" else "レモン汁, 水, 抹茶, くるみ[ロースト], じゃがいも ,ブロッコリー")
            run_search(input_prompt)
            
    with cols[2]:
        if st.button("Green onion , Vermicelli , Chicken meat , Sesame oil , Silk tofu" if language == "English" else "青ネギ , 春雨 ,  鶏ささみ ,  ごま油 ,  絹豆腐"):
            input_prompt = ("Green onion , Vermicelli , Chicken meat , Sesame oil , Silk tofu" if language == "English" else "青ネギ , 春雨 ,  鶏ささみ ,  ごま油 ,  絹豆腐")
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
