from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio
import html
import re
import os
from aiohttp import web

API_BOT = '9130525949:AAGfRf01NHcqgcnBHA0L1DtN33lJiZlbKbE'

bot = Bot(token=API_BOT, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

ADMIN_ID = -1004420152286

class Questionnaire(StatesGroup):
    name = State()
    age = State()
    level = State()
    skills = State()
    sociability = State()
    telegram_username = State()
    roblox_nick = State()
    skin_photo = State()

# Состояние для админа (ожидание текста ответа конкретному пользователю)
class AdminReply(StatesGroup):
    waiting_for_reply = State()

# Главное инлайн-меню для пользователя
def get_inline_keyboard():
    kb = [
        [InlineKeyboardButton(text="Заполнить анкету", callback_data="start_ank")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Инлайн-кнопки под анкетой в админ-группе
def get_admin_action_keyboard(user_id: int):
    kb = [
        [InlineKeyboardButton(text="Ответить", callback_data=f"admin_reply_{user_id}")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

# Кнопка отмены для админа
def get_cancel_keyboard():
    kb = [
        [InlineKeyboardButton(text="Отменить ответ", callback_data="admin_cancel")]
    ]
    return InlineKeyboardMarkup(inline_keyboard=kb)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_name = message.from_user.first_name
    await message.answer(
        f"<b>Приветствую, {user_name}!</b> 👋\n\n"
        "<i>Нажмите на кнопку ниже, чтобы вызвать анкету на вступление в клан.</i>",
        reply_markup=get_inline_keyboard()
    )

@dp.callback_query(F.data == "start_ank")
async def callback_start_ank(callback: CallbackQuery, state: FSMContext):
    await state.set_state(Questionnaire.name)
    await callback.message.answer("<b>1/8.</b> Введите ваше <b>имя или псевдоним</b>:")
    await callback.answer()

@dp.message(Command('anc'))
async def start_questionnaire_cmd(message: Message, state: FSMContext):
    await state.set_state(Questionnaire.name)
    await message.answer("<b>1/8.</b> Введите ваше <b>имя или псевдоним</b>:")

@dp.message(Questionnaire.name)
async def process_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("<i>Пожалуйста, отправьте имя текстом.</i>")
        return
    await state.update_data(name=message.text)
    await state.set_state(Questionnaire.age)
    await message.answer("<b>2/8.</b> Ваш <b>возраст</b> <i>(берем с 13+)</i>:")

@dp.message(Questionnaire.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("<i>Пожалуйста, введите возраст только цифрами.</i>")
        return
    await state.update_data(age=message.text)
    await state.set_state(Questionnaire.level)
    await message.answer("<b>3/8.</b> Ваш <b>уровень</b> <i>(берем от 40+)</i>:")

@dp.message(Questionnaire.level)
async def process_level(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("<i>Пожалуйста, введите ваш уровень только цифрами.</i>")
        return
    await state.update_data(level=message.text)
    await state.set_state(Questionnaire.skills)
    await message.answer("<b>4/8.</b> Ваши <b>умения</b> <i>(Не обязательно)</i>:")

@dp.message(Questionnaire.skills)
async def process_skills(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("<i>Пожалуйста, опишите умения текстом.</i>")
        return
    await state.update_data(skills=message.text)
    await state.set_state(Questionnaire.sociability)
    await message.answer("<b>5/8.</b> <b>Общительный</b> ли вы человек?")

@dp.message(Questionnaire.sociability)
async def process_sociability(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("<i>Пожалуйста, ответьте текстом.</i>")
        return
    await state.update_data(sociability=message.text)
    await state.set_state(Questionnaire.telegram_username)
    await message.answer("<b>6/8.</b> Укажите ваш <b>юз в телеграме</b> <i>(на английском через @)</i>:")

@dp.message(Questionnaire.telegram_username)
async def process_tg(message: Message, state: FSMContext):
    if not message.text or not re.fullmatch(r'@[a-zA-Z0-9_]{4,32}', message.text):
        await message.answer("<i>Введите корректный юз на английском языке, начиная со знака @).</i>")
        return
    await state.update_data(telegram_username=message.text)
    await state.set_state(Questionnaire.roblox_nick)
    await message.answer("<b>7/8.</b> Ваш <b>ник в роблоксе</b> <i>(только на английском)</i>:")

@dp.message(Questionnaire.roblox_nick)
async def process_roblox(message: Message, state: FSMContext):
    if not message.text or not re.fullmatch(r'[a-zA-Z0-9_]{3,20}', message.text):
        await message.answer("<i>Ник в Роблоксе должен быть на английском языке без пробелов.</i>")
        return
    await state.update_data(roblox_nick=message.text)
    await state.set_state(Questionnaire.skin_photo)
    await message.answer("<b>8/8.</b> Отправьте <b>скриншот вашего скина</b> <i>(картинкой)</i>:")

# Обработка фото (поддерживает и фото, и документы-картинки)
@dp.message(Questionnaire.skin_photo, F.photo | F.document)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id if message.photo else message.document.file_id
    data = await state.update_data(skin_photo=photo_id)
    
    name = html.escape(data['name'])
    skills = html.escape(data['skills'])
    sociability = html.escape(data['sociability'])
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else f"id{user_id}"

    summary = (
        f"<b>Новая анкета в клан</b>\n"
        f"<b>Отправитель:</b> {username}, ID - {user_id}\n\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Возраст:</b> {data['age']}\n"
        f"<b>Лвл:</b> {data['level']}\n"
        f"<b>Умения:</b> <i>{skills}</i>\n"
        f"<b>Общительный ли:</b> <i>{sociability}</i>\n"
        f"<b>Юз ТГ (из анкеты):</b> {data['telegram_username']}\n"
        f"<b>Ник в РБ:</b> <code>{data['roblox_nick']}</code>"
    )
    
    try:
        await bot.send_photo(
            chat_id=ADMIN_ID, 
            photo=photo_id, 
            caption=summary,
            reply_markup=get_admin_action_keyboard(user_id)
        )
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")

    await message.answer(
        "<b>Анкета успешно отправлена!</b>\n"
        "<i>Ожидайте ответа от администрации.</i>",
        reply_markup=get_inline_keyboard()
    )
    await state.clear()

@dp.message(Questionnaire.skin_photo)
async def process_photo_incorrect(message: Message):
    await message.answer("<i>Пожалуйста, отправьте именно фотографию скина.</i>")

@dp.callback_query(F.data.startswith("admin_reply_"))
async def admin_start_reply(callback: CallbackQuery, state: FSMContext):
    if callback.message.chat.id != ADMIN_ID:
        await callback.answer("Эта кнопка доступна только администраторам в группе.", show_alert=True)
        return

    target_user_id = int(callback.data.split("_")[2])
    
    await state.set_state(AdminReply.waiting_for_reply)
    await state.update_data(target_user_id=target_user_id)
    
    await bot.send_message(
        chat_id=ADMIN_ID,
        text=f"Введите ответ (ID: <code>{target_user_id}</code>):",
        reply_markup=get_cancel_keyboard()
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_cancel")
async def admin_cancel_reply(callback: CallbackQuery, state: FSMContext):
    if callback.message.chat.id != ADMIN_ID:
        await callback.answer()
        return

    await state.clear()
    await bot.send_message(
        chat_id=ADMIN_ID,
        text="<i>Ответ отменен.</i>"
    )
    await callback.answer()

@dp.message(F.chat.id == ADMIN_ID, AdminReply.waiting_for_reply)
async def send_reply_to_user(message: Message, state: FSMContext):
    data = await state.get_data()
    target_user_id = data.get("target_user_id")
    
    if not target_user_id:
        await state.clear()
        return

    try:
        await bot.send_message(
            chat_id=target_user_id,
            text=f"<b>Ответ от администрации клана:</b>\n\n{message.text}"
        )
        await message.answer(f"<i>Ответ успешно доставлен <code>{target_user_id}</code>!</i>")
    except Exception as e:
        await message.answer(f"<i>Не удалось отправить сообщение: {e}</i>")
    
    await state.clear()

@dp.message(F.chat.type == "private", ~F.text.startswith('/'))
async def user_to_admin_dialog(message: Message):
    user_id = message.from_user.id
    username = f"@{message.from_user.username}" if message.from_user.username else f"id{user_id}"

    forward_text = (
        f"Сообщение от {username}, ID - {user_id}\n"
        f"текст: {html.escape(message.text)}"
    )

    try:
        await bot.send_message(
            chat_id=ADMIN_ID,
            text=forward_text,
            reply_markup=get_admin_action_keyboard(user_id)
        )
        await message.answer("<i>Ваше сообщение отправлено администрации. Ожидайте ответа!</i>")
    except Exception as e:
        print(f"Ошибка пересылки сообщения админам: {e}")

async def handle(request):
    return web.Response(text="Bot is running!")

async def main():
    app = web.Application()
    app.router.add_get('/', handle)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

    print("Bot Start")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())