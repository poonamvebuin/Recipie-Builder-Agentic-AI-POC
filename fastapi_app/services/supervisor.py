import json
from uuid import uuid4

from agno.agent import Agent
from agno.knowledge.json import JSONKnowledgeBase
from agno.models.openai import OpenAIChat
from agno.storage.postgres import PostgresStorage
import os
from typing import Dict, Any

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
        # self.knowledge_base.load(recreate=False)
        self.agent = Agent(
            name="Supervisor",
            model=OpenAIChat(id="gpt-4o-mini"),
            knowledge=self.knowledge_base,
            search_knowledge=True,
            read_chat_history=True,
            storage=self.storage,
            system_message=f"""
                You are a Japanese recipe expert. Your two main responsibilities are:

                1. Suggesting recipes from our official database.
                2. Providing reviews and user feedback for dishes already suggested.

                ---
                📌 RECIPE DATABASE RULES:

                - ONLY suggest recipes from this exact list:
                {', '.join(self.japanese_recipe_titles)}

                - Titles may include English translations:
                {self.recipe_titles}

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
                - [Japanese title] (English translation)
                - [Japanese title]
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
                {', '.join(self.japanese_recipe_titles)}

                - Review quotes must be taken from actual data
            """,
            markdown=True,
            show_tool_calls=True
        )
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
        
    def create_chat(self) -> Agent:
        self.agent.agent_session = None
        self.agent.session_id = str(uuid4())
        if self.agent.model:
            self.agent.model.clear()
        if self.agent.memory is None:
            self.agent.initialize_agent()

        welcome_msg = self.get_welcome_message(self.language)["message"]
       
        agent=self._update_memory(self.agent,welcome_msg)
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

    def get_supervisor_prompt(self, preferences, prompt):
        is_review_request = any(
            keyword in prompt.lower()
            for keyword in ["what people like", "which one is best", "top rated", "reviews", "recommend best"]
        )
        print('----------is_review_request', is_review_request)
        if preferences:
            text = ""
            if preferences.taste:
                text += f" - Taste must be {preferences.taste}"
            if preferences.cooking_time:
                text += f" - Cooking Time must be {preferences.cooking_time}"
            if preferences.ingredients:
                text += f" - Ingredients to include: {', '.join(preferences.ingredients) if preferences.ingredients else 'No specific ingredients'}"
            if preferences.allergy_or_ingredient_to_avoid:
                text += f"""MOST IMPORTANT: Suggest Recipe which don't have mentioned Allergies
                        Allergies/Avoid: {', '.join(preferences.allergy_or_ingredient_to_avoid) if preferences.allergy_or_ingredient_to_avoid else 'None specified'}
                        """
            if preferences.dietry:
                text += f" - Diet must be {preferences.dietry}."
            # Include user preferences in the prompt
            preferences_text = f"""
                    IMPORTANT USER PREFERENCES:
                    {text}

                    Based on these preferences and the user's request: "{prompt}", suggest 5 suitable recipes.
                    Please ensure All the user preferences must be satisfied

                    IMPORTANT FORMATTING RULES:
                    1. Format your response as conversational text, followed by "RECIPE SUGGESTIONS:" 
                    2. List each recipe on a new line
                    3. For Japanese recipes, use format: "寿司 (Sushi)" - Japanese name first, then English in parentheses
                    4. ONLY include the recipe names - NO URLs, NO image links, NO descriptions, NO additional text
                    5. DO NOT use JSON format

                    Example correct format:
                    Here are some recipe suggestions based on your preferences.

                    RECIPE SUGGESTIONS:
                    寿司 (Sushi)
                    天ぷら (Tempura)
                    ラーメン (Ramen)
                    うどん (Udon)
                    そば (Soba)
                    """
            prompt = f"{preferences_text} IMPORTANT: Generate response in {self.language}"

        # if weather_data:
        #     prompt += f"""MUST ADD WEATHER DETAILS AND SUGGEST RECIPE
        #                 {weather_data['temperature']}:
        #                     - If the temperature is over 30°C and the weather is hot or sunny, suggest cold or refreshing dishes, drinks.
        #                     - If the temperature is below 15°C and the weather is cold, suggest warm and comforting dishes, drinks.
        #                     - If the temperature is between 15°C and 30°C, suggest balanced dishes,drinks that are neither too hot nor too cold.
        #                 {weather_data['description']}:
        #                     - If  weather data includes the word **rain**: suggest meal based on rain"""

        # if is_review_request:
        #     reviewed_data = get_suggested_titles_with_reviews(st.session_state.last_recipe_suggestions)
        #     if not reviewed_data:
        #         st.warning("❌ No review data available. Showing previous recipe suggestions again:")
        #
        #         if st.session_state.last_recipe_suggestions:
        #             repeat_response = "No review data available. Here are the previous suggestions again:\n\nRECIPE SUGGESTIONS:\n"
        #             repeat_response += "\n".join(st.session_state.last_recipe_suggestions)
        #
        #             with st.chat_message("assistant"):
        #                 st.markdown(repeat_response)
        #
        #             st.session_state.supervisor_history.append({"role": "assistant", "content": repeat_response})
        #
        #             # Show buttons for previous suggestions
        #             st.subheader("🍽️ Suggested Recipes:")
        #             for suggestion in st.session_state.last_recipe_suggestions:
        #                 cleaned_name = clean_recipe_name(suggestion)
        #                 if st.button(cleaned_name):
        #                     st.session_state.final_dish_choice = re.sub(r'\s*\(.*?\)', '', cleaned_name).strip()
        #                     st.session_state.ready_for_recipe = True
        #                     st.rerun()
        #         return
        #     else:
        #         reviewed_text = ""
        #         for review in reviewed_data[:2]:
        #             reviewed_text += f"Dish: {review['japanese_name']}\n"
        #             reviewed_text += f"Rating: {review['average_rating']} (from {review['total_reviews']} reviews)\n"
        #             reviewed_text += "Comments:\n"
        #
        #             comments = review.get("all_comments", [])
        #             for idx, comment in enumerate(comments):
        #                 reviewed_text += f"{idx + 1}. {comment}\n"
        #
        #             reviewed_text += "---\n"
        #
        #         prompt += f"""
        #                         The user asked: "{user_input}"
        #
        #                         You are an assistant helping the user decide which recipe is most liked **from a previous list**.
        #
        #                         DO NOT SUGGEST ANY NEW RECIPES. You must ONLY use the review data below.
        #
        #                         REVIEW DATA:
        #                         {reviewed_text}
        #
        #                         TASK:
        #                         1. Carefully read all listed reviews for each dish.
        #                         2. Choose the top 1–2 dishes based on rating and user feedback.
        #                         3. In your response, show the dish name, rating, and quote several real comments from the list.
        #                         4. Then write: "RECIPE SUGGESTIONS:" and list ONLY those 1–2 dish names on separate lines.
        #
        #                         IMPORTANT:
        #                         - DO NOT make up new dishes or comments.
        #                         - DO NOT summarize vaguely — use real reviews.
        #                         - Write in a friendly, natural tone in {language}.
        #                     """

        self.msg = [{"role": "user", "content": prompt}]
        print(self.msg)

    def process_user_message(self, session_id: str, data) -> dict[str, Any]:
        self.get_supervisor_prompt(data.preferences, data.prompt)
        run_response = self.agent.run(messages=self.msg, session_id=session_id, stream=False)
        print(run_response.content)
        data = run_response.content.split("RECIPE SUGGESTIONS:")
        return {
            "response": data[0],
            "suggestions": data[1].split("\n")[1::]
        }


    