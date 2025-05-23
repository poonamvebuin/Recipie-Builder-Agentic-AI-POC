import time
import streamlit as st
from typing import Iterator
from agno.agent import RunResponse
import json
import re

from Agent.recipe import clean_recipe_name, get_agent, search_for_recipe_exact, stream_response_chunks
from Agent.cart import add_item_to_cart, display_cart_summary
from Agent.product import get_available_ingredients
from Agent.supervisor import get_supervisor_agent
from Agent.weather import get_cities_in_country, get_weather

# Streamlit Config
st.set_page_config(page_title="Recipe Builder", layout="centered")

# Sidebar - Language
st.sidebar.header("🌐 Language Preferences")
language_options = ["English", "Japanese"]
language = st.sidebar.selectbox("Choose your preferred language:", language_options, index=0)


with st.chat_message("assistant"):
    if language == 'English':
        st.write("**Welcome to your Personal cooking  Assistant! 🍽️**")
        st.write("I'm here to help you discover the perfect recipes or find exactly what you need for your kitchen. Let's start creating something delicious together! 😄")
        st.write("You've got two amazing options today:")
        st.write("1. **Recipe Creation** 🍳: Want to create a custom dish? Tell me your taste, time, and ingredients, and I'll suggest recipes that fit your vibe! Whether you're in the mood for something sweet, savory, or spicy, I've got you covered. Let's get cooking! 🌟")
        st.write("2. **Product Finder** 🛒: Looking for ingredients or kitchen products? I can help you find exactly what you need. Just tell me what you have in mind or upload your list, and I'll search for the best products available! Add them to your cart and shop with ease. 🛍️")
        st.write("👇 **Choose an option** and let's get started on your cooking  journey!")
        col1, col2 = st.columns([1, 1]) 
        with col1:
            if st.button("Chat with Recipe Assistant", key="recipe_creator_button", help="Click to start creating a recipe", use_container_width=True):
                st.session_state.mode = 'recipe'

        with col2:
            if st.button("Product Finder", key="product_finder_button", help="Click to find products", use_container_width=True):
                st.session_state.mode = 'product'
    if language == 'Japanese':
        st.write("**ようこそ、あなたのパーソナル料理アシスタントへ！🍽️**")
        st.write("私は、完璧なレシピを見つけるお手伝いや、キッチンに必要なものを見つけるお手伝いをします。一緒においしいものを作り始めましょう！😄")
        st.write("今日は、2つの素晴らしいオプションがあります：")
        st.write("1. **レシピ作成** 🍳: カスタム料理を作りたいですか？あなたの味、時間、そして材料を教えてくれれば、それにぴったりのレシピを提案します！甘いもの、塩辛いもの、辛いもの、どれを作りたい気分でもお任せください。さあ、料理を始めましょう！🌟")
        st.write("2. **製品探し** 🛒: 材料やキッチン用品を探していますか？欲しいものを教えてくれれば、最適な製品を見つけます！リストをアップロードするか、思いついたものを言ってください。見つけた製品をカートに追加して、簡単にお買い物ができます！🛍️")
        st.write("👇 **オプションを選んで**、あなたの料理の旅を始めましょう！")
        col1, col2 = st.columns([1, 1]) 
        with col1:
            if st.button("レシピアシスタントとチャット", key="recipe_creator_button", help="レシピ作成を始めるにはクリックしてください", use_container_width=True):
                st.session_state.mode = 'recipe'

        with col2:
            if st.button("製品探し", key="product_finder_button", help="製品を見つけるにはクリックしてください", use_container_width=True):
                st.session_state.mode = 'product'


st.session_state.start_prompt_shown = False


# App Header
# st.title("🍳 Recipe Creation Assistant 🍳")
# st.header("🧑‍🍳 Chat with Recipe Assistant")

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
    # Preference Collection UI in Sidebar
    st.title("🧑‍🍳 Chat with Recipe Assistant")

    st.sidebar.header("📍 Your Location")

    # Input for country
    countries_options = ["None", "India", "Japan"]
    country = st.sidebar.selectbox("Enter your country:", countries_options, index=0)

    city = None
    weather_data = None
    if country != "None":
        cities = get_cities_in_country(country)
        if cities:
            city = st.sidebar.selectbox("Choose a city", cities)
            if city != "None":
                # print('-------city', city)
                weather_data = get_weather(city, country)
                print('----------weather', weather_data)
                if weather_data:
                    st.sidebar.write(f"🌡️ Temperature: {weather_data['temperature']}°C")
                    # st.sidebar.write(f"💧 Humidity: {weather_data['humidity']}%")
                    st.sidebar.write(f"☁️ Weather: {weather_data['description']}")


    st.sidebar.header("🍽️ Your Preferences")

    # Only show preference inputs if not yet collected
    if not st.session_state.preferences_collected:
        taste_options = ["Sweet", "Savory", "Spicy", "Tangy", "Mild", "No Preference"]
        st.session_state.preferences["taste"] = st.sidebar.selectbox("Taste Preference:", taste_options, index=5)

        time_options = ["Quick (< 30 min)", "Medium (30-60 min)", "Long (> 60 min)", "No Preference"]
        st.session_state.preferences["cooking_time"] = st.sidebar.selectbox("Cooking Time:", time_options, index=3)

        ingredients_input = st.sidebar.text_area("Ingredients you want to use (comma separated):")
        if ingredients_input:
            st.session_state.preferences["ingredients"] = [i.strip() for i in ingredients_input.split(",")]

        allergies_input = st.sidebar.text_area("Allergies or ingredients to avoid (comma separated):")
        if allergies_input:
            st.session_state.preferences["allergies"] = [a.strip() for a in allergies_input.split(",")]

        diet_options = ["No Preference", "Vegetarian", "Vegan", "Non-Vegetarian"]
        st.session_state.preferences["diet"] = st.sidebar.selectbox("Dietary Preference:", diet_options, index=0)

        if st.sidebar.button("Save Preferences"):
            st.session_state.preferences_collected = True
            st.sidebar.success("Preferences saved! Ask for recipe suggestions.")
    else:
        # Display saved preferences
        st.sidebar.write(f"**Taste:** {st.session_state.preferences['taste']}")
        st.sidebar.write(f"**Cooking Time:** {st.session_state.preferences['cooking_time']}")
        st.sidebar.write(
            f"**Ingredients:** {', '.join(st.session_state.preferences['ingredients']) if st.session_state.preferences['ingredients'] else 'No specific ingredients'}")
        st.sidebar.write(
            f"**Allergies:** {', '.join(st.session_state.preferences['allergies']) if st.session_state.preferences['allergies'] else 'None specified'}")
        st.sidebar.write(f"**Diet:** {st.session_state.preferences['diet']}")

        if st.sidebar.button("Edit Preferences"):
            st.session_state.preferences_collected = False
            st.rerun()
    # Show full chat history always
    for msg in st.session_state.supervisor_history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Chat Input
    if user_input := st.chat_input("Ask for a recipe suggestion..."):
        # Store user's message
        st.session_state.supervisor_history.append({"role": "user", "content": user_input, "language": language})

        # Display user input
        with st.chat_message("user"):
            st.markdown(user_input)

        user_message_count = sum(1 for msg in st.session_state.supervisor_history if msg["role"] == "user")

        # Check if the request is specifically for recipe suggestions based on preferences
        # is_suggestion_request = any(keyword in user_input.lower() for keyword in
        #                             ["suggest", "recommendation", "what can i make", "recipe", "dish"])

        # Check if the request is specifically for Japanese recipes
        st.session_state.is_japanese_request = "japanese" in user_input.lower() or "japan" in user_input.lower() or "日本" in user_input
        if st.session_state.preferences_collected:
            text = ""
            if st.session_state.preferences['taste']:
                text += f" - Taste must be {st.session_state.preferences['taste']}"
            if st.session_state.preferences['cooking_time']:
                text += f" - Cooking Time must be {st.session_state.preferences['cooking_time']}"
            if st.session_state.preferences['ingredients']:
                text += f" - Ingredients to include: {', '.join(st.session_state.preferences['ingredients']) if st.session_state.preferences['ingredients'] else 'No specific ingredients'}"
            if st.session_state.preferences['allergies']:
                text += f"""MOST IMPORTANT: Suggest Recipe which don't have mentioned Allergies
                Allergies/Avoid: {', '.join(st.session_state.preferences['allergies']) if st.session_state.preferences['allergies'] else 'None specified'}
                """
            if st.session_state.preferences['diet']:
                text += f" - Diet must be {st.session_state.preferences['diet']}."
            # Include user preferences in the prompt
            preferences_text = f"""
            IMPORTANT USER PREFERENCES:
            {text}

            Based on these preferences and the user's request: "{user_input}", suggest 5 suitable recipes.
            Please ensure All the user preferences must be satisfied

            IMPORTANT FORMATTING RULES:
            1. Format your response as conversational text, followed by "RECIPE SUGGESTIONS:" 
            2. List each recipe on a new line
            3. For Japanese recipes, use format: "寿司 (Sushi)" - Japanese name first, then English in parentheses
            4. ONLY include the recipe names - NO URLs, NO image links, NO descriptions, NO additional text
            5. DO NOT use JSON format

            Example correct format:
            Here are some recipe suggestions based on your preferences.

            RECIPE SUGGESTIONS:
            寿司 (Sushi)
            天ぷら (Tempura)
            ラーメン (Ramen)
            うどん (Udon)
            そば (Soba)
            """
            prompt = f"{preferences_text} IMPORTANT: Generate response in {language}"
        else:
            # Process request without specific preference information
            no_preference_indicators = [
                "no preferences", "not having specific preferences", "any recipe is fine",
                "no specific", "don't have preferences", "no particular preferences",
                "just suggest", "whatever you suggest", "anything is fine"
            ]
            has_explicit_no_preference = any(indicator in user_input.lower() for indicator in no_preference_indicators)

            prompt = f"{user_input}"
            if st.session_state.is_japanese_request:
                prompt += " IMPORTANT: For Japanese recipes, ALWAYS include both the Japanese name in Japanese characters AND English translation in the format: 寿司 (Sushi). Never suggest Japanese recipes without Japanese characters."

            if has_explicit_no_preference:
                prompt += " USER HAS EXPLICITLY STATED NO PREFERENCES, PROVIDE RECIPE SUGGESTIONS IMMEDIATELY."
            elif user_message_count > 1:
                prompt += " THIS IS A FOLLOW-UP MESSAGE WITH USER PREFERENCES, PROVIDE RECIPE SUGGESTIONS NOW."

            prompt += f"""
            IMPORTANT FORMATTING RULES: 
            - Generate response in {language}
            - alway give msg like this when no preference: give msg like i search for prefrnce but no prefrence so i will suggest some recipes
            - Format your response as conversational text, followed by "RECIPE SUGGESTIONS:" 
            - List each recipe on a new line
            - For Japanese recipes, use format: "寿司 (Sushi)" - Japanese name first, then English in parentheses
            - ONLY include the recipe names - NO URLs, NO image links, NO descriptions, NO additional text
            - DO NOT use JSON format
            """
        if weather_data:
            prompt += f"""MUST ADD WEATHER DETAILS AND SUGGEST RECIPE
                {weather_data['temperature']}:
                    - If the temperature is over 30°C and the weather is hot or sunny, suggest cold or refreshing dishes, drinks.
                    - If the temperature is below 15°C and the weather is cold, suggest warm and comforting dishes, drinks.
                    - If the temperature is between 15°C and 30°C, suggest balanced dishes,drinks that are neither too hot nor too cold.
                {weather_data['description']}:
                    - If  weather data includes the word **rain**: suggest meal based on rain"""
            
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
        print(msg)
        # response_iterator = st.session_state.supervisor_agent.run(message=prompt, stream=True)
        response_iterator = st.session_state.supervisor_agent.run(messages=msg, stream=True)
        # print('------------msg', msg)
        # response_iterator = st.session_state.weather_agent.run(messages=msg, stream=True)
        with st.chat_message("assistant"):
            full_response = st.write_stream(stream_response_chunks(response_iterator))

        # Store assistant response
        st.session_state.supervisor_history.append({"role": "assistant", "content": full_response})

        # Extract suggestions for button display
        dish_suggestions = []

        # First try to parse as JSON (in case the model returns JSON)
        try:
            json_response = json.loads(full_response)
            if isinstance(json_response, dict) and "suggestions" in json_response and isinstance(
                    json_response["suggestions"], list):
                dish_suggestions = json_response["suggestions"]

                # Create a formatted response with RECIPE SUGGESTIONS: marker for display
                formatted_response = json_response.get("message",
                                                    "Here are some recipe suggestions:") + "\n\nRECIPE SUGGESTIONS:\n"
                formatted_response += "\n".join(dish_suggestions)

                # Update the stored response to use our formatted version with the marker
                st.session_state.supervisor_history[-1]["content"] = formatted_response
                full_response = formatted_response
        except (json.JSONDecodeError, ValueError):
            # Not valid JSON, continue with existing text extraction
            pass

        # If no suggestions were found via JSON, try the text marker approach
        if not dish_suggestions and "RECIPE SUGGESTIONS:" in full_response:
            # Split the content at the marker and take everything after it
            suggestion_section = full_response.split("RECIPE SUGGESTIONS:", 1)[1].strip()
            # Process each line in the suggestion section
            for line in suggestion_section.splitlines():
                line = line.strip()
                if line:
                    # Remove common punctuation that might appear
                    if line.endswith((".", ",", ";", "?", "!", ":", "。", "、", "！", "？", "：", "；")):
                        line = line[:-1].strip()

                    # Clean the recipe name
                    line = clean_recipe_name(line)

                    # Add to suggestions if non-empty
                    if line and not line.lower().startswith(("if ", "when ", "please ", "let me")):
                        dish_suggestions.append(line)

            # For Japanese requests, verify that suggestions have Japanese characters
            if st.session_state.is_japanese_request and dish_suggestions:
                print('--------dish_suggestions', dish_suggestions)
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
                        f"IMPORTANT: Do NOT include URLs, links, or descriptions - ONLY the recipe names. "
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
        # print('----dishhhhhhhhhhhhhh----', dish_suggestions)
        if dish_suggestions:
            st.session_state.dish_suggestions = dish_suggestions
            st.session_state.final_dish_choice = None
            st.session_state.ready_for_recipe = False


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
        # Build context from conversation history and preferences
        conversation_history = ""
        for msg in st.session_state.supervisor_history:
            conversation_history += f"{msg['content']}\n"

        preferences_context = ""
        if st.session_state.preferences_collected:
            preferences = st.session_state.preferences
            preferences_list = []

            if preferences['taste'] and preferences['taste'] != "No Preference":
                preferences_list.append(f"- Taste: {preferences['taste']}")
            
            if preferences['cooking_time'] and preferences['cooking_time'] != "No Preference":
                preferences_list.append(f"- Cooking Time: {preferences['cooking_time']}")
            
            if preferences['ingredients']:
                if preferences['ingredients']:
                    preferences_list.append(f"- Ingredients to include: {', '.join(preferences['ingredients'])}")
            
            if preferences['allergies']:
                if preferences['allergies']:
                    preferences_list.append(f"- Allergies/Avoid: {', '.join(preferences['allergies'])}")
            
            if preferences['diet'] and preferences['diet'] != "No Preference":
                preferences_list.append(f"- Diet: {preferences['diet']}")

            # Join all valid preferences together
            if preferences_list:
                preferences_context = "User Preferences:\n" + "\n".join(preferences_list)

        # Construct prompt for recipe agent using context
        cleaned_dish_name = re.sub(r'\s*\(.*?\)', '', st.session_state.final_dish_choice)
        cleaned_dish_name = re.sub(r'^\s*-*\s*', '', cleaned_dish_name)
        
        recipe_from_json = search_for_recipe_exact(cleaned_dish_name)
        if recipe_from_json:
            prompt = (
                f"Please translate the following recipe into {language}:\n\n"
                f"{preferences_context}\n\n"
                f"Recipe: {recipe_from_json}\n\n"
                f"Adjust the ingredients, times and quantities proportionally to match for given {conversation_history} servings. "
                f"Ensure that all quantities are modified proportionally and the INGREDIANTS appear on separate lines. "
                f"Do not omit any important details in the translation."
            )
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

            if recipe.image_url and recipe.image_url.startswith(('http://', 'https://')):
                # Only display if it's a valid URL
                st.image(recipe.image_url, caption=recipe.recipe_title)
            elif recipe.image_url:
                # If there's an image URL but it's not valid, just display a message
                st.write("Image not available")

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
        else:
            st.error(f"No reccipe found for{cleaned_dish_name}")


    # Ingredient Matching & Cart
    if recipe_generated:
        st.title("🛒 Product Finder for Ingredients")

        if st.button("Find Available Ingredients"):
            with st.spinner("Finding matching products... ⏳"):
                st.session_state.available_ingredients = get_available_ingredients(
                    st.session_state.recipe.ingredients, language
                )
                st.session_state.search_done = True  # <-- Use session state instead of a local variable

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
                    min_value=1, max_value=10, value=1, step=1, key=f"qty_{i}"
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


if st.session_state.mode == 'product':
    st.title("🛒 Product Finder")
    product_input = st.text_input("Enter products or ingredients:")
    if st.button("Find Products"):
        # Simulate product search
        products = get_available_ingredients(product_input.split(","), language)
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
                min_value=1, max_value=10, value=1, step=1, key=f"qty_{i}"
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
