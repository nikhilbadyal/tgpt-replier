from environs import Env

from chatgpt.chatgpt import ChatGPT
from telegram.replier import Telegram

env = Env()
env.read_env()


if __name__ == "__main__":
    gpt = ChatGPT()
    Telegram("nikhilbadyal").listen(gpt)
