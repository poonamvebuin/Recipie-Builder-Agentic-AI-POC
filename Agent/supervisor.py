# supervisor.py

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

db_url = f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"

# Initialize knowledge base
knowledge_base = JSONKnowledgeBase(
    path="recipe_data/all_recipes.json",
    vector_db=PgVector(
        table_name="json_documents",
        db_url = db_url
    ),
)
# Load the knowledge base
knowledge_base.load(recreate=False)


class SupervisorResponse(BaseModel):
    message: str
    suggestions: List[str]

# Helper function to translate English queries to Japanese
def translate_to_japanese(text):
    try:
        translator = GoogleTranslator(source='en', target='ja')
        return translator.translate(text)
    except Exception as e:
        print(f"Translation error: {e}")
        return text  # Return original text if translation fails


# Load the actual recipe data to ensure we have exact recipe titles
def load_recipe_data(json_path="recipe_data/all_recipes.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading recipe data: {e}")
        return []

# Extract all recipe titles with their English translations (if available)
def extract_recipe_titles(recipe_data):
    titles_with_translations = []

    for recipe in recipe_data:
        japanese_title = recipe.get('title', '')
        english_name = recipe.get('english_name', '')

        if japanese_title:
            formatted_title = f"{japanese_title}" + (f" ({english_name})" if english_name else "")
            titles_with_translations.append(formatted_title)

    return titles_with_translations

# Load the recipe data
recipe_data = load_recipe_data()

# Extract the recipe titles
recipe_titles = extract_recipe_titles(recipe_data)

# Create a simple lookup set of just the Japanese titles for verification
japanese_recipe_titles = {recipe.get('title', '') for recipe in recipe_data if recipe.get('title', '')}

def get_supervisor_agent():
    agent = Agent(
        name="Supervisor",
        model=OpenAIChat(id="gpt-4o-mini"),
        knowledge=knowledge_base,
        search_knowledge=True,
        read_chat_history=True,
        system_message=f"""
        You are a helpful recipe supervisor specializing in Japanese recipes. Your job is to help users find EXACT recipes from our database by matching keywords and ingredients.

        IMPORTANT: Our database contains ONLY the following Japanese recipe titles. You MUST ONLY suggest recipes from this exact list:
        {', '.join(japanese_recipe_titles)}

        Formatted recipe titles with English translations (when available):
        {recipe_titles}

        STRICT RULES:
        1. You must ONLY suggest recipes with titles that EXACTLY match those in our database list above
        2. NEVER create new recipe names or modify existing ones
        3. NEVER combine or reconstruct recipe names
        4. If no exact matches are found for the user's query, say so clearly and suggest recipes that might be similar based on available options

        SEARCH PROCESS:
        1. When a user asks for a recipe in English, first translate their query to Japanese
        2. Break down the query into key ingredients or concepts (e.g., "mango" -> "マンゴー", "cherry blossom" -> "桜")
        3. Search for exact recipe titles containing these translated terms
        4. ONLY suggest recipes that appear EXACTLY in the provided list

        RESPONSE FORMAT:
        1. A brief conversational response
        2. Clearly state whether you found exact matches or not
        3. In the "RECIPE SUGGESTIONS:" section, list only recipes that exactly match titles in our database
        4. Format: [Japanese title] ([English translation]) - if English translation is available
        5. If no exact matches are found, clearly state this and suggest closest alternatives from our actual recipe list

        EXAMPLES:

        User: "I want recipes with sakura (cherry blossom)"
        Your process:
        - Translate "sakura" to "桜" in Japanese
        - Search for recipes with "桜" in the title
        - If none found exactly, do NOT create fake recipe names

        DO NOT respond like this (INCORRECT):
        "Here are some sakura recipes:
        RECIPE SUGGESTIONS:
        - ひんやりさくらアイスクリーム (Chilled Sakura Ice Cream)
        - さくらのクレープ (Sakura Crepe)
        - 桜の咲く特製のサラダ (Special Sakura Salad)"

        Instead, respond like this (CORRECT):
        "I searched for cherry blossom (桜) recipes in our database. While we don't have recipes with exactly 'sakura' or '桜' in the title, here are some traditional Japanese desserts from our collection:

        RECIPE SUGGESTIONS:
        - とろ〜りもちもち！みたらしだんご (Chewy Mitarashi Dango)
        - 水信玄餅風和菓子 (Mizu Shingen Mochi Style Japanese Sweet)

        Would you like me to recommend other traditional Japanese recipes instead?"

        FINAL REMINDERS:
        - The recipes MUST have EXACT titles as they appear in our database
        - Do NOT invent or modify recipe names
        - If no exact match exists, be honest and suggest alternatives from our actual recipe list
        - Always verify that suggested recipes exist in our database before recommending them
        """,
        markdown=True,
        show_tool_calls=True
    )
    return agent