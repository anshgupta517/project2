"""Flask launcher that starts the Gradio UI in a background thread.

Run this file to start a Flask server (with auto-reload) and have the
Gradio demo served alongside it. The root route redirects to the Gradio UI.
"""

import os
import threading
from flask import Flask, redirect

from assistant import ui

app = Flask(__name__)

_gradio_started = False

def start_gradio():
    global _gradio_started
    if _gradio_started:
        return
    _gradio_started = True
    # prevent_thread_lock allows Gradio to run inside a background thread
    ui.demo.launch(share=False, prevent_thread_lock=True)


@app.route("/")
def index():
    # Redirect to the default local Gradio address
    return redirect("http://127.0.0.1:7860/")


if __name__ == "__main__":
    # Only start Gradio in the reloader child process to avoid double starts.
    # Werkzeug sets WERKZEUG_RUN_MAIN to 'true' in the reloader child.
    should_start_gradio = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    if should_start_gradio:
        t = threading.Thread(target=start_gradio, daemon=True)
        t.start()

    # Start Flask in debug mode so it reloads on file changes.
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=True)
