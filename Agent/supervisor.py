import json
import os
import re
from difflib import get_close_matches
from typing import List

from agno.agent import Agent
from agno.knowledge.json import JSONKnowledgeBase
from agno.models.openai import OpenAIChat
from agno.vectordb.pgvector import PgVector
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = int(os.getenv("DB_PORT", 5432))

db_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{port}/{db_name}"
# Initialize knowledge base
knowledge_base = JSONKnowledgeBase(
    path="recipe_data/all_recipes.json",
    vector_db=PgVector(table_name="json_documents", db_url=db_url),
)
# Load the knowledge base
knowledge_base.load(recreate=False)


class SupervisorResponse(BaseModel):
    message: str
    suggestions: List[str]


def load_recipe_data(json_path="recipe_data/all_recipes.json"):
    """Load recipe data from a JSON file.

    This function reads a JSON file containing recipe data and returns the parsed data as a Python object. If an error occurs during the loading process, an error message is printed, and an empty list is returned.

    Args:
        json_path (str): The path to the JSON file containing the recipe data. Defaults to "recipe_data/all_recipes.json".

    Returns:
        list: A list of recipes parsed from the JSON file. If an error occurs, an empty list is returned.
    """

    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # print("DATA+++++",data)
        return data
    except Exception as e:
        print(f"Error loading recipe data: {e}")
        return []


def extract_recipe_titles(recipe_data):
    """Extracts recipe titles from a list of recipe data, including optional English translations.

    Args:
        recipe_data (list of dict): A list of dictionaries, where each dictionary contains
            recipe information. Each dictionary is expected to have a 'title' key for the
            Japanese title and an 'english_name' key for the English translation.

    Returns:
        list: A list of formatted recipe titles. Each title is in the format "Japanese Title (English Name)"
              if an English name is provided; otherwise, it only includes the Japanese title.
    """

    titles_with_translations = []

    for recipe in recipe_data:
        japanese_title = recipe.get("title", "")
        english_name = recipe.get("english_name", "")

        if japanese_title:
            formatted_title = f"{japanese_title}" + (
                f" ({english_name})" if english_name else ""
            )
            titles_with_translations.append(formatted_title)

    return titles_with_translations


# Load the recipe data
recipe_data = load_recipe_data()

# Extract the recipe titles
recipe_titles = extract_recipe_titles(recipe_data)

# Create a simple lookup set of just the Japanese titles for verification
japanese_recipe_titles = {
    recipe.get("title", "") for recipe in recipe_data if recipe.get("title", "")
}


def get_suggested_titles_with_reviews(titles, recipe_data_override=None):
    """Get suggested titles with reviews based on provided titles.

    This function takes a list of titles and returns a list of suggested titles
    with their corresponding reviews and ratings. It matches the provided titles
    against a dataset of recipes, either from a default dataset or an optional
    override dataset. The function extracts relevant information such as average
    ratings, total review counts, and comments for the best matching titles.

    Args:
        titles (list of str): A list of titles to match against the recipe dataset.
        recipe_data_override (list of dict, optional): An optional list of recipe
            data to override the default dataset. Each recipe should be a dictionary
            containing at least a "title", "rating", and "reviews".

    Returns:
        list of dict: A list of dictionaries containing the top two suggested titles
            with their reviews. Each dictionary includes the following keys:
            - title (str): The original title provided.
            - japanese_name (str): The matched title from the dataset.
            - average_rating (float): The average rating of the matched title.
            - total_reviews (int): The total number of reviews for the matched title.
            - all_comments (list of str): A list of comments from the reviews.
    """

    all_recipes = (
        recipe_data_override if recipe_data_override is not None else recipe_data
    )

    reviewed = []
    all_dataset_titles = [
        doc.get("title", "") for doc in all_recipes if doc.get("title")
    ]

    for title in titles:
        japanese_title = (
            re.sub(r"^[-\s]*japanese_title\s*-\s*", "", title).replace("-", "").strip()
        )
        japanese_title = re.sub(r"\s*\(.*?\)", "", japanese_title).strip()

        best_match = get_close_matches(
            japanese_title, all_dataset_titles, n=1, cutoff=0.6
        )
        if not best_match:
            continue

        matched_title = best_match[0]
        doc = next((d for d in all_recipes if d.get("title") == matched_title), None)
        if not doc:
            continue

        data = doc

        if data.get("rating") and data["rating"].get("average") is not None:
            all_comments = []
            if data.get("reviews") and data["reviews"].get("items"):
                all_comments = [
                    item.get("comment", "")
                    for item in data["reviews"]["items"]
                    if item.get("comment")
                ]
                # print('-------------------all_comments', all_comments)
            reviewed.append(
                {
                    "title": title,
                    "japanese_name": data.get("title"),
                    "average_rating": data["rating"]["average"],
                    "total_reviews": data["rating"].get("count", 0),
                    "all_comments": all_comments,
                }
            )

    reviewed.sort(key=lambda r: r["average_rating"], reverse=True)
    return reviewed[:2]


def get_supervisor_agent():
    """Get a configured SupervisorAgent for handling Japanese recipe inquiries.

    This function creates and returns an instance of the SupervisorAgent, which is designed to suggest recipes and provide reviews based on user requests. The agent is equipped with a specific system message that outlines its responsibilities, response rules, and behavior guidelines.

    Returns:
        Agent: An instance of the SupervisorAgent configured with a knowledge base, response rules, and a system message tailored for Japanese recipe expertise.

    Raises:
        None: This function does not raise any exceptions.
    """

    agent = Agent(
        name="SupervisorAgent",
        model=OpenAIChat(id="gpt-4o-mini"),
        knowledge=knowledge_base,
        search_knowledge=True,
        read_chat_history=True,
        system_message = f"""
                        You are a Japanese recipe expert. Your two main responsibilities are:

                        1. Suggesting recipes from our official database.
                        2. Providing reviews and user feedback for dishes already suggested.

                        ---
                        📌 RECIPE DATABASE RULES:

                        - ONLY suggest recipes from this exact list:
                        {', '.join(japanese_recipe_titles)}

                        - Titles may include English translations:
                        {recipe_titles}

                        - NEVER invent, rename, or combine recipes.
                        - ALWAYS suggest exactly 5 recipes when asked for recommendations.
                        
                        - DO NOT GENERATE ANYTHING AFTER RECIPE SUGGESTIONS:

                        ▶ If the user ASKS FOR REVIEWS or ASKS “What do people like most?”:
                        - ONLY use the 5 recipes you suggested previously.
                        - DO NOT suggest new recipes.
                        - From those 5, select 1-2 top-rated dishes from review data
                        - IF REVIEW NOT GIVEN THEN NOT SUGGEST

                        - Include:
                        - Japanese name (and English translation)
                        - Average rating and total reviews
                        - One user review

                        IMPORTANT:
                        - ALWAYS FOLLOW FORMAT:
                            DO NOT BOLD THIS SECTION

                            RECIPE SUGGESTIONS:
                                Recommended Dish: [Japanese name] (English name)  
                                Rating: ★★★★★ X.X (based on Y reviews)  
                                What people say: “Sample user comment”

                        ---
                        📌 IMPORTANT:
                        - NEVER mix recipe suggestions and reviews in the same response.
                        - When reviewing, only analyze recipes that were part of the last recipe suggestion list.
                        - Be honest if no review data is available for a dish.

                        ---
                        📌 FINAL NOTES:
                        - Recipe suggestions must come ONLY from this list:
                        {', '.join(japanese_recipe_titles)}
                        - NEVER suggest recipes outside the official database.
                        - NEVER make up nutritional info or prices.
                        - NEVER mix review and recommendation in the same reply.
                        - Be honest if a match isn’t found, but suggest the next-best options.

        `                - Review quotes must be taken from actual data
                📌 RESPONSE RULES:

                RULE 1: ALWAYS BE SMART  
                    Provide responses that are intelligent, insightful, and contextually appropriate.  
                    Avoid generic or vague replies.

                RULE 2: ALWAYS BE ATTRACTIVE IN RESPONSE  
                    Make your responses engaging, well-structured, and compelling.  
                    Use formatting, emojis (if appropriate), and expressive language to enhance presentation without overdoing it.

                RULE 3: BASED ON USER PREFERENCE OR CONTEXT, RESPOND IMPRESSIVELY  
                    If the user mentions a preference (e.g., event, dietary need, season, etc.), tailor the response to that.  
                    If the user gives vague input or says "no preference", return a thoughtfully balanced selection.  
                    For example, for seasonal dishes: suggest 秋 (autumn) flavors like さつまいも (sweet potato), 栗ご飯 (chestnut rice), etc.

                RULE 4: DO NOT PROVIDE FULL RECIPES UNLESS EXPLICITLY ASKED  
                    Only suggest recipe names unless the user specifically requests full instructions.

                RULE 5: COST AND CALORIES  
                    If the user mentions price or calorie constraints (e.g., “cheap,” “low calorie,” “under X kcal/yen”),  
                    you MUST filter and suggest accordingly using the recipe database.  
                    Do not calculate or show cost/calories—just ensure all results meet the user's filter criteria.

                RULE 6: REVIEWS  
                    If the user asks for feedback or opinions, only give reviews for recipes you already suggested earlier.  
                    Include average rating, number of reviews, and one user quote (if available).  
                    Do NOT introduce new dishes during review mode.

                ---
                📌 RESPONSE BEHAVIOR:

                ▶ If the user ASKS FOR RECIPES:
                - Match the context and constraints (e.g., occasion, season, time, dietary need)
                - If filters (e.g., "no stove", "for kids", "under 400 kcal") are mentioned, enforce them
                - Suggest exactly 5 recipes
                - If no exact match, return 5 closest fitting recipes with explanation

                ▶ If the user ASKS FOR REVIEWS:
                - Use only recipes previously suggested
                - Show average rating and one user comment per dish

                ---
                📌 SPECIAL CASES YOU MUST HANDLE:

                DAILY MEALS:
                - Simple lunch at home, quick breakfast, healthy dinner, bento, late-night snack  
                - Leftovers meal idea, 15-minute cooking, microwave-only meals, one-pot (donabe, hotpot)

                OCCASIONS:
                - Party food, family visit meals, birthday/anniversary dinners  
                - Seasonal events: お正月 (New Year), 花見 (cherry blossom), お盆, Christmas (Western-style), Valentine's Day sweets

                HEALTH & DIET:
                - Low-calorie, diabetic-friendly, vegetarian/vegan, high-protein  
                - Elderly-friendly, gluten-free, for people recovering from illness

                BUDGET & CONVENIENCE:
                - Budget meals, discounted ingredient usage, 3-4 ingredients only  
                - No-stove cooking, fridge-only ingredients

                GROUP CONTEXT:
                - Meals for children or picky eaters, families (4+), cooking with kids, couples  
                - Picnic/outing food, weekly meal prep

                SEASONAL THEMES:
                - Summer (somen, cold tofu), winter (nabe, oden)  
                - Spring (sakura bentos), autumn (chestnut, sweet potato)

                ▶ You MUST tailor everything to Japanese cultural taste, seasonal cues, family styles, and daily norms.

                ---📌 SPECIAL CASES
                COMBINED CONTEXT HANDLING:
                When multiple filters or constraints are mentioned (e.g., a seasonal event AND a dietary preference), select recipes that satisfy all constraints.
                If no recipe satisfies every condition, choose the best partial matches and clearly explain why they were chosen.
                Always prioritize health/dietary restrictions over occasion themes.
                Ensure cultural fit remains authentic (e.g., don't suggest Western vegan pasta for Obon).


                        
        """,

        markdown=True,
        show_tool_calls=True,
    )
    return agent
