from typing import List, Optional, Dict, Any
from pydantic import BaseModel, ConfigDict
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.storage.postgres import PostgresStorage
from textwrap import dedent
import os
from dotenv import load_dotenv
import json
import re
import time
from typing import Iterator
from agno.agent import RunResponse
import streamlit as st

db_host = st.secrets["host"]
db_user = st.secrets["user"]
db_password = st.secrets["password"]
db_name = st.secrets["dbname"]
port = st.secrets["port"]

load_dotenv()

db_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{port}/{db_name}"


# Define VideoSource and VideoData models if needed, omitted for brevity

class RecipeOutput(BaseModel):
    recipe_title: str
    cuisine_type: Optional[str] = None
    cook_time: Optional[str] = None
    total_time: Optional[str] = None
    ingredients: Optional[str] = None
    instructions: Optional[List[str]] = None
    nutrients: Optional[Dict[str, str]] = None
    difficulty_level: Optional[str] = None
    serving_size: Optional[str] = None
    extra_features: Optional[Dict[str, str]] = None
    image_url: Optional[str] = None
    suggestions: Optional[List[str]] = None
    explanation: Optional[str] = None
    mp4_url: Optional[str] = None

# Function to stream assistant response using a generator
def stream_response_chunks(response_iterator: Iterator[RunResponse]):
    try:
        # Handle iterable response
        for chunk in response_iterator:
            yield chunk.content
            time.sleep(0.01)
    except TypeError:
        # Handle non-iterable response (single RunResponse object)
        if hasattr(response_iterator, 'content'):
            yield response_iterator.content


def clean_recipe_name(recipe_text):
    """Clean recipe text to remove URLs and other unwanted elements"""
    # Remove URLs (http://, https://, www.)
    recipe_text = re.sub(r'https?://\S+|www\.\S+', '', recipe_text)

    # Remove any text after a hyphen or dash if it looks like a description
    recipe_text = re.sub(r'\s+-\s+.*$', '', recipe_text)

    # Remove any text in square brackets that's not part of Japanese formatting
    if not any(ord(char) > 127 for char in recipe_text):  # If not Japanese
        recipe_text = re.sub(r'\[.*?\]', '', recipe_text)

    # Remove trailing punctuation and whitespace
    recipe_text = recipe_text.strip().rstrip('.,;:!?')

    return recipe_text.strip()

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
    for recipe in recipe_data:
        # print('-----search--------recipe', recipe) 
        # print('-----get-------title', recipe.get('title', ''))
        if recipe.get('title', '').strip() == title.strip():
            raw_steps = recipe.get("steps", [])
            processed_instructions = []
            if not raw_steps:
                processed_instructions = []
            elif isinstance(raw_steps[0], dict):
                for i, step in enumerate(raw_steps, 1):
                    desc = step.get("description", "")
                    processed_instructions.append(f"{i}. {desc}")
            
            else:
                for i, step in enumerate(raw_steps, 1):
                    clean_step = step
                    jp_numbers = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧", "⑨", "⑩"]
                    if step=="" or step=="\n":
                        break
                    if any(clean_step.startswith(jp_num) for jp_num in jp_numbers):
                        for j, jp_num in enumerate(jp_numbers, 1):
                            if clean_step.startswith(jp_num):
                                clean_step = clean_step[1:].strip()
                                break
                    elif (clean_step.strip() and 
                          (clean_step[0].isdigit() or 
                           clean_step.startswith("Step") or
                           clean_step[0] in "abcABC")):
                        for j, char in enumerate(clean_step):
                            if j > 0 and char in [".", ":", ")", "、", "．"] and clean_step[:j].strip().replace("Step", "").strip().isalnum():
                                clean_step = clean_step[j+1:].strip()
                                break

                    processed_instructions.append(f"{i}. {clean_step}")
            serving_size = None
            servings_info = recipe.get("servings", {})
            if 'value' in servings_info:
                serving_size = f"{servings_info.get('value')} {servings_info.get('unit', '')}".strip()
            if serving_size is None:
                serving_size = servings_info.get("raw_text", None)
            mp4_url = None
            poster_url=None
            # nutrients=None
            if recipe.get("source", None)=="delishkitchen":
                #image for delishikitchen
                try:
                    poster_url = recipe.get("video_data",{}).get("poster_url")
                except KeyError:
                    poster_url = None

                # video url extraction for mp4 video
                sources = recipe.get("video_data", {}).get("sources", [])
                
                for source in sources:
                    if source.get("type") == "video/mp4":
                        mp4_url = source.get("url")
                        break      
                # nutrients=recipe.get("nutrients",None) 
            else:
                poster_url = recipe.get("image_url", None)
            result = {
                "recipe_title": recipe.get("title", ""),
                "cuisine_type": recipe.get("source", None),  
                "total_time": recipe.get("cooking_time",None),
                "ingredients": "\n".join([ingredient['name'] for ingredient in recipe.get("ingredients", [])]),
                "instructions": processed_instructions,
                "serving_size": serving_size,
                "image_url":poster_url ,
                "mp4_url":mp4_url,
                "nutrients":recipe.get("nutrients",None) 
            }
                    
            if recipe.get("difficulty_level"):
                result["difficulty_level"] = recipe.get("difficulty_level")
            
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
    # db_url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@" \
    #          f"{os.getenv('DB_HOST')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"
    # storage = PostgresStorage(
    #     table_name="agent_sessions",
    #     db_url=db_url,
    #     auto_upgrade_schema=True
    # )

    agent = Agent(
        name="Recipe Agent",
        model=OpenAIChat(id="gpt-4o-mini"),
        system_message = dedent(f"""
            Your task is to provide the recipe details in the language specified by the user.
            IMPORTANT:
            - Translate the recipe into the language provided by the user.
            - Maintain the original meaning and context of the recipe.
            - If the recipe is in a different language than translate it accordingly.
            - Modify the recipe only if the number of people is more than the current servings. Adjust the ingredients, time, instructions proportionally.
            - When outputting the ingredients, ensure each ingredient appears on a **new line**.
            - If the ingredients contain line breaks (`\n`), maintain them and output each ingredient on a **separate line**.
        """),
        search_knowledge=True, 
        markdown=True,
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        read_chat_history=True,
        response_model=RecipeOutput
    )
    return agent
