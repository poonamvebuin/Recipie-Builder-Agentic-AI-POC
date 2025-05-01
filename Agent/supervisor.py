# supervisor.py

from agno.agent import Agent
from agno.team.team import Team
from pydantic import BaseModel
from typing import Dict, List
import json
from agno.knowledge.json import JSONKnowledgeBase
from agno.vectordb.pgvector import PgVector
from agno.models.openai import OpenAIChat
from deep_translator import GoogleTranslator
import os
from dotenv import load_dotenv
from difflib import get_close_matches
import re
import json
import streamlit as st

db_host = st.secrets["database"]["host"]
db_user = st.secrets["database"]["user"]
db_password = st.secrets["database"]["password"]
db_name = st.secrets["database"]["dbname"]
port = st.secrets["database"]["port"]

load_dotenv()

db_url = f"postgresql+psycopg://{db_user}:{db_password}@{db_host}:{port}/{db_name}"
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


# Load the actual recipe data to ensure we have exact recipe titles
def load_recipe_data(json_path="recipe_data/all_recipes.json"):
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        # print("DATA+++++",data)
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

def get_suggested_titles_with_reviews(titles, recipe_data_override=None):
    all_recipes = recipe_data_override if recipe_data_override is not None else recipe_data

    reviewed = []
    all_dataset_titles = [doc.get("title", "") for doc in all_recipes if doc.get("title")]

    for title in titles:
        japanese_title = re.sub(r'^[-\s]*japanese_title\s*-\s*', '', title).replace('-', '').strip()
        japanese_title = re.sub(r'\s*\(.*?\)', '', japanese_title).strip()

        best_match = get_close_matches(japanese_title, all_dataset_titles, n=1, cutoff=0.6)
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
                all_comments = [item.get("comment", "") for item in data["reviews"]["items"] if item.get("comment")]
                print('-------------------all_comments', all_comments)
            reviewed.append({
                "title": title,
                "japanese_name": data.get("title"),
                "average_rating": data["rating"]["average"],
                "total_reviews": data["rating"].get("count", 0),
                "all_comments": all_comments
            })

    reviewed.sort(key=lambda r: r["average_rating"], reverse=True)
    return reviewed[:2]

def get_supervisor_agent():
    agent = Agent(
        name="SupervisorAgent",
        model=OpenAIChat(id="gpt-4o-mini"),
        knowledge=knowledge_base,
        search_knowledge=True,
        read_chat_history=True,
        system_message=f"""
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

                        ---
                        📌 RESPONSE BEHAVIOR:

                        ▶ If the user ASKS FOR RECIPES:
                        - Translate keywords into Japanese if needed.
                        - Search for EXACT matches in titles.
                        - If no match, say so clearly and suggest 5 closest titles from the official list.
                        - Format:

                        RECIPE SUGGESTIONS:
                        -  Recommended Dish: [Japanese title] (English translation)
                        -  Recommended Dish: [Japanese title]
                        - ...

                        ▶ If the user ASKS FOR REVIEWS or ASKS “What do people like most?”:
                        - ONLY use the 5 recipes you suggested previously.
                        - DO NOT suggest new recipes.
                        - From those 5, select 1-2 top-rated dishes from review data
                        - IF REVIEW NOT GIVEN THEN NOT SUGGEST

                        - Include:
                        - Japanese name (and English translation if available)
                        - Average rating and total reviews
                        - One user review

                        - Format:

                        RECIPE SUGGESTIONS:
                        DO NOT BOLD THIS SECTION
                        ---
                        Recommended Dish: [Japanese name] (English name)  
                        Rating: ★★★★★ X.X (based on Y reviews)  
                        What people say: “Sample user comment”
                        ---

                        ---
                        📌 IMPORTANT:
                        - NEVER mix recipe suggestions and reviews in the same response.
                        - When reviewing, only analyze recipes that were part of the last recipe suggestion list.
                        - Be honest if no review data is available for a dish.

                        ---
                        📌 FINAL NOTES:
                        - Recipe suggestions must come ONLY from this list:
                        {', '.join(japanese_recipe_titles)}

                        - Review quotes must be taken from actual data
        """,
        markdown=True,
        show_tool_calls=True
    )
    return agent
