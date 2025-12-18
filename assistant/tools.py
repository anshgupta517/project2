import json

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
