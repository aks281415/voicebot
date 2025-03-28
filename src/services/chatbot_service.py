from openai import OpenAI
from src.models.chat_history import ChatMemory
from src.constants import OPENAI_API_KEY, CHATBOT_PROMPT_FILE_PATH, MODEL
from src.utils.file_utils import load_file

client = OpenAI(api_key=OPENAI_API_KEY)

SYSTEM_PROMPT = load_file(CHATBOT_PROMPT_FILE_PATH)
memory = ChatMemory(max_len=10)

def chatbot(user_input):
    memory.add_user_message(user_input)

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT}
    ] + memory.get_context()

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages
    )
    
    reply = response.choices[0].message.content
    memory.add_bot_message(reply)

    return reply