import os
from dotenv import load_dotenv
import pyaudio

load_dotenv(".env")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CHATBOT_PROMPT_FILE_PATH = "config/prompts/chatbot-prompt-file.txt"
MODEL = "gpt-4o"

# PyAudio settings
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
CHUNK = 1024
CHUNK_DURATION_SEC = 1
MAX_DURATION=12
SILENCE_THRESHOLD=6
SPEECH_THRESHOLD=200