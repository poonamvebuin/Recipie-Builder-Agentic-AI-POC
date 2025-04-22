# supervisor.py

from agno.agent import Agent
from pydantic import BaseModel
from typing import Dict, List
import json
from agno.knowledge.json import JSONKnowledgeBase
from agno.vectordb.pgvector import PgVector
from agno.models.openai import OpenAIChat
from deep_translator import GoogleTranslator

# Initialize knowledge base
knowledge_base = JSONKnowledgeBase(
    path="recipe_data/all_recipes.json",
    vector_db=PgVector(
        table_name="json_documents",
        db_url="postgresql+psycopg://postgres:root@localhost:5432/agno_db",
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

def get_supervisor_agent():
    agent = Agent(
        name="Supervisor",
        model=OpenAIChat(id="gpt-4o-mini"),
        knowledge=knowledge_base,
        search_knowledge=True,
        read_chat_history=True,
        system_message=f"""
        You are a helpful recipe supervisor. Your job is to help users find recipes from our database by matching concepts and ingredients.

        KEY SEARCH FUNCTIONALITY:
        1. When a user asks for a type of dish (e.g., "sweet sushi"):
           - Perform semantic search on both "title" AND "description" fields
           - Break down the query into key components ("sweet" and "sushi")
           - Search for dishes that contain EITHER or BOTH components
           - Return actual recipe titles from the database that best match the concepts
        
        2. NEVER say "I couldn't find X in our database" unless you've thoroughly searched by:
           - Breaking down the query into components
           - Searching titles AND descriptions
           - Looking for partial matches
           - Checking for semantic equivalents

        SEARCH APPROACH:
        - For a query like "sweet sushi":
          1. Search for recipes with "sushi/寿司" in title
          2. From those results, prioritize any that mention "sweet/甘い" in description
          3. If none found, search for recipes with "sweet/甘い" in description that might be sushi-adjacent
        
        - Always prioritize recipes that match BOTH concepts, but return recipes that match at least ONE concept
        - Use both English AND Japanese terms when searching (sushi/寿司, sweet/甘い, etc.)

        RESPONSE FORMAT:
        Always format your responses as conversational text. When providing recipe suggestions,
        include "RECIPE SUGGESTIONS:" followed by each recipe title on a new line.

        When suggesting recipes:
        - List the EXACT recipe titles from the database
        - Format as: [Japanese title] ([English translation])
        - Include 3-5 suggestions maximum
        - Add a brief explanation of why each recipe might satisfy the user's query

        EXAMPLE CORRECT RESPONSES:
        
        User: "I want sweet sushi dishes"
        Response:
        "Here are some sushi recipes from our database that have sweet elements:

        RECIPE SUGGESTIONS:
        フルーツ寿司 (Fruit Sushi) - A sweet variation with fresh fruits on top of sushi rice
        いなり寿司 (Inari Sushi) - Sweet fried tofu pouches filled with sushi rice
        太巻き寿司 (Futomaki Sushi) - Contains sweet elements like egg and sometimes sweet sauce

        These recipes offer sweet flavor profiles while still being authentic sushi dishes."

        IMPORTANT: 
        - The recipe titles MUST exactly match those in the database
        - If user asks for a concept combination (like "sweet sushi"), return recipes that match both concepts if possible
        - If no recipes match both concepts, return recipes that match at least one concept
        - Never refuse to provide suggestions - always offer the closest matching recipes
        """,
        markdown=True,
        show_tool_calls=True
    )
    return agent