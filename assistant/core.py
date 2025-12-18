import json
import assistant
from assistant import agents
from assistant import tts as tts_module
from assistant import tools as tools_module

# Bring over tools in the same shape the original code expected
tools = tools_module.tools


def _build_chat_display(conv_history):
    chat_display = []
    for msg in conv_history:
        if msg.get("role") == "user" and msg.get("content"):
            chat_display.append([msg["content"], None])
        elif msg.get("role") == "assistant" and msg.get("content"):
            if chat_display and chat_display[-1][1] is None:
                chat_display[-1][1] = msg["content"]
            else:
                chat_display.append([None, msg["content"]])
    return chat_display


def voice_chat(audio, history, enable_tts):
    """Process voice input and return AI response with agent functionality"""
    # use shared conversation history from package
    conversation_history = assistant.conversation_history

    if audio is None:
        print("[voice_chat] No audio provided")
        return history, conversation_history, None, "⚪ Ready"

    try:
        print("[voice_chat] Transcribing audio...")
        status = "🎤 Transcribing..."

        # Step 1: Transcribe audio
        with open(audio, "rb") as file:
            transcription = assistant.client.audio.transcriptions.create(
                file=(audio, file.read()),
                model="whisper-large-v3",
            )

        user_message = transcription.text.strip()

        print(f"[voice_chat] Transcription: {user_message}")

        # Add to internal history with simple dedupe
        try:
            last_user = None
            for msg in reversed(conversation_history):
                if msg.get("role") == "user" and msg.get("content"):
                    last_user = msg.get("content").strip()
                    break

            if last_user is None or last_user != user_message:
                print(f"[voice_chat] Adding to conversation history: {user_message}")
                conversation_history.append({"role": "user", "content": user_message})
            else:
                # Duplicate detected — ignore this transcription to prevent double input
                print(f"[voice_chat] Ignored duplicate user transcription: {user_message}")
                chat_display = _build_chat_display(conversation_history)

                status = "⚪ Ready"
                return chat_display, conversation_history, None, status
        except Exception as e:
            print(f"[voice_chat] Error when adding to conversation history: {str(e)}")
            conversation_history.append({"role": "user", "content": user_message})

        # Filter history to only include valid messages for API (only user and assistant)
        valid_history = []
        for msg in conversation_history:
            if msg.get("role") in ["user", "assistant"] and msg.get("content"):
                valid_history.append({"role": msg["role"], "content": msg["content"]})

        print(f"[voice_chat] Valid history: {valid_history}")

        status = "🤖 Processing..."

        # Step 2: Get AI response with tool calling
        try:
            response = assistant.client.chat.completions.create(
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
        except Exception as e:
            print(f"[voice_chat] Chat completion failed: {str(e)}")

            lowered = user_message.lower()
            if any(k in lowered for k in ("tell me about", "tell me something about", "who is", "what is", "what are")):
                wiki_result = agents.search_wikipedia(user_message)
                try:
                    wiki_json = json.loads(wiki_result)
                    if "error" not in wiki_json:
                        ai_message = f"{wiki_json.get('title')}: {wiki_json.get('summary')} (More: {wiki_json.get('url', '')})"
                    else:
                        ai_message = wiki_json.get("error")
                except Exception:
                    ai_message = wiki_result

                conversation_history.append({"role": "assistant", "content": ai_message})

                audio_output = None
                if enable_tts and ai_message:
                    print(f"[voice_chat] Generating speech from: {ai_message}")
                    audio_output = tts_module.text_to_speech(ai_message)

                chat_display = _build_chat_display(conversation_history)

                status = "✅ Complete"
                return chat_display, conversation_history, audio_output, status
            raise

        response_message = response.choices[0].message

        # Step 3: Handle tool calls
        if getattr(response_message, "tool_calls", None):
            print("[voice_chat] Using tools...")
            status = "🔧 Using tools..."
            tool_call = response_message.tool_calls[0] if response_message.tool_calls else None
            function_name = tool_call.function.name
            function_args = json.loads(tool_call.function.arguments)

            if function_name == "get_weather":
                function_response = agents.get_weather(function_args["city"])
            elif function_name == "calculate":
                function_response = agents.calculate(function_args["expression"])
            elif function_name == "get_world_time":
                function_response = agents.get_world_time(function_args["city"])
            elif function_name == "search_wikipedia":
                function_response = agents.search_wikipedia(function_args["query"])
            elif function_name == "get_news":
                function_response = agents.get_news(function_args.get("category", "general"))
            elif function_name == "convert_currency":
                function_response = agents.convert_currency(
                    function_args["amount"],
                    function_args["from_currency"],
                    function_args["to_currency"]
                )
            elif function_name == "get_definition":
                function_response = agents.get_definition(function_args["word"])
            else:
                function_response = json.dumps({"error": "Unknown function"})

            final_messages = [
                {"role": "system", "content": "You are a helpful voice assistant. Present information in a natural, conversational way. Keep responses concise."}
            ]
            final_messages.append({"role": "user", "content": user_message})
            final_messages.append({
                "role": "user",
                "content": f"Based on this information: {function_response}, please provide a natural response."
            })

            try:
                final_response = assistant.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=final_messages,
                    temperature=0.7,
                    max_tokens=300
                )
                ai_message = final_response.choices[0].message.content
            except Exception as e_final:
                # If the final model call fails (tool-use / generation errors), fallback
                print(f"[voice_chat] Final response creation failed: {str(e_final)}")
                try:
                    parsed = json.loads(function_response)
                    if isinstance(parsed, dict) and "error" not in parsed:
                        # Wikipedia-like result
                        if "title" in parsed and "summary" in parsed:
                            ai_message = f"{parsed.get('title')}: {parsed.get('summary')} (More: {parsed.get('url', '')})"
                        # News headlines
                        elif "headlines" in parsed:
                            ai_message = "Top headlines: " + "; ".join(parsed.get('headlines', []))
                        # Currency / simple numeric responses
                        else:
                            ai_message = str(parsed)
                    else:
                        ai_message = parsed.get("error") if isinstance(parsed, dict) else str(parsed)
                except Exception:
                    # As a last resort, return the raw function response string
                    ai_message = function_response
        else:
            ai_message = response_message.content

        print(f"[voice_chat] AI message: {ai_message}")

        conversation_history.append({"role": "assistant", "content": ai_message})

        audio_output = None
        if enable_tts and ai_message:
            print(f"[voice_chat] Generating speech from: {ai_message}")
            audio_output = tts_module.text_to_speech(ai_message)

        chat_display = _build_chat_display(conversation_history)

        status = "✅ Complete"
        return chat_display, conversation_history, audio_output, status

    except Exception as e:
        print(f"[voice_chat] Error in voice chat: {str(e)}")
        error_msg = f"Error: {str(e)}"
        conversation_history.append({"role": "assistant", "content": error_msg})
        chat_display = _build_chat_display(conversation_history)
        return chat_display, conversation_history, None, "❌ Error"


def clear_conversation():
    assistant.conversation_history = []
    return [], [], None, "⚪ Ready"
