from aiogram import types, Dispatcher

from config import ADMIN_ID
from create_bot import bot
from handlers.user import prepare_message_text
from create_bot import create_error_message

is_admin = lambda message: message.from_user.id == int(ADMIN_ID)

async def setbalance(message: types.Message):
    try:
        try:
            payee = message.text.split()[1]
        except IndexError:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Укажите имя получателя'))
            return

        try:
            sum = int(message.text.split()[2])
        except IndexError:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Укажите сумму'))
            return
        except ValueError:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Укажите корректную сумму'))
            return

        if not (user := bot.user_actioner.get_user_by_username(payee)):
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Пользователь не найден'))
            return
        else:
            user_id = user[0]

        bot.user_actioner.update_balance(user_id, sum)

        await bot.send_message(message.chat.id, prepare_message_text(message, f'Деньги отправлены {user[2]}'))
    except Exception as err:
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})

def register_admin_handlers(dp: Dispatcher):
    dp.register_message_handler(setbalance, is_admin, commands=['setbalance', 'setb'])
