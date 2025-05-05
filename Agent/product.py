import re

# from fuzzywuzzy import fuzz, process
from deep_translator import GoogleTranslator
from rapidfuzz import fuzz, process

from Database.database import search_products


def clean_ingredient(ingredient):
    """Cleans and extracts ingredient names from a given string.
    
    This function processes a string containing ingredient information, removing unwanted characters and phrases, and extracting relevant components. It handles text within parentheses, splits components by specific delimiters, and filters out common terms that are not needed for ingredient identification.
    
    Args:
        ingredient (str): The input string containing ingredient information.
    
    Returns:
        list: A list of cleaned and filtered ingredient names in lowercase.
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

    # Final filtered list
    return [w.lower() for w in components if w.lower() not in blacklist and w]


def find_similar_products(cleaned_ingredients, products_db, threshold=85):

    results = set()
    product_names = [product[0].lower() for product in products_db]

    for ingredient in cleaned_ingredients:
        best_match = process.extractOne(
            ingredient, product_names, scorer=fuzz.token_set_ratio
        )
        # print('-ingredient',ingredient,'----best_match', best_match)
        if best_match and best_match[1] >= threshold:
            for product in products_db:
                if best_match[0] == product[0].lower():
                    results.add(tuple(product))
    return list(results)


def get_available_ingredients(recipe_ingredients, language):
    """Get available ingredients for a recipe and translate them if necessary.
    
    This function processes a list or string of recipe ingredients, cleans them, and translates them into Japanese if the specified language is not Japanese. It then searches for similar products in a database and returns a list of matching products with their details.
    
    Args:
        recipe_ingredients (list or str): The ingredients of the recipe, either as a list or a newline-separated string.
        language (str): The language in which to return the product names. If not "Japanese", the names will be translated from Japanese to English.
    
    Returns:
        list: A list of dictionaries containing product details, including product name, tax, price, and weight. If the language is Japanese, the product names will be in Japanese; otherwise, they will be translated to English.
    """

    if isinstance(recipe_ingredients, list):
        cleaned_ingredients = re.sub(r'\n+', '\n', recipe_ingredients)
        raw_ingredients = [i.strip() for i in cleaned_ingredients.split('\n') if i.strip()]
    elif isinstance(recipe_ingredients, str):

        cleaned_ingredients = re.sub(r'\n+', '\n', recipe_ingredients)
        raw_ingredients = [i.strip() for i in cleaned_ingredients.split('\n') if i.strip()]
    else:
        raw_ingredients = []

    cleaned_ingredients = [
        sub_ing for i in raw_ingredients for sub_ing in clean_ingredient(i)
    ]
    # cleaned_ingredients = [clean_ingredient(i) for i in raw_ingredients]
    # print('---cleaned_ingredients---', cleaned_ingredients)
    if language.lower() != "japanese":
        try:
            translated_ingredients = [
                GoogleTranslator(source="en", target="ja").translate(i)
                for i in cleaned_ingredients
            ]
        except Exception as e:
            print("Translation failed:", e)
            translated_ingredients = cleaned_ingredients
    else:
        translated_ingredients = cleaned_ingredients

    # print('------translated_ingredient_list (to JP)----', translated_ingredients)
    products_db = search_products()
    products_db = [list(p) for p in products_db]
    matches = find_similar_products(translated_ingredients, products_db)
    # print('--------matches--------', matches)
    if language.lower() != "japanese":
        translated_matches = []
        for match in matches:
            translated_match = {
                "Product_name": GoogleTranslator(source="ja", target="en").translate(
                    match[0]
                ),
                "Tax": match[1],
                "Price": f"{match[2]}",
                "Weight": f"{match[3]} {match[4]}"
            }
            translated_matches.append(translated_match)
        # print('---------translated_matches-------', translated_matches)
        return translated_matches
    else:
        return [
            {
                "Product_name": p[0],
                "Tax": p[1],
                "Price": f"{p[2]}",
                "Weight": f"{p[3]} {p[4]}"
            }
            for p in matches
        ]
