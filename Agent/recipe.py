from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.postgres import PostgresStorage
from textwrap import dedent
import os
from dotenv import load_dotenv

load_dotenv()

from agno.knowledge.json import JSONKnowledgeBase
from agno.vectordb.pgvector import PgVector

db_url = f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"

# Initialize knowledge base and vector database
knowledge_base = JSONKnowledgeBase(
    path="recipe_data/all_recipes.json",
    vector_db=PgVector(
        table_name="json_documents",
        db_url = db_url
        
    ),
)

# Define VideoSource and VideoData models if needed, omitted for brevity

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
    suggestions: Optional[List[str]] = None
    explanation: Optional[str] = None


import json

def load_recipe_data(json_path="recipe_data/all_recipes.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading recipe data: {e}")
        return []


def search_for_recipe_exact(title: str):

    recipe_data = load_recipe_data()  
    # print('-------------recipe_data', recipe_data)  
    for recipe in recipe_data:
        # print('-------------recipe', recipe) 
        if recipe.get('title', '') == title:
        
        
            result = {
                "recipe_title": recipe.get("title", ""),
                "cuisine_type": recipe.get("source", None),  
                "prep_time": recipe.get("cooking_time", {}).get("value", None),
                "cook_time": recipe.get("cooking_time", {}).get("value", None),
                "total_time": recipe.get("cooking_time", {}).get("value", None),
                "ingredients": "\n".join([ingredient['name'] for ingredient in recipe.get("ingredients", [])]),
                "instructions": recipe.get("steps", []),
                "serving_size": recipe.get("servings", {}).get("value", None),
                "image_url": recipe.get("image_url", None),
            }
            
            
            if recipe.get("nutritional_info"):
                result["nutritional_info"] = recipe.get("nutritional_info")
            
            if recipe.get("difficulty_level"):
                result["difficulty_level"] = recipe.get("difficulty_level")
            
            if recipe.get("storage_instructions"):
                result["storage_instructions"] = recipe.get("storage_instructions")
            
            if recipe.get("extra_features"):
                result["extra_features"] = recipe.get("extra_features")
            
            if recipe.get("suggestions"):
                result["suggestions"] = recipe.get("suggestions")
            
            if recipe.get("explanation"):
                result["explanation"] = recipe.get("explanation")
            
            return result
        
    return None

# Function to create the agent
# def get_agent():
#     db_url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
#              f"{os.getenv('DB_HOST')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"
#     storage = PostgresStorage(
#         table_name="agent_sessions",
#         db_url=db_url,
#         auto_upgrade_schema=True
#     )

#     agent = Agent(
#         name="Recipe Agent",
#         model=OpenAIChat(id="gpt-4o-mini"),
#         system_message=dedent("""
#             Your task is to find an exact match for the recipe using its Japanese title in the knowledge base.
#             If found, return the recipe with the title, ingredients, and a brief set of instructions.
#             If no match is found, respond with: "Sorry, the recipe '[recipe_name]' was not found."
#         """),
#         knowledge=knowledge_base,
#         search_knowledge=True,
#         markdown=True,
#         add_datetime_to_instructions=True,
#         show_tool_calls=True,
#         read_chat_history=True,
#         response_model=RecipeOutput
#     )

#     # Integrating the custom search function into the agent
#     agent._search_recipe = search_for_recipe_exact  # Adding the search function to agent's workflow

#     return agent


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
        model=OpenAIChat(id="gpt-4o-mini"),
        system_message=dedent("""
            Your task is to output the recipe details exactly as provided in the input.
            IMPORTANT:
            - DO NOT TRANSLATE the recipe into any language. 
            - Maintain the original Japanese language of the recipe.
            - Ensure that the recipe is not rephrased, translated, or modified in any way except for minor adjustments based on the user's preferences (like serving size).
            - If any modifications are made, **keep the original language intact**.
            - Modify recipe based on people.
            - GIVE RESPONSE ONLY ONCE.
        """),
        search_knowledge=True, 
        markdown=True,
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        read_chat_history=True,
        response_model=RecipeOutput
    )
    return agent
