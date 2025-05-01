import pandas as pd
import streamlit as st
import json
import streamlit as st
from typing import Iterator
from agno.agent import RunResponse
import json
import re
from Agent.cart import add_item_to_cart, display_cart_summary, remove_item_from_cart
from Agent.product import get_available_ingredients
from Agent.recipe import clean_recipe_name, search_for_recipe_exact, stream_response_chunks
from Agent.supervisor import get_suggested_titles_with_reviews
from Agent.weather import get_cities_in_country, get_weather
from streamlit_app.streamlit_product import product_cart

def get_recipe_suggestions(language):
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
                # print('----------weather', weather_data)
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
        is_review_request = any(
            keyword in user_input.lower()
            for keyword in ["what people like", "which one is best", "top rated", "reviews", "recommend best"]
        )
        print('----------is_review_request', is_review_request)
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
            
        if is_review_request and st.session_state.last_recipe_suggestions:
            reviewed_data = get_suggested_titles_with_reviews(st.session_state.last_recipe_suggestions)
            if not reviewed_data:
                st.warning("❌ No review data available. Showing previous recipe suggestions again:")

                if st.session_state.last_recipe_suggestions:
                    repeat_response = "No review data available. Here are the previous suggestions again:\n\nRECIPE SUGGESTIONS:\n"
                    repeat_response += "\n".join(st.session_state.last_recipe_suggestions)

                    with st.chat_message("assistant"):
                        st.markdown(repeat_response)

                    st.session_state.supervisor_history.append({"role": "assistant", "content": repeat_response})

                    # Show buttons for previous suggestions
                    st.subheader("🍽️ Suggested Recipes:")
                    for suggestion in st.session_state.last_recipe_suggestions:
                        cleaned_name = clean_recipe_name(suggestion)
                        if st.button(cleaned_name):
                            st.session_state.final_dish_choice = re.sub(r'\s*\(.*?\)', '', cleaned_name).strip()
                            st.session_state.ready_for_recipe = True
                            st.rerun()
                return
            else:
                reviewed_text = ""
                for review in reviewed_data[:2]:
                    reviewed_text += f"Dish: {review['japanese_name']}\n"
                    reviewed_text += f"Rating: {review['average_rating']} (from {review['total_reviews']} reviews)\n"
                    reviewed_text += "Comments:\n"

                    comments = review.get("all_comments", [])
                    for idx, comment in enumerate(comments):
                        reviewed_text += f"{idx+1}. {comment}\n"

                    reviewed_text += "---\n"

                prompt += f"""
                        The user asked: "{user_input}"

                        You are an assistant helping the user decide which recipe is most liked **from a previous list**.

                        DO NOT SUGGEST ANY NEW RECIPES. You must ONLY use the review data below.

                        REVIEW DATA:
                        {reviewed_text}

                        TASK:
                        1. Carefully read all listed reviews for each dish.
                        2. Choose the top 1–2 dishes based on rating and user feedback.
                        3. In your response, show the dish name, rating, and quote several real comments from the list.
                        4. Then write: "RECIPE SUGGESTIONS:" and list ONLY those 1–2 dish names on separate lines.

                        IMPORTANT:
                        - DO NOT make up new dishes or comments.
                        - DO NOT summarize vaguely — use real reviews.
                        - Write in a friendly, natural tone in {language}.
                    """

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
        # print(msg)
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
            st.session_state.dish_suggestions = list(dict.fromkeys(dish_suggestions))
            st.session_state.last_recipe_suggestions = st.session_state.dish_suggestions.copy()  # <-- ADD THIS
            st.session_state.final_dish_choice = None
            st.session_state.ready_for_recipe = False


    if st.session_state.dish_suggestions:
        st.subheader("🍽️ Suggested Recipes:")
        for suggestion in st.session_state.dish_suggestions:
            if suggestion.startswith("Recommended Dish:"):
                match = re.search(r"Recommended Dish:\s*(.+)", suggestion)
                if match:
                    dish_name = clean_recipe_name(match.group(1).strip())
                    print('--------dish_name', dish_name)
                    dish_name = re.sub(r'\s*\(.*?\)', '', dish_name).strip()
                    if st.button(dish_name):
                        st.session_state.final_dish_choice = dish_name
                        st.session_state.ready_for_recipe = True
                        st.rerun()
            elif not suggestion.lower().startswith(("rating:", "what people say:")):
                cleaned_name = clean_recipe_name(suggestion)
                print('--------dish_name', cleaned_name)
                if st.button(cleaned_name):
                    st.session_state.final_dish_choice = cleaned_name
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
                st.image(recipe.image_url, caption=recipe.recipe_title)
            elif recipe.image_url:
                st.write("Image not available")
            if recipe.mp4_url and recipe.mp4_url.startswith(('http://', 'https://')):
                st.video(recipe.mp4_url)
            else:
                st.write("Video not available")

            info = {
                "Recipe Title": recipe.recipe_title,
                "Cuisine Type": recipe.cuisine_type,
                "Total Time": recipe.total_time,
                "Serving Size": recipe.serving_size,
                "Difficulty Level": recipe.difficulty_level,
            }
            for key, value in info.items():
                st.subheader(f"**{key}:**")
                st.write(value)
            st.subheader("Ingredients:")
            for i, value in enumerate(recipe.ingredients.split("\n"), start=1):
                st.write(f"{i}. {value}")

            st.subheader("Instructions:")
            
            for step in recipe.instructions:
                st.write(f"{step}")

            if recipe.extra_features:
                st.subheader("Extra Features")
                for key, value in recipe.extra_features.items():
                    st.write(f"**{key.replace('_', ' ').title()}**: {value or 'N/A'}")

            st.subheader("Nutritional Info")
            if recipe.nutrients:
                #Display nutritional information
                df = pd.DataFrame(recipe.nutrients.items(), columns=["Nutrient", "Amount"])
                df_no_index = df.reset_index(drop=True)
                styled_df = df_no_index.style.set_table_styles(
                    [{
                        'selector': 'thead th',
                        'props': [('background-color', '#f1f1f1'), ('color', 'black'), ('font-weight', 'bold')]
                    }, {
                        'selector': 'tbody td',
                        'props': [('padding', '10px'), ('text-align', 'center')]
                    }]
                ).set_properties(**{
                    'font-size': '14px',
                    'font-family': 'Arial, sans-serif',
                    'color': '#333333'
                })
                
                
                st.dataframe(styled_df)
            else:
                st.write("No nutritional info found!")

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

        for item in st.session_state.cart_items:
            if st.button(f'Remove {item["Product_name"]} from cart'):
                remove_item_from_cart(item["Product_name"])
                break  
        
        if st.session_state.success_message:
            st.success(st.session_state.success_message)
            st.session_state.success_message = None
        # if st.button("Find Available Ingredients"):
        #     with st.spinner("Finding matching products... ⏳"):
        #         product_cart(st.session_state.recipe.ingredients, language)
