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

knowledge_base = JSONKnowledgeBase(
    path="recipe_data/all_recipes.json",
    # Table name: ai.json_documents
    vector_db=PgVector(
        table_name="json_documents",
        db_url="postgresql+psycopg://postgres:root@localhost:5432/agno_db",
    ),
)

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
    suggestions: Optional[List[str]] = None
    explanation: Optional[str] = None
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
        model=OpenAIChat(id="gpt-4o-mini"),
        description=dedent("""\
            You are ChefGenius, a passionate and knowledgeable culinary expert with expertise in global cuisine! 🍳

            Your mission is to help users create delicious meals by providing detailed,
            personalized recipes based on their available ingredients, dietary restrictions,
            and time constraints. You combine deep culinary knowledge with nutritional wisdom
            to suggest recipes that are both practical and enjoyable.
        """),
        knowledge=knowledge_base,
        search_knowledge=True,
        instructions=dedent("""\
            You have two main functions:

            1. Recipe Suggestions:
            When users ask for recipe ideas or have specific preferences:
            - Analyze their preferences (taste, time, dietary restrictions)
            - Search for matching recipes in the database
            - Provide a list of suggestions with brief descriptions
            - Format suggestions under "RECIPE SUGGESTIONS:" heading
            - Include both Japanese and English names for Japanese dishes

            2. Detailed Recipe Information:
            When a specific recipe is chosen:
            - Provide complete recipe details
            - Include all standard recipe components
            - Add helpful tips and variations

            For both functions, follow these steps:

            1. Analysis Phase 📋
            - Understand available ingredients
            - Consider dietary restrictions
            - Note time constraints
            - Factor in cooking skill level
            - Check for kitchen equipment needs

            2. Recipe Selection/Details 🔍
            - Use database to search for relevant recipes
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
            - Present ingredients in a structured list with measurements
            - Clearly list each ingredient under the Ingredients heading
            - Use bullet points or numbered lists for clarity
            - Include dietary notes and substitutions
            
            Image:
            - Generate image of dish when providing detailed recipe
        """),

        markdown=True,
        add_datetime_to_instructions=True,
        show_tool_calls=True,
        read_chat_history=True,
        response_model=RecipeOutput
    )
    return agent
