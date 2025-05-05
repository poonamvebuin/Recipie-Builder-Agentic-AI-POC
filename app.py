import json
import uuid

import pandas as pd
import streamlit as st

from Agent.recipe import get_agent
from Agent.supervisor import get_supervisor_agent
from Database.database import save_conversation_to_postgres
from streamlit_app.streamlit_product import get_product_suggestions
from streamlit_app.streamlit_recipe import get_recipe_suggestions
from streamlit_app.streamlit_welcom import display_welcome_message

# Streamlit Config
st.set_page_config(page_title="Recipe Builder", layout="centered")

# Sidebar - Language
st.sidebar.header("🌐 Language Preferences")
language_options = ["English", "Japanese"]
language = st.sidebar.selectbox(
    "Choose your preferred language:", language_options, index=0
)

display_welcome_message(language)

# Initialize essential session state
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())
if "recipe_agent" not in st.session_state:
    st.session_state.recipe_agent = get_agent()
if "supervisor_agent" not in st.session_state:
    st.session_state.supervisor_agent = get_supervisor_agent()

# Initialize all other default session keys
defaults = {
    "supervisor_history": [],
    "final_dish_choice": None,
    "ready_for_recipe": False,
    "cart_items": [],
    "available_ingredients": [],
    "last_added": None,
    "dish_suggestions": [],
    "search_done": False,
    "preferences": {
        "taste": None,
        "cooking_time": None,
        "ingredients": [],
        "allergies": [],
        "diet": None
    },
    "preferences_collected": False,
    "is_japanese_request": False,
    "mode": None,
    "previous_mode": None,
    "cart_updated": False,
    "success_message": None,
    "last_recipe_suggestions": [],
    "recommended_dishes": [],
    "recipe": None
}

for key, value in defaults.items():
    if key not in st.session_state:
        st.session_state[key] = value

# --- RESET ON MODE SWITCH ---
if st.session_state.mode != st.session_state.previous_mode:
    # Reset shared product/ingredient state
    st.session_state.available_ingredients = []
    st.session_state.search_done = False
    st.session_state.cart_items = []
    st.session_state.last_added = None
    st.session_state.cart_updated = False
    st.session_state.success_message = None

    if st.session_state.previous_mode == "recipe":
        # Clear recipe-specific state
        st.session_state.supervisor_history = []
        st.session_state.final_dish_choice = None
        st.session_state.ready_for_recipe = False
        st.session_state.dish_suggestions = []
        st.session_state.last_recipe_suggestions = []
        st.session_state.preferences_collected = False
        st.session_state.recommended_dishes = []
        st.session_state.recipe = None

    elif st.session_state.previous_mode == "product":
        # No additional state needed
        pass

    # Update previous mode
    st.session_state.previous_mode = st.session_state.mode

# --- MAIN MODE HANDLING ---
if st.session_state.mode == 'recipe':
    get_recipe_suggestions(language)

elif st.session_state.mode == 'product':
    get_product_suggestions(language)

# --- SAVE TO DATABASE IF NEEDED ---
if st.session_state.supervisor_history or st.session_state.final_dish_choice:
    session_id = st.session_state.get("session_id")
    chat_history = json.dumps(st.session_state.get("supervisor_history", []))
    preferences = json.dumps(st.session_state.get("preferences", {}))
    cart = json.dumps(st.session_state.get("cart_items", []))
    product = st.session_state.get("available_ingredients", "")
    recipe_choice = st.session_state.get("final_dish_choice", "")
    save_conversation_to_postgres(
        session_id, chat_history, preferences, cart, product, recipe_choice
    )
