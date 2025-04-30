import json
from uuid import uuid4

from agno.agent import Agent
from agno.knowledge.json import JSONKnowledgeBase
from agno.models.openai import OpenAIChat
from agno.storage.postgres import PostgresStorage
import os
from typing import Dict

from agno.vectordb.pgvector import PgVector
from dotenv import load_dotenv
from agno.models.message import Message
from agno.run.response import RunResponse, RunEvent
from agno.memory.agent import AgentRun, AgentMemory
from agno.memory.v2.memory import Memory

load_dotenv()

class RecipeChatAgent:
    def __init__(self, language: str):
        self.language = language
        self.db_url = f"postgresql+psycopg://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('PORT')}/{os.getenv('DB_NAME')}"

        self.recipe_data = self._load_recipe_data()
        self.recipe_titles = self._extract_recipe_titles(self.recipe_data)
        self.japanese_recipe_titles = {recipe.get('title', '') for recipe in self.recipe_data if recipe.get('title', '')}
        
        self.storage = PostgresStorage(
        table_name="agent_sessions",
        db_url=self.db_url,
        auto_upgrade_schema=True)

        self.knowledge_base = JSONKnowledgeBase(
        path="recipe_data/all_recipes.json",
        vector_db=PgVector(
            table_name="json_documents",
            db_url=self.db_url
        ),
        )
        self.knowledge_base.load(recreate=False)
    def _load_recipe_data(self,json_path="recipe_data/all_recipes.json"):
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            return data
        except Exception as e:
            print(f"Error loading recipe data: {e}")
            return []
    
    def _extract_recipe_titles(self,recipe_data):
        titles_with_translations = []

        for recipe in recipe_data:
            japanese_title = recipe.get('title', '')
            english_name = recipe.get('english_name', '')

            if japanese_title:
                formatted_title = f"{japanese_title}" + (f" ({english_name})" if english_name else "")
                titles_with_translations.append(formatted_title)

        return titles_with_translations
    
    def _update_memory(self,agent,welcome_msg):
        welcome_message_obj = Message(
            role=agent.model.assistant_message_role if agent.model else "assistant",
            content=welcome_msg
        )

        if isinstance(agent.memory, AgentMemory):
            agent.memory.add_run(
                AgentRun(
                    response=RunResponse(
                        content=welcome_msg,
                        session_id=agent.session_id,
                        agent_id=agent.agent_id,
                        event=RunEvent.run_response,
                        messages=[welcome_message_obj]
                    ),
                    message=welcome_message_obj
                )
            )
        elif isinstance(agent.memory, Memory):
            agent.memory.add_run(
                session_id=agent.session_id,
                run=RunResponse(
                    content=welcome_msg,
                    session_id=agent.session_id,
                    agent_id=agent.agent_id,
                    event=RunEvent.run_response,
                    messages=[welcome_message_obj]
                )
            )
        else:
            raise Exception("Unknown memory type for agent")

        agent.write_to_storage(session_id=agent.session_id)
        return agent
        
    def create_agent(self) -> Agent:
        agent = Agent(
            name="Supervisor",
            model=OpenAIChat(id="gpt-4o-mini"),
            knowledge=self.knowledge_base,
            search_knowledge=True,
            read_chat_history=True,
            storage=self.storage,
            introduction=f"""
            You are a helpful recipe supervisor specializing in Japanese recipes. Your job is to help users find EXACT recipes from our database by matching keywords and ingredients.

            IMPORTANT: 
            - Our database contains ONLY the following Japanese recipe titles. You MUST ONLY suggest recipes from this exact list:
            {', '.join(self.japanese_recipe_titles)}
            - Formatted recipe titles with English translations (when available):
            {self.recipe_titles}
            - ALWAY SUGGEST 5 RECIPES

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
        agent.agent_session = None
        agent.session_id = str(uuid4())
        if agent.model:
            agent.model.clear()
        if agent.memory is None:
            agent.initialize_agent()

        welcome_msg = self.get_welcome_message(self.language)["message"]
       
        agent=self._update_memory(agent,welcome_msg)
        return agent

    def get_welcome_message(self,language: str) -> Dict:
        """Get welcome message based on language preference"""
        
        if language.lower() == 'english':
            return {
                "message": "I'm here to help you discover the perfect recipes or find exactly what you need for your kitchen. Let's start creating something delicious together! 😄",
                "options": ["Recipe Creation", "Product Finder"],
                "option_message": [
                    "Want to create a custom dish? Tell me your taste, time, and ingredients, and I'll suggest recipes that fit your vibe! Whether you're in the mood for something sweet, savory, or spicy, I've got you covered. Let's get cooking! ",
                    "Looking for ingredients or kitchen products? I can help you find exactly what you need. Just tell me what you have in mind or upload your list, and I'll search for the best products available! Add them to your cart and shop with ease. "
                ]
            }
        elif language.lower() == 'japanese':
            return {
                "message": "私は、完璧なレシピを見つけるお手伝いや、キッチンに必要なものを見つけるお手伝いをします。一緒においしいものを作り始めましょう！😄",
                "options": ["レシピ作成", "製品探し"],
                "option_message": [
                    "カスタム料理を作りたいですか？あなたの味、時間、そして材料を教えてくれれば、それにぴったりのレシピを提案します！甘いもの、塩辛いもの、辛いもの、どれを作りたい気分でもお任せください。さあ、料理を始めましょう！",
                    "材料やキッチン用品を探していますか？欲しいものを教えてくれれば、最適な製品を見つけます！リストをアップロードするか、思いついたものを言ってください。見つけた製品をカートに追加して、簡単にお買い物ができます！"
                ]
            }
        else:
            return {
                "message": "Welcome to the Recipe Assistant! Please choose a supported language.",
                "options": ["English", "Japanese"],
                "option_message": ["Switch to English", "Switch to Japanese"]
            }


    