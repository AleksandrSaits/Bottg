import os
import sqlite3
import random
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

# ===== НАСТРОЙКИ =====
TOKEN = "8614039525:AAF2c9BWQqwFWxLQKCrBH-4-2YEA41w8z-A"
OWNER_ID = 8287969191 # ТВОЙ ID (узнай через @userinfobot)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== СИСТЕМА РАНГОВ =====
RANKS = {
    "demon": {
        "name": "🔥 Линия Демонов",
        "levels": [
            (0, "👶 Демонёнок"),
            (100, "😈 Бес"),
            (500, "👿 Имп"),
            (1500, "🦇 Суккуб"),
            (3000, "💀 Архидемон"),
            (6000, "🔥 Повелитель Ада"),
            (12000, "👑 Владыка Демонов"),
            (25000, "🌋 Абсолютный Хаос"),
        ]
    },
    "god": {
        "name": "⚡ Линия Богов",
        "levels": [
            (0, "🧍 Смертный"),
            (100, "🙏 Посвящённый"),
            (500, "⚔️ Полубог"),
            (1500, "🛡️ Бог Войны"),
            (3000, " Бог Мудрости"),
            (6000, "🏛️ Олимпиец"),
            (12000, "👑 Верховный Бог"),
            (25000, "✨ Творец Миров"),
        ]
    },
    "earth": {
        "name": " Линия Земли",
        "levels": [
            (0, "🚶 Странник"),
            (100, "⚔️ Воин"),
            (500, "🛡️ Рыцарь"),
            (1500, "🏰 Паладин"),
            (3000, " Герой"),
            (6000, "📖 Легенда"),
            (12000, "🏆 Чемпион"),
            (25000, " Хранитель Мира"),
        ]
    },
    "shadow": {
        "name": "🌑 Линия Теней",
        "levels": [
            (0, "️ Адепт"),
            (100, "📖 Ученик"),
            (500, "🔮 Маг"),
            (1500, "📕 Архимаг"),
            (3000, "⚡ Чародей"),
            (6000, "💀 Некромант"),
            (12000, "👁️ Повелитель Теней"),
            (25000, " Вечный"),
        ]
    }
}

def get_rank(coins, line="demon"):
    """Получить ранг по количеству монет"""
    levels = RANKS[line]["levels"]
    current_rank = levels[0][1]
    for threshold, rank_name in levels:
        if coins >= threshold:
            current_rank = rank_name
        else:
            break
    return current_rank

def get_next_rank(coins, line="demon"):
    """Получить следующий ранг"""
    levels = RANKS[line]["levels"]
    for threshold, rank_name in levels:
        if coins < threshold:
            return threshold, rank_name
    return None, "МАКСИМУМ"

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    
    # Пользователи
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, 
                       coins INTEGER DEFAULT 0, gems INTEGER DEFAULT 0,
                       is_premium INTEGER DEFAULT 0, last_daily TEXT,
                       rank_line TEXT DEFAULT 'demon', clan_id INTEGER)''')
    
    # Админы групп
    cursor.execute('''CREATE TABLE IF NOT EXISTS group_admins 
                      (group_id INTEGER, user_id INTEGER, role TEXT, 
                       UNIQUE(group_id, user_id))''')
    
    # Кланы
    cursor.execute('''CREATE TABLE IF NOT EXISTS clans 
                      (clan_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                       name TEXT, owner_id INTEGER, 
                       coins INTEGER DEFAULT 0, members INTEGER DEFAULT 1)''')
    
    conn.commit()
    conn.close()

def get_user(user_id, username=None):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    elif username and user[1] != username:
        cursor.execute("UPDATE users SET username = ? WHERE user_id = ?", (username, user_id))
        conn.commit()
    conn.close()
    return user

def get_user_by_username(username):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def update_coins(user_id, amount):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET coins = coins + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def update_gems(user_id, amount):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET gems = gems + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def set_premium(user_id):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def set_rank_line(user_id, line):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET rank_line = ? WHERE user_id = ?", (line, user_id))
    conn.commit()
    conn.close()

def get_all_users():
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    users = cursor.fetchall()
    conn.close()
    return users

def get_top_users(limit=10):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT username, coins, rank_line FROM users ORDER BY coins DESC LIMIT ?", (limit,))
    top = cursor.fetchall()
    conn.close()
    return top

# ===== КЛАНЫ =====
def create_clan(name, owner_id):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO clans (name, owner_id) VALUES (?, ?)", (name, owner_id))
    clan_id = cursor.lastrowid
    cursor.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan_id, owner_id))
    conn.commit()
    conn.close()
    return clan_id

def get_clan(clan_id):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM clans WHERE clan_id = ?", (clan_id,))
    clan = cursor.fetchone()
    conn.close()
    return clan

def join_clan(user_id, clan_id):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET clan_id = ? WHERE user_id = ?", (clan_id, user_id))
    cursor.execute("UPDATE clans SET members = members + 1 WHERE clan_id = ?", (clan_id,))
    conn.commit()
    conn.close()

def leave_clan(user_id):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET clan_id = NULL WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def add_admin(group_id, user_id, role):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT OR REPLACE INTO group_admins VALUES (?, ?, ?)", (group_id, user_id, role))
        conn.commit()
    except:
        pass
    conn.close()

def get_admins(group_id):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, role FROM group_admins WHERE group_id = ?", (group_id,))
    admins = cursor.fetchall()
    conn.close()
    return admins

init_db()

# ===== FSM СОСТОЯНИЯ =====
class AdminStates(StatesGroup):
    waiting_broadcast = State()
    waiting_addcoins = State()
    waiting_addgems = State()

class ClanStates(StatesGroup):
    waiting_create = State()

# ===== МЕНЮ КОМАНД =====
async def set_commands():
    commands = [
        BotCommand(command='start', description=' Главное меню'),
        BotCommand(command='profile', description='👤 Мой профиль'),
        BotCommand(command='balance', description='💰 Баланс'),
        BotCommand(command='daily', description='🎁 Ежедневный бонус'),
        BotCommand(command='casino', description='🎰 Казино'),
        BotCommand(command='shop', description='🛒 Магазин'),
        BotCommand(command='rank', description=' Мой ранг'),
        BotCommand(command='changerank', description='🔄 Сменить линию ранга'),
        BotCommand(command='clan', description='⚔️ Клан'),
        BotCommand(command='top', description='🏆 Топ игроков'),
        BotCommand(command='admins', description='👥 Администрация'),
        BotCommand(command='help', description=' Помощь'),
    ]
    await bot.set_my_commands(commands)

def is_owner(user_id):
    return user_id == OWNER_ID

# ===== ГЛАВНОЕ МЕНЮ =====
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    rank = get_rank(user[2], user[6])
    premium_badge = "👑 PREMIUM | " if user[5] else ""
    owner_badge = "🔱 ВЛАДЕЛЕЦ | " if is_owner(message.from_user.id) else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🎁 Daily", callback_data="daily"),
         InlineKeyboardButton(text="🎰 Казино", callback_data="casino")],
        [InlineKeyboardButton(text="🛒 Магазин", callback_data="shop"),
         InlineKeyboardButton(text="📊 Ранг", callback_data="rank")],
        [InlineKeyboardButton(text="⚔️ Клан", callback_data="clan"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
        [InlineKeyboardButton(text=" Администрация", callback_data="admins_list")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
    ])
    
    if is_owner(message.from_user.id):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_panel")
        ])
    
    caption = (
        f"👋 {owner_badge}{premium_badge}Добро пожаловать, **{message.from_user.full_name}**!\n\n"
        f"{rank}\n"
        f"🪙 **Coins:** {user[2]}\n"
        f"💎 **Gems:** {user[3]}\n\n"
        f"Выбирай действие 👇"
    )
    
    await message.answer(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ===== ПРОФИЛЬ =====
@dp.message(Command('profile'))
async def cmd_profile(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    rank = get_rank(user[2], user[6])
    next_threshold, next_rank = get_next_rank(user[2], user[6])
    clan = get_clan(user[7]) if user[7] else None
    
    text = (
        f"👤 **ПРОФИЛЬ**\n\n"
        f"**Имя:** {message.from_user.full_name}\n"
        f"**Username:** @{message.from_user.username or 'не указан'}\n\n"
        f"{rank}\n"
        f"🪙 **Coins:** {user[2]}\n"
        f"💎 **Gems:** {user[3]}\n"
        f"👑 **Premium:** {'Да' if user[5] else 'Нет'}\n"
        f"⚔️ **Клан:** {clan[1] if clan else 'Нет'}\n\n"
    )
    
    if next_threshold:
        progress = (user[2] / next_threshold) * 100
        text += f"📈 **До следующего ранга:** {next_threshold - user[2]} 🪙 ({progress:.1f}%)\n"
        text += f" **Следующий ранг:** {next_rank}"
    
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data == "profile")
async def cb_profile(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    rank = get_rank(user[2], user[6])
    next_threshold, next_rank = get_next_rank(user[2], user[6])
    clan = get_clan(user[7]) if user[7] else None
    
    text = (
        f" **ПРОФИЛЬ**\n\n"
        f"**Имя:** {callback.from_user.full_name}\n"
        f"**Username:** @{callback.from_user.username or 'не указан'}\n\n"
        f"{rank}\n"
        f" **Coins:** {user[2]}\n"
        f"💎 **Gems:** {user[3]}\n"
        f" **Premium:** {'Да' if user[5] else 'Нет'}\n"
        f"⚔️ **Клан:** {clan[1] if clan else 'Нет'}\n\n"
    )
    
    if next_threshold:
        progress = (user[2] / next_threshold) * 100
        text += f" **До следующего ранга:** {next_threshold - user[2]} 🪙 ({progress:.1f}%)\n"
        text += f" **Следующий ранг:** {next_rank}"
    
    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=" Сменить линию", callback_data="changerank")],
            [InlineKeyboardButton(text="️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== РАНГ =====
@dp.message(Command('rank'))
async def cmd_rank(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    rank = get_rank(user[2], user[6])
    line_name = RANKS[user[6]]["name"]
    next_threshold, next_rank = get_next_rank(user[2], user[6])
    
    text = (
        f"📊 **ТВОЙ РАНГ**\n\n"
        f"{line_name}\n"
        f"**Текущий:** {rank}\n"
        f"🪙 **Coins:** {user[2]}\n\n"
    )
    
    if next_threshold:
        progress = (user[2] / next_threshold) * 100
        bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        text += f" **Прогресс:** [{bar}] {progress:.0f}%\n"
        text += f"🎯 **Следующий:** {next_rank} ({next_threshold} 🪙)"
    else:
        text += " **МАКСИМАЛЬНЫЙ РАНГ!**"
    
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data == "rank")
async def cb_rank(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    rank = get_rank(user[2], user[6])
    line_name = RANKS[user[6]]["name"]
    next_threshold, next_rank = get_next_rank(user[2], user[6])
    
    text = (
        f"📊 **ТВОЙ РАНГ**\n\n"
        f"{line_name}\n"
        f"**Текущий:** {rank}\n"
        f"🪙 **Coins:** {user[2]}\n\n"
    )
    
    if next_threshold:
        progress = (user[2] / next_threshold) * 100
        bar = "█" * int(progress / 10) + "░" * (10 - int(progress / 10))
        text += f"📈 **Прогресс:** [{bar}] {progress:.0f}%\n"
        text += f" **Следующий:** {next_rank} ({next_threshold} 🪙)"
    else:
        text += "🏆 **МАКСИМАЛЬНЫЙ РАНГ!**"
    
    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔄 Сменить линию", callback_data="changerank")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== СМЕНА ЛИНИИ РАНГА =====
@dp.message(Command('changerank'))
async def cmd_changerank(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Демоны", callback_data="line_demon"),
         InlineKeyboardButton(text=" Боги", callback_data="line_god")],
        [InlineKeyboardButton(text=" Земля", callback_data="line_earth"),
         InlineKeyboardButton(text="🌑 Тени", callback_data="line_shadow")],
    ])
    
    await message.answer(
        "🔄 **ВЫБЕРИ ЛИНИЮ РАЗВИТИЯ**\n\n"
        "⚠️ Прогресс сохранится, но ранг изменится!",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "changerank")
async def cb_changerank(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔥 Демоны", callback_data="line_demon"),
         InlineKeyboardButton(text="⚡ Боги", callback_data="line_god")],
        [InlineKeyboardButton(text="🌍 Земля", callback_data="line_earth"),
         InlineKeyboardButton(text="🌑 Тени", callback_data="line_shadow")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
    ])
    
    await callback.message.edit_text(
        "🔄 **ВЫБЕРИ ЛИНИЮ РАЗВИТИЯ**\n\n"
        "⚠️ Прогресс сохранится, но ранг изменится!",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.startswith("line_"))
async def cb_line_select(callback: types.CallbackQuery):
    line = callback.data.split("_")[1]
    set_rank_line(callback.from_user.id, line)
    user = get_user(callback.from_user.id, callback.from_user.username)
    new_rank = get_rank(user[2], line)
    
    await callback.message.edit_text(
        f"✅ **Линия изменена!**\n\n"
        f"{RANKS[line]['name']}\n"
        f"**Твой ранг:** {new_rank}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== БАЛАНС =====
@dp.message(Command('balance'))
async def cmd_balance(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    rank = get_rank(user[2], user[6])
    
    await message.answer(
        f"💰 **ТВОЙ БАЛАНС**\n\n"
        f"{rank}\n"
        f"🪙 **Coins:** {user[2]} (игровая)\n"
        f"💎 **Gems:** {user[3]} (донат)\n\n"
        f"🪙 Coins: /daily, казино\n"
        f"💎 Gems: покупка за ⭐️",
        parse_mode=ParseMode.MARKDOWN
    )

@dp.callback_query(F.data == "balance")
async def cb_balance(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    rank = get_rank(user[2], user[6])
    
    await callback.message.edit_text(
        f"💰 **ТВОЙ БАЛАНС**\n\n"
        f"{rank}\n"
        f"🪙 **Coins:** {user[2]} (игровая)\n"
        f"💎 **Gems:** {user[3]} (донат)\n\n"
        f" Coins: /daily, казино\n"
        f"💎 Gems: покупка за ⭐️",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== DAILY =====
@dp.message(Command('daily'))
async def cmd_daily(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user[5] == today:
        await message.answer(" Ты уже забрал награду сегодня!\n\nПриходи завтра 🌅")
        return
    
    reward = random.randint(100, 300)
    update_coins(message.from_user.id, reward)
    
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (today, message.from_user.id))
    conn.commit()
    conn.close()
    
    await message.answer(
        f"🎉 **ЕЖЕДНЕВНАЯ НАГРАДА!**\n\n"
        f"Ты получил **{reward} 🪙**\n\n"
        f"Новый баланс: {user[2] + reward} 🪙"
    )

@dp.callback_query(F.data == "daily")
async def cb_daily(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user[5] == today:
        await callback.answer("⏳ Уже забрал сегодня!", show_alert=True)
        return
    
    reward = random.randint(100, 300)
    update_coins(callback.from_user.id, reward)
    
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (today, callback.from_user.id))
    conn.commit()
    conn.close()
    
    await callback.message.edit_text(
        f" **ЕЖЕДНЕВНАЯ НАГРАДА!**\n\n"
        f"Ты получил **{reward} 🪙**\n\n"
        f"Новый баланс: {user[2] + reward} 🪙",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔜 Завтра", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== КАЗИНО С АНИМАЦИЕЙ =====
@dp.message(Command('casino'))
async def cmd_casino(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=" Красное (x2)", callback_data="bet_red"),
         InlineKeyboardButton(text="⚫ Чёрное (x2)", callback_data="bet_black")],
        [InlineKeyboardButton(text=" Зелёное (x14)", callback_data="bet_green")],
    ])
    
    await message.answer(
        "🎰 **КАЗИНО**\n\n"
        "Выбери ставку:\n"
        "🔴 **Красное** — x2 (1-7)\n"
        "⚫ **Чёрное** — x2 (8-14)\n"
        "🟢 **Зелёное** — x14 (0)\n\n"
        "Минимальная ставка: 10 ",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "casino")
async def cb_casino(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="bet_red"),
         InlineKeyboardButton(text="⚫ Чёрное (x2)", callback_data="bet_black")],
        [InlineKeyboardButton(text="🟢 Зелёное (x14)", callback_data="bet_green")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
    ])
    
    await callback.message.edit_text(
        "🎰 **КАЗИНО**\n\n"
        "Выбери ставку:\n"
        "🔴 **Красное** — x2 (1-7)\n"
        "⚫ **Чёрное** — x2 (8-14)\n"
        "🟢 **Зелёное** — x14 (0)\n\n"
        "Минимальная ставка: 10 🪙",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.in_(["bet_red", "bet_black", "bet_green"]))
async def process_bet(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    
    if user[2] < 10:
        await callback.answer("❌ Нужно минимум 10 🪙", show_alert=True)
        return
    
    color_choice = callback.data.split("_")[1]
    color_name = "🔴 Красное" if color_choice == "red" else " Чёрное" if color_choice == "black" else "🟢 Зелёное"
    
    await callback.message.edit_text(
        f" **Введите сумму ставки:**\n\n"
        f"Твой баланс: {user[2]} 🪙\n"
        f"Выбрано: {color_name}\n\n"
        f"*(Напиши число в чат)*"
    )
    await callback.answer()

@dp.message()
async def handle_bet_amount(message: types.Message):
    if not message.text or not message.text.isdigit():
        return
    
    bet_amount = int(message.text)
    user = get_user(message.from_user.id, message.from_user.username)
    
    if bet_amount < 10:
        await message.answer(" Минимальная ставка: 10 🪙")
        return
    
    if bet_amount > user[2]:
        await message.answer("❌ Недостаточно средств!")
        return
    
    update_coins(message.from_user.id, -bet_amount)
    
    # АНИМАЦИЯ
    emojis = ["🎰", "🔴", "⚫", "🟢", "🎲"]
    for i in range(10):
        emoji = random.choice(emojis)
        num = random.randint(0, 14)
        await message.edit_text(
            f"🎰 **КРУТИМ РУЛЕТКУ...** {emoji}\n\n"
            f"Ставка: {bet_amount} \n"
            f"Число: {num}\n\n"
            f"{'' if num <= 7 else '' if num >= 8 else '🟢'}"
        )
        await asyncio.sleep(0.3)
    
    result = random.randint(0, 14)
    
    if result == 0:
        color, emoji, color_name = "green", "🟢", "ЗЕЛЁНОЕ"
    elif result <= 7:
        color, emoji, color_name = "red", "🔴", "КРАСНОЕ"
    else:
        color, emoji, color_name = "black", "⚫", "ЧЁРНОЕ"
    
    win = random.choice([True, False])
    
    if win:
        win_amount = bet_amount * 2
        update_coins(message.from_user.id, win_amount)
        new_balance = user[2] - bet_amount + win_amount
        
        await message.edit_text(
            f"🎰 **РЕЗУЛЬТАТ:** {emoji} {color_name}\n\n"
            f"🎉 **ТЫ ВЫИГРАЛ!**\n\n"
            f"Ставка: {bet_amount} \n"
            f"Выигрыш: {win_amount} 🪙 (x2)\n"
            f"Новый баланс: {new_balance} 🪙",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎰 Ещё раз", callback_data="casino"),
                 InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_menu")]
            ])
        )
    else:
        new_balance = user[2] - bet_amount
        
        await message.edit_text(
            f"🎰 **РЕЗУЛЬТАТ:** {emoji} {color_name}\n\n"
            f"😔 **ПРОИГРЫШ**\n\n"
            f"Ставка: {bet_amount} 🪙\n"
            f"Остаток: {new_balance} 🪙",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎰 Ещё раз", callback_data="casino"),
                 InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_menu")]
            ])
        )

# ===== МАГАЗИН =====
@dp.message(Command('shop'))
async def cmd_shop(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ 100 💎 за 1 Звезду", callback_data="buy_100gems")],
        [InlineKeyboardButton(text="⭐️ 500 💎 за 5 Звёзд", callback_data="buy_500gems")],
        [InlineKeyboardButton(text="👑 PREMIUM (500 💎)", callback_data="buy_premium")],
    ])
    
    await message.answer(
        "🛒 **МАГАЗИН GEMS**\n\n"
        "💎 **Курс:** 1 ⭐️ = 100 💎\n\n"
        "👑 **PREMIUM:** 500 💎\n"
        "_Особый статус и привилегии_\n\n"
        "🪙 Coins — для игр\n"
        "💎 Gems — для премиума",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "shop")
async def cb_shop(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ 100 💎 за 1 Звезду", callback_data="buy_100gems")],
        [InlineKeyboardButton(text="⭐️ 500 💎 за 5 Звёзд", callback_data="buy_500gems")],
        [InlineKeyboardButton(text="👑 PREMIUM (500 💎)", callback_data="buy_premium")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
    ])
    
    await callback.message.edit_text(
        "🛒 **МАГАЗИН GEMS**\n\n"
        "💎 **Курс:** 1 ⭐️ = 100 💎\n\n"
        "👑 **PREMIUM:** 500 💎\n"
        "_Особый статус и привилегии_\n\n"
        "🪙 Coins — для игр\n"
        "💎 Gems — для премиума",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.in_(["buy_100gems", "buy_500gems"]))
async def process_buy_stars(callback: types.CallbackQuery):
    amount_gems = 100 if callback.data == "buy_100gems" else 500
    stars_cost = 1 if callback.data == "buy_100gems" else 5
    
    await callback.message.answer_invoice(
        title=f"Покупка {amount_gems} Gems",
        description=f"Оплата {stars_cost} Telegram Звёздами ️",
        payload=f"buy_gems_{amount_gems}",
        provider_token="",
        currency="XTR",
        prices=[LabeledPrice(label="Gems", amount=stars_cost)],
    )
    await callback.answer()

@dp.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)

@dp.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    
    if payload.startswith("buy_gems_"):
        amount_gems = int(payload.split("_")[2])
        update_gems(user_id, amount_gems)
        user = get_user(user_id, message.from_user.username)
        await message.answer(
            f"✅ **Оплата прошла!**\n\n"
            f"Тебе начислено **{amount_gems} 💎**\n\n"
            f"Баланс Gems: {user[3]} 💎"
        )

@dp.callback_query(F.data == "buy_premium")
async def cb_buy_premium(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    
    if user[5] == 1:
        await callback.answer("👑 У тебя уже есть PREMIUM!", show_alert=True)
        return
    
    if user[3] >= 500:
        update_gems(callback.from_user.id, -500)
        set_premium(callback.from_user.id)
        await callback.message.edit_text(
            "🎉 **ПОЗДРАВЛЯЕМ!**\n\n"
            "👑 **PREMIUM статус** активирован!\n\n"
            "Теперь ты особенный! 💎",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
            ])
        )
        await callback.answer()
    else:
        await callback.answer(f"❌ Нужно 500 💎, у тебя {user[3]} 💎", show_alert=True)

# ===== КЛАН =====
@dp.message(Command('clan'))
async def cmd_clan(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username)
    clan = get_clan(user[7]) if user[7] else None
    
    if clan:
        text = (
            f"⚔️ **ТВОЙ КЛАН**\n\n"
            f"**Название:** {clan[1]}\n"
            f"👑 **Владелец:** {clan[2]}\n"
            f"🪙 **Казна:** {clan[3]} 🪙\n"
            f"👥 **Участников:** {clan[4]}\n"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=" Выйти из клана", callback_data="clan_leave")],
        ])
    else:
        text = (
            f"⚔️ **КЛАН**\n\n"
            f"Ты не состоишь в клане.\n\n"
            f"Создай свой клан за **1000 🪙**!"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=" Создать клан", callback_data="clan_create")],
        ])
    
    await message.answer(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

@dp.callback_query(F.data == "clan")
async def cb_clan(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    clan = get_clan(user[7]) if user[7] else None
    
    if clan:
        text = (
            f"⚔️ **ТВОЙ КЛАН**\n\n"
            f"**Название:** {clan[1]}\n"
            f"👑 **Владелец:** {clan[2]}\n"
            f"🪙 **Казна:** {clan[3]} 🪙\n"
            f"👥 **Участников:** {clan[4]}\n"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🚪 Выйти", callback_data="clan_leave")],
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
        ])
    else:
        text = (
            f"️ **КЛАН**\n\n"
            f"Ты не состоишь в клане.\n\n"
            f"Создай свой клан за **1000 🪙**!"
        )
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="➕ Создать клан", callback_data="clan_create")],
            [InlineKeyboardButton(text="️ Назад", callback_data="back_to_menu")],
        ])
    
    await callback.message.edit_text(text, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)
    await callback.answer()

@dp.callback_query(F.data == "clan_create")
async def cb_clan_create(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    
    if user[2] < 1000:
        await callback.answer("❌ Нужно 1000 🪙 для создания клана!", show_alert=True)
        return
    
    await callback.message.edit_text(
        " **СОЗДАНИЕ КЛАНА**\n\n"
        "Напиши название клана:\n"
        "*(Отмени командой /cancel)*"
    )
    await callback.answer()

@dp.message(ClanStates.waiting_create)
async def process_clan_create(message: types.Message, state: FSMContext):
    name = message.text
    user = get_user(message.from_user.id, message.from_user.username)
    
    if user[2] < 1000:
        await message.answer("❌ Недостаточно монет!")
        await state.clear()
        return
    
    update_coins(message.from_user.id, -1000)
    clan_id = create_clan(name, message.from_user.id)
    
    await message.answer(
        f"✅ **Клан создан!**\n\n"
        f"**Название:** {name}\n"
        f"**ID:** {clan_id}\n\n"
        f"Списано: 1000 🪙",
        parse_mode=ParseMode.MARKDOWN
    )
    await state.clear()

@dp.callback_query(F.data == "clan_leave")
async def cb_clan_leave(callback: types.CallbackQuery):
    leave_clan(callback.from_user.id)
    await callback.message.edit_text(
        "🚪 **Ты вышел из клана!**",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== ТОП =====
@dp.message(Command('top'))
async def cmd_top(message: types.Message):
    top = get_top_users(10)
    
    text = "🏆 **ТОП-10 ИГРОКОВ**\n\n"
    for i, (username, coins, line) in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        rank = get_rank(coins, line)
        text += f"{medal} **{username or 'Аноним'}:** {coins} 🪙 — {rank}\n"
    
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data == "top")
async def cb_top(callback: types.CallbackQuery):
    top = get_top_users(10)
    
    text = "🏆 **ТОП-10 ИГРОКОВ**\n\n"
    for i, (username, coins, line) in enumerate(top, 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        rank = get_rank(coins, line)
        text += f"{medal} **{username or 'Аноним'}:** {coins} 🪙 — {rank}\n"
    
    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== АДМИНИСТРАЦИЯ =====
@dp.message(Command('admins'))
async def cmd_admins(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("⚠️ Эта команда работает только в группах!")
        return
    
    admins = get_admins(message.chat.id)
    
    if not admins:
        await message.answer(
            "👑 **АДМИНИСТРАЦИЯ**\n\n"
            "⚪ _Список пуст_\n\n"
            "Добавь бота как админа и используй /addadmin"
        )
        return
    
    owners = [a for a in admins if a[1] == 'owner']
    co_owners = [a for a in admins if a[1] == 'co_owner']
    admin_list = [a for a in admins if a[1] == 'admin']
    mods = [a for a in admins if a[1] == 'mod']
    
    text = " **АДМИНИСТРАЦИЯ ГРУППЫ** 👑\n\n"
    
    if owners:
        text += "══════ **OWNERS** ══════\n"
        for user_id, _ in owners:
            try:
                member = await message.chat.get_member(user_id)
                badge = "🔱 " if is_owner(user_id) else ""
                text += f"• {badge}{member.user.full_name}\n"
            except:
                text += f"• User {user_id}\n"
        text += "\n"
    
    if co_owners:
        text += "────────── **CO-OWNERS** ──────────\n"
        for user_id, _ in co_owners:
            try:
                member = await message.chat.get_member(user_id)
                text += f"• {member.user.full_name}\n"
            except:
                text += f"• User {user_id}\n"
        text += "\n"
    
    if admin_list:
        text += "────────── **ADMINS** ──────────\n"
        for user_id, _ in admin_list:
            try:
                member = await message.chat.get_member(user_id)
                text += f"• {member.user.full_name}\n"
            except:
                text += f"• User {user_id}\n"
        text += "\n"
    
    if mods:
        text += "────────── **MODERATORS** ──────────\n"
        for user_id, _ in mods:
            try:
                member = await message.chat.get_member(user_id)
                text += f"• {member.user.full_name}\n"
            except:
                text += f"• User {user_id}\n"
    
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data == "admins_list")
async def cb_admins_list(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "👥 **АДМИНИСТРАЦИЯ**\n\n"
        "Эта команда работает в группах.\n"
        "Напиши /admins в групповом чате!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

@dp.message(Command('addadmin'))
async def cmd_addadmin(message: types.Message):
    if message.chat.type == 'private':
        await message.answer("⚠️ Только в группах!")
        return
    
    member = await message.chat.get_member(message.from_user.id)
    if member.status not in ['creator', 'administrator']:
        await message.answer("⚠️ У тебя нет прав!")
        return
    
    if not message.reply_to_message:
        await message.answer(
            "➕ **ДОБАВЛЕНИЕ АДМИНА**\n\n"
            "Ответь на сообщение и напиши:\n"
            "/addadmin owner | co_owner | admin | mod"
        )
        return
    
    args = message.text.split()
    if len(args) < 2:
        await message.answer("Укажи роль: owner, co_owner, admin или mod")
        return
    
    role = args[1]
    if role not in ['owner', 'co_owner', 'admin', 'mod']:
        await message.answer("❌ Неверная роль!")
        return
    
    user_id = message.reply_to_message.from_user.id
    add_admin(message.chat.id, user_id, role)
    
    user = message.reply_to_message.from_user
    await message.answer(f"✅ **{user.full_name}** → **{role.upper()}**")

# ===== АДМИН-ПАНЕЛЬ =====
@dp.message(Command('admin'))
async def cmd_admin(message: types.Message):
    if not is_owner(message.from_user.id):
        await message.answer(" Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="💰 Добавить Coins", callback_data="admin_addcoins")],
        [InlineKeyboardButton(text=" Добавить Gems", callback_data="admin_addgems")],
        [InlineKeyboardButton(text=" Пользователи", callback_data="admin_users")],
    ])
    
    await message.answer(
        "⚙️ **АДМИН-ПАНЕЛЬ ВЛАДЕЛЬЦА**\n\n"
        "Выбери действие:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: types.CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="💰 Добавить Coins", callback_data="admin_addcoins")],
        [InlineKeyboardButton(text=" Добавить Gems", callback_data="admin_addgems")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")],
    ])
    
    await callback.message.edit_text(
        "⚙️ **АДМИН-ПАНЕЛЬ ВЛАДЕЛЬЦА**\n\n"
        "Выбери действие:",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_stats")
async def cb_admin_stats(callback: types.CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    
    users = get_all_users()
    total_coins = sum(u[2] for u in users)
    total_gems = sum(u[3] for u in users)
    premium_count = sum(1 for u in users if u[5] == 1)
    
    await callback.message.edit_text(
        f"📊 **СТАТИСТИКА БОТА**\n\n"
        f"👥 **Всего пользователей:** {len(users)}\n"
        f" **Premium:** {premium_count}\n"
        f"🪙 **Всего Coins:** {total_coins}\n"
        f" **Всего Gems:** {total_gems}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_addcoins")
async def cb_admin_addcoins(callback: types.CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💰 **ДОБАВИТЬ COINS**\n\n"
        "Напиши: @username сумма\n"
        "Пример: @Mr_V3ktor 12000\n\n"
        "*(Отмени: /cancel)*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_addgems")
async def cb_admin_addgems(callback: types.CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💎 **ДОБАВИТЬ GEMS**\n\n"
        "Напиши: @username сумма\n"
        "Пример: @Mr_V3ktor 500\n\n"
        "*(Отмени: /cancel)*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_users")
async def cb_admin_users(callback: types.CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    
    users = get_all_users()[:20]
    
    text = " **ПОСЛЕДНИЕ ПОЛЬЗОВАТЕЛИ:**\n\n"
    for user in users:
        rank = get_rank(user[2], user[6])
        text += f"• {user[1] or 'Аноним'}: {user[2]}🪙 {rank}\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

# ===== ОБРАБОТКА АДМИН-КОМАНД =====
@dp.message()
async def handle_admin_commands(message: types.Message):
    if not is_owner(message.from_user.id):
        return
    
    text = message.text or ""
    
    # Добавить Coins
    if text.startswith('/addcoins ') or (message.reply_to_message and text.isdigit()):
        parts = text.replace('/addcoins ', '').split()
        if len(parts) == 2:
            username = parts[0].lstrip('@')
            amount = int(parts[1])
            user = get_user_by_username(username)
            if user:
                update_coins(user[0], amount)
                await message.answer(f"✅ Начислено {amount} 🪙 пользователю @{username}")
            else:
                await message.answer("❌ Пользователь не найден!")
        return
    
    # Добавить Gems
    if text.startswith('/addgems '):
        parts = text.replace('/addgems ', '').split()
        if len(parts) == 2:
            username = parts[0].lstrip('@')
            amount = int(parts[1])
            user = get_user_by_username(username)
            if user:
                update_gems(user[0], amount)
                await message.answer(f"✅ Начислено {amount} 💎 пользователю @{username}")
            else:
                await message.answer("❌ Пользователь не найден!")
        return

# ===== ПОМОЩЬ =====
@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    await message.answer(
        "❓ **ПОМОЩЬ**\n\n"
        "🏠 /start — Главное меню\n"
        " /profile — Мой профиль\n"
        "💰 /balance — Баланс\n"
        "🎁 /daily — Ежедневный бонус\n"
        "🎰 /casino — Казино\n"
        " /shop — Магазин\n"
        "📊 /rank — Мой ранг\n"
        "🔄 /changerank — Сменить линию\n"
        "⚔️ /clan — Клан\n"
        " /top — Топ игроков\n"
        "👥 /admins — Администрация\n"
        "❓ /help — Эта справка\n\n"
        "🔱 **Владелец:** /admin"
    )

@dp.callback_query(F.data == "help")
async def cb_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "❓ **ПОМОЩЬ**\n\n"
        " /start — Главное меню\n"
        "👤 /profile — Мой профиль\n"
        "💰 /balance — Баланс\n"
        "🎁 /daily — Ежедневный бонус\n"
        "🎰 /casino — Казино\n"
        "🛒 /shop — Магазин\n"
        " /rank — Мой ранг\n"
        "🔄 /changerank — Сменить линию\n"
        "⚔️ /clan — Клан\n"
        "🏆 /top — Топ игроков\n"
        "👥 /admins — Администрация\n"
        "❓ /help — Эта справка\n\n"
        "🔱 **Владелец:** /admin",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== НАЗАД =====
@dp.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username)
    rank = get_rank(user[2], user[6])
    premium_badge = "👑 PREMIUM | " if user[5] else ""
    owner_badge = " ВЛАДЕЛЕЦ | " if is_owner(callback.from_user.id) else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👤 Профиль", callback_data="profile")],
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🎁 Daily", callback_data="daily"),
         InlineKeyboardButton(text="🎰 Казино", callback_data="casino")],
        [InlineKeyboardButton(text=" Магазин", callback_data="shop"),
         InlineKeyboardButton(text="📊 Ранг", callback_data="rank")],
        [InlineKeyboardButton(text="⚔️ Клан", callback_data="clan"),
         InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
        [InlineKeyboardButton(text="👥 Администрация", callback_data="admins_list")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
    ])
    
    if is_owner(callback.from_user.id):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_panel")
        ])
    
    await callback.message.edit_text(
        f"👋 {owner_badge}{premium_badge}С возвращением, **{callback.from_user.full_name}**!\n\n"
        f"{rank}\n"
        f"🪙 **Coins:** {user[2]}\n"
        f"💎 **Gems:** {user[3]}\n\n"
        f"Выбирай действие:",
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=keyboard
    )
    await callback.answer()

# ===== ПРИВЕТСТВИЕ В ГРУППЕ =====
@dp.chat_member()
async def chat_member_update(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == 'member':
        user = event.new_chat_member.user
        
        if is_owner(user.id):
            await event.answer(
                f"🔱 **ВНИМАНИЕ! ВЛАДЕЛЕЦ БОТА ЗАШЁЛ В ЧАТ!** 🎉\n\n"
                f"👑 **{user.full_name}** присоединился к нам!\n\n"
                f"Это создатель бота — относитесь с уважением! 💎"
            )
            add_admin(event.chat.id, user.id, 'owner')
        else:
            await event.answer(
                f"👋 **Добро пожаловать**, {user.full_name}!\n\n"
                f"/daily — забери бонус\n"
                f"/casino — испытай удачу\n"
                f"/admins — администрация"
            )

# ===== ЗАПУСК =====
async def main():
    await set_commands()
    print("✅ БОТ ЗАПУЩЕН! Всё работает! 🔥")
    print(f"🔱 Владелец: {OWNER_ID}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
