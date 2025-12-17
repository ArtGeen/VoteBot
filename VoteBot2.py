import asyncio
import json
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

# ================== НАСТРОЙКИ ==================

BOT_TOKEN = "8590222261:AAGFy4XM6vYEnykovBPy6966mWoWFrgD4Qc"

ADMIN_IDS = {5199152901}  # <-- ID админа (можно несколько)

VOTES_FILE = Path("votes.json")

NOMINATIONS = {
    "n1": "Кулинарный Олимп",
    "n2": "Мисс очарование",
    "n3": "Душа компании",
    "n4": "Гений креатива",
}

PARTICIPANTS = {
    "p1": "Андреева Раиса Михайловна",
    "p2": "Ведина Ольга Николаевна",
    "p3": "Механикова Людмила Васильевна",
    "p4": "Крюкова Елена Владимировна",
    "p5": "Гольчевская Ирина Валерьевна",
    "p6": "Распутина Екатерина Александровна",
    "p7": "Попова Любовь Анатольевна",
    "p8": "Аникеева Ольга Васильевна",
    "p9": "Миронова Анна Александровна",
    "p10": "Тарасова Ирина Александровна",
    "p11": "Сахаровская Елена Анатольевна",
    "p12": "Анганаева Маргарита Семеновна",
    "p13": "Хамаганова Любовь Викторовна",
    "p14": "Жапова Оюна Нимаевна",
}

# ================== ХРАНИЛИЩЕ ==================

def load_votes():
    if VOTES_FILE.exists():
        return json.loads(VOTES_FILE.read_text(encoding="utf-8"))
    return {"votes": {}}

def save_votes(data):
    VOTES_FILE.write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

votes_data = load_votes()

# ================== КНОПКИ ==================

# def nominations_kb():
#     return InlineKeyboardMarkup(
#         inline_keyboard=[
#             [InlineKeyboardButton(text=name, callback_data=f"nom:{key}")]
#             for key, name in NOMINATIONS.items()
#         ]
#     )

def nominations_kb_for_user(user_id: int):
    keyboard = []

    user_id = str(user_id)

    for nom_key, nom_name in NOMINATIONS.items():
        votes_in_nom = votes_data.get("votes", {}).get(nom_key, {})

        if user_id not in votes_in_nom:
            keyboard.append([
                InlineKeyboardButton(
                    text=nom_name,
                    callback_data=f"nom:{nom_key}"
                )
            ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def participants_kb(nomination):
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(
                text=name,
                callback_data=f"vote:{nomination}:{pid}"
            )]
            for pid, name in PARTICIPANTS.items()
        ]
    )

# ================== БОТ ==================

bot = Bot(BOT_TOKEN)
dp = Dispatcher()

# ================== ХЕНДЛЕРЫ ==================

def start_kb(user_id: int):
    keyboard = []

    # админская кнопка
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton(
                text="📊 Итоги по номинациям",
                callback_data="admin:results_menu"
            )
        ])

    # номинации
    for nom_key, nom_name in NOMINATIONS.items():
        votes = votes_data.get("votes", {}).get(nom_key, {})
        if str(user_id) not in votes:
            keyboard.append([
                InlineKeyboardButton(
                    text=nom_name,
                    callback_data=f"nom:{nom_key}"
                )
            ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.message(F.text == "/start")
async def start(message: Message):
    kb = start_kb(message.from_user.id)

    if not kb.inline_keyboard:
        await message.answer("✅ Вы уже проголосовали во всех номинациях!")
        return

    await message.answer(
        "Выберите действие:",
        reply_markup=kb
    )

@dp.callback_query(F.data.startswith("nom:"))
async def choose_nomination(callback: CallbackQuery):
    nom = callback.data.split(":")[1]
    await callback.message.edit_text(
        f"{NOMINATIONS[nom]}\n\nВыберите участника:",
        reply_markup=participants_kb(nom)
    )

@dp.callback_query(F.data.startswith("vote:"))
async def vote(callback: CallbackQuery):
    _, nom, participant = callback.data.split(":")
    user_id = str(callback.from_user.id)

    votes_data.setdefault("votes", {})
    votes_data["votes"].setdefault(nom, {})

    if user_id in votes_data["votes"][nom]:
        await callback.answer(
            "❌ Вы уже голосовали в этой номинации",
            show_alert=True
        )
        return

    votes_data["votes"][nom][user_id] = participant
    save_votes(votes_data)

    kb = nominations_kb_for_user(callback.from_user.id)

    if not kb.inline_keyboard:
        await callback.message.edit_text(
            "🎉 Спасибо! Вы проголосовали во всех номинациях."
        )
    else:
        await callback.message.edit_text(
            "✅ Голос принят!\n\n"
            "Вы можете проголосовать в другой номинации:",
            reply_markup=kb
        )

@dp.message(F.text == "/results")
async def results(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        return

    text = "📊 **Итоги голосования:**\n\n"

    for nom, votes in votes_data.get("votes", {}).items():
        counter = {}
        for p in votes.values():
            counter[p] = counter.get(p, 0) + 1

        text += f"{NOMINATIONS[nom]}:\n"
        for pid, count in counter.items():
            text += f"— {PARTICIPANTS[pid]}: {count}\n"
        text += "\n"

    await message.answer(text)

def admin_nominations_results_kb():
    keyboard = [
        [
            InlineKeyboardButton(
                text=name,
                callback_data=f"admin_results:{key}"
            )
        ]
        for key, name in NOMINATIONS.items()
    ]

    keyboard.append([
        InlineKeyboardButton(
            text="⬅ Назад к голосованию",
            callback_data="admin:back_to_voting"
        )
    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

def admin_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Итоги по номинациям",
                    callback_data="admin:results_menu"
                )
            ]
        ]
    )



@dp.callback_query(F.data == "admin:results_menu")
async def admin_results_menu(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    await callback.message.edit_text(
        "📊 Выберите номинацию:",
        reply_markup=admin_nominations_results_kb()
    )

@dp.callback_query(F.data.startswith("admin_results:"))
async def admin_results_nomination(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer("❌ Нет доступа", show_alert=True)
        return

    nom = callback.data.split(":")[1]
    votes = votes_data.get("votes", {}).get(nom, {})

    text = f"📊 Итоги — {NOMINATIONS[nom]}\n\n"

    if not votes:
        text += "❌ В этой номинации пока нет голосов"
    else:
        counter = {}
        for p in votes.values():
            counter[p] = counter.get(p, 0) + 1

        # Вывод голосов
        for pid, count in counter.items():
            text += f"{PARTICIPANTS[pid]} — {count}\n"

        # Определяем победителя
        max_votes = max(counter.values())
        winners = [PARTICIPANTS[pid] for pid, count in counter.items() if count == max_votes]

        if len(winners) == 1:
            text += f"\n🏆 Победитель: {winners[0]}"
        else:
            text += f"\n🏆 Победители (ничья): {', '.join(winners)}"

    await callback.message.edit_text(
        text,
        reply_markup=back_to_results_menu_kb()
    )


def back_to_results_menu_kb():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅ Назад к номинациям",
                    callback_data="admin:results_menu"
                )
            ]
        ]
    )

def back_to_voting_kb(user_id: int):
    keyboard = []

    # если админ — показываем кнопку итогов
    if user_id in ADMIN_IDS:
        keyboard.append([
            InlineKeyboardButton(
                text="📊 Итоги по номинациям",
                callback_data="admin:results_menu"
            )
        ])

    # доступные номинации для голосования
    for nom_key, nom_name in NOMINATIONS.items():
        votes = votes_data.get("votes", {}).get(nom_key, {})
        if str(user_id) not in votes:
            keyboard.append([
                InlineKeyboardButton(
                    text=nom_name,
                    callback_data=f"nom:{nom_key}"
                )
            ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)

@dp.callback_query(F.data == "admin:back_to_voting")
async def back_to_voting(callback: CallbackQuery):
    await callback.message.edit_text(
        "Выберите действие:",
        reply_markup=back_to_voting_kb(callback.from_user.id)
    )

# ================== ЗАПУСК ==================

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

