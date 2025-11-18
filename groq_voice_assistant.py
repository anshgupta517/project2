import gradio as gr
from groq import Groq
import os
import requests
import json

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

conversation_history = []

# Agent Function: Weather Lookup
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
                "wind": f"{current['windspeedKmph']} km/h"
            }
            return json.dumps(weather_info)
        return json.dumps({"error": "Could not fetch weather"})
    except Exception as e:
        return json.dumps({"error": str(e)})

# Define tools for the LLM
tools = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather information for a city",
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
                {"role": "system", "content": "You are a helpful voice assistant with access to weather information. When users ask about weather, use the get_weather function. Be concise and friendly."},
                *conversation_history
            ],
            tools=tools,
            tool_choice="auto",
            temperature=0.7,
            max_tokens=200
        )
        
        response_message = response.choices[0].message
        
        # Step 3: Handle tool calls
        if response_message.tool_calls:
            # Execute the function
            tool_call = response_message.tool_calls[0]
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)
            
            if function_name == "get_weather":
                function_response = get_weather(function_args["city"])
                
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
                        {"role": "system", "content": "You are a helpful voice assistant. Present weather information in a natural, conversational way."},
                        *conversation_history
                    ],
                    temperature=0.7,
                    max_tokens=200
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
    # 🤖 AI Voice Assistant with Agent Functionality
    **Real-time Weather Information**
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