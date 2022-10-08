from aiogram import Bot, Dispatcher, types

from settings import settings
from database.controller import get_user, set_user


bot = Bot(token=settings.bot_token)
dp = Dispatcher(bot)


@dp.message_handler(commands=["start", "settings"])
async def setup_command(message: types.Message):
    user = get_user(message.from_user.id)
    user.okveds = []
    user.chat_id = message.chat.id
    keyboard = (
        types.InlineKeyboardMarkup(row_width=1)
        .add(types.InlineKeyboardButton(text="Управленец 💼", callback_data="director"))
        .add(types.InlineKeyboardButton(text="Бухгалтер 💵", callback_data="accountant"))
    )
    m = await bot.send_message(
        message.from_user.id,
        "Добрый день. Этот бот будет отправлять вам новостной дайджест. Давайте пройдём небольшую анкету. Выберите роль:",
        reply_markup=keyboard,
    )
    user.last_message_id = m.message_id
    set_user(user)


@dp.callback_query_handler(lambda callback_query: callback_query.data in ["director", "accountant"])
async def callback_user(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    user.state = "OKVED"
    set_user(user)
    keyboard = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton(text="Нет ОКВЭДов 🙁", callback_data="save")
    )
    await bot.edit_message_text(
        "Отправьте интересующие вас ОКВЭДы:",
        message_id=user.last_message_id,
        chat_id=user.chat_id,
        reply_markup=keyboard,
    )


@dp.message_handler(regexp=r"([\d]{1,3})+(\.[\d]{1,3}|){1,}")
async def okved_handler(message: types.Message):
    user = get_user(message.from_user.id)
    if not user.state == "OKVED":
        return
    user.okveds = (user.okveds or []) + [message.text]
    set_user(user)
    text = "Выбранные ОКВЭДы:\n" + "\n".join(user.okveds)
    keyboard = types.InlineKeyboardMarkup(row_width=1).add(
        types.InlineKeyboardButton(text="Сохранить", callback_data="save")
    )
    await bot.edit_message_text(text, message_id=user.last_message_id, chat_id=user.chat_id, reply_markup=keyboard)


@dp.callback_query_handler(lambda callback_query: callback_query.data == "save")
async def callback_save(callback_query: types.CallbackQuery):
    user = get_user(callback_query.from_user.id)
    user.state = "READY"
    keyboard = types.ReplyKeyboardMarkup().add(types.KeyboardButton("Получить дайджест"))
    if user.okveds is None or len(user.okveds) == 0:
        text = "Поехали 🚀\nБез ОКВЭДов"
        await bot.edit_message_reply_markup(chat_id=user.chat_id, message_id=user.last_message_id)
        await bot.send_message(chat_id=user.chat_id, text=text, reply_markup=keyboard)
    else:
        keyboard = keyboard.add(types.KeyboardButton("Получить персонализированную подборку")).add(
            types.KeyboardButton("Получить дайджест о контрагентах")
        )
        text = "Поехали 🚀\nВаши ОКВЭДы:\n" + "\n".join(user.okveds)
        await bot.edit_message_reply_markup(chat_id=user.chat_id, message_id=user.last_message_id)
        await bot.send_message(chat_id=user.chat_id, text=text, reply_markup=keyboard)
    set_user(user)


@dp.message_handler(lambda message: message.text == "Получить дайджест")
async def digest_handler(message: types.Message):
    await bot.send_message(chat_id=message.from_id, text="Дайджест")


@dp.message_handler(lambda message: message.text == "Получить персонализированную подборку")
async def digest_handler(message: types.Message):
    user = get_user(message.from_user.id)
    if user.okveds is None or len(user.okveds) == 0:
        await setup_command(message)
        return
    await bot.send_message(chat_id=message.from_id, text=f"Подборка для пользователя {user.id}")


@dp.message_handler(lambda message: message.text == "Получить дайджест о контрагентах")
async def digest_handler(message: types.Message):
    user = get_user(message.from_user.id)
    if user.okveds is None or len(user.okveds) == 0:
        await setup_command(message)
        return
    await bot.send_message(chat_id=message.from_id, text=f"Подборка о контрагентах для пользователя {user.id}")
