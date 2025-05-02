import requests
from agno.agent import Agent
from pydantic import BaseModel
from typing import Dict, List
import json
from agno.knowledge.json import JSONKnowledgeBase
from agno.vectordb.pgvector import PgVector
from agno.models.openai import OpenAIChat
from deep_translator import GoogleTranslator
import os
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv('API_KEY')
BASE_URL = os.getenv('BASE_URL')


import requests

# GeoNames API Endpoint
# GEO_API_URL = "http://api.geonames.org/searchJSON"
# GEO_API_USERNAME = "kamaliyapoonam" 

# def get_cities_in_country(country_name: str):
#     params = {
#         "formatted": "true",
#         "lang": "en",
#         "country": country_name,
#         "username": GEO_API_USERNAME,
#         "maxRows": 500  
#     }
#     print('--------------------1111111111111')
    
#     response = requests.get(GEO_API_URL, params=params)
#     print('----------333333333333', response.text, response.status_code)
#     if response.status_code == 200:
#         print('----------4444444')
#         data = response.json()
#         cities = [city['name'] for city in data['geonames']]
#         return cities
#     else:
#         return None

japan_cities = [
    "None", "Tokyo", "Osaka", "Kyoto", "Hokkaido", "Fukuoka", "Sapporo", "Nagasaki", "Kobe", "Yokohama", "Hiroshima",
    "Nara", "Sendai", "Kamakura", "Shizuoka", "Kochi", "Chiba", "Fukushima", "Okinawa", "Kagawa", "Gifu"
]

india_cities = [
    "None", "Delhi", "Mumbai", "Bangalore", "Kolkata", "Chennai", "Hyderabad", "Ahmedabad", "Pune", "Jaipur", "Lucknow",
    "Kanpur", "Nagpur", "Indore", "Chandigarh", "Bhopal", "Coimbatore", "Visakhapatnam", "Patna", "Surat", "Vadodara"
]

# Function to get cities based on the country
def get_cities_in_country(country_name: str):
    if country_name.lower() == "japan":
        return japan_cities
    elif country_name.lower() == "india":
        return india_cities
    else:
        return [] 
    
def get_weather(city: str, country='JP'):
    url = f"{BASE_URL}?q={city},{country}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    # print('-----------response', response.text, response.status_code)
    if response.status_code == 200:
        data = response.json()
        weather = {
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description'],
            'humidity': data['main']['humidity'],
        }
        return weather
    else:
        return None
