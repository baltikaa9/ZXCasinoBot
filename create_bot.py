from datetime import datetime

from aiogram import Bot, Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from config import BOT_TOKEN, TG_API_URL, ADMIN_ID
from clients.telegram_client import TelegramClient
from clients.sqlite_client import SQLiteClient
from clients.user_actioner import UserActioner


class MyBot(Bot):
    def __init__(self, tg_client: TelegramClient, user_actioner: UserActioner, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tg_client = tg_client
        self.user_actioner = user_actioner

    def setup_resources(self):
        self.user_actioner.setup()

    def shutdown(self):
        self.user_actioner.shutdown()


telegram_client = TelegramClient(token=BOT_TOKEN, base_url=TG_API_URL)  # для отправки сырых запросов
user_actioner = UserActioner(SQLiteClient('clients/users.db'))
bot = MyBot(token=BOT_TOKEN, tg_client=telegram_client, user_actioner=user_actioner)
dp = Dispatcher(bot, storage=MemoryStorage())

def create_error_message(err: Exception) -> str:
    return f'{datetime.now()} : {err.__class__} : {err}'

if __name__ == '__main__':
    params = {'chat_id': ADMIN_ID, 'text': 'uwu'}
