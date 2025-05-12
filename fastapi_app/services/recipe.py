from datetime import time
import json
import re
from textwrap import dedent
from uuid import uuid4
from fastapi_app.common.schema import Nutrient, RecipeOutput
from agno.agent import Agent
from agno.knowledge.json import JSONKnowledgeBase
from agno.models.openai import OpenAIChat
from agno.storage.postgres import PostgresStorage
import os
from typing import Dict, Any, Iterator

from dotenv import load_dotenv
from agno.agent import Agent, RunResponse


load_dotenv()

class RecipeDetailsAgent:
    def __init__(self, language: str):
        self.language = language
        self.db_url = f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"

        self.recipe_data = self._load_recipe_data()
        
        self.storage = PostgresStorage(
        table_name="agent_sessions",
        db_url=self.db_url,
        auto_upgrade_schema=True)

        self.agent=Agent(
        name="Recipe Agent",
        model=OpenAIChat(id="gpt-4o-mini"),
        system_message=dedent(
            f"""
            Your task is to provide the recipe details in the language specified by the user.
            IMPORTANT:
            - Translate the recipe into the language provided by the user.
            - Maintain the original meaning and context of the recipe.
            - If the recipe is in a different language than translate it accordingly.
            - Change the serving size and quantity of the ingredients only when specified in the prompt and not from the past conversations.
            - If user prompts recipe for any specifc serving or like for people of 2 or a group then make chnages in both ingredients quantity and serving size proportionally. 
            - the serving size and ingredients quantity both must change never change only one of them on your own. If not specified take as it is from the database.
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
        response_model=RecipeOutput,)
    
    def _stream_response_chunks(response_iterator: Iterator[RunResponse]):
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


    def _clean_recipe_name(recipe_text):
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

    def _load_recipe_data(self,json_path="recipe_data/all_recipes.json"):
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
    
    def search_for_recipe_exact(self,title: str):
        """Search for a recipe by its exact title.

        This function loads recipe data and searches for a recipe that matches the given title exactly. If found, it processes the recipe's steps, ingredients, and other relevant information, returning a structured dictionary with the recipe details.

        Args:
            title (str): The exact title of the recipe to search for.

        Returns:
            dict or None: A dictionary containing the recipe details such as title, cuisine type, total time, ingredients, instructions, serving size, image URL, MP4 URL, nutrients, and optional fields like difficulty level, extra features, suggestions, and explanation. Returns None if no matching recipe is found.
        """

        recipe_data = self.recipe_data
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
                    "ingredients": [ingredient["name"]+str(ingredient.get("quantity")) for ingredient in recipe.get("ingredients", [])],
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

    def get_recipe(self,session_id, data):
        # Retrieve the recipe data from the database
        selected_recipes=data.selected_recipes
        text = ""
        if data.preferences:
            if data.preferences.taste:
                text += f" - Taste must be {data.preferences.taste}"
            if data.preferences.cooking_time:
                text += f" - Cooking Time must be {data.preferences.cooking_time}"
            if data.preferences.ingredients:
                text += f" - Ingredients to include: {', '.join(data.preferences.ingredients) if data.preferences.ingredients else 'No specific ingredients'}"
            if data.preferences.allergy_or_ingredient_to_avoid:
                text += f"""- MOST IMPORTANT: Recipe which don't have mentioned Allergies: Allergies/Avoid: {', '.join(data.preferences.allergy_or_ingredient_to_avoid) if data.preferences.allergy_or_ingredient_to_avoid else 'None specified'}"""
            if data.preferences.dietry:
                text += f" - Diet must be {data.preferences.dietry}."
        cleaned_dish_name = re.sub(
            r"\s*\(.*?\)", "", selected_recipes
        )
        print(text)
        cleaned_dish_name = re.sub(r"^\s*-*\s*", "", cleaned_dish_name)
        recipe_from_json = self.search_for_recipe_exact(cleaned_dish_name)
        if recipe_from_json:
            raw_japanese_ingredients = recipe_from_json.get("ingredients", [])
            prompt = (
                f"Please translate the following recipe into {self.language}:\n\n"
                f"{text}\n\n"
                f"Recipe: {recipe_from_json}\n\n"
                # f"Adjust the ingredients, times and quantities proportionally to match for given {self.conversation_history} servings. "
                f"Ensure that all quantities are modified proportionally "
                f"Do not omit any important details in the translation."
            )
            run_response: Iterator[RunResponse] = self.agent.run(
                prompt, stream=True
            )
            recipe = run_response.content   
            return recipe
    