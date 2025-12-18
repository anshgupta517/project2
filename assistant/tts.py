import tempfile
from gtts import gTTS


def text_to_speech(text):
    """Convert text to speech using Google TTS"""
    try:
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        output_file = temp_file.name
        temp_file.close()
        
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(output_file)
        return output_file
    except Exception as e:
        print(f"TTS Error: {str(e)}")
        return None
