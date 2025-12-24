import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton
)
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.bot import DefaultBotProperties

# ====== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ======
TOKEN = os.getenv("TOKEN")  # токен бота
REPORT_CHAT_ID = int(os.getenv("REPORT_CHAT_ID"))  # ID чата отчётности
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # ID руководителя

# ====== ИНИЦИАЛИЗАЦИЯ ======
storage = MemoryStorage()

bot = Bot(
    token=TOKEN,
    default=DefaultBotProperties(parse_mode="HTML")
)

dp = Dispatcher(storage=storage)

# ====== FSM СТАНЫ ======
class ReportFSM(StatesGroup):
    shift = State()
    type = State()
    dop_status = State()
    text = State()

# ====== КНОПКИ ======
def shift_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=s, callback_data=f"shift_{s}")]
        for s in ["8-20", "11-23", "14-02", "20-08"]
    ])

def type_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ ДОП", callback_data="type_dop"),
            InlineKeyboardButton(text="👀 ВИ", callback_data="type_vi"),
        ]
    ])

def dop_kb():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Всё ок", callback_data="dop_ok"),
            InlineKeyboardButton(text="⚠️ Внимание", callback_data="dop_warn"),
        ]
    ])

# Persistent кнопка меню
menu_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="/start")]
    ],
    resize_keyboard=True,
    one_time_keyboard=False
)

# ====== ФУНКЦИИ ======
def mention_user(user):
    return f'<a href="tg://user?id={user.id}">{user.full_name}</a>'

def mention_admin():
    return f'<a href="tg://user?id={ADMIN_ID}">Руководитель</a>'

# ====== ХЕНДЛЕРЫ ======
@dp.message(F.text == "/start")
async def start(msg: Message, state: FSMContext):
    # Удаляем команду пользователя
    try:
        await msg.delete()
    except:
        pass

    # Отправляем меню смен с кнопкой меню
    await bot.send_message(
        msg.chat.id,
        "Выбирай смену:",
        reply_markup=shift_kb()
    )
    # Кнопка меню внизу экрана (persistent)
    await bot.send_message(
        msg.chat.id,
        "Меню:",
        reply_markup=menu_kb
    )

    await state.clear()  # сброс предыдущих состояний

@dp.callback_query(F.data.startswith("shift_"))
async def choose_shift(cb, state: FSMContext):
    shift = cb.data.split("_")[1]
    await state.u
