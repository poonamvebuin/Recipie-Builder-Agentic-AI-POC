import os
import re
from typing import List, Dict, Any
from dotenv import load_dotenv
from deep_translator import GoogleTranslator
from rapidfuzz import fuzz, process

from fastapi_app.models.product import fetch_products


class ProductFinderAgent:
    """ProductFinderAgent is a class that facilitates the retrieval and processing of product information from a PostgreSQL database, as well as the translation and cleaning of ingredient data.
    
    Attributes:
        db_host (str): The database host retrieved from the environment variable DB_HOST.
        db_user (str): The database user retrieved from the environment variable DB_USER.
        db_password (str): The database password retrieved from the environment variable DB_PASSWORD.
        db_name (str): The database name retrieved from the environment variable DB_NAME.
        db_port (int): The database port retrieved from the environment variable DB_PORT, defaults to 5432 if not set.
    
    Methods:
        translate: Translates a word from a source language to a target language using Google Translator.
        clean_ingredient: Cleans and extracts relevant components from a given ingredient string.
        find_similar_products: Finds products similar to the given ingredients based on a similarity threshold.
        get_available_ingredients: Processes a list of recipe ingredients, cleans and translates them if necessary, fetches available products, and formats the results for output.
    """


    def translate(self, word: str, source_lang: str = "en", target_lang: str = "ja") -> str:
        """Translate a word from a source language to a target language using Google Translator.
        
        Args:
            word (str): The word to be translated.
            source_lang (str, optional): The language code of the source language. Defaults to "en".
            target_lang (str, optional): The language code of the target language. Defaults to "ja".
        
        Returns:
            str: The translated word.
        
        Raises:
            Exception: If there is an error during the translation process.
        """

        try:
            return GoogleTranslator(source=source_lang, target=target_lang).translate(word)
        except Exception as e:
            raise Exception(f"Translation error for word '{word}': {e}")

    def clean_ingredient(self, ingredient: str) -> List[str]:
        """Cleans and extracts relevant components from a given ingredient string.
        
        This method processes the input ingredient string to remove unwanted characters, 
        extracts components found within parentheses, and filters out common terms that 
        are not needed for further processing. The cleaned components are returned as a 
        list of lowercase strings.
        
        Args:
            ingredient (str): The ingredient string to be cleaned and processed.
        
        Returns:
            List[str]: A list of cleaned and relevant ingredient components in lowercase.
        
        Raises:
            Exception: If an error occurs during the cleaning process, an exception is raised 
            with a message indicating the problematic ingredient.
        """

        try:
            inside_parentheses = re.findall(r"[（(](.*?)[）)]", ingredient)
            components = []

            for part in inside_parentheses:
                for sub_part in re.split(r"[・,、/]", part):
                    cleaned = re.sub(
                        r"[-–—•\d/.]+[a-zA-Z]*|🌶|🌾|[^\w\sぁ-んァ-ン一-龯]", "", sub_part
                    ).strip()
                    if cleaned:
                        components.append(cleaned)

            main_part = re.sub(r"[（(].*?[）)]", "", ingredient)
            cleaned_main = re.sub(
                r"[-–—•\d/.]+[a-zA-Z]*|🌶|🌾|[^\w\sぁ-んァ-ン一-龯]", "", main_part
            ).strip()
            if cleaned_main:
                components.append(cleaned_main)

            blacklist = {
                "tablespoon", "teaspoon", "grams", "ml", "cup", "medium", "fresh", "frozen",
                "tablespoons", "pieces", "mix", "chopped", "for", "to", "taste", "or", "g",
                "serving", "leaves", "wedges", "finely", "paste", "powder", "薬味", "香味野菜",
            }

            return [word.lower() for word in components if word.lower() not in blacklist and word]
        except Exception as e:
            raise Exception(f"Ingredient cleaning error for '{ingredient}': {e}")

    def find_similar_products(
        self,
        ingredients: List[str],
        product_rows: List[List[Any]],
        threshold: int = 85,
    ) -> List[List[Any]]:
        """Finds products similar to the given ingredients based on a similarity threshold.
        
        This function takes a list of ingredients and a list of product rows, and attempts to find products that match the ingredients based on a specified similarity threshold. It uses fuzzy string matching to determine the similarity between the normalized ingredient names and the product names.
        
        Args:
            ingredients (List[str]): A list of ingredient names to match against the products.
            product_rows (List[List[Any]]): A list of product rows, where each row contains product information.
            threshold (int, optional): The minimum similarity score (0-100) for a match to be considered valid. Defaults to 85.
        
        Returns:
            List[List[Any]]: A list of matched product rows that are similar to the provided ingredients.
        
        Raises:
            Exception: If an error occurs during the product matching process.
        """
        
        try:
            matched = set()

            product_name_map = {
                re.sub(r"\s+", "", str(product[1]).lower()): product
                for product in product_rows
            }

            for ingredient in ingredients:
                normalized_ingredient = re.sub(r"\s+", "", ingredient.lower())
                match = process.extractOne(
                    normalized_ingredient,
                    list(product_name_map.keys()),
                    scorer=fuzz.ratio
                )

                print("Ingredient:", ingredient)
                print("Normalized:", normalized_ingredient)
                print("Match result:", match)

                if match and match[1] >= threshold:
                    matched_product = product_name_map[match[0]]
                    print("Matched product:", matched_product)
                    matched.add(tuple(matched_product))
                else:
                    print("No suitable match found for:", ingredient)

            print("Matched results:", matched)
            return [list(item) for item in matched]
        except Exception as e:
            raise Exception(f"Product matching error: {e}")

    def get_available_ingredients(
        self, recipe_ingredients: List[str], language: str
    ) -> List[Dict[str, Any]]:
        """Get available ingredients for a recipe.
        
        This method processes a list of recipe ingredients, cleans and translates them if necessary, 
        fetches available products, and formats the results for output.
        
        Args:
            recipe_ingredients (List[str]): A list of ingredients required for the recipe.
            language (str): The language in which the ingredient names should be returned. 
                            If not Japanese, the names will be translated from Japanese to English.
        
        Returns:
            List[Dict[str, Any]]: A list of dictionaries containing available product information, 
                                  including product ID, name, price, tax, and weight.
        
        Raises:
            Exception: If there is an error during ingredient cleaning, translation, product fetching, 
                       or formatting of the product information.
        """
        
        try:
            print("Original ingredients:", recipe_ingredients)
            print("Language:", language)

            cleaned = [
                component
                for ingredient in recipe_ingredients
                for component in self.clean_ingredient(ingredient)
            ]

            if language.lower() != "japanese":
                try:
                    translated = [self.translate(word, "en", "ja") for word in cleaned]
                except Exception:
                    translated = cleaned
            else:
                translated = cleaned

            print("Cleaned ingredients (used for matching):", translated)

            products = fetch_products()
            matches = self.find_similar_products(translated, products)

            formatted = []

            for product in matches:
                try:
                    (
                        product_id,
                        name,
                        tax,
                        price,
                        weight,
                        unit,
                        brand,
                        is_vegan
                    ) = product

                    if language.lower() != "japanese":
                        name = self.translate(name, "ja", "en")

                    tax_parts = tax.split('%')
                    price_with_tax = tax_parts[1].strip() if len(tax_parts) > 1 else tax
                    tax_value = str(re.search(r"\d+", tax_parts[0]).group()) if tax_parts and re.search(r"\d+", tax_parts[0]) else "0"

                    formatted.append({
                        "product_id": str(product_id),
                        "product_name": name.strip(),
                        "price": str(price),
                        "tax": tax_value,
                        "price_with_tax": price_with_tax,
                        "weight": f"{weight} {unit}".replace("pieces", "個"),
                    })

                except Exception as e:
                    raise Exception(f"Error formatting product row: {e}")

            return formatted
        except Exception as e:
            raise Exception(f"Ingredient lookup error: {e}")
