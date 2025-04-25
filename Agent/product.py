import re
from rapidfuzz import fuzz, process
# from fuzzywuzzy import fuzz, process
from deep_translator import GoogleTranslator
from Database.database import search_products

def clean_ingredient(ingredient):
    cleaned = re.sub(r'【.*?】', '', ingredient) 
    cleaned = re.sub(r'[-–—•\d/.]+[a-zA-Z]*|🌶|🌾|[^\w\s]', '', cleaned)  
    cleaned = cleaned.strip()

    blacklist = {
        "tablespoon", "teaspoon", "grams", "ml", "cup", "medium", "fresh", "frozen","【 A】", "tablespoons", "pieces", "mix"
        "chopped", "for", "to", "taste", "or", "g", "serving", "leaves", "wedges", "finely", "paste", "powder"
    }
    words = [w for w in cleaned.lower().split() if w not in blacklist]
    return ' '.join(words).strip()

def find_similar_products(cleaned_ingredients, products_db, threshold=85):
    results = set()
    product_names = [product[0].lower() for product in products_db]

    for ingredient in cleaned_ingredients:
        best_match = process.extractOne(ingredient, product_names, scorer=fuzz.token_set_ratio)
        print('-ingredient',ingredient,'----best_match', best_match)
        if best_match and best_match[1] >= threshold:
            for product in products_db:
                if best_match[0] == product[0].lower():
                    results.add(tuple(product))
    return list(results)

def get_available_ingredients(recipe_ingredients, language):
    if isinstance(recipe_ingredients, list):
        ingredient_list = [i.strip() for i in recipe_ingredients if i]
    elif isinstance(recipe_ingredients, str):
        ingredient_list = [i.strip() for i in recipe_ingredients.split(",") if i]
    else:
        ingredient_list = []
    # print('---ingredient_list----', ingredient_list)

    cleaned_ingredients = [clean_ingredient(i) for i in ingredient_list]
    # print('---cleaned_ingredients---', cleaned_ingredients)

    if language.lower() != "Japanese":
        try:
            ingredient_list = [
                GoogleTranslator(source='auto', target='ja').translate(i)
                for i in cleaned_ingredients
            ]
            # print('------translated-ingredient_list----', ingredient_list)
        except Exception as e:
            print("Translation failed:", e)
    else:
        ingredient_list = cleaned_ingredients

    products_db = search_products()
    # print('----product_db', products_db)
    products_db = [list(p) for p in products_db]

    matches = find_similar_products(ingredient_list, products_db)
    # print('--------matches--------', matches)

    # Translate product details if the language is not Japanese
    if language.lower() != "japanese":
        translated_matches = []
        for match in matches:
            translated_match = {
                "Product_name": GoogleTranslator(source='auto', target='en').translate(match[0]),
                "Tax": match[1],
                "Price": f"{match[2]}",
                "Weight": f"{match[5]} {match[6]}"
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
                "Weight": f"{p[5]} {p[6]}"
            }
            for p in matches
        ]
