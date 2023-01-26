from aiogram import Bot, Dispatcher, executor, types
from loguru import logger

from create_bot import bot, dp, create_error_message
from handlers import user, admin

user.register_user_handlers(dp)
admin.register_admin_handlers(dp)


async def on_startup(_):
    bot.setup_resources()


async def on_shutdown(_):
    bot.shutdown()


if __name__ == '__main__':
    logger.add('logs.log', enqueue=True)
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=on_shutdown)
