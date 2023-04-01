from environs import Env

from chatgpt.chatgpt import ChatGPT
from sqlitedb.sqlite import SQLiteDatabase
from telegram.replier import Telegram

env = Env()
env.read_env()
db = SQLiteDatabase()

if __name__ == "__main__":
    gpt = ChatGPT()
    Telegram("nikhilbadyal").listen(gpt)
