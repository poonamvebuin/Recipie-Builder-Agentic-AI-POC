from fuzzywuzzy import fuzz, process
from deep_translator import GoogleTranslator
from Database import search_products

def find_similar_products(ingredients, products_db):
    results = set()
    for ingredient in ingredients:
        words = ingredient.split()
        product_names = [f"{product[0]}" for product in products_db]
        for word in words:
            best_match = process.extractOne(word, product_names, scorer=fuzz.partial_ratio)
            if best_match and best_match[1] >= 100:
                for product in products_db:
                    if best_match[0].lower() in product[0].lower():
                        results.add(tuple(product))
    return list(results)

def get_available_ingredients(recipe_ingredients, language="English"):
    ingredient_list = [i.strip() for i in recipe_ingredients.split('\n') if i]
    
    if language.lower() != "english":
        try:
            ingredient_list = [
                GoogleTranslator(source='auto', target='en').translate(i)
                for i in ingredient_list
            ]
        except Exception:
            pass

    products_db = search_products()
    products_db = [list(p) for p in products_db]

    matches = find_similar_products([i.lower() for i in ingredient_list], products_db)

    return [
        {
            "Product_name": p[0], "Description": p[1], "Price": f"{p[2]}Rs",
            "Category": p[4], "Brand": p[7], "Weight": f"{p[5]}{p[6]}"
        }
        for p in matches
    ]
