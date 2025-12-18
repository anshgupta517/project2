import os

# Disable Gradio analytics to avoid outgoing telemetry requests that may hang
# Set before importing gradio so the analytics thread is not started.
os.environ.setdefault("GRADIO_ANALYTICS_ENABLED", "false")

import gradio as gr
from assistant.core import voice_chat, clear_conversation


def build_ui():
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
        
        gr.Markdown("""
        # AI Voice Assistant with Multi-Agent System
        **7 Agents:** Weather | Calculator | World Time | Wikipedia | News | Currency | Dictionary
        """)
        
        state = gr.State([])
        
        with gr.Row():
            with gr.Column(scale=3):
                status_box = gr.Textbox(
                    value="⚪ Ready",
                    label="Status",
                    interactive=False,
                    elem_classes="status-box"
                )
                
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

        audio_input.stop_recording(
            voice_chat,
            inputs=[audio_input, state, enable_tts],
            outputs=[chatbot, state, audio_output, status_box]
        )

        clear_btn.click(
            clear_conversation,
            outputs=[chatbot, state, audio_output, status_box]
        )

    return demo


demo = build_ui()
