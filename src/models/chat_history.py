from collections import deque

class ChatMemory:
    def __init__(self, max_len=10):
        self.history = deque(maxlen=max_len)

    def add_user_message(self, message: str):
        self.history.append({"role": "user", "content": message})

    def add_bot_message(self, message: str):
        self.history.append({"role": "assistant", "content": message})

    def get_context(self):
        return list(self.history)

    def clear(self):
        self.history.clear()
