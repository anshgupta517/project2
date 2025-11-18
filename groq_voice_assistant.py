import gradio as gr
from groq import Groq
import os

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

conversation_history = []

def voice_chat(audio):
    """Process voice input and return AI response"""
    
    # Step 1: Transcribe audio
    with open(audio, "rb") as file:
        transcription = client.audio.transcriptions.create(
            file=(audio, file.read()),
            model="whisper-large-v3",
        )
    
    user_message = transcription.text
    conversation_history.append({"role": "user", "content": user_message})
    
    # Step 2: Get AI response
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful assistant. Be concise."},
            *conversation_history
        ],
        temperature=0.7,
        max_tokens=150
    )
    
    ai_message = response.choices[0].message.content
    conversation_history.append({"role": "assistant", "content": ai_message})
    
    # Format conversation for display
    chat_display = ""
    for msg in conversation_history[-6:]:  # Show last 3 exchanges
        role = "You" if msg["role"] == "user" else "AI"
        chat_display += f"**{role}:** {msg['content']}\n\n"
    
    return chat_display

# Create interface
demo = gr.Interface(
    fn=voice_chat,
    inputs=gr.Audio(sources=["microphone"], type="filepath", label="🎤 Speak"),
    outputs=gr.Markdown(label="💬 Conversation"),
    title="🤖 Free Voice Assistant",
    description="Powered by Groq (100% Free). Click record, speak, and get instant AI responses!",
    theme=gr.themes.Soft()
)

if __name__ == "__main__":
    demo.launch()