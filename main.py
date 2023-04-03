from environs import Env

from chatgpt.chatgpt import ChatGPT
from sqlitedb.sqlite import SQLiteDatabase
from telegram.replier import Telegram

project_name = "tgpt-replier"
env = Env()
env.read_env()
db = SQLiteDatabase(project_name)
if __name__ == "__main__":
    gpt = ChatGPT()
    if env.str("BOT_TOKEN", None):
        Telegram(project_name).bot_listener(gpt)
    else:
        Telegram(project_name).private_listen(gpt)
