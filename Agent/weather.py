import os
import requests
from dotenv import load_dotenv

load_dotenv()

API_KEY = os.getenv("API_KEY")
BASE_URL = os.getenv("BASE_URL")


# japan_cities = [
#     "None",
#     "Tokyo",
#     "Osaka",
#     "Kyoto",
#     "Hokkaido",
#     "Fukuoka",
#     "Sapporo",
#     "Nagasaki",
#     "Kobe",
#     "Yokohama",
#     "Hiroshima",
#     "Nara",
#     "Sendai",
#     "Kamakura",
#     "Shizuoka",
#     "Kochi",
#     "Chiba",
#     "Fukushima",
#     "Okinawa",
#     "Kagawa",
#     "Gifu",
# ]

japan_cities = [
    "なし",
    "東京",
    "大阪",
    "京都",
    "北海道",
    "福岡",
    "札幌",
    "長崎",
    "神戸",
    "横浜",
    "広島",
    "奈良",
    "仙台",
    "鎌倉",
    "静岡",
    "高知",
    "千葉",
    "福島",
    "沖縄",
    "香川",
    "岐阜",
]


# india_cities = [
#     "None",
#     "Delhi",
#     "Mumbai",
#     "Bangalore",
#     "Kolkata",
#     "Chennai",
#     "Hyderabad",
#     "Ahmedabad",
#     "Pune",
#     "Jaipur",
#     "Lucknow",
#     "Kanpur",
#     "Nagpur",
#     "Indore",
#     "Chandigarh",
#     "Bhopal",
#     "Coimbatore",
#     "Visakhapatnam",
#     "Patna",
#     "Surat",
#     "Vadodara",
# ]

india_cities = [
    "なし",
    "デリー",
    "ムンバイ",
    "バンガロール",
    "コルカタ",
    "チェンナイ",
    "ハイデラバード",
    "アーメダバード",
    "プネー",
    "ジャイプール",
    "ルクナウ",
    "カーンプル",
    "ナグプール",
    "インドール",
    "チャンディーガル",
    "ボーパール",
    "コインバトール",
    "ヴィシャーカパトナム",
    "パトナ",
    "スーラト",
    "バドーダラー",
]


# City translation maps (JP/IN → English)
japan_city_map = {
    "東京": "Tokyo",
    "大阪": "Osaka",
    "京都": "Kyoto",
    "北海道": "Hokkaido",
    "福岡": "Fukuoka",
    "札幌": "Sapporo",
    "長崎": "Nagasaki",
    "神戸": "Kobe",
    "横浜": "Yokohama",
    "広島": "Hiroshima",
    "奈良": "Nara",
    "仙台": "Sendai",
    "鎌倉": "Kamakura",
    "静岡": "Shizuoka",
    "高知": "Kochi",
    "千葉": "Chiba",
    "福島": "Fukushima",
    "沖縄": "Okinawa",
    "香川": "Kagawa",
    "岐阜": "Gifu",
}

india_city_map = {
    "デリー": "Delhi",
    "ムンバイ": "Mumbai",
    "バンガロール": "Bangalore",
    "コルカタ": "Kolkata",
    "チェンナイ": "Chennai",
    "ハイデラバード": "Hyderabad",
    "アーメダバード": "Ahmedabad",
    "プネー": "Pune",
    "ジャイプール": "Jaipur",
    "ルクナウ": "Lucknow",
    "カーンプル": "Kanpur",
    "ナグプール": "Nagpur",
    "インドール": "Indore",
    "チャンディーガル": "Chandigarh",
    "ボーパール": "Bhopal",
    "コインバトール": "Coimbatore",
    "ヴィシャーカパトナム": "Visakhapatnam",
    "パトナ": "Patna",
    "スーラト": "Surat",
    "バドーダラー": "Vadodara",
}

# Country code mapping
country_code_map = {"日本": "JP", "インド": "IN"}


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

    if country_name.lower() == "日本":
        return japan_cities
    elif country_name.lower() == "インド":
        return india_cities
    else:
        return []


def get_weather(city: str, country: str = "JP"):
    """Retrieve the current weather information for a specified city and country.

    Args:
        city (str): The name of the city for which to retrieve the weather.
        country (str, optional): The country code (ISO 3166-1) for the city. Defaults to "JP".

    Returns:
        dict or None: A dictionary containing the temperature, weather description, and humidity if the request is successful; otherwise, None.
    """
    
    # Convert city to English
    if country == "JP":
        city = japan_city_map.get(city, city)
    elif country == "IN":
        city = india_city_map.get(city, city)

    url = f"{BASE_URL}?q={city},{country}&appid={API_KEY}&units=metric"

    try:
        print(f"Requesting weather for: {city}, Country: {country}")
        response = requests.get(url)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            data = response.json()
            if "main" in data and "weather" in data:
                return {
                    "temperature": data["main"].get("temp"),
                    "description": data["weather"][0].get("description"),
                    "humidity": data["main"].get("humidity"),
                }
            else:
                return {"error": "Incomplete weather data received."}
        else:
            return {
                "error": f"API Error: {response.status_code} - {response.json().get('message', '')}"
            }
    except Exception as e:
        return {"error": f"Exception occurred: {str(e)}"}
