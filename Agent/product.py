import re
from fuzzywuzzy import fuzz, process
from deep_translator import GoogleTranslator
from Database.database import search_products

def clean_ingredient(ingredient):
    cleaned = re.sub(r'[-–—•\d/.]+[a-zA-Z]*|🌶|🌾|[^\w\s]', '', ingredient)
    blacklist = {
        "tablespoon", "teaspoon", "grams", "ml", "cup", "medium", "fresh", "frozen",
        "chopped", "for", "to", "taste", "or", "g", "serving", "leaves", "wedges", "finely", "paste", "powder"
    }
    words = [w for w in cleaned.lower().split() if w not in blacklist]
    return ' '.join(words).strip()

def find_similar_products(cleaned_ingredients, products_db, threshold=85):
    results = set()
    product_names = [product[0].lower() for product in products_db]

    for ingredient in cleaned_ingredients:
        best_match = process.extractOne(ingredient, product_names, scorer=fuzz.token_set_ratio)
        if best_match and best_match[1] >= threshold:
            for product in products_db:
                if best_match[0] == product[0].lower():
                    results.add(tuple(product))
    return list(results)

def get_available_ingredients(recipe_ingredients, language="English"):
    ingredient_list = [i.strip() for i in recipe_ingredients.split('\n') if i]
    print('---ingredient_list----', ingredient_list)

    if language.lower() != "English":
        try:
            ingredient_list = [
                GoogleTranslator(source='auto', target='en').translate(i)
                for i in ingredient_list
            ]
        except Exception as e:
            print("Translation failed:", e)

    cleaned_ingredients = [clean_ingredient(i) for i in ingredient_list]
    print('---cleaned_ingredients---', cleaned_ingredients)

    products_db = search_products()
    print('----products_db---', products_db)
    products_db = [list(p) for p in products_db]

    matches = find_similar_products(cleaned_ingredients, products_db)
    print('--------matches--------', matches)

    return [
        {
            "Product_name": p[0],
            "Description": p[1],
            "Price": f"{p[2]} Rs",
            "Category": p[4],
            "Brand": p[7],
            "Weight": f"{p[5]} {p[6]}"
        }
        for p in matches
    ]
