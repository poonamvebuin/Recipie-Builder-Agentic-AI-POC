import requests
from agno.agent import Agent
from pydantic import BaseModel
from typing import Dict, List
import json
from agno.knowledge.json import JSONKnowledgeBase
from agno.vectordb.pgvector import PgVector
from agno.models.openai import OpenAIChat
from deep_translator import GoogleTranslator
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = 'ff60d6c19189e5685023a1b1f2d87f90'
BASE_URL = 'http://api.openweathermap.org/data/2.5/weather'


import requests

# GeoNames API Endpoint
# GEO_API_URL = "http://api.geonames.org/searchJSON"
# GEO_API_USERNAME = "kamaliyapoonam" 

# def get_cities_in_country(country_name: str):
#     params = {
#         "formatted": "true",
#         "lang": "en",
#         "country": country_name,
#         "username": GEO_API_USERNAME,
#         "maxRows": 500  
#     }
#     print('--------------------1111111111111')
    
#     response = requests.get(GEO_API_URL, params=params)
#     print('----------333333333333', response.text, response.status_code)
#     if response.status_code == 200:
#         print('----------4444444')
#         data = response.json()
#         cities = [city['name'] for city in data['geonames']]
#         return cities
#     else:
#         return None

japan_cities = [
    "None", "Tokyo", "Osaka", "Kyoto", "Hokkaido", "Fukuoka", "Sapporo", "Nagasaki", "Kobe", "Yokohama", "Hiroshima",
    "Nara", "Sendai", "Kamakura", "Shizuoka", "Kochi", "Chiba", "Fukushima", "Okinawa", "Kagawa", "Gifu"
]

india_cities = [
    "None", "Delhi", "Mumbai", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Lucknow",
    "Kanpur", "Nagpur", "Indore", "Chandigarh", "Bhopal", "Coimbatore", "Visakhapatnam", "Patna", "Surat", "Vadodara"
]

# Function to get cities based on the country
def get_cities_in_country(country_name: str):
    if country_name.lower() == "japan":
        return japan_cities
    elif country_name.lower() == "india":
        return india_cities
    else:
        return [] 
    
def get_weather(city: str, country='JP'):
    url = f"{BASE_URL}?q={city},{country}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    print('-----------response', response.text, response.status_code)
    if response.status_code == 200:
        data = response.json()
        weather = {
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
        }
        return weather
    else:
        return None

# db_url = f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"

# # Initialize knowledge base
# knowledge_base = JSONKnowledgeBase(
#     path="recipe_data/all_recipes.json",
#     vector_db=PgVector(
#         table_name="json_documents",
#         db_url = db_url
#     ),
# )
# # Load the knowledge base
# knowledge_base.load(recreate=False)


# class SupervisorResponse(BaseModel):
#     message: str
#     suggestions: List[str]


# # Load the actual recipe data to ensure we have exact recipe titles
# def load_recipe_data(json_path="recipe_data/all_recipes.json"):
#     try:
#         with open(json_path, "r", encoding="utf-8") as f:
#             data = json.load(f)
#         return data
#     except Exception as e:
#         print(f"Error loading recipe data: {e}")
#         return []

# # Extract all recipe titles with their English translations (if available)
# def extract_recipe_titles(recipe_data):
#     titles_with_translations = []

#     for recipe in recipe_data:
#         japanese_title = recipe.get('title', '')
#         english_name = recipe.get('english_name', '')

#         if japanese_title:
#             formatted_title = f"{japanese_title}" + (f" ({english_name})" if english_name else "")
#             titles_with_translations.append(formatted_title)

#     return titles_with_translations

# # Extract recipe titles and their ingredients
# def extract_recipe_titles_and_ingredients(recipe_data):
#     titles_with_ingredients = []
#     for recipe in recipe_data:
#         title = recipe.get('title', '')
#         ingredients = recipe.get('ingredients', [])
#         if title:
#             titles_with_ingredients.append({
#                 'title': title,
#                 'ingredients': ingredients
#             })
#     return titles_with_ingredients

# # Load the recipe data
# recipe_data = load_recipe_data()

# # Extract the recipe titles
# recipe_titles = extract_recipe_titles(recipe_data)

# # Create a simple lookup set of just the Japanese titles for verification
# japanese_recipe_titles = {recipe.get('title', '') for recipe in recipe_data if recipe.get('title', '')}

# titles_with_ingredients = extract_recipe_titles_and_ingredients(recipe_data)

# def get_weather_agent():
#     agent = Agent(
#         name="weather agent",
#         model=OpenAIChat(id="gpt-4o-mini"),
#         knowledge=knowledge_base,
#         search_knowledge=True,
#         read_chat_history=True,
#         system_message=f"""
#         You are a helpful recipe advisor specializing in Japanese recipes based on the current weather.
#         Your task is to suggest recipes based on the weather data(Temprature) provided and give suggestions which is more suitable based on weather based on title and ingrediands{titles_with_ingredients}. 

#         IMPORTANT: 
#         - Our database contains ONLY the following Japanese recipe titles. You MUST ONLY suggest recipes from this exact list:
#         {', '.join(japanese_recipe_titles)}
#         - Formatted recipe titles with English translations (when available):
#         {recipe_titles}
#         - ALWAY SUGGEST 5 RECIPES
#         Ensure to suggest recipes based on the current weather and the ingredients available.

#         Consider the following weather conditions for recipe suggestions:
        
        # - If the temperature is over 25°C and the weather is hot or sunny, suggest cold or refreshing dishes, drinks like sushi, salads, or chilled noodles.
        # - If the temperature is below 15°C and the weather is cold, suggest warm and comforting dishes, drinks like ramen, curry, or soups.
        # - If the temperature is between 15°C and 25°C, suggest balanced dishes,drinks that are neither too hot nor too cold, such as tempura, rice bowls, or stir-fries.

#         When you provide your suggestions, ensure that they come from this list of exact recipe titles and ingredients. Do NOT invent or modify recipe names.

#         Example:
#         User: "Suggest some japanese dishes"
#         Agent: "I searched based on temprature weather is sunny. Here are some refreshing dishes for sunny weather:
#         RECIPE SUGGESTIONS:
#         """,
#         markdown=True,
#         show_tool_calls=True
#     )
#     return agent
