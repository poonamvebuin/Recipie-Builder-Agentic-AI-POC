import re
from deep_translator import GoogleTranslator
from rapidfuzz import fuzz, process
from Database.database import search_products
import streamlit as st


@st.cache_data
def translate_word(word, src="en", tgt="ja"):
    """Translate a word from a source language to a target language using Google Translator.

    Args:
        word (str): The word to be translated.
        src (str, optional): The source language code (default is "en" for English).
        tgt (str, optional): The target language code (default is "ja" for Japanese).

    Returns:
        str: The translated word in the target language.
    """

    return GoogleTranslator(source=src, target=tgt).translate(word)


@st.cache_data
def load_product_db():
    """Loads the product database.

    This function retrieves a list of products from the search_products function
    and converts each product into a list.

    Returns:
        list: A list of products, where each product is represented as a list.
    """

    return [list(p) for p in search_products()]


def clean_ingredient(ingredient):
    """Clean and extract relevant components from a given ingredient string.

    This function processes an ingredient string to remove unwanted characters and
    phrases, particularly those within parentheses and common measurement terms.
    It returns a list of cleaned ingredient components in lowercase.

    Args:
        ingredient (str): The ingredient string to be cleaned.

    Returns:
        list: A list of cleaned ingredient components, excluding any terms
              specified in the blacklist.
    """

    inside_parentheses = re.findall(r"[（(](.*?)[）)]", ingredient)
    components = []

    for part in inside_parentheses:
        split_parts = re.split(r"[・,、/]", part)
        for sp in split_parts:
            cleaned = re.sub(
                r"[-–—•\d/.]+[a-zA-Z]*|🌶|🌾|[^\w\sぁ-んァ-ン一-龯]", "", sp
            ).strip()
            if cleaned:
                components.append(cleaned)

    without_parens = re.sub(r"[（(].*?[）)]", "", ingredient)
    cleaned_main = re.sub(
        r"[-–—•\d/.]+[a-zA-Z]*|🌶|🌾|[^\w\sぁ-んァ-ン一-龯]", "", without_parens
    ).strip()
    if cleaned_main:
        components.append(cleaned_main)

    blacklist = {
        "tablespoon",
        "teaspoon",
        "grams",
        "ml",
        "cup",
        "medium",
        "fresh",
        "frozen",
        "tablespoons",
        "pieces",
        "mix",
        "chopped",
        "for",
        "to",
        "taste",
        "or",
        "g",
        "serving",
        "leaves",
        "wedges",
        "finely",
        "paste",
        "powder",
        "薬味",
        "香味野菜",
    }

    return [w.lower() for w in components if w.lower() not in blacklist and w]


def find_similar_products(cleaned_ingredients, products_db, threshold=85):
    results = set()

    # Normalize product names
    product_name_map = {
        re.sub(r"\s+", "", product[0].lower()): product
        for product in products_db
    }

    for ingredient in cleaned_ingredients:
        normalized_ingredient = re.sub(r"\s+", "", ingredient.lower())
        print("-----ingredient", normalized_ingredient)

        best_match = process.extractOne(
            normalized_ingredient, list(product_name_map.keys()), scorer=fuzz.ratio
        )

        print("-----best_match", best_match)
        if best_match and best_match[1] >= threshold:
            matched_product = product_name_map[best_match[0]]
            results.add(tuple(matched_product))

    return list(results)


@st.cache_data(show_spinner="🔍 Finding ingredients...")
def get_available_ingredients(recipe_ingredients, language):
    """Get available ingredients based on the provided recipe ingredients and language.
    
    This function processes a list or string of recipe ingredients, cleans and translates them if necessary, and then finds similar products from a product database. The results are returned in a structured format.
    
    Args:
        recipe_ingredients (list or str): A list of ingredients or a string containing ingredients separated by newlines.
        language (str): The language in which the ingredients should be processed. Currently supports English and Japanese.
    
    Returns:
        list of dict: A list of dictionaries containing product information, including product name, tax, price, and weight. The structure of the returned dictionaries depends on the specified language.
        
    Raises:
        Exception: If translation fails, the function will return cleaned ingredients without translation.
    """
    
    if isinstance(recipe_ingredients, list):
        recipe_ingredients = "\n".join(recipe_ingredients)

    if isinstance(recipe_ingredients, str):
        cleaned_text = re.sub(r"\n+", "\n", recipe_ingredients)
        raw_ingredients = [
            i.strip() for i in cleaned_text.split("\n") if i.strip()
        ]
    else:
        raw_ingredients = []

    cleaned_ingredients = [
        sub_ing for i in raw_ingredients for sub_ing in clean_ingredient(i)
    ]

    if language.lower() != "japanese":
        try:
            translated_ingredients = [
                translate_word(i, "en", "ja") for i in cleaned_ingredients
            ]
        except Exception:
            translated_ingredients = cleaned_ingredients
    else:
        translated_ingredients = cleaned_ingredients

    print('-----translated_ingredients', translated_ingredients)
    products_db = load_product_db()
    matches = find_similar_products(translated_ingredients, products_db)

    if language.lower() != "japanese":
        return [
            {
                "Product_name": translate_word(match[0], "ja", "en"),
                "Tax": match[1],
                "Price": f"{match[2]}",
                "Weight": f"{match[5]} {match[6]}",
            }
            for match in matches
        ]
    else:
        return [
            {
                "Product_name": p[0],
                "Tax": p[1],
                "Price": f"{p[2]}",
                "Weight": f"{p[3]} {p[4]}",
            }
            for p in matches
        ]
