from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart, Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
import asyncio
import html
import re

API_BOT = '9130525949:AAGfRf01NHcqgcnBHA0L1DtN33lJiZlbKbE'

# Включаем HTML-форматирование по умолчанию для всех сообщений бота
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

def get_keyboard():
    kb = [
        [KeyboardButton(text="Анкета")]
    ]
    return ReplyKeyboardMarkup(keyboard=kb, resize_keyboard=True)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "<b>Приветствую!</b> \n\n"
        "<i>Нажмите на кнопку «Анкета» ниже, чтобы начать её заполнение для вступления в клан.</i>",
        reply_markup=get_keyboard()
    )

@dp.message(F.text == "Анкета")
@dp.message(Command('anc'))
async def start_questionnaire(message: Message, state: FSMContext):
    await state.set_state(Questionnaire.name)
    await message.answer("<b>1/8.</b> Введите ваше <b>имя или псевдоним</b>:")

@dp.message(Questionnaire.name)
async def process_name(message: Message, state: FSMContext):
    if not message.text:
        await message.answer("<i>Пожалуйста, отправьте имя текстом.</i>")
        return
    await state.update_data(name=message.text)
    await state.set_state(Questionnaire.age)
    await message.answer("<b>2/8.</b> Ваш <b>возраст</b> <i>(требование 13+)</i>:")

@dp.message(Questionnaire.age)
async def process_age(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("⚠️ <i>Пожалуйста, введите возраст только цифрами (например: 14).</i>")
        return
    
    await state.update_data(age=message.text)
    await state.set_state(Questionnaire.level)
    await message.answer("<b>3/8.</b> Ваш <b>уровень</b> <i>(лвл 40+)</i>:")

@dp.message(Questionnaire.level)
async def process_level(message: Message, state: FSMContext):
    if not message.text or not message.text.isdigit():
        await message.answer("<i>Пожалуйста, введите ваш уровень только цифрами</i>")
        return

    await state.update_data(level=message.text)
    await state.set_state(Questionnaire.skills)
    await message.answer("<b>4/8.</b> Ваши <b>умения</b> <i>(если их нет, напишите «нет»)</i>:")

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
    await message.answer("<b>6/8.</b> Укажите ваш <b>юз в телеграме</b> <i>(на английском через @, например: @username)</i>:")

@dp.message(Questionnaire.telegram_username)
async def process_tg(message: Message, state: FSMContext):
    if not message.text or not re.fullmatch(r'@[a-zA-Z0-9_]{4,32}', message.text):
        await message.answer("<i>Введите корректный юз на английском языке, начиная со знака @ (например: @username).</i>")
        return

    await state.update_data(telegram_username=message.text)
    await state.set_state(Questionnaire.roblox_nick)
    await message.answer("<b>7/8.</b> Ваш <b>ник в роблоксе</b> <i></i>:")

@dp.message(Questionnaire.roblox_nick)
async def process_roblox(message: Message, state: FSMContext):
    if not message.text or not re.fullmatch(r'[a-zA-Z0-9_]{3,20}', message.text):
        await message.answer("<i>Ник в Роблоксе должен быть на английском языке без пробелов (можно цифры и _).</i>")
        return

    await state.update_data(roblox_nick=message.text)
    await state.set_state(Questionnaire.skin_photo)
    await message.answer("<b>8/8.</b> Отправьте <b>скрин вашего скина</b> <i></i>:")

@dp.message(Questionnaire.skin_photo, F.photo)
async def process_photo(message: Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    data = await state.update_data(skin_photo=photo_id)
    
    # Экранируем пользовательский ввод на случай символов < или >
    name = html.escape(data['name'])
    skills = html.escape(data['skills'])
    sociability = html.escape(data['sociability'])

    summary = (
        "<b>Новая анкета в клан!</b>\n\n"
        f"<b>Имя:</b> {name}\n"
        f"<b>Возраст:</b> {data['age']}\n"
        f"<b>Лвл:</b> {data['level']}\n"
        f"<b>Умения:</b> <i>{skills}</i>\n"
        f"<b>Общительность:</b> <i>{sociability}</i>\n"
        f"<b>Юз ТГ:</b> {data['telegram_username']}\n"
        f"<b>Ник в Роблоксе:</b> <code>{data['roblox_nick']}</code>"
    )
    
    try:
        await bot.send_photo(chat_id=ADMIN_ID, photo=photo_id, caption=summary)
    except Exception as e:
        print(f"Ошибка отправки в группу: {e}")

    await message.answer(
        "<b>Ответ отправлен!</b>\n"
        "<i>Ожидайте сообщение от администрации.</i>",
        reply_markup=get_keyboard()
    )
    await state.clear()

@dp.message(Questionnaire.skin_photo)
async def process_photo_incorrect(message: Message):
    await message.answer("<i>Пожалуйста, отправьте именно фотографию скина (картинкой).</i>")

async def main():
    print("Bot Start")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())