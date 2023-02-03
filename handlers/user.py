import asyncio
import random
from datetime import date

from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.utils.exceptions import RetryAfter
from loguru import logger

from config import ADMIN_ID
from create_bot import bot, create_error_message


def prepare_message_text(message: types.Message, text: str):
    return text if (
            message.chat.type == 'private' or message.from_user.first_name is None) else f'{message.from_user.first_name}, {text}'


async def except_flood_control(message: types.Message, error: RetryAfter):
    logger.exception(error)
    bot.tg_client.post('SendSticker',
                       params={'chat_id': message.chat.id,
                               'sticker': 'CAACAgIAAxkBAAIMi2O7PIfuVdj9f7kWnlBsATYR04XfAAIVAQACakzKJOMhpgmhfoV6LQQ'})
    bot.tg_client.post('SendMessage',
                       params={'chat_id': message.chat.id, 'text': f'Пожалуйста подождите {error.timeout} секунд'})
    await asyncio.sleep(error.timeout)


async def parse_bet(message: types.Message, game: str):
    try:
        bet = message.text.split()[1]
        if bet == 'all':
            return bet
        else:
            bet = int(bet)
        if bet <= 0:
            raise ValueError
    except (IndexError, ValueError):
        match game:
            case 'slots':
                await message.answer(prepare_message_text(message, 'Сделайте ставку (/slots <ставка>)'))
            case 'dice':
                await message.answer(prepare_message_text(message, 'Сделайте ставку (/dice <ставка>)'))
        return
    return bet


def check_user_existence(func):
    async def _wrapper(message: types.Message):
        if not bot.user_actioner.user_exists(message.from_user.id):
            await bot.send_message(message.chat.id,
                                   prepare_message_text(message, 'Пожалуйста зарегистрируйтесь (/start).'))
        else:
            await func(message)
    return _wrapper


async def help(message: types.Message):
    await bot.send_message(message.chat.id, '/slots (/s) <ставка> - крутить слоты 🎰\n'
                                            '/dice (/d) <ставка> - игра в кости 🎲\n'
                                            '/shell - игра в наперстки 🛢 (5 раз в день)\n'
                                            '/balance (/b) - узнать свой баланс\n'
                                            '/free - подачки для бедных (в разработке)\n'
                                            '/give <username> <amount> - передать пользователю <username> <amount> денег (Пример: /give soslblbu 10000)\n'
                                            '/top - топ игроков')


async def start(message: types.Message):
    try:
        user_id = message.from_user.id
        username = message.from_user.username
        firstname = message.from_user.first_name if message.from_user.first_name is not None else username
        create_new_user = False

        user = bot.user_actioner.get_user(user_id)
        if not user:
            bot.user_actioner.create_user(user_id, username, firstname, 10000, date.today(), 0)
            create_new_user = True

        await bot.send_message(message.chat.id, prepare_message_text(message,
                                                                     f'Вы {"уже" if not create_new_user else "успешно"} зарегистрированы.'))
        await bot.send_message(message.chat.id,
                               prepare_message_text(message, 'Чтобы узнать команды введите /help или /?'))
    except Exception as err:
        logger.exception(err)
        bot.tg_client.post('SendMessage', params={'chat_id': message.chat.id, 'text': 'Что-то пошло не так 😕'})
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})


@check_user_existence
async def slots(message: types.Message):
    double_combinations = [2, 3, 4, 6, 11, 16, 17, 21, 23, 24, 27, 32, 33, 38, 41, 42, 44, 48, 49, 54, 59, 61, 62, 63]
    triple_combinations = [1, 22, 43]
    try:
        # if not bot.user_actioner.user_exist(message.from_user.id):
        #     await bot.send_message(message.chat.id,
        #                            prepare_message_text(message, 'Пожалуйста зарегистрируйтесь (/start).'))
        #     return

        balance = bot.user_actioner.get_balance(message.from_user.id)

        bet = await parse_bet(message, game='slots')
        if bet is None:
            return
        elif bet == 'all':
            bet = balance

        if bet > balance:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Недостаточно денег 😆'))
        else:
            await bot.send_message(message.chat.id, prepare_message_text(message, f'Ваша ставка: {bet}'))
            try:
                value = (await bot.send_dice(message.chat.id, emoji='🎰', disable_notification=True)).dice.value
            except RetryAfter as err:
                await except_flood_control(message=message, error=err)
                value = (await bot.send_dice(message.chat.id, emoji='🎰', disable_notification=True)).dice.value

            await asyncio.sleep(1.7)

            if value in double_combinations:
                kf = 1.3
            elif value in triple_combinations:
                kf = 10.6
            elif value == 64:
                kf = 77.7
                await bot.send_message(message.chat.id, prepare_message_text(message, 'Ураааа Джекпот'))
                await bot.send_sticker(message.chat.id,
                                       sticker='CAACAgIAAxkBAAIFLmO55fvi8ZcfP8WD_kF20AFW0FiUAAL9EgACb_UgSEvMq_w7YHwjLQQ')
            else:
                kf = 0
                await bot.send_sticker(message.chat.id,
                                       sticker='CAACAgIAAxkBAAIFJWO55ZXFOtwIjNCHNuAJ-ua9IA0cAALCFAACgIlASIt6Bgox9eyvLQQ')

            prize = int(bet * kf)
            await bot.send_message(message.chat.id, prepare_message_text(message, f'Вы выиграли {prize}'))

            bot.user_actioner.update_balance(message.from_user.id, balance - bet + prize)
    except Exception as err:
        logger.exception(err)
        bot.tg_client.post('SendMessage', params={'chat_id': message.chat.id, 'text': 'Что-то пошло не так 😕'})
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})


class GameDice(StatesGroup):
    user_die = State()


async def throw_dice(bet: int, message: types.Message, state: FSMContext):
    try:
        value = (await bot.send_dice(message.chat.id, emoji='🎲', disable_notification=True)).dice.value
    except RetryAfter as err:
        await except_flood_control(message=message, error=err)
        value = (await bot.send_dice(message.chat.id, emoji='🎲', disable_notification=True)).dice.value

    await asyncio.sleep(3.5)
    await bot.send_message(message.chat.id, prepare_message_text(message, 'Ваша очередь бросать'))
    await state.update_data(bot_value=value, bet=bet)
    await state.set_state(GameDice.user_die)


@check_user_existence
async def dice_start(message: types.Message, state: FSMContext):
    try:
        # if not bot.user_actioner.user_exist(message.from_user.id):
        #     await bot.send_message(message.chat.id,
        #                            prepare_message_text(message, 'Пожалуйста зарегистрируйтесь (/start).'))
        #     return

        balance = bot.user_actioner.get_balance(message.from_user.id)

        bet = await parse_bet(message, game='dice')
        if bet is None:
            return
        elif bet == 'all':
            bet = balance

        if bet > balance:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Недостаточно денег 😆'))
        else:
            await bot.send_message(message.chat.id, prepare_message_text(message, f'Ваша ставка: {bet}'))
            await throw_dice(bet, message=message, state=state)
    except Exception as err:
        logger.exception(err)
        bot.tg_client.post('SendMessage', params={'chat_id': message.chat.id, 'text': 'Что-то пошло не так 😕'})
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})


async def dice_finish_correct(message: types.Message, state: FSMContext):
    try:
        await asyncio.sleep(3.5)
        value = message.dice.value
        bot_value = (await state.get_data())["bot_value"]
        bet = (await state.get_data())["bet"]
        balance = bot.user_actioner.get_balance(message.from_user.id)

        if value > bot_value:
            await bot.send_message(message.chat.id, prepare_message_text(message, f'Вы выиграли {bet} zxcoins 😕'))
            await bot.send_sticker(message.chat.id,
                                   sticker='CAACAgIAAxkBAAIFwGO56ReZHVjKSw1J3Z5buHwCNH4HAAJHAQACe04qEC2-TTtxjiCwLQQ')
            bot.user_actioner.update_balance(message.from_user.id, balance + bet)
        elif value < bot_value:
            await bot.send_message(message.chat.id, prepare_message_text(message, f'Вы проиграли {bet} zxcoins 🤗'))
            await bot.send_sticker(message.chat.id,
                                   sticker='CAACAgIAAxkBAAIFV2O55vBU3GjUixXYVmN0HuPf9nJ4AAJyAQACe04qECgVel2DlZ_HLQQ')
            bot.user_actioner.update_balance(message.from_user.id, balance - bet)
        else:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Ничья, кидаем еще раз'))
            await throw_dice(bet, message=message, state=state)
            return

        await state.finish()
    except Exception as err:
        logger.exception(err)
        bot.tg_client.post('SendMessage', params={'chat_id': message.chat.id, 'text': 'Что-то пошло не так 😕'})
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})


async def dice_finish_incorrect(message: types.Message, state: FSMContext):
    await bot.send_message(message.chat.id, prepare_message_text(message, 'Кидай кубик 😡'))


class GameShell(StatesGroup):
    user_choice = State()


@check_user_existence
async def shell_game(message: types.Message, state: FSMContext):
    try:
        # if not bot.user_actioner.user_exist(user_id=message.from_user.id):
        #     await bot.send_message(message.chat.id,
        #                            prepare_message_text(message, 'Пожалуйста зарегистрируйтесь (/start).'))
        #     return

        if bot.user_actioner.get_shell_date(user_id=message.from_user.id) == date.today() and \
                bot.user_actioner.get_shell_count(user_id=message.from_user.id) == 5:
            await bot.send_message(message.chat.id,
                                   prepare_message_text(message, 'Лимит исчерпан, приходите завтра.'))
            return
        elif bot.user_actioner.get_shell_date(user_id=message.from_user.id) != date.today():
            bot.user_actioner.update_shell_date(user_id=message.from_user.id, updated_date=date.today())
            bot.user_actioner.update_shell_count(user_id=message.from_user.id, updated_count=0)

        prizes = ['💰', '💵', '💎', '💳', '💍', '👑', '💊', '💉', '🚬', '📎']
        prize = random.choice(prizes)

        case_left = '🛢🛢🛢\n' \
                    f'{prize}'
        case_mid = '🛢🛢🛢\n' \
                   f'       {prize}'
        case_right = '🛢🛢🛢\n' \
                     f'              {prize}'
        case_default = '🛢🛢🛢'

        cases = {1: case_left, 2: case_mid, 3: case_right}

        await bot.send_message(message.chat.id, prepare_message_text(message, 'Угадаешь где приз, заберешь его'))
        try:
            bot_msg = await bot.send_message(message.chat.id, case_default)
            await asyncio.sleep(1)
            await bot.edit_message_text(random.choice(list(cases.values())), message.chat.id, bot_msg.message_id)
            await asyncio.sleep(1)
            await bot.edit_message_text(case_default, message.chat.id, bot_msg.message_id)
        except RetryAfter as err:
            await except_flood_control(message=message, error=err)

        markup = types.InlineKeyboardMarkup()
        buttons = []
        for i in range(1, 4):
            buttons.append(types.InlineKeyboardButton(str(i), callback_data=str(i)))

        markup.row(*buttons)

        shuffle_msg = await bot.send_message(message.chat.id, 'Перемешиваю...')
        await asyncio.sleep(1.5)
        await bot.edit_message_text(prepare_message_text(message, 'Угадай где приз'), message.chat.id,
                                    shuffle_msg.message_id, reply_markup=markup)
        await state.update_data(cases=cases, bot_msg=bot_msg, shuffle_msg=shuffle_msg)
        await state.set_state(GameShell.user_choice)
    except Exception as err:
        logger.exception(err)
        bot.tg_client.post('SendMessage', params={'chat_id': message.chat.id, 'text': 'Что-то пошло не так 😕'})
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})


async def callback_shell(callback: types.CallbackQuery, state: FSMContext):
    value = random.randint(1, 3)
    cases = (await state.get_data())['cases']
    bot_msg = (await state.get_data())['bot_msg']
    shuffle_msg = (await state.get_data())['shuffle_msg']

    await bot.edit_message_text(cases[value], callback.message.chat.id, bot_msg.message_id)

    if value == int(callback.data):
        prize = random.randint(1000, 30001)
        await bot.send_message(callback.message.chat.id, f'Вы угадали и получаете {prize}')
        await bot.delete_message(callback.message.chat.id, shuffle_msg.message_id)
        bot.user_actioner.update_balance(callback.from_user.id,
                                         bot.user_actioner.get_balance(callback.from_user.id) + prize)
        await state.finish()
    else:
        await bot.send_message(callback.message.chat.id, 'Вы не угадали')
        await bot.delete_message(callback.message.chat.id, shuffle_msg.message_id)
        await state.finish()

    cur_shell_count = bot.user_actioner.get_shell_count(user_id=callback.from_user.id)
    bot.user_actioner.update_shell_count(user_id=callback.from_user.id, updated_count=cur_shell_count + 1)
    await callback.answer()


@check_user_existence
async def balance(message: types.Message):
    try:
        # if not bot.user_actioner.user_exist(message.from_user.id):
        #     await bot.send_message(message.chat.id,
        #                            prepare_message_text(message, 'Пожалуйста зарегистрируйтесь (/start).'))
        #     return

        balance = bot.user_actioner.get_balance(message.from_user.id)

        if not balance:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'У вас нет денег 🤣🤣'))
        else:
            await bot.send_message(message.chat.id, prepare_message_text(message, f'Ваш баланс: {balance} zxcoins.'))
    except Exception as err:
        logger.exception(err)
        bot.tg_client.post('SendMessage', params={'chat_id': message.chat.id, 'text': 'Что-то пошло не так 😕'})
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})


@check_user_existence
async def free(message: types.Message):
    try:
        # if not bot.user_actioner.user_exist(message.from_user.id):
        #     await bot.send_message(message.chat.id,
        #                            prepare_message_text(message, 'Пожалуйста зарегистрируйтесь (/start).'))
        #     return

        balance = bot.user_actioner.get_balance(message.from_user.id)

        if balance < 10000:
            await bot.send_message(message.chat.id, prepare_message_text(message,
                                                                         'Поздравляю, вам начислены подачки в размере 10000 zxcoins 🎊'))
            bot.user_actioner.update_balance(message.from_user.id, balance + 10000)
        else:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Вы слишком богатый 😐'))
    except Exception as err:
        logger.exception(err)
        bot.tg_client.post('SendMessage', params={'chat_id': message.chat.id, 'text': 'Что-то пошло не так 😕'})
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})


@check_user_existence
async def give(message: types.Message):
    try:
        # if not bot.user_actioner.user_exist(message.from_user.id):
        #     await bot.send_message(message.chat.id,
        #                            prepare_message_text(message, 'Пожалуйста зарегистрируйтесь (/start).'))
        #     return

        try:
            payee = message.text.split()[1]
        except IndexError:
            await bot.send_message(message.chat.id,
                                   prepare_message_text(message, 'Укажите имя пользователя в тг и сумму\n'
                                                                 'Пример: /give soslblbu 10000'))
            return

        try:
            sum = int(message.text.split()[2])
            if sum < 0:
                raise ValueError
        except IndexError:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Укажите сумму\n'
                                                                                  'Пример: /give soslblbu 10000'))
            return
        except ValueError:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Укажите нормальную сумму\n'
                                                                                  'Пример: /give soslblbu 10000'))
            return

        if not (user := bot.user_actioner.get_user_by_username(payee)):
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Пользователь не найден'))
            return
        else:
            user_id = user[0]

        balance = bot.user_actioner.get_balance(message.from_user.id)
        if sum > balance:
            await bot.send_message(message.chat.id, prepare_message_text(message, 'Недостаточно денег'))
            return

        bot.user_actioner.update_balance(message.from_user.id, balance - sum)
        bot.user_actioner.update_balance(user_id, bot.user_actioner.get_balance(user_id) + sum)

        await bot.send_message(message.chat.id, prepare_message_text(message, f'Деньги отправлены "{user[2]}"'))
        await bot.send_message(user_id, f'{message.from_user.first_name} перевел(а) вам {sum} zxcoins\n'
                                        f'Ваш баланс: {bot.user_actioner.get_balance(user_id=user_id)} zxcoins')
    except Exception as err:
        logger.exception(err)
        bot.tg_client.post('SendMessage', params={'chat_id': message.chat.id, 'text': 'Что-то пошло не так 😕'})
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})


async def top(message: types.Message):
    try:
        top = ''
        users = bot.user_actioner.get_top_users()
        for index, user in enumerate(users):
            top += f'{index + 1}. {user[0]}   {user[1]} zxcoins\n'
        await bot.send_message(message.chat.id, f'Топ игроков:\n{top}')
    except Exception as err:
        logger.exception(err)
        bot.tg_client.post('SendMessage', params={'chat_id': message.chat.id, 'text': 'Что-то пошло не так 😕'})
        bot.tg_client.post('SendMessage', params={'chat_id': ADMIN_ID, 'text': f'{message.text}\n\n'
                                                                               f'{create_error_message(err)}'})


async def zxc(message: types.Message):
    zxcs = ['Zxc', 'zXc', 'zxC']
    msg = await message.answer('zxc')
    while True:
        for zxc in zxcs:
            await asyncio.sleep(0.5)
            await msg.edit_text(zxc)


async def test(message: types.Message):
    print(message.sticker)
    await bot.send_sticker(message.chat.id,
                           sticker='CAACAgIAAxkBAAIFJWO55ZXFOtwIjNCHNuAJ-ua9IA0cAALCFAACgIlASIt6Bgox9eyvLQQ')


def register_user_handlers(dp: Dispatcher):
    dp.register_message_handler(start, commands=['start'])
    dp.register_message_handler(slots, commands=['slots', 's'])
    dp.register_message_handler(balance, commands=['balance', 'b'])
    dp.register_message_handler(top, commands=['top'])
    dp.register_message_handler(give, commands=['give'])
    dp.register_message_handler(zxc, commands=['zxc'])
    dp.register_message_handler(dice_start, commands=['dice', 'd'])
    dp.register_message_handler(dice_finish_correct, content_types=['dice'], state=GameDice.user_die)
    dp.register_message_handler(dice_finish_incorrect, state=GameDice.user_die)
    dp.register_message_handler(shell_game, commands=['shell'])
    dp.register_message_handler(help, commands=['help', '?'])
    dp.register_message_handler(free, commands=['free'])
    # dp.register_message_handler(test, content_types=['sticker'])

    dp.register_callback_query_handler(callback_shell, lambda callback: callback.data in ['1', '2', '3'],
                                       state=GameShell.user_choice)
