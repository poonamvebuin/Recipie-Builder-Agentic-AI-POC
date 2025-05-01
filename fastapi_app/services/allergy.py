from collections import defaultdict
import logging
import re
import openai
from typing import List
from fastapi_app.common.schema import PredictAllergy
# from fastapi_app.models.allergy import get_similarity_out, ignore_word_query, insert_allergy, insert_history, update_allergy
from fastapi_app.common.utils import get_embedding


# def postprocess_prediction(output, threshold_window):
#     """Filter predictions based on a threshold and return top results."""
#     threshold = threshold_window * max(item[2] for item in output)
#     filtered_data = [out for out in output if out[2] >= threshold]
#     return filtered_data[:3] if len(filtered_data) > 3 else filtered_data
#
#
# def make_predictions(input_list, db):
#     """Make predictions for a list of input ingredients."""
#
#     ignore_word_db_data = ignore_word_query(db)
#
#     ignore_words_mapping = defaultdict(list)
#
#     # Iterate over the original data and map the values
#     for ingredient, allergy in ignore_word_db_data:
#         ignore_words_mapping[allergy].append(ingredient)
#
#     # Convert defaultdict to a regular dictionary
#     ignore_words_mapping = dict(ignore_words_mapping)
#     logging.info(f"Ignore words: {ignore_words_mapping}")
#
#     # Fetch data embeddings from the database
#     input_embedding = get_embedding(list(input_list))
#
#     final_predictions = []
#     for ele in input_embedding["data"]:
#         inp_txt = input_list[ele["index"]]
#         similar_out_db = get_similarity_out(ele["embedding"], db=db)
#         # Convert tuple DB output to list and append input text in list
#         similar_out_db_update = [list(i) + [inp_txt] for i in similar_out_db]
#         similar_out = postprocess_prediction(
#             similar_out_db_update, threshold_window=0.99
#         )
#         # Remove ignore words from list
#         final_predictions += [
#             out
#             for out in similar_out
#             if out[3] not in ignore_words_mapping.get(out[1], [])
#         ]
#
#     return final_predictions
#
#
# def process(data: PredictAllergy, db):
#     try:
#         # Data Processing
#         if "(一部に" in data.data:
#             ingredients, users_allergy = data.data.split("(一部に")
#             users_allergy = users_allergy.replace("乳成分", "乳")
#             users_allergy = [
#                 i.strip()
#                 for i in users_allergy.replace("を含む)", "").split("・")
#                 if i.strip()
#             ]
#         else:
#             ingredients, users_allergy = data.data, []
#
#         # Extracting ingredient_list
#         ingredient_list = set(
#             filter(None, (x.strip() for x in re.split(r"[、,]", ingredients)))
#         )
#
#         logging.info(
#             f"------------>ingredients : {ingredient_list}, users_allergy : {users_allergy}"
#         )
#
#         # Making Predictions
#         predictions_jpn = make_predictions(list(ingredient_list), db)
#
#         # Building predictions_dict
#         predictions_dict = {}
#
#         for i in predictions_jpn:
#             key = i[1]
#             value = i[3]
#
#             if value not in predictions_dict.get(key, []):
#                 predictions_dict.setdefault(key, []).append(value)
#
#         logging.info(f"predictions_dict : {predictions_dict}")
#
#         allergy_list = data.allergy_list
#
#         # Generating Output
#         output_jpn = {allergen: {"status": 0} for allergen in allergy_list}
#
#         for allergy_name in output_jpn:
#             if allergy_name in users_allergy:
#                 output_jpn[allergy_name]["status"] = 3
#                 output_jpn[allergy_name]["source_list"] = list(ingredient_list)
#
#             if allergy_name in predictions_dict:
#                 output_jpn[allergy_name]["status"] = 2
#                 output_jpn[allergy_name]["source_list"] = predictions_dict[allergy_name]
#
#             if allergy_name in users_allergy and allergy_name in predictions_dict:
#                 output_jpn[allergy_name]["status"] = 1
#                 output_jpn[allergy_name]["source_list"] = predictions_dict[allergy_name]
#
#         status = 2
#         response_body = {
#             "allergy_dict": output_jpn,
#             "ingredient_list": list(ingredient_list),
#         }
#         response_code = 200
#         logging.info(output_jpn)
#     except Exception as e:
#         logging.info(f"An error occurred: {e}")
#         status = 3
#         response_code = 404
#         response_body = {"error": str(e)}
#
#     # Logging and Response Building
#     response = {"statusCode": response_code, "body": response_body}
#
#     insert_history(db, dict(data), response_body, response, status)
#     logging.info("Prediction Done!")
#     return response
#
#
# def update_or_insert_data_db(
#     allergy_name: str, remove_ingrediant: list, add_ingredian: list, db
# ):
#     try:
#         if len(remove_ingrediant):
#
#             logging.info(f"Updating Record for : {remove_ingrediant}")
#
#             return update_allergy(allergy_name, remove_ingrediant, db)
#
#         elif len(add_ingredian):
#             logging.info(f"Inserting Record for : {add_ingredian}")
#
#             return insert_allergy(add_ingredian, db)
#
#     except Exception as e:
#         logging.info(f"An error occurred: {e}")
