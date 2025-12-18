import requests
import json
from datetime import datetime
import pytz
import wikipedia


# Agent Function 1: Weather Lookup
def get_weather(city):
    """Get weather for a city using wttr.in (free, no API key needed)"""
    try:
        url = f"https://wttr.in/{city}?format=j1"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            current = data['current_condition'][0]
            weather_info = {
                "city": city,
                "temperature": f"{current['temp_C']}°C ({current['temp_F']}°F)",
                "condition": current['weatherDesc'][0]['value'],
                "humidity": f"{current['humidity']}%",
                "wind": f"{current['windspeedKmph']} km/h",
                "feels_like": f"{current['FeelsLikeC']}°C"
            }
            return json.dumps(weather_info)
        return json.dumps({"error": "Could not fetch weather"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# Agent Function 2: Calculator
def calculate(expression):
    """Safely evaluate mathematical expressions"""
    try:
        # Remove any potentially dangerous characters
        allowed_chars = "0123456789+-*/(). "
        cleaned = ''.join(c for c in expression if c in allowed_chars)
        
        # Evaluate safely
        result = eval(cleaned, {"__builtins__": {}}, {})
        return json.dumps({
            "expression": expression,
            "result": result
        })
    except Exception as e:
        return json.dumps({"error": f"Cannot calculate: {str(e)}"})


# Agent Function 3: World Time
def get_world_time(city):
    """Get current time in a city"""
    try:
        timezone_map = {
            "london": "Europe/London",
            "paris": "Europe/Paris",
            "new york": "America/New_York",
            "tokyo": "Asia/Tokyo",
            "sydney": "Australia/Sydney",
            "dubai": "Asia/Dubai",
            "singapore": "Asia/Singapore",
            "los angeles": "America/Los_Angeles",
            "chicago": "America/Chicago",
            "toronto": "America/Toronto",
            "mumbai": "Asia/Kolkata",
            "delhi": "Asia/Kolkata",
            "bangalore": "Asia/Kolkata",
            "kolkata": "Asia/Kolkata",
            "beijing": "Asia/Shanghai",
            "moscow": "Europe/Moscow",
            "berlin": "Europe/Berlin",
            "madrid": "Europe/Madrid",
            "rome": "Europe/Rome",
            "amsterdam": "Europe/Amsterdam",
            "hong kong": "Asia/Hong_Kong",
            "bangkok": "Asia/Bangkok",
            "istanbul": "Europe/Istanbul",
            "cairo": "Africa/Cairo",
            "mexico city": "America/Mexico_City",
            "sao paulo": "America/Sao_Paulo",
            "buenos aires": "America/Argentina/Buenos_Aires",
            "johannesburg": "Africa/Johannesburg"
        }
        
        city_lower = city.lower()
        timezone = timezone_map.get(city_lower)
        
        if not timezone:
            return json.dumps({"error": f"Timezone not found for {city}"})
        
        tz = pytz.timezone(timezone)
        current_time = datetime.now(tz)
        
        time_info = {
            "city": city,
            "time": current_time.strftime("%I:%M %p"),
            "date": current_time.strftime("%B %d, %Y"),
            "day": current_time.strftime("%A"),
            "timezone": timezone
        }
        return json.dumps(time_info)
    except Exception as e:
        return json.dumps({"error": str(e)})


# Agent Function 4: Wikipedia Search
def search_wikipedia(query):
    """Search Wikipedia and return summary"""
    try:
        wikipedia.set_lang("en")
        search_results = wikipedia.search(query, results=3)
        
        if not search_results:
            return json.dumps({"error": f"No Wikipedia results found for '{query}'"})
        
        try:
            summary = wikipedia.summary(search_results[0], sentences=4, auto_suggest=False)
            page = wikipedia.page(search_results[0], auto_suggest=False)
            
            wiki_info = {
                "title": page.title,
                "summary": summary,
                "url": page.url
            }
            return json.dumps(wiki_info)
        except wikipedia.exceptions.DisambiguationError as e:
            summary = wikipedia.summary(e.options[0], sentences=4, auto_suggest=False)
            page = wikipedia.page(e.options[0], auto_suggest=False)
            
            wiki_info = {
                "title": page.title,
                "summary": summary,
                "url": page.url
            }
            return json.dumps(wiki_info)
            
    except Exception as e:
        return json.dumps({"error": f"Wikipedia search failed: {str(e)}"})


# Agent Function 5: News Headlines
def get_news(category="general"):
    """Get latest news headlines"""
    try:
        url = "https://feeds.bbci.co.uk/news/rss.xml"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(response.content)
            headlines = []
            for item in root.findall('.//item')[:5]:
                title = item.find('title').text
                headlines.append(title)
            
            return json.dumps({
                "headlines": headlines,
                "source": "BBC News",
                "count": len(headlines)
            })
    except Exception as e:
        return json.dumps({"error": f"Could not fetch news: {str(e)}"})


# Agent Function 6: Currency Converter
def convert_currency(amount, from_currency, to_currency):
    """Convert currency using free exchange rate API"""
    try:
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency.upper()}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()
            rates = data['rates']
            
            if to_currency.upper() not in rates:
                return json.dumps({"error": f"Currency {to_currency} not found"})
            
            converted_amount = float(amount) * rates[to_currency.upper()]
            
            return json.dumps({
                "original_amount": amount,
                "from_currency": from_currency.upper(),
                "to_currency": to_currency.upper(),
                "converted_amount": round(converted_amount, 2),
                "exchange_rate": rates[to_currency.upper()]
            })
        return json.dumps({"error": "Could not fetch exchange rates"})
    except Exception as e:
        return json.dumps({"error": str(e)})


# Agent Function 7: Dictionary
def get_definition(word):
    """Get word definition using Free Dictionary API"""
    try:
        url = f"https://api.dictionaryapi.dev/api/v2/entries/en/{word}"
        response = requests.get(url, timeout=5)
        
        if response.status_code == 200:
            data = response.json()[0]
            
            meanings = []
            for meaning in data.get('meanings', [])[:2]:  # Get first 2 meanings
                part_of_speech = meaning.get('partOfSpeech', '')
                definitions = meaning.get('definitions', [])
                if definitions:
                    meanings.append({
                        "part_of_speech": part_of_speech,
                        "definition": definitions[0].get('definition', ''),
                        "example": definitions[0].get('example', '')
                    })
            
            return json.dumps({
                "word": word,
                "meanings": meanings,
                "phonetic": data.get('phonetic', '')
            })
        return json.dumps({"error": f"Definition not found for '{word}'"})
    except Exception as e:
        return json.dumps({"error": str(e)})
