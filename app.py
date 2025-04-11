import streamlit as st
from Recipe import get_agent
from Cart import add_item_to_cart, display_cart_summary
from Product import get_available_ingredients
from agno.agent import RunResponse
from typing import Iterator

st.set_page_config(page_title="Recipe Builder", layout="centered")
st.title("🍳 Recipe Creation Assistant 🍳")

st.sidebar.header("🌐 Language Preferences")
language_options = ["English", "Hindi", "Spanish", "French", "German", "Italian", "Japanese", "Chinese", "Arabic"]
language = st.sidebar.selectbox("Choose your preferred language:", language_options, index=0)

if "cart_items" not in st.session_state:
    st.session_state.cart_items = []
if "available_ingredients" not in st.session_state:
    st.session_state.available_ingredients = []
if "last_added" not in st.session_state:
    st.session_state.last_added = None

agent = get_agent()
recipe_generated = False

prompt = st.text_input("Ask me anything about recipe")

if prompt:
    with st.spinner("Processing your request... ⏳"):
        localized_prompt = f"{prompt}\n\nPlease respond in {language}."
        run_response: Iterator[RunResponse] = agent.run(localized_prompt, stream=True)
        recipe = run_response.content

        st.title("🍽️ Deliciously Recipe 🍽️")
        info = {
            "Recipe Title": recipe.recipe_title,
            "Cuisine Type": recipe.cuisine_type,
            "Preparation Time": recipe.prep_time,
            "Cooking Time": recipe.cook_time,
            "Total Time": recipe.total_time,
            "Serving Size": recipe.serving_size,
            "Difficulty Level": recipe.difficulty_level,
            "Ingredients": recipe.ingredients,
        }
        for key, value in info.items():
            st.subheader(f"**{key}:**")
            st.write(value)

        st.subheader("Instructions")
        for step in recipe.instructions:
            st.write(f"- {step}")

        if recipe.extra_features:
            st.subheader("Extra Features")
            for key, value in recipe.extra_features.items():
                st.write(f"**{key.replace('_', ' ').title()}**: {value or 'N/A'}")

        st.subheader("Nutritional Info")
        st.write(recipe.nutritional_info)

        st.subheader("Storage Instructions")
        st.write(recipe.storage_instructions)

        st.session_state.recipe = recipe
        recipe_generated = True

if recipe_generated:
    st.title("🛒 Product Finder for Ingredients")

    if st.button("Find Available Ingredients"):
        with st.spinner("Finding matching products... ⏳"):
            st.session_state.available_ingredients = get_available_ingredients(
                st.session_state.recipe.ingredients, language
            )

    if st.session_state.available_ingredients:
        st.subheader("Matching Products:")
        product_list = st.session_state.available_ingredients

        for i, product in enumerate(product_list):
            st.subheader(f"{product['Product_name']} ({product['Category']})")
            st.write(f"Description: {product['Description']}")
            st.write(f"Brand: {product['Brand']}")
            st.write(f"Price: {product['Price']}")
            st.write(f"Weight: {product['Weight']}")

            quantity = st.number_input(
                f"Quantity for {product['Product_name']}",
                min_value=1, max_value=10, value=1, step=1, key=f"qty_{i}"
            )

            if st.button(f"Add {product['Product_name']} to Cart", key=f"add_{i}"):
                add_item_to_cart(product, quantity)
                st.session_state.last_added = product["Product_name"]

    if st.session_state.last_added:
        st.success(f"✅ {st.session_state.last_added} added to cart!")
        st.session_state.last_added = None

    if st.session_state.cart_items:
        st.title("🧺 Your Cart:")
        for item_line in display_cart_summary():
            st.write(item_line)
