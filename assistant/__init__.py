import os
from dotenv import load_dotenv
from groq import Groq

# Load environment variables from .env file
load_dotenv()

# Initialize Groq client
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

# Initialize NewsAPI client key placeholder
NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "your_news_api_key_here")

# Shared conversation history (mutable list)
conversation_history = []
