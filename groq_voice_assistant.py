"""Launcher for the modular AI voice assistant UI."""

from assistant import ui


if __name__ == "__main__":
    try:
        ui.demo.launch(share=False)
    except Exception as e:
        print(f"Failed to launch the UI: {str(e)}")

