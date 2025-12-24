import os
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

# ====== ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ======
TOKEN = os.getenv("TOKEN")  # токен бота
REPORT_CHAT_ID = None  # временно
ADMIN_ID = int(os.getenv("ADMIN_ID"))  # ID руководителя

# ====== ИНИЦИАЛИЗАЦИЯ ======
bot = Bot(TOKEN, parse_mode="HTML")
dp = Dispatcher()
# Временный хендлер для получения chat_id
@dp.message()
async def get_chat_id(msg: Message):
    await msg.answer(f"Chat ID этого чата: {msg.chat.id}")
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
        for s in ["8", "11", "14", "20"]
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

# ====== ФУНКЦИИ ======
def mention_user(user):
    return f'<a href="tg://user?id={user.id}">{user.full_name}</a>'

def mention_admin():
    return f'<a href="tg://user?id={ADMIN_ID}">Руководитель</a>'

# ====== ХЕНДЛЕРЫ ======
@dp.message(F.text == "/start")
async def start(msg: Message, state: FSMContext):
    await msg.answer("Выбирай смену:", reply_markup=shift_kb())
    await state.set_state(ReportFSM.shift)

@dp.callback_query(F.data.startswith("shift_"))
async def choose_shift(cb, state: FSMContext):
    shift = cb.data.split("_")[1]
    await state.update_data(shift=shift)
    await cb.message.edit_text(f"Смена {shift}. Что дальше?", reply_markup=type_kb())
    await state.set_state(ReportFSM.type)

@dp.callback_query(F.data == "type_dop")
async def dop(cb, state: FSMContext):
    await cb.message.edit_text("ДОП статус:", reply_markup=dop_kb())
    await state.set_state(ReportFSM.dop_status)

@dp.callback_query(F.data == "dop_ok")
async def dop_ok(cb, state: FSMContext):
    data = await state.get_data()
    date = datetime.now().strftime("%d.%m.%Y")
    user_mention = mention_user(cb.from_user)
    text = (
        "✅\n"
        f"Эпизоды [{date}]\n"
        "эпизоды обработаны.\n\n"
        f"Ответственный: {user_mention}, смена {data['shift']}"
    )
    await bot.send_message(REPORT_CHAT_ID, text)
    await state.clear()
    await cb.message.edit_text("Отправлено ✔️")

@dp.callback_query(F.data == "dop_warn")
async def dop_warn(cb, state: FSMContext):
    await cb.message.edit_text("Напиши, на кого обратить внимание:")
    await state.set_state(ReportFSM.text)
    await state.update_data(dop_warn=True)

@dp.callback_query(F.data == "type_vi")
async def vi(cb, state: FSMContext):
    await cb.message.edit_text("Напиши саммари ВИ:")
    await state.set_state(ReportFSM.text)
    await state.update_data(dop_vi=True)

@dp.message(ReportFSM.text)
async def input_text(msg: Message, state: FSMContext):
    data = await state.get_data()
    date = datetime.now().strftime("%d.%m.%Y")
    user_mention = mention_user(msg.from_user)

    # ДОП ⚠️
    if data.get("dop_warn"):
        text = (
            "⚠️\n"
            f"Эпизоды [{date}]\n"
            "Эпизоды обработаны.\n"
            f"На кого стоит обратить внимание:\n{msg.text}\n\n"
            f"Ответственный: {user_mention}, смена {data['shift']}"
        )
    # ВИ
    elif data.get("dop_vi") or data.get("type_vi"):
        text = (
            "👀\n"
            f"[ВИ] [{date}]\n\n"
            f"Саммари:\n{msg.text}\n\n"
            f"Ответственный: {user_mention}\n"
            f"Статус: требует внимания {mention_admin()}"
        )
    else:
        text = "Неопределённый сценарий"

    await bot.send_message(REPORT_CHAT_ID, text)
    await state.clear()
    await msg.answer("Готово ✔️")

# ====== ЗАПУСК ======
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
