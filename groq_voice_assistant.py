import gradio as gr
from groq import Groq
import os
import requests
import json
from datetime import datetime
import pytz
import wikipedia
import edge_tts
import asyncio
from newsapi import NewsApiClient
import tempfile
from dotenv import load_dotenv

# Optional offline TTS fallback
try:
    import pyttsx3
    HAVE_PYTTSX3 = True
except Exception:
    HAVE_PYTTSX3 = False

# Optional online fallback (gTTS)
try:
    from gtts import gTTS
    HAVE_GTTS = True
except Exception:
    HAVE_GTTS = False

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initialize NewsAPI client (get free API key from https://newsapi.org/)
# For now, using a placeholder - replace with your API key
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "your_news_api_key_here")
try:
    newsapi = NewsApiClient(api_key=NEWS_API_KEY)
except:
    newsapi = None

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

# NEW Agent Function 5: News Headlines
def get_news(category="general"):
    """Get latest news headlines"""
    try:
        # Fallback to RSS feed if NewsAPI not available
        if not newsapi or NEWS_API_KEY == "your_news_api_key_here":
            # Using BBC RSS feed as fallback
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
        else:
            # Use NewsAPI
            top_headlines = newsapi.get_top_headlines(
                language='en',
                page_size=5
            )
            
            headlines = [article['title'] for article in top_headlines['articles'][:5]]
            
            return json.dumps({
                "headlines": headlines,
                "count": len(headlines)
            })
    except Exception as e:
        return json.dumps({"error": f"Could not fetch news: {str(e)}"})

# NEW Agent Function 6: Currency Converter
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

# NEW Agent Function 7: Dictionary
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

# Text-to-Speech Function
async def text_to_speech_async(text, voice="en-US-AriaNeural"):
    """Convert text to speech using Edge TTS"""
    try:
        # Create a temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        output_file = temp_file.name
        temp_file.close()

        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(output_file)
        return output_file
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        # Fallback: try offline pyttsx3 if available
        if HAVE_PYTTSX3:
            try:
                return await asyncio.to_thread(_pyttsx3_save, text)
            except Exception as e2:
                print(f"Pyttsx3 fallback failed: {e2}")
        return None


def _pyttsx3_save(text):
    """Save TTS using pyttsx3 to a temporary WAV file (blocking)."""
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
    output_file = temp_file.name
    temp_file.close()

    engine = pyttsx3.init()
    engine.setProperty('rate', 160)
    engine.save_to_file(text, output_file)
    engine.runAndWait()
    try:
        engine.stop()
    except Exception:
        pass
    return output_file

def text_to_speech(text, voice="en-US-AriaNeural"):
    """Synchronous wrapper for text_to_speech"""
    return asyncio.run(text_to_speech_async(text, voice))


def _gtts_save(text, lang='en'):
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
    output_file = temp_file.name
    temp_file.close()
    tts = gTTS(text=text, lang=lang)
    tts.save(output_file)
    return output_file

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

def voice_chat(audio, history, enable_tts, voice_selection):
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
        
        user_message = transcription.text
        
        # Add to internal history
        conversation_history.append({"role": "user", "content": user_message})
        
        # Filter history to only include valid messages for API
        valid_history = []
        for msg in conversation_history:
            if msg.get("role") in ["user", "assistant", "system"] and msg.get("content"):
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
            
            # Add tool call result to simple history (as assistant message for display)
            conversation_history.append({
                "role": "assistant",
                "content": f"Tool {function_name} returned: {function_response}"
            })
            
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
            audio_output = text_to_speech(ai_message, voice_selection)
        
        # Format chat for Gradio depending on Gradio version
        def gradio_supports_messages_format():
            try:
                ver = getattr(gr, "__version__", "")
                parts = ver.split('.')
                major = int(parts[0]) if parts else 0
                minor = int(parts[1]) if len(parts) > 1 else 0
                # Gradio switched to message dicts around 4.44+
                return (major > 4) or (major == 4 and minor >= 44)
            except Exception:
                return False

        if gradio_supports_messages_format():
            # Newer Gradio expects a list of dicts like {role, content}
            chat_display = []
            for msg in conversation_history:
                role = msg.get("role")
                content = msg.get("content")
                if not role or not content:
                    continue
                if role not in ["user", "assistant", "system"]:
                    role = "assistant"
                chat_display.append({"role": role, "content": content})
        else:
            # Older Gradio (like 4.16.0) expects list of [user_text, bot_text] tuples
            chat_display = []
            for msg in conversation_history:
                role = msg.get("role")
                content = msg.get("content")
                if not role or not content:
                    continue
                if role == "user":
                    chat_display.append([content, None])
                elif role == "assistant":
                    if chat_display and chat_display[-1][1] is None:
                        chat_display[-1][1] = content
                    else:
                        chat_display.append([None, content])
        
        status = "✅ Complete"
        
        return chat_display, conversation_history, audio_output, status
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        conversation_history.append({"role": "assistant", "content": error_msg})
        
        # Format for display depending on Gradio version
        def gradio_supports_messages_format():
            try:
                ver = getattr(gr, "__version__", "")
                parts = ver.split('.')
                major = int(parts[0]) if parts else 0
                minor = int(parts[1]) if len(parts) > 1 else 0
                return (major > 4) or (major == 4 and minor >= 44)
            except Exception:
                return False

        if gradio_supports_messages_format():
            chat_display = []
            for msg in conversation_history:
                role = msg.get("role")
                content = msg.get("content")
                if not role or not content:
                    continue
                if role not in ["user", "assistant", "system"]:
                    role = "assistant"
                chat_display.append({"role": role, "content": content})
        else:
            chat_display = []
            for msg in conversation_history:
                role = msg.get("role")
                content = msg.get("content")
                if not role or not content:
                    continue
                if role == "user":
                    chat_display.append([content, None])
                elif role == "assistant":
                    if chat_display and chat_display[-1][1] is None:
                        chat_display[-1][1] = content
                    else:
                        chat_display.append([None, content])
        
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
                info="AI will respond with voice"
            )
            
            voice_selection = gr.Dropdown(
                label="Voice Selection",
                choices=[
                    "en-US-AriaNeural",
                    "en-US-GuyNeural",
                    "en-GB-SoniaNeural",
                    "en-GB-RyanNeural",
                    "en-AU-NatashaNeural",
                    "en-IN-NeerjaNeural"
                ],
                value="en-US-AriaNeural",
                info="Choose AI voice"
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
            ✅ Multi-language Voices
            """)
    
    # Event handlers
    audio_input.stop_recording(
        voice_chat,
        inputs=[audio_input, state, enable_tts, voice_selection],
        outputs=[chatbot, state, audio_output, status_box]
    )
    
    clear_btn.click(
        clear_conversation,
        outputs=[chatbot, state, audio_output, status_box]
    )

if __name__ == "__main__":
    demo.launch(share=False)