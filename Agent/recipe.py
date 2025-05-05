import json
import os
import re
import time
from textwrap import dedent
from typing import Dict, Iterator, List, Optional

import streamlit as st
from agno.agent import Agent, RunResponse
from agno.models.openai import OpenAIChat
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT", 5432))

db_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{port}/{db_name}"


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


def stream_response_chunks(response_iterator: Iterator[RunResponse]):
    """Streams response chunks from a given iterator.

    This function takes an iterator of `RunResponse` objects and yields the content of each chunk. If a `TypeError` occurs, it checks if the iterator has a `content` attribute and yields that instead.

    Args:
        response_iterator (Iterator[RunResponse]): An iterator that yields `RunResponse` objects.

    Yields:
        Any: The content of each `RunResponse` chunk or the content attribute if a TypeError occurs.

    Raises:
        TypeError: If the provided iterator is not of the expected type and does not have a `content` attribute.
    """

    try:
        # Handle iterable response
        for chunk in response_iterator:
            yield chunk.content
            time.sleep(0.01)
    except TypeError:
        # Handle non-iterable response (single RunResponse object)
        if hasattr(response_iterator, "content"):
            yield response_iterator.content


def clean_recipe_name(recipe_text):
    """Clean the recipe name by removing URLs, unwanted text, and specific characters.

    This function processes the input recipe text to remove any URLs, trailing punctuation,
    and specific unwanted text patterns. If the recipe text does not contain Japanese characters,
    it also removes any text enclosed in square brackets.

    Args:
        recipe_text (str): The original recipe name to be cleaned.

    Returns:
        str: The cleaned recipe name with unwanted elements removed.
    """

    # Remove URLs (http://, https://, www.)
    recipe_text = re.sub(r"https?://\S+|www\.\S+", "", recipe_text)

    # Remove any text after a hyphen or dash if it looks like a description
    recipe_text = re.sub(r"\s+-\s+.*$", "", recipe_text)

    # Remove any text in square brackets that's not part of Japanese formatting
    if not any(ord(char) > 127 for char in recipe_text):  # If not Japanese
        recipe_text = re.sub(r"\[.*?\]", "", recipe_text)

    # Remove trailing punctuation and whitespace
    recipe_text = recipe_text.strip().rstrip(".,;:!?")

    return recipe_text.strip()


def load_recipe_data(json_path="recipe_data/all_recipes.json"):
    """Load recipe data from a JSON file.

    This function reads a JSON file containing recipe data and returns the parsed data as a Python object. If an error occurs during the loading process, an error message is printed, and an empty list is returned.

    Args:
        json_path (str): The path to the JSON file containing the recipe data. Defaults to "recipe_data/all_recipes.json".

    Returns:
        list: A list containing the recipe data if loaded successfully, or an empty list if an error occurs.
    """

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"Error loading recipe data: {e}")
        return []


def search_for_recipe_exact(title: str):
    """Search for a recipe by its exact title.

    This function loads recipe data and searches for a recipe that matches the given title exactly. If found, it processes the recipe's steps, ingredients, and other relevant information, returning a structured dictionary with the recipe details.

    Args:
        title (str): The exact title of the recipe to search for.

    Returns:
        dict or None: A dictionary containing the recipe details such as title, cuisine type, total time, ingredients, instructions, serving size, image URL, MP4 URL, nutrients, and optional fields like difficulty level, extra features, suggestions, and explanation. Returns None if no matching recipe is found.
    """

    recipe_data = load_recipe_data()
    for recipe in recipe_data:
        if recipe.get("title", "").strip() == title.strip():
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
                    if step == "" or step == "\n":
                        break
                    if any(clean_step.startswith(jp_num) for jp_num in jp_numbers):
                        for j, jp_num in enumerate(jp_numbers, 1):
                            if clean_step.startswith(jp_num):
                                clean_step = clean_step[1:].strip()
                                break
                    elif clean_step.strip() and (
                        clean_step[0].isdigit()
                        or clean_step.startswith("Step")
                        or clean_step[0] in "abcABC"
                    ):
                        for j, char in enumerate(clean_step):
                            if (
                                j > 0
                                and char in [".", ":", ")", "、", "．"]
                                and clean_step[:j]
                                .strip()
                                .replace("Step", "")
                                .strip()
                                .isalnum()
                            ):
                                clean_step = clean_step[j + 1 :].strip()
                                break

                    processed_instructions.append(f"{i}. {clean_step}")
            serving_size = None
            servings_info = recipe.get("servings", {})
            if "value" in servings_info:
                serving_size = f"{servings_info.get('value')} {servings_info.get('unit', '')}".strip()
            if serving_size is None:
                serving_size = servings_info.get("raw_text", None)
            mp4_url = None
            poster_url = None
            if recipe.get("source", None) == "delishkitchen":
                # image for delishikitchen
                try:
                    poster_url = recipe.get("video_data", {}).get("poster_url")
                except KeyError:
                    poster_url = None

                # video url extraction for mp4 video
                sources = recipe.get("video_data", {}).get("sources", [])

                for source in sources:
                    if source.get("type") == "video/mp4":
                        mp4_url = source.get("url")
                        break
            else:
                poster_url = recipe.get("image_url", None)
            nutrient_info = None
            if recipe.get("nutrients"):
                nutrient_info = []
                nutrients_raw = recipe.get("nutrients", {})
                if nutrients_raw:
                    for name, data in nutrients_raw.items():
                        nutrient_info.append(
                            {name: str(data["value"]) + str(data["unit"])}
                        )

            result = {
                "recipe_title": recipe.get("title", ""),
                "cuisine_type": recipe.get("source", None),
                "total_time": recipe.get("cooking_time", None),
                "ingredients": "\n".join(
                    [ingredient["name"] for ingredient in recipe.get("ingredients", [])]
                ),
                "instructions": processed_instructions,
                "serving_size": serving_size,
                "image_url": poster_url,
                "mp4_url": mp4_url,
                "nutrients": nutrient_info,
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


def get_agent():
    """Creates and returns an instance of the Recipe Agent.

    This agent is designed to provide recipe details in the language specified by the user. It includes functionality for translating recipes, adjusting ingredient quantities based on the number of servings, and formatting output appropriately.

    Returns:
        Agent: An instance of the Recipe Agent configured with specific parameters for recipe handling.

    Attributes:
        name (str): The name of the agent, set to "Recipe Agent".
        model (OpenAIChat): The model used for generating responses, specifically the GPT-4o-mini variant.
        system_message (str): Instructions for the agent detailing its responsibilities, including translation and formatting requirements.
        search_knowledge (bool): Indicates whether the agent can search for knowledge, set to True.
        markdown (bool): Indicates whether the agent supports markdown formatting, set to True.
        add_datetime_to_instructions (bool): Indicates whether to include the current date and time in instructions, set to True.
        show_tool_calls (bool): Indicates whether to display tool calls made by the agent, set to True.
        read_chat_history (bool): Indicates whether the agent can read previous chat history, set to True.
        response_model (type): The model used for structuring the response, set to RecipeOutput.
    """

    agent = Agent(
        name="Recipe Agent",
        model=OpenAIChat(id="gpt-4o-mini"),
        system_message=dedent(
            f"""
            Your task is to provide the recipe details in the language specified by the user.
            IMPORTANT:
            - Translate the recipe into the language provided by the user.
            - Maintain the original meaning and context of the recipe.
            - If the recipe is in a different language than translate it accordingly.
            - Modify the recipe only if the number of people is more than the current servings. Adjust the ingredients, time, instructions proportionally.
            - When outputting the ingredients, ensure each ingredient appears on a **new line**.
            - provide proper nutrients information in key value pair. Don't change any value from its data
            - If the ingredients contain line breaks (`\n`), maintain them and output each ingredient on a **separate line**.
        """
        ),
        search_knowledge=True,
        markdown=True,
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        read_chat_history=True,
        response_model=RecipeOutput,
    )
    return agent
