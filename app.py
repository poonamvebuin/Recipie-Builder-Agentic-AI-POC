import streamlit as st
from typing import Iterator
from agno.agent import RunResponse

from Agent.recipe import get_agent, check_recipe_exists, format_recipe_output
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
    
    # Check if user is indicating no preferences
    no_preference_indicators = [
        "no preferences", "not having specific preferences", "any recipe is fine", 
        "no specific", "don't have preferences", "no particular preferences", 
        "just suggest", "whatever you suggest", "anything is fine"
    ]
    
    has_explicit_no_preference = any(indicator in user_input.lower() for indicator in no_preference_indicators)
    
    # Count previous messages to determine if we've already had a clarification exchange
    user_message_count = sum(1 for msg in st.session_state.supervisor_history if msg["role"] == "user")
    
    # Check if the request is specifically for Japanese recipes
    is_japanese_request = "japanese" in user_input.lower() or "japan" in user_input.lower() or "日本" in user_input
    
    # Construct the prompt
    prompt = f"{user_input}"
    
    if is_japanese_request:
        prompt += " IMPORTANT: For Japanese recipes, ALWAYS include both the Japanese name in Japanese characters AND English translation in the format: 寿司 (Sushi). Never suggest Japanese recipes without Japanese characters."
    
    if has_explicit_no_preference:
        prompt += " USER HAS EXPLICITLY STATED NO PREFERENCES, PROVIDE RECIPE SUGGESTIONS IMMEDIATELY."
    elif user_message_count > 1:
        prompt += " THIS IS A FOLLOW-UP MESSAGE WITH USER PREFERENCES, PROVIDE RECIPE SUGGESTIONS NOW."

    prompt += f" IMPORTANT: Generate response in {language}"
    msg = [{"role": "user", "content": prompt}]
    
    # Include conversation history for context if this isn't the first message
    if user_message_count > 1 and len(st.session_state.supervisor_history) >= 2:
        context_messages = []
        # Add the last 2 exchanges for context
        for i in range(min(4, len(st.session_state.supervisor_history))):
            if len(st.session_state.supervisor_history) - i - 1 >= 0:
                prev_msg = st.session_state.supervisor_history[len(st.session_state.supervisor_history) - i - 1]
                context_messages.insert(0, {"role": prev_msg["role"], "content": prev_msg["content"]})
        
        # Add current message
        context_messages.append({"role": "user", "content": prompt})
        msg = context_messages
    
    response = st.session_state.supervisor_agent.run(
        messages=msg,
        stream=False
    )

    st.session_state.supervisor_history.append({"role": "assistant", "content": response.content})

    # Extract suggestions for button display
    dish_suggestions = []
    if "RECIPE SUGGESTIONS:" in response.content:
        # Split the content at the marker and take everything after it
        suggestion_section = response.content.split("RECIPE SUGGESTIONS:", 1)[1].strip()
        
        # Process each line in the suggestion section
        for line in suggestion_section.splitlines():
            line = line.strip()
            if line:
                # Remove common punctuation that might appear
                if line.endswith((".", ",", ";", "?", "!", ":", ")", "）", "。", "、", "！", "？", "：", "；")):
                    line = line[:-1].strip()
                
                # Add to suggestions if non-empty
                if line and not line.lower().startswith(("if ", "when ", "please ", "let me")):
                    dish_suggestions.append(line)
    
    # For Japanese requests, verify that suggestions have Japanese characters
    if is_japanese_request and dish_suggestions:
        has_japanese_chars = False
        for suggestion in dish_suggestions:
            # Check if any suggestion contains Japanese characters
            if any(ord(char) > 127 for char in suggestion):
                has_japanese_chars = True
                break
        
        # If no Japanese characters found, force regeneration with Japanese
        if not has_japanese_chars:
            force_japanese_prompt = (
                f"Based on the user request for Japanese recipes, please provide ONLY recipe suggestions "
                f"with BOTH Japanese characters AND English translations. Format each suggestion as: "
                f"[Japanese name in Japanese characters] ([English translation]). "
                f"Examples: 寿司 (Sushi), 天ぷら (Tempura), ラーメン (Ramen). "
                f"Start with 'RECIPE SUGGESTIONS:' and list 5 suitable recipes."
            )
            
            force_msg = [{"role": "user", "content": force_japanese_prompt}]
            force_response = st.session_state.supervisor_agent.run(
                messages=force_msg,
                stream=False
            )
            
            # Replace the previous response
            st.session_state.supervisor_history[-1]["content"] = force_response.content
            
            # Extract new suggestions
            if "RECIPE SUGGESTIONS:" in force_response.content:
                suggestion_section = force_response.content.split("RECIPE SUGGESTIONS:", 1)[1].strip()
                dish_suggestions = [line.strip() for line in suggestion_section.splitlines() if line.strip()]

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
            f"Provide response in the language: {language}."
            f"preferece:\n{conversation_history}\n\n"
            f"Based on the above preferences, generate a recipe for '{st.session_state.final_dish_choice}'. "
        )

        print('----------prompt', prompt)
        existing_recipe = check_recipe_exists(prompt)
        if existing_recipe:
            recipe = format_recipe_output(existing_recipe)
        else:
            run_response: Iterator[RunResponse] = st.session_state.recipe_agent.run(prompt, stream=True)
            recipe = run_response.content

        st.title("🍽️ Deliciously Recipe 🍽️")
        
        # Display recipe image or video if available
        # if recipe.video_data and recipe.video_data.get('poster_url'):
        #     # If video data is available, use the poster_url as the image
        #     st.image(recipe.video_data.get('poster_url'), caption=recipe.recipe_title)
        
        #     # Check if there's a video source with type "video/mp4"
        #     video_sources = recipe.video_data.get('sources', [])
        #     mp4_video = next((source for source in video_sources if source.get('type') == 'video/mp4'), None)
        
        #     if mp4_video and mp4_video.get('url'):
        #         st.video(mp4_video.get('url'))
        if recipe.image_url:
            # If only image is available, display it
            st.image(recipe.image_url, caption=recipe.recipe_title)
        
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

        if existing_recipe:
            st.info("This recipe was retrieved from **Belc's recipe collection**.")
        else:
            st.info("This recipe was generated by **ChatGPT** based on your preferences. **Please verify before cook**.")

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
