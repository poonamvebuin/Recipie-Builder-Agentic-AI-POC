import streamlit as st
from Agent.recipe import get_agent
from Agent.supervisor import get_supervisor_agent
from streamlit_app.streamlit_welcom import display_welcome_message
from streamlit_app.streamlit_product import get_product_suggestions
from streamlit_app.streamlit_recipe import get_recipe_suggestions

# Streamlit Config
st.set_page_config(page_title="Recipe Builder", layout="centered")

# Sidebar - Language
st.sidebar.header("🌐 Language Preferences")
language_options = ["English", "Japanese"]
language = st.sidebar.selectbox("Choose your preferred language:", language_options, index=0)


display_welcome_message(language)

# Session State Initialization
if "recipe_agent" not in st.session_state:
    st.session_state.recipe_agent = get_agent()
if "supervisor_agent" not in st.session_state:
    st.session_state.supervisor_agent = get_supervisor_agent()
# if "weather_agent" not in st.session_state:
#     st.session_state.weather_agent = get_weather_agent()
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
if "search_done" not in st.session_state:
    st.session_state.search_done = False
if "preferences" not in st.session_state:
    st.session_state.preferences = {
        "taste": None,
        "cooking_time": None,
        "ingredients": [],
        "allergies": [],
        "diet": None
    }
if "preferences_collected" not in st.session_state:
    st.session_state.preferences_collected = False
if "is_japanese_request" not in st.session_state:
    st.session_state.is_japanese_request = False
if "mode" not in st.session_state:
    st.session_state.mode = None



if st.session_state.mode == 'recipe':
    get_recipe_suggestions(language)

if st.session_state.mode == 'product':
    get_product_suggestions(language)
    