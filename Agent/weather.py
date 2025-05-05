import json
import os
from typing import Dict, List

import requests
from agno.agent import Agent
from agno.knowledge.json import JSONKnowledgeBase
from agno.models.openai import OpenAIChat
from agno.vectordb.pgvector import PgVector
from deep_translator import GoogleTranslator
from dotenv import load_dotenv
from pydantic import BaseModel

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")


japan_cities = [
    "None",
    "Tokyo",
    "Osaka",
    "Kyoto",
    "Hokkaido",
    "Fukuoka",
    "Sapporo",
    "Nagasaki",
    "Kobe",
    "Yokohama",
    "Hiroshima",
    "Nara",
    "Sendai",
    "Kamakura",
    "Shizuoka",
    "Kochi",
    "Chiba",
    "Fukushima",
    "Okinawa",
    "Kagawa",
    "Gifu",
]

india_cities = [
    "None",
    "Delhi",
    "Mumbai",
    "Bangalore",
    "Kolkata",
    "Chennai",
    "Hyderabad",
    "Ahmedabad",
    "Pune",
    "Jaipur",
    "Lucknow",
    "Kanpur",
    "Nagpur",
    "Indore",
    "Chandigarh",
    "Bhopal",
    "Coimbatore",
    "Visakhapatnam",
    "Patna",
    "Surat",
    "Vadodara",
]


def get_cities_in_country(country_name: str):
    """Retrieve a list of cities in a specified country.

    Args:
        country_name (str): The name of the country for which to retrieve cities.
                            Accepted values are "Japan" and "India".

    Returns:
        list: A list of cities in the specified country.
              Returns a list of cities in Japan if the country name is "Japan",
              a list of cities in India if the country name is "India",
              or an empty list if the country name is not recognized.
    """

    if country_name.lower() == "japan":
        return japan_cities
    elif country_name.lower() == "india":
        return india_cities
    else:
        return []


def get_weather(city: str, country="JP"):
    """Retrieve the current weather information for a specified city and country.

    Args:
        city (str): The name of the city for which to retrieve the weather.
        country (str, optional): The country code (ISO 3166-1) for the city. Defaults to "JP".

    Returns:
        dict or None: A dictionary containing the temperature, weather description, and humidity if the request is successful; otherwise, None.
    """

    url = f"{BASE_URL}?q={city},{country}&appid={API_KEY}&units=metric"
    response = requests.get(url)
    # print('-----------response', response.text, response.status_code)
    if response.status_code == 200:
        data = response.json()
        weather = {
            "temperature": data["main"]["temp"],
            "description": data["weather"][0]["description"],
            "humidity": data["main"]["humidity"],
        }
        return weather
    else:
        return None
