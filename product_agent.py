
import re
import psycopg2
from fuzzywuzzy import fuzz
from fuzzywuzzy import process
from dotenv import load_dotenv
import os

load_dotenv()

db_host = os.getenv("DB_HOST")
db_user = os.getenv("DB_USER")
db_password = os.getenv("DB_PASSWORD")
db_name = os.getenv("DB_NAME")
port = os.getenv("PORT")

def connect_to_postgres():
    try:
        conn = psycopg2.connect(
            dbname=db_name, 
            user=db_user, 
            password=db_password, 
            host=db_host,  
            port=port
        )
        return conn
    except Exception as e:
        print(f"Error connecting to PostgreSQL: {e}")
        return None


def get_latest_recipe_memory():
    # print('3333333333333')
    conn = connect_to_postgres()
    query = """
        SELECT memory
        FROM ai.agent_sessions
        ORDER BY updated_at ASC
        LIMIT 1;
    """
    cursor = conn.cursor()
    # print('44444444')
    cursor.execute(query)
    memory_data = cursor.fetchall()
    # print('5555555555', memory_data)
    conn.close()

    if memory_data:
        # print('01010101', memory_data[0][0])
        return memory_data[0][0] 
    return None


def search_products():
    # print('1414141414')
    conn = connect_to_postgres()
    query = """
        SELECT product_name, description, price, stock_quantity, category, weight, unit, brand, expiry_date, is_vegan FROM ai.products;
    """
    cursor = conn.cursor()
    cursor.execute(query)
    rows = cursor.fetchall()
    conn.close()
    # print('15151515', rows)
    return rows


def extract_ingredients_block(recipe_text):
    print("Extracting ingredients block from recipe...")
    content = recipe_text["runs"][-1]["response"]["content"]
    # print("content List:", content)

    ingredients_section = re.search(r"#### Ingredients(.*?)(#### Instructions|### Recipe Selection|$)", content, re.DOTALL)

    if ingredients_section:
        ingredients_content = ingredients_section.group(1).strip()
        # print("Extracted Ingredients Content:")
        # print(ingredients_content) 
        return ingredients_content

    else:
        print("No ingredients section found.")
        return ""
    


def find_similar_products(ingredients, products_db):
    results = set()

    for ingredient in ingredients:
        # print(f"Searching for: {ingredient}")
        
        ingredient_words = ingredient.split()
        # print(f"Ingredient split into words: {ingredient_words}")
        
        product_descriptions = [f"{product[0]}" for product in products_db]
        # print('---------product_descriptions', product_descriptions)
        for word in ingredient_words:
            best_match = process.extractOne(word, product_descriptions, scorer=fuzz.partial_ratio)
            # print(f"Best match for {word}: {best_match}")

            if best_match and best_match[1] >= 100:
                matched_description = best_match[0]
                # print('-----matched_description-----', matched_description)

                for product in products_db:
                    product_description = f"{product[0]}"
                    # print('-----product_description-----', product_description)
                    if matched_description.lower() in product_description.lower():
                        results.add(tuple(product))
    
    return list(results)


def get_available_ingredients():
    memory = get_latest_recipe_memory()

    if not memory:
        print('No memory found!')
        return []

    ingredient_names = extract_ingredients_block(memory)
    # print('------ingredient_names-----', ingredient_names)
    products_db = search_products()
    print('---------products_db', products_db)
    
    for i, product in enumerate(products_db):
        products_db[i] = list(product)
 
    ingredient_names_list = [ingredient.strip().lower() for ingredient in ingredient_names.split('\n') if ingredient]
    print('---------ingredient_names_list', ingredient_names_list)
    
    matching_products = find_similar_products(ingredient_names_list, products_db)
    # print('---------matching_products', matching_products)

    result_strings = []
    for product in matching_products:
        result_strings.append(f"Product: {product[0]}, Category: {product[4]}, Brand: {product[7]}, Price: {product[2]}Rs")
    return "\n".join(result_strings)


if __name__ == "__main__":
    available = get_available_ingredients()
    print("Available Ingredients:")
    print(available)