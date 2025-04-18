from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.postgres import PostgresStorage
from textwrap import dedent
import os
from dotenv import load_dotenv
import json
import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from deep_translator import GoogleTranslator

load_dotenv()

class VideoSource(BaseModel):
    url: str
    type: str
    model_config = ConfigDict(extra='forbid')

class VideoData(BaseModel):
    poster_url: str
    sources: List[VideoSource]
    model_config = ConfigDict(extra='forbid')

class RecipeOutput(BaseModel):
    recipe_title: str
    cuisine_type: Optional[str] = None
    prep_time: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[List[str]] = None
    nutritional_info: Optional[str] = None
    difficulty_level: Optional[str] = None
    serving_size: Optional[str] = None
    storage_instructions: Optional[str] = None
    extra_features: Optional[Dict[str, str]] = None
    image_url: Optional[str] = None
    # video_data: Optional[VideoData] = None
    # model_config = ConfigDict(
    #     extra='forbid',
    #     json_schema_extra={
    #         "type": "object",
    #         "properties": {
    #             "recipe_title": {"type": "string"},
    #             "cuisine_type": {"type": "string"},
    #             "prep_time": {"type": "string"},
    #             "cook_time": {"type": "string"},
    #             "total_time": {"type": "string"},
    #             "ingredients": {"type": "string"},
    #             "instructions": {
    #                 "type": "array",
    #                 "items": {"type": "string"}
    #             },
    #             "nutritional_info": {"type": "string"},
    #             "difficulty_level": {"type": "string"},
    #             "serving_size": {"type": "string"},
    #             "storage_instructions": {"type": "string"},
    #             "extra_features": {
    #                 "type": "object",
    #                 "additionalProperties": {"type": "string"}
    #             },
    #             "image_url": {"type": "string"},
    #             "video_data": {
    #                 "type": "object",
    #                 "additionalProperties": False,
    #                 "properties": {
    #                     "poster_url": {"type": "string"},
    #                     "sources": {
    #                         "type": "array",
    #                         "items": {
    #                             "type": "object",
    #                             "additionalProperties": False,
    #                             "properties": {
    #                                 "url": {"type": "string"},
    #                                 "type": {"type": "string"}
    #                             },
    #                             "required": ["url", "type"]
    #                         }
    #                     }
    #                 },
    #                 "required": ["poster_url", "sources"]
    #             }
    #         },
    #         "required": ["recipe_title"]
    #     }
    # )

def get_agent():
    
    db_url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
             f"{os.getenv('DB_HOST')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"
    storage = PostgresStorage(
        table_name="agent_sessions",
        db_url=db_url,
        auto_upgrade_schema=True
    )

    agent = Agent(
        name="Recipe Agent",
        model=OpenAIChat(id="gpt-4o"),
        description=dedent("""\
            You are ChefGenius, a passionate and knowledgeable culinary expert with expertise in global cuisine! 🍳

            Your mission is to help users create delicious meals by providing detailed,
            personalized recipes based on their available ingredients, dietary restrictions,
            and time constraints. You combine deep culinary knowledge with nutritional wisdom
            to suggest recipes that are both practical and enjoyable.
        """),

        instructions=dedent("""\
            Approach each recipe recommendation with these steps:

            1. Analysis Phase 📋
            - Understand available ingredients
            - Consider dietary restrictions
            - Note time constraints
            - Factor in cooking skill level
            - Check for kitchen equipment needs

            2. Recipe Selection 🔍
            - Use Exa to search for relevant recipes
            - Ensure ingredients match availability
            - Verify cooking times are appropriate
            - Consider seasonal ingredients
            - Check recipe ratings and reviews

            3. Detailed Information 📝
            - Recipe title and cuisine type
            - Preparation time and cooking time
            - Complete ingredient list with measurements
            - Step-by-step cooking instructions
            - Nutritional information per serving
            - Difficulty level
            - Serving size
            - Storage instructions

            4. Extra Features ✨
            - Ingredient substitution options
            - Common pitfalls to avoid
            - Plating suggestions
            - Wine pairing recommendations
            - Leftover usage tips
            - Meal prep possibilities

            Presentation Style:
            - Use clear markdown formatting
            - Present ingredients in a structured list
            - Number cooking steps clearly
            - Add emoji indicators for:
            🌱 Vegetarian
            🌿 Vegan
            🌾 Gluten-free
            🥜 Contains nuts
            ⏱️ Quick recipes
            - Include tips for scaling portions
            - Note allergen warnings
            - Highlight make-ahead steps
            - Suggest side dish pairings

            Ingredients Section:
            - Present ingredients in a structured list with measurements.
            - Clearly list each ingredient under the Ingredients heading, with units and amounts.
            - Use bullet points or numbered lists for clarity.
            - Ensure any special dietary notes or substitutions are included next to the relevant ingredients.
            
            Image:
            - Generate image of dish   
            
        """),

        markdown=True,
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        # storage=storage,
        response_model=RecipeOutput
    )
    return agent

# Load the recipe data
recipes_path="recipe_data/all_recipes.json"
with open(recipes_path, 'r', encoding='utf-8') as f:
    recipes = json.load(f)

# Initialize the sentence transformer
model = SentenceTransformer('all-MiniLM-L6-v2')

# Create embeddings for each recipe title
title_embeddings = model.encode([recipe.get('title', '') for recipe in recipes])

# Initialize the FAISS index
dimension = title_embeddings.shape[1]
title_index = faiss.IndexFlatL2(dimension)
title_index.add(title_embeddings.astype('float32'))

def extract_recipe_name(prompt):
    """
    Extract the recipe name from the prompt, handling various formats and languages.
    
    Args:
        prompt: The user's prompt
        
    Returns:
        The extracted recipe name
    """
    # Common patterns in different languages
    patterns = [
        # English patterns
        r"recipe (?:for|of) (.+?)(?:\?|$)",
        r"how (?:to|do I) (?:make|cook|prepare) (.+?)(?:\?|$)",
        r"can you (?:give|share|provide) (?:me )?(?:the )?recipe (?:for|of) (.+?)(?:\?|$)",
        r"what is the recipe (?:for|of) (.+?)(?:\?|$)",
        r"show me (?:the )?recipe (?:for|of) (.+?)(?:\?|$)",
        r"tell me (?:about|how to make) (.+?)(?:\?|$)",
        r"i want (?:to make|to cook) (.+?)(?:\?|$)",
        r"i need (?:a )?recipe (?:for|of) (.+?)(?:\?|$)",
        
        # Japanese patterns (romanized)
        r"(.+?) no reshipi",
        r"(.+?) no ryori",
        r"(.+?) no tsukurikata",
        r"(.+?) no tsukurihou",
        r"(.+?) no tsukurikata wo oshiete",
        r"(.+?) no reshipi wo kudasai",
        
        # Generic patterns (fallback)
        r"(.+?)(?:\?|$)"
    ]

    patterns += [r'([\u3040-\u30ff\u4e00-\u9faf]+)\s*\(']

    import re
    
    # Try each pattern
    for pattern in patterns:
        match = re.search(pattern, prompt, re.IGNORECASE)
        if match:
            recipe_name = match.group(1).strip()
            # Remove common words that might be part of the prompt but not the recipe name
            recipe_name = re.sub(r'^(the|a|an)\s+', '', recipe_name, flags=re.IGNORECASE)
            matches = re.findall(r'([\u3040-\u30ff\u4e00-\u9faf]+)', recipe_name)
            return matches[0] if matches else recipe_name.strip()
    
    # If no pattern matches, return the whole prompt
    return prompt.strip()

def translate_to_japanese(text):
    try:
        translated_text = GoogleTranslator(source='auto', target='ja').translate(text)
        return translated_text
    except Exception as e:
        print("Translation failed:", e)
        return None
    

def check_recipe_exists(prompt, language, threshold=0.6, min_threshold=0.1):
    extract_recipe = extract_recipe_name(prompt)
    print(f"Extracted recipe name: {extract_recipe}")

    recipe_name = (
        translate_to_japanese(extract_recipe) if language != 'ja' else extract_recipe
    )
    print('------------recipe_name', recipe_name)

    query_embedding = model.encode([recipe_name])

    while threshold >= min_threshold:
        print(f"Searching with threshold: {threshold}")
        distances, indices = title_index.search(query_embedding.astype('float32'), k=10)

        search_results = []
        for i, distance in enumerate(distances[0]):
            if distance < threshold:
                matched_recipe = recipes[indices[0][i]]
                print(f"Found match: {matched_recipe.get('title')} with distance {distance}")

                image_url = matched_recipe.get('image_url', '')
                if image_url and image_url.startswith('/') and 'belc.jp' in matched_recipe.get('url', ''):
                    image_url = f"https://www.belc.jp{image_url}"
                if image_url:
                    print(f"Recipe Image: {image_url}")

                if 'video_data' in matched_recipe and matched_recipe['video_data']:
                    video_data = matched_recipe['video_data']
                    print(f"Recipe Video: {video_data.get('poster_url', '')}")
                    for source in video_data.get('sources', []):
                        print(f"Video URL: {source.get('url', '')}")

                search_results.append(matched_recipe)

        if search_results:
            return search_results

        threshold -= 0.1

    print("No match found after all attempts")
    return None

def format_recipe_output(recipe_data):
    """
    Format recipe data into the RecipeOutput model.
    
    Args:
        recipe_data: The recipe data from the database
        
    Returns:
        A formatted RecipeOutput object
    """
    # Extract ingredients
    # print('----------------recipe_data', recipe_data)
    recipe_data = recipe_data[0]
    ingredients = recipe_data.get('ingredients', [])
    if isinstance(ingredients, list):
        # Handle different ingredient formats
        if ingredients and isinstance(ingredients[0], dict) and 'name' in ingredients[0]:
            ingredients_text = '\n'.join([f"- {ing.get('name', '')} ({ing.get('quantity', '')})" 
                                         for ing in ingredients])
        else:
            ingredients_text = '\n'.join([f"- {ing}" for ing in ingredients])
    else:
        ingredients_text = str(ingredients)
    
    # Extract instructions
    instructions = recipe_data.get('steps', [])
    if isinstance(instructions, list):
        instructions_list = instructions
    else:
        instructions_list = [str(instructions)]
    
    # Handle image URL (handle both absolute and relative URLs)
    image_url = recipe_data.get('image_url')
    if image_url and image_url.startswith('/'):
        # For relative URLs from belc.jp, prefix with base URL
        if 'belc.jp' in recipe_data.get('url', ''):
            image_url = f"https://www.belc.jp{image_url}"
    
    # Create video data if present
    video_data_dict = recipe_data.get('video_data')
    video_data = None
    if video_data_dict:
        sources = []
        for source in video_data_dict.get('sources', []):
            sources.append(VideoSource(
                url=source.get('url', ''),
                type=source.get('type', '')
            ))
        
        if sources and video_data_dict.get('poster_url'):
            video_data = VideoData(
                poster_url=video_data_dict.get('poster_url', ''),
                sources=sources
            )
    
    # Create the formatted output
    return RecipeOutput(
        recipe_title=recipe_data.get('title', ''),
        cuisine_type=recipe_data.get('cuisine_type', ''),
        prep_time=recipe_data.get('prep_time', ''),
        cook_time=recipe_data.get('cook_time', ''),
        total_time=recipe_data.get('total_time', ''),
        ingredients=ingredients_text,
        instructions=instructions_list,
        nutritional_info=recipe_data.get('nutritional_info', ''),
        difficulty_level=recipe_data.get('difficulty_level', ''),
        serving_size=recipe_data.get('serving_size', ''),
        storage_instructions=recipe_data.get('storage_instructions', ''),
        extra_features=recipe_data.get('extra_features', {}),
        image_url=image_url,
        video_data=video_data
    )

# def display_search_results(search_query, top_k=3, threshold=0.7):
#     """
#     Display search results with images and videos.
    
#     Args:
#         search_query: The user's search query
#         top_k: Number of top results to show
#         threshold: Similarity threshold
        
#     Returns:
#         List of matching recipes
#     """
#     recipe_name = extract_recipe_name(search_query)
#     query_embedding = model.encode([recipe_name])
    
#     # Search by title
#     distances, indices = title_index.search(query_embedding.astype('float32'), k=top_k)
    
#     results = []
#     print(f"Search results for '{recipe_name}':")
    
#     for i, distance in enumerate(distances[0]):
#         if distance < threshold:
#             matched_recipe = recipes[indices[0][i]]
#             formatted_recipe = format_recipe_output(matched_recipe)
            
#             print(f"\n{i+1}. {formatted_recipe.recipe_title} (Relevance: {1-distance:.2f})")
            
#             # Display image
#             if formatted_recipe.image_url:
#                 print(f"Image: {formatted_recipe.image_url}")
            
#             # Display video preview
#             if formatted_recipe.video_data:
#                 print(f"Video Preview: {formatted_recipe.video_data.poster_url}")
#                 if formatted_recipe.video_data.sources:
#                     print(f"Watch: {formatted_recipe.video_data.sources[0].url}")
            
#             # Show brief details
#             print(f"Cuisine: {formatted_recipe.cuisine_type or 'Not specified'}")
#             print(f"Prep time: {formatted_recipe.prep_time or 'Not specified'}")
#             print(f"Cook time: {formatted_recipe.cook_time or 'Not specified'}")
            
#             results.append(formatted_recipe)
    
#     if not results:
#         print("No matching recipes found.")
    
#     return results
