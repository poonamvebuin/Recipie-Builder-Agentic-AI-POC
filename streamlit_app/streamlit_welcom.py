import streamlit as st


def display_welcome_message(language):
    """Displays a welcome message to the user based on the selected language.

    This function presents a personalized welcome message for a cooking assistant application. It provides options for recipe creation and product finding, encouraging user interaction through buttons.

    Args:
        language (str): The language in which the welcome message should be displayed.
                        Supported values are "English" and "Japanese".

    Returns:
        None: This function does not return a value. It directly interacts with the Streamlit interface to display messages and buttons.
    """ 
    
    
    with st.chat_message("assistant"):
        if language == "English":

            with st.expander("👀 Click to view how this app works"):
                st.image("flow_image_en.png", caption="App Flow: Recipe Creation or Product Finder")
            st.write("**Welcome to your Personal cooking Assistant! 🍽️**")
            st.write(
                "I'm here to help you discover the perfect recipes or find exactly what you need for your kitchen. Let's start creating something delicious together! 😄"
            )
            st.write("You've got two amazing options today:")
            st.write(
                "1. **Recipe Creation** 🍳: Want to create a custom dish? Tell me your taste, time, and ingredients, and I'll suggest recipes that fit your vibe! Whether you're in the mood for something sweet, savory, or spicy, I've got you covered. Let's get cooking! 🌟"
            )
            st.write(
                "2. **Product Finder** 🛒: Looking for ingredients or kitchen products? I can help you find exactly what you need. Just tell me what you have in mind or upload your list, and I'll search for the best products available! Add them to your cart and shop with ease. 🛍️"
            )
            st.write(
                "👇 **Choose an option** and let's get started on your cooking journey!"
            )
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(
                    "Chat with Recipe Assistant",
                    key="recipe_creator_button",
                    help="Click to start creating a recipe",
                    use_container_width=True,
                ):
                    st.session_state.mode = "recipe"

            with col2:
                if st.button(
                    "Product Finder",
                    key="product_finder_button",
                    help="Click to find products",
                    use_container_width=True,
                ):
                    st.session_state.mode = "product"

        elif language == "Japanese":
            with st.expander("👀 このアプリの動作を見るにはクリックしてください"):
                st.image("flow_image_jp.png", caption="アプリの流れ レシピ作成または商品検索")
            st.write("**ようこそ、あなたのパーソナル料理アシスタントへ！🍽️**")
            st.write(
                "私は、完璧なレシピを見つけるお手伝いや、キッチンに必要なものを見つけるお手伝いをします。一緒においしいものを作り始めましょう！😄"
            )
            st.write("今日は、2つの素晴らしいオプションがあります：")
            st.write(
                "1. **レシピ作成** 🍳: カスタム料理を作りたいですか？あなたの味、時間、そして材料を教えてくれれば、それにぴったりのレシピを提案します！甘いもの、塩辛いもの、辛いもの、どれを作りたい気分でもお任せください。さあ、料理を始めましょう！🌟"
            )
            st.write(
                "2. **製品探し** 🛒: 材料やキッチン用品を探していますか？欲しいものを教えてくれれば、最適な製品を見つけます！リストをアップロードするか、思いついたものを言ってください。見つけた製品をカートに追加して、簡単にお買い物ができます！🛍️"
            )
            st.write("👇 **オプションを選んで**、あなたの料理の旅を始めましょう！")
            col1, col2 = st.columns([1, 1])
            with col1:
                if st.button(
                    "レシピアシスタントとチャット",
                    key="recipe_creator_button",
                    help="レシピ作成を始めるにはクリックしてください",
                    use_container_width=True,
                ):
                    st.session_state.mode = "recipe"

            with col2:
                if st.button(
                    "製品探し",
                    key="product_finder_button",
                    help="製品を見つけるにはクリックしてください",
                    use_container_width=True,
                ):
                    st.session_state.mode = "product"
