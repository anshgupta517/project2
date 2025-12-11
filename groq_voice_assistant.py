import gradio as gr
from groq import Groq
import os
import requests
import json
from datetime import datetime
import pytz
import wikipedia
import tempfile
from dotenv import load_dotenv
from gtts import gTTS

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initialize NewsAPI client (get free API key from https://newsapi.org/)
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "your_news_api_key_here")

conversation_history = []

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
        # Common timezone mappings
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
        # Using BBC RSS feed
        url = "https://feeds.bbci.co.uk/news/rss.xml"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            # Simple parsing of RSS feed
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

# Text-to-Speech Function using gTTS (Google TTS)
def text_to_speech(text):
    """Convert text to speech using Google TTS"""
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        output_file = temp_file.name
        temp_file.close()
        
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_file)
        return output_file
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return None

# Define tools for the LLM
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a city. Use this when users ask about weather, temperature, or climate conditions.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g., London, New York, Tokyo"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Perform mathematical calculations. Use this for math problems, percentages, conversions, etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The mathematical expression to evaluate, e.g., '15 * 20', '100 / 4', '(50 + 30) * 2'"
                    }
                },
                "required": ["expression"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_world_time",
            "description": "Get the current time and date in any major city. Use this when users ask 'what time is it in...', 'current time in...', etc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The city name, e.g., London, New York, Tokyo, Paris"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_wikipedia",
            "description": "Search Wikipedia for information about any topic - people, places, concepts, events, etc. Use this when users ask 'who is', 'what is', 'tell me about', or want to learn about something.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "The topic to search for on Wikipedia, e.g., 'Albert Einstein', 'Quantum Computing', 'Eiffel Tower'"
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_news",
            "description": "Get latest news headlines. Use this when users ask about news, current events, or what's happening in the world.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "News category (general, business, technology, sports, etc.)",
                        "default": "general"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "convert_currency",
            "description": "Convert amount from one currency to another. Use this when users ask to convert money or currency exchange rates.",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The amount to convert"
                    },
                    "from_currency": {
                        "type": "string",
                        "description": "Source currency code, e.g., USD, EUR, GBP, INR"
                    },
                    "to_currency": {
                        "type": "string",
                        "description": "Target currency code, e.g., USD, EUR, GBP, INR"
                    }
                },
                "required": ["amount", "from_currency", "to_currency"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_definition",
            "description": "Get the definition and meaning of a word. Use this when users ask 'what does X mean', 'define X', or want to know word meanings.",
            "parameters": {
                "type": "object",
                "properties": {
                    "word": {
                        "type": "string",
                        "description": "The word to define"
                    }
                },
                "required": ["word"]
            }
        }
    }
]

def voice_chat(audio, history, enable_tts):
    """Process voice input and return AI response with agent functionality"""
    
    global conversation_history
    
    if audio is None:
        return history, conversation_history, None, "⚪ Ready"
    
    try:
        # Update status
        status = "🎤 Transcribing..."
        
        # Step 1: Transcribe audio
        with open(audio, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio, file.read()),
                model="whisper-large-v3",
            )
        
        user_message = transcription.text.strip()

        # Add to internal history with simple dedupe to avoid duplicate transcriptions
        # If the last user message is identical to the new transcription, skip appending.
        try:
            last_user = None
            for msg in reversed(conversation_history):
                if msg.get("role") == "user" and msg.get("content"):
                    last_user = msg.get("content").strip()
                    break

            if last_user is None or last_user != user_message:
                conversation_history.append({"role": "user", "content": user_message})
            else:
                # Duplicate detected — ignore this transcription to prevent double input
                print("[groq_voice_assistant] Ignored duplicate user transcription")
        except Exception:
            # On any unexpected error, fall back to appending the message
            conversation_history.append({"role": "user", "content": user_message})
        
        # Filter history to only include valid messages for API (only user and assistant)
        valid_history = []
        for msg in conversation_history:
            if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                valid_history.append({"role": msg["role"], "content": msg["content"]})
        
        status = "🤖 Processing..."
        
        # Step 2: Get AI response with tool calling
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant with access to weather, calculator, world time, Wikipedia, news, currency conversion, and dictionary. Use the appropriate tool when users ask relevant questions. Be concise and friendly."},
                *valid_history
            ],
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=300
        )
        
        response_message = response.choices[0].message
        
        # Step 3: Handle tool calls
        if response_message.tool_calls:
            status = "🔧 Using tools..."
            
            # Execute the function
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            # Call the appropriate function
            if function_name == "get_weather":
                function_response = get_weather(function_args["city"])
            elif function_name == "calculate":
                function_response = calculate(function_args["expression"])
            elif function_name == "get_world_time":
                function_response = get_world_time(function_args["city"])
            elif function_name == "search_wikipedia":
                function_response = search_wikipedia(function_args["query"])
            elif function_name == "get_news":
                function_response = get_news(function_args.get("category", "general"))
            elif function_name == "convert_currency":
                function_response = convert_currency(
                    function_args["amount"],
                    function_args["from_currency"],
                    function_args["to_currency"]
                )
            elif function_name == "get_definition":
                function_response = get_definition(function_args["word"])
            else:
                function_response = json.dumps({"error": "Unknown function"})
            
            # Get final response with function result
            final_messages = [
                {"role": "system", "content": "You are a helpful voice assistant. Present information in a natural, conversational way. Keep responses concise."}
            ]
            
            # Add user message
            final_messages.append({"role": "user", "content": user_message})
            
            # Add tool result as context
            final_messages.append({
                "role": "user", 
                "content": f"Based on this information: {function_response}, please provide a natural response."
            })
            
            final_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=final_messages,
                temperature=0.7,
                max_tokens=300
            )
            
            ai_message = final_response.choices[0].message.content
        else:
            ai_message = response_message.content
        
        # Add AI response to history
        conversation_history.append({"role": "assistant", "content": ai_message})
        
        # Generate TTS if enabled
        audio_output = None
        if enable_tts and ai_message:
            status = "🔊 Generating speech..."
            audio_output = text_to_speech(ai_message)
        
        # Format for Gradio chatbot display (list of [user, bot] pairs)
        chat_display = []
        for msg in conversation_history:
            if msg.get("role") == "user" and msg.get("content"):
                chat_display.append([msg["content"], None])
            elif msg.get("role") == "assistant" and msg.get("content"):
                if chat_display and chat_display[-1][1] is None:
                    chat_display[-1][1] = msg["content"]
                else:
                    chat_display.append([None, msg["content"]])
        
        status = "✅ Complete"
        
        return chat_display, conversation_history, audio_output, status
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        conversation_history.append({"role": "assistant", "content": error_msg})
        
        # Format for display
        chat_display = []
        for msg in conversation_history:
            if msg.get("role") == "user" and msg.get("content"):
                chat_display.append([msg["content"], None])
            elif msg.get("role") == "assistant" and msg.get("content"):
                if chat_display and chat_display[-1][1] is None:
                    chat_display[-1][1] = msg["content"]
                else:
                    chat_display.append([None, msg["content"]])
        
        return chat_display, conversation_history, None, "❌ Error"

def clear_conversation():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return [], [], None, "⚪ Ready"

# Create enhanced Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), css="""
    .gradio-container {
        max-width: 1200px !important;
    }
    .status-box {
        padding: 10px;
        border-radius: 8px;
        text-align: center;
        font-weight: bold;
    }
""") as demo:
    
    # Header
    gr.Markdown("""
    # 🤖 AI Voice Assistant with Multi-Agent System
    **7 Agents:** Weather | Calculator | World Time | Wikipedia | News | Currency | Dictionary
    """)
    
    # State to hold conversation history
    state = gr.State([])
    
    with gr.Row():
        with gr.Column(scale=3):
            # Status indicator
            status_box = gr.Textbox(
                value="⚪ Ready",
                label="Status",
                interactive=False,
                elem_classes="status-box"
            )
            
            # Chat interface
            chatbot = gr.Chatbot(
                label="Conversation",
                height=400
            )
            
            with gr.Row():
                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎤 Click to Record Your Voice"
                )
            
            # Audio output for TTS
            audio_output = gr.Audio(
                label="🔊 AI Voice Response",
                autoplay=True,
                visible=True
            )
            
            with gr.Row():
                clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary", size="sm")
        
        with gr.Column(scale=1):
            gr.Markdown("### ⚙️ Settings")
            
            enable_tts = gr.Checkbox(
                label="Enable Voice Response",
                value=True,
                info="AI will respond with voice (Google TTS)"
            )
            
            gr.Markdown("### 📋 Example Queries")
            gr.Markdown("""
            - "What's the weather in London?"
            - "Calculate 15 times 20"
            - "What time is it in Tokyo?"
            - "Tell me about Albert Einstein"
            - "What's the latest news?"
            - "Convert 100 USD to EUR"
            - "Define serendipity"
            """)
            
            gr.Markdown("### 🎯 Features")
            gr.Markdown("""
            ✅ Voice Input & Output
            ✅ 7 AI Agents
            ✅ Real-time Processing
            ✅ Google Text-to-Speech
            """)
    
    # Event handlers
    audio_input.stop_recording(
        voice_chat,
        inputs=[audio_input, state, enable_tts],
        outputs=[chatbot, state, audio_output, status_box]
    )
    
    clear_btn.click(
        clear_conversation,
        outputs=[chatbot, state, audio_output, status_box]
    )

if __name__ == "__main__":
    demo.launch(share=False)