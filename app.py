import streamlit as st
from typing import Iterator
from agno.agent import RunResponse

from Agent.recipe import get_agent
from Agent.cart import add_item_to_cart, display_cart_summary
from Agent.product import get_available_ingredients
from Agent.supervisor import get_supervisor_agent

# Streamlit Config
st.set_page_config(page_title="Recipe Builder", layout="centered")

# Sidebar - Language
st.sidebar.header("🌐 Language Preferences")
language_options = ["English","Japanese"]
language = st.sidebar.selectbox("Choose your preferred language:", language_options, index=0)

# App Header
# st.title("🍳 Recipe Creation Assistant 🍳")
st.header("🧑‍🍳 Chat with Recipe Assistant")

# Session State Initialization
if "recipe_agent" not in st.session_state:
    st.session_state.recipe_agent = get_agent()
if "supervisor_agent" not in st.session_state:
    st.session_state.supervisor_agent = get_supervisor_agent()
if "supervisor_history" not in st.session_state:
    st.session_state.supervisor_history = []
if "final_dish_choice" not in st.session_state:
    st.session_state.final_dish_choice = None
if "ready_for_recipe" not in st.session_state:
    st.session_state.ready_for_recipe = False
if "cart_items" not in st.session_state:
    st.session_state.cart_items = []
if "available_ingredients" not in st.session_state:
    st.session_state.available_ingredients = []
if "last_added" not in st.session_state:
    st.session_state.last_added = None
if "dish_suggestions" not in st.session_state:
    st.session_state.dish_suggestions = []

# Show full chat history always
# for msg in st.session_state.supervisor_history:
#     with st.chat_message(msg["role"]):
#         st.markdown(msg["content"])

# Chat Input
user_input = st.chat_input("Ask for a recipe suggestion...")

if user_input:
    st.session_state.supervisor_history.append({"role": "user", "content": user_input, "language": language})
    prompt = f"{user_input} generate response in {language}"

    # response = st.session_state.supervisor_agent.run(
    #     messages=[{"role": "user", "content": prompt}],
    #     stream=False
    # )
    msg = [{"role": "user", "content": prompt}]
    response = st.session_state.supervisor_agent.run(
        messages=msg,
        stream=False
    )

    st.session_state.supervisor_history.append({"role": "assistant", "content": response.content})

    # Extract suggestions for button display
    dish_suggestions = []
    for line in response.content.splitlines():
        line = line.strip()
        if "." in line or "。" in line or "?" in line or "？" in line:
            if "." in line:
                parts = line.split(".", 1)
            elif "。" in line:
                parts = line.split("。", 1)
            else:
                parts = line.split("?", 1) 

            suggestion = parts[1].strip() if len(parts) > 1 else parts[0].strip()

            if suggestion and not (suggestion.endswith("?") or suggestion.endswith("？") or suggestion.endswith("）") or suggestion.endswith(")") or suggestion.endswith(".") or suggestion.endswith("。") or suggestion.endswith(":") or suggestion.endswith("！") or suggestion.endswith("：")):
                dish_suggestions.append(suggestion)
    if dish_suggestions:
        st.session_state.dish_suggestions = dish_suggestions
        st.session_state.final_dish_choice = None
        st.session_state.ready_for_recipe = False

# Show full chat history always
for msg in st.session_state.supervisor_history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# Show suggestion buttons
if st.session_state.dish_suggestions:
    st.subheader("🍽️ Suggested Recipes:")
    for suggestion in st.session_state.dish_suggestions:
        if st.button(suggestion):
            st.session_state.final_dish_choice = suggestion
            st.session_state.ready_for_recipe = True
            st.rerun()

# Generate recipe
recipe_generated = False
if st.session_state.ready_for_recipe and st.session_state.final_dish_choice:
    with st.spinner("Generating your recipe..."):

        # Build context from conversation history
        conversation_history = ""
        for msg in st.session_state.supervisor_history:
            conversation_history += f"{msg['content']}\n"

        # Construct prompt for recipe agent using context
        prompt = (
            f"preferece:\n{conversation_history}\n\n"
            f"Based on the above preferences, generate a recipe for '{st.session_state.final_dish_choice}'. "
            f"Ensure it matches the language: {language}."
        )

        print('----------prompt', prompt)

        run_response: Iterator[RunResponse] = st.session_state.recipe_agent.run(prompt, stream=True)
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

        # Reset trigger
        # st.session_state.ready_for_recipe = False
        # st.session_state.dish_suggestions = []

# Ingredient Matching & Cart
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
