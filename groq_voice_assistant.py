import gradio as gr
from groq import Groq
import os
import requests
import json
from datetime import datetime
import pytz

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

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
    }
]

def voice_chat(audio, history):
    """Process voice input and return AI response with agent functionality"""
    
    if audio is None:
        return history, conversation_history
    
    try:
        # Step 1: Transcribe audio
        with open(audio, "rb") as file:
            transcription = client.audio.transcriptions.create(
                file=(audio, file.read()),
                model="whisper-large-v3",
            )
        
        user_message = transcription.text
        
        # Add to internal history
        conversation_history.append({"role": "user", "content": user_message})
        
        # Step 2: Get AI response with tool calling
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a helpful voice assistant with access to weather information, calculator, and world time. Use the appropriate tool when users ask relevant questions. Be concise and friendly."},
                *conversation_history
            ],
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=250
        )
        
        response_message = response.choices[0].message
        
        # Step 3: Handle tool calls
        if response_message.tool_calls:
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
            else:
                function_response = json.dumps({"error": "Unknown function"})
            
            # Add function call to history
            conversation_history.append({
                "role": "assistant",
                "content": None,
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "arguments": tool_call.function.arguments
                        }
                    }
                ]
            })
            
            conversation_history.append({
                "role": "tool",
                "content": function_response,
                "tool_call_id": tool_call.id
            })
            
            # Get final response with function result
            final_response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful voice assistant. Present information in a natural, conversational way."},
                    *conversation_history
                ],
                temperature=0.7,
                max_tokens=250
            )
            
            ai_message = final_response.choices[0].message.content
        else:
            ai_message = response_message.content
        
        # Add AI response to history
        conversation_history.append({"role": "assistant", "content": ai_message})
        
        # Format for Gradio chatbot display (list of tuples)
        chat_display = []
        for msg in conversation_history:
            if msg["role"] == "user":
                chat_display.append((msg["content"], None))
            elif msg["role"] == "assistant" and msg.get("content"):
                # Update last user message to include AI response
                if chat_display and chat_display[-1][1] is None:
                    chat_display[-1] = (chat_display[-1][0], msg["content"])
                else:
                    chat_display.append((None, msg["content"]))
        
        return chat_display, conversation_history
        
    except Exception as e:
        error_msg = f"Error: {str(e)}"
        conversation_history.append({"role": "assistant", "content": error_msg})
        
        # Format for display
        chat_display = []
        for msg in conversation_history:
            if msg["role"] == "user":
                chat_display.append((msg["content"], None))
            elif msg["role"] == "assistant" and msg.get("content"):
                if chat_display and chat_display[-1][1] is None:
                    chat_display[-1] = (chat_display[-1][0], msg["content"])
                else:
                    chat_display.append((None, msg["content"]))
        
        return chat_display, conversation_history

def clear_conversation():
    """Clear conversation history"""
    global conversation_history
    conversation_history = []
    return [], []

# Create enhanced Gradio interface
with gr.Blocks(theme=gr.themes.Soft(), css="""
    .gradio-container {
        max-width: 1000px !important;
    }
""") as demo:
    
    # Header
    gr.Markdown("""
    # 🤖 AI Voice Assistant with Multi-Agent System
    **Weather | Calculator | World Time | Powered by Groq AI**
    """)
    
    # State to hold conversation history
    state = gr.State([])
    
    with gr.Row():
        with gr.Column(scale=3):
            # Chat interface
            chatbot = gr.Chatbot(
                label="Conversation",
                height=450,
                avatar_images=(None, "🤖")
            )
            
            with gr.Row():
                audio_input = gr.Audio(
                    sources=["microphone"],
                    type="filepath",
                    label="🎤 Click to Record Your Voice"
                )
            
            with gr.Row():
                clear_btn = gr.Button("Clear Chat", variant="secondary", size="sm")
        
        with gr.Column(scale=1):
            gr.Markdown("""
            ### 🌤️ Weather Agent
            - "Weather in London?"
            - "How's Tokyo today?"
            
            ### 🧮 Calculator Agent
            - "What's 15% of 2500?"
            - "Calculate 48 * 37"
            - "What's 1024 / 8?"
            
            ### 🌍 World Time Agent
            - "What time in Tokyo?"
            - "Current time in Paris?"
            - "Time in New York?"
            
            ### 💬 General Chat
            - "Tell me a joke"
            - "How are you?"
            
            ---
            
            ✅ Voice Recognition  
            ✅ 3 Agent Functions  
            ✅ Context Memory  
            """)
    
    # Event handlers
    audio_input.stop_recording(
        voice_chat,
        inputs=[audio_input, state],
        outputs=[chatbot, state]
    )
    
    clear_btn.click(
        clear_conversation,
        outputs=[chatbot, state]
    )

if __name__ == "__main__":
    demo.launch(share=False)