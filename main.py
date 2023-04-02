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
    Telegram(project_name).listen(gpt)
