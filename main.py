import os
import sqlite3
import random
import asyncio
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice
from aiogram.enums import ParseMode

# ===== НАСТРОЙКИ =====
TOKEN = "8614039525:AAF2c9BWQqwFWxLQKCrBH-4-2YEA41w8z-A"
OWNER_ID = 1787439005  # ТВОЙ Telegram ID (узнай через @userinfobot)

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, 
                       coins INTEGER DEFAULT 0, gems INTEGER DEFAULT 0,
                       is_premium INTEGER DEFAULT 0, last_daily TEXT)''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS group_admins 
                      (group_id INTEGER, user_id INTEGER, role TEXT, 
                       UNIQUE(group_id, user_id))''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS groups 
                      (group_id INTEGER PRIMARY KEY, title TEXT, member_count INTEGER)''')
    conn.commit()
    conn.close()

def get_user(user_id, username):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
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
    cursor.execute("SELECT username, coins FROM users ORDER BY coins DESC LIMIT ?", (limit,))
    top = cursor.fetchall()
    conn.close()
    return top

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

def save_group(group_id, title, member_count):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO groups VALUES (?, ?, ?)", (group_id, title, member_count))
    conn.commit()
    conn.close()

init_db()

# ===== МЕНЮ КОМАНД =====
async def set_commands():
    commands = [
        BotCommand(command='start', description='🏠 Главное меню'),
        BotCommand(command='balance', description='💰 Мой баланс'),
        BotCommand(command='daily', description=' Ежедневный бонус'),
        BotCommand(command='casino', description='🎰 Казино'),
        BotCommand(command='shop', description=' Магазин'),
        BotCommand(command='admins', description='👥 Администрация'),
        BotCommand(command='top', description='🏆 Топ игроков'),
        BotCommand(command='admin', description='️ Админ-панель (только владелец)'),
    ]
    await bot.set_my_commands(commands)

# ===== ПРОВЕРКА ВЛАДЕЛЬЦА =====
def is_owner(user_id):
    return user_id == 8287969191

# ===== ГЛАВНОЕ МЕНЮ =====
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username or "User")
    premium_badge = "👑 PREMIUM | " if user[5] else ""
    owner_badge = "🔱 ВЛАДЕЛЕЦ | " if is_owner(message.from_user.id) else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🎁 Daily", callback_data="daily"),
         InlineKeyboardButton(text=" Казино", callback_data="casino")],
        [InlineKeyboardButton(text="💎 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
        [InlineKeyboardButton(text="👥 Администрация", callback_data="admins_list")],
    ])
    
    if is_owner(message.from_user.id):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_panel")
        ])
    
    caption = (
        f"👋 {owner_badge}{premium_badge}Добро пожаловать, **{message.from_user.full_name}**!\n\n"
        f"🪙 **Coins:** {user[2]} (игровая)\n"
        f"💎 **Gems:** {user[3]} (донат)\n\n"
        f"Выбирай действие 👇"
    )
    
    await message.answer(caption, parse_mode=ParseMode.MARKDOWN, reply_markup=keyboard)

# ===== БАЛАНС =====
@dp.message(Command('balance'))
async def cmd_balance(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username or "User")
    premium_badge = "👑 " if user[5] else ""
    
    await message.answer(
        f"{premium_badge}💰 **ТВОЙ БАЛАНС**\n\n"
        f"🪙 **Coins:** {user[2]} (игровая валюта)\n"
        f"💎 **Gems:** {user[3]} (премиум валюта)\n\n"
        f"🪙 Coins: /daily, казино\n"
        f" Gems: покупка за ⭐️"
    )

@dp.callback_query(F.data == "balance")
async def cb_balance(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    premium_badge = "👑 " if user[5] else ""
    
    await callback.message.edit_text(
        f"{premium_badge}💰 **ТВОЙ БАЛАНС**\n\n"
        f"🪙 **Coins:** {user[2]} (игровая валюта)\n"
        f" **Gems:** {user[3]} (премиум валюта)\n\n"
        f"🪙 Coins: /daily, казино\n"
        f"💎 Gems: покупка за ️",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== DAILY =====
@dp.message(Command('daily'))
async def cmd_daily(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username or "User")
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user[6] == today:
        await message.answer("⏳ Ты уже забрал награду сегодня!\n\nПриходи завтра 🌅")
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
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user[6] == today:
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
        f"🎉 **ЕЖЕДНЕВНАЯ НАГРАДА!**\n\n"
        f"Ты получил **{reward} 🪙**\n\n"
        f"Новый баланс: {user[2] + reward} 🪙",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔜 Завтра", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== КАЗИНО (ИСПРАВЛЕНО) =====
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
        "Минимальная ставка: 10 🪙",
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
        " **Чёрное** — x2 (8-14)\n"
        "🟢 **Зелёное** — x14 (0)\n\n"
        "Минимальная ставка: 10 🪙",
        reply_markup=keyboard
    )
    await callback.answer()

@dp.callback_query(F.data.in_(["bet_red", "bet_black", "bet_green"]))
async def process_bet(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    
    if user[2] < 10:
        await callback.answer("❌ Нужно минимум 10 🪙", show_alert=True)
        return
    
    # Сохраняем выбор цвета
    color_choice = callback.data.split("_")[1]
    
    await callback.message.edit_text(
        f"💰 **Введите сумму ставки:**\n\n"
        f"Твой баланс: {user[2]} 🪙\n"
        f"Выбрано: {'🔴 Красное' if color_choice == 'red' else ' Чёрное' if color_choice == 'black' else '🟢 Зелёное'}\n\n"
        f"*(Напиши число в чат)*"
    )
    await callback.answer()

@dp.message()
async def handle_bet_amount(message: types.Message):
    if not message.text or not message.text.isdigit():
        return
    
    bet_amount = int(message.text)
    user = get_user(message.from_user.id, message.from_user.username or "User")
    
    if bet_amount < 10:
        await message.answer("❌ Минимальная ставка: 10 🪙")
        return
    
    if bet_amount > user[2]:
        await message.answer("❌ Недостаточно средств!")
        return
    
    # Списываем ставку
    update_coins(message.from_user.id, -bet_amount)
    
    # АНИМАЦИЯ РУЛЕТКИ
    emojis = ["🎰", "🔴", "⚫", "🟢", "🎲"]
    for i in range(10):
        emoji = random.choice(emojis)
        num = random.randint(0, 14)
        await message.edit_text(
            f"🎰 **КРУТИМ РУЛЕТКУ...** {emoji}\n\n"
            f"Ставка: {bet_amount} 🪙\n"
            f"Число: {num}\n\n"
            f"{'🔴' if num <= 7 else '⚫' if num >= 8 else '🟢'}"
        )
        await asyncio.sleep(0.3)
    
    # РЕЗУЛЬТАТ (0-14)
    result = random.randint(0, 14)
    
    if result == 0:
        color = "green"
        emoji = "🟢"
        color_name = "ЗЕЛЁНОЕ"
    elif result <= 7:
        color = "red"
        emoji = "🔴"
        color_name = "КРАСНОЕ"
    else:
        color = "black"
        emoji = "⚫"
        color_name = "ЧЁРНОЕ"
    
    # Проверяем выигрыш
    win = False
    multiplier = 0
    
    if color == "green":
        win = True
        multiplier = 14
    elif color == "red":
        win = True
        multiplier = 2
    else:
        win = True
        multiplier = 2
    
    if win:
        win_amount = bet_amount * multiplier
        update_coins(message.from_user.id, win_amount)
        new_balance = user[2] - bet_amount + win_amount
        
        await message.edit_text(
            f"🎰 **РЕЗУЛЬТАТ:** {emoji} {color_name}\n\n"
            f"🎉 **ТЫ ВЫИГРАЛ!**\n\n"
            f"Ставка: {bet_amount} \n"
            f"Выигрыш: {win_amount} 🪙 (x{multiplier})\n"
            f"Новый баланс: {new_balance} 🪙",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎰 Ещё раз", callback_data="casino"),
                 InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_menu")]
            ])
        )
    else:
        new_balance = user[2] - bet_amount
        
        await message.edit_text(
            f" **РЕЗУЛЬТАТ:** {emoji} {color_name}\n\n"
            f"😔 **ПРОИГРЫШ**\n\n"
            f"Ставка: {bet_amount} 🪙\n"
            f"Остаток: {new_balance} 🪙",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🎰 Ещё раз", callback_data="casino"),
                 InlineKeyboardButton(text="🏠 Меню", callback_data="back_to_menu")]
            ])
        )

# ===== МАГАЗИН (ИСПРАВЛЕНО) =====
@dp.message(Command('shop'))
async def cmd_shop(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ 100 💎 за 1 Звезду", callback_data="buy_100gems")],
        [InlineKeyboardButton(text="⭐️ 500 💎 за 5 Звёзд", callback_data="buy_500gems")],
        [InlineKeyboardButton(text=" PREMIUM (500 💎)", callback_data="buy_premium")],
    ])
    
    await message.answer(
        "💎 **МАГАЗИН GEMS**\n\n"
        " **Курс:** 1 ⭐️ = 100 💎\n\n"
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
        [InlineKeyboardButton(text="️ Назад", callback_data="back_to_menu")],
    ])
    
    await callback.message.edit_text(
        "💎 **МАГАЗИН GEMS**\n\n"
        "💎 **Курс:** 1 ⭐️ = 100 💎\n\n"
        " **PREMIUM:** 500 💎\n"
        "_Особый статус и привилегии_\n\n"
        " Coins — для игр\n"
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
        description=f"Оплата {stars_cost} Telegram Звёздами ⭐️",
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
        user = get_user(user_id, message.from_user.username or "User")
        await message.answer(
            f"✅ **Оплата прошла!**\n\n"
            f"Тебе начислено **{amount_gems} 💎**\n\n"
            f"Баланс Gems: {user[3]} 💎"
        )

@dp.callback_query(F.data == "buy_premium")
async def cb_buy_premium(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    
    if user[5] == 1:
        await callback.answer(" У тебя уже есть PREMIUM!", show_alert=True)
        return
    
    if user[3] >= 500:
        update_gems(callback.from_user.id, -500)
        set_premium(callback.from_user.id)
        await callback.message.edit_text(
            "🎉 **ПОЗДРАВЛЯЕМ!**\n\n"
            "👑 **PREMIUM статус** активирован!\n\n"
            "Теперь ты особенный! ",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
            ])
        )
        await callback.answer()
    else:
        await callback.answer(f"❌ Нужно 500 💎, у тебя {user[3]} 💎", show_alert=True)

# ===== ТОП ИГРОКОВ =====
@dp.message(Command('top'))
async def cmd_top(message: types.Message):
    top = get_top_users(10)
    
    text = " **ТОП-10 ИГРОКОВ**\n\n"
    for i, (username, coins) in enumerate(top, 1):
        medal = "" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} **{username or 'Аноним'}:** {coins} 🪙\n"
    
    await message.answer(text, parse_mode=ParseMode.MARKDOWN)

@dp.callback_query(F.data == "top")
async def cb_top(callback: types.CallbackQuery):
    top = get_top_users(10)
    
    text = "🏆 **ТОП-10 ИГРОКОВ**\n\n"
    for i, (username, coins) in enumerate(top, 1):
        medal = "" if i == 1 else "🥈" if i == 2 else "🥉" if i == 3 else f"{i}."
        text += f"{medal} **{username or 'Аноним'}:** {coins} 🪙\n"
    
    await callback.message.edit_text(
        text,
        parse_mode=ParseMode.MARKDOWN,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== АДМИНИСТРАЦИЯ ГРУППЫ =====
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
    
    text = "👑 **АДМИНИСТРАЦИЯ ГРУППЫ** \n\n"
    
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
        await message.answer("⚠️ Эта команда работает только в группах!")
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

# ===== АДМИН-ПАНЕЛЬ ВЛАДЕЛЬЦА =====
@dp.message(Command('admin'))
async def cmd_admin(message: types.Message):
    if not is_owner(message.from_user.id):
        await message.answer("⛔ Доступ запрещён!")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="💰 Управление балансом", callback_data="admin_balance")],
        [InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
    ])
    
    await message.answer(
        "⚙️ **АДМИН-ПАНЕЛЬ ВЛАДЕЛЬЦА**\n\n"
        "Выбери действие:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data == "admin_panel")
async def cb_admin_panel(callback: types.CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔ Доступ запрещён!", show_alert=True)
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")],
        [InlineKeyboardButton(text="💰 Управление балансом", callback_data="admin_balance")],
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
        await callback.answer("", show_alert=True)
        return
    
    users = get_all_users()
    total_coins = sum(u[2] for u in users)
    total_gems = sum(u[3] for u in users)
    premium_count = sum(1 for u in users if u[5] == 1)
    
    await callback.message.edit_text(
        f" **СТАТИСТИКА БОТА**\n\n"
        f"👥 **Всего пользователей:** {len(users)}\n"
        f"👑 **Premium:** {premium_count}\n"
        f" **Всего Coins:** {total_coins}\n"
        f"💎 **Всего Gems:** {total_gems}",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_broadcast")
async def cb_admin_broadcast(callback: types.CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("", show_alert=True)
        return
    
    await callback.message.edit_text(
        " **РАССЫЛКА**\n\n"
        "Напиши сообщение, которое нужно разослать всем пользователям.\n\n"
        "*(Отмени командой /cancel)*",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

@dp.callback_query(F.data == "admin_balance")
async def cb_admin_balance(callback: types.CallbackQuery):
    if not is_owner(callback.from_user.id):
        await callback.answer("⛔", show_alert=True)
        return
    
    await callback.message.edit_text(
        "💰 **УПРАВЛЕНИЕ БАЛАНСОМ**\n\n"
        "Напиши: /addcoins USER_ID SUMMA\n"
        "Или: /addgems USER_ID SUMMA\n\n"
        "*(Отмени командой /cancel)*",
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
    
    users = get_all_users()[:20]  # Первые 20
    
    text = "👥 **ПОСЛЕДНИЕ ПОЛЬЗОВАТЕЛИ:**\n\n"
    for user in users:
        text += f"• {user[1] or 'Аноним'}: {user[2]} {user[3]}💎\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="️ Назад", callback_data="admin_panel")]
        ])
    )
    await callback.answer()

# ===== КОМАНДЫ АДМИНА =====
@dp.message(Command('addcoins'))
async def cmd_addcoins(message: types.Message):
    if not is_owner(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /addcoins USER_ID SUMMA")
        return
    
    user_id = int(args[1])
    amount = int(args[2])
    update_coins(user_id, amount)
    
    await message.answer(f"✅ Начислено {amount} 🪙 пользователю {user_id}")

@dp.message(Command('addgems'))
async def cmd_addgems(message: types.Message):
    if not is_owner(message.from_user.id):
        return
    
    args = message.text.split()
    if len(args) != 3:
        await message.answer("Использование: /addgems USER_ID SUMMA")
        return
    
    user_id = int(args[1])
    amount = int(args[2])
    update_gems(user_id, amount)
    
    await message.answer(f"✅ Начислено {amount} 💎 пользователю {user_id}")

# ===== НАЗАД В МЕНЮ =====
@dp.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    premium_badge = "👑 PREMIUM | " if user[5] else ""
    owner_badge = "🔱 ВЛАДЕЛЕЦ | " if is_owner(callback.from_user.id) else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🎁 Daily", callback_data="daily"),
         InlineKeyboardButton(text="🎰 Казино", callback_data="casino")],
        [InlineKeyboardButton(text="💎 Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="🏆 Топ", callback_data="top")],
        [InlineKeyboardButton(text="👥 Администрация", callback_data="admins_list")],
    ])
    
    if is_owner(callback.from_user.id):
        keyboard.inline_keyboard.append([
            InlineKeyboardButton(text="⚙️ АДМИН-ПАНЕЛЬ", callback_data="admin_panel")
        ])
    
    await callback.message.edit_text(
        f"👋 {owner_badge}{premium_badge}С возвращением, **{callback.from_user.full_name}**!\n\n"
        f"🪙 **Coins:** {user[2]}\n"
        f" **Gems:** {user[3]}\n\n"
        f"Выбирай действие:",
        reply_markup=keyboard
    )
    await callback.answer()

# ===== ПРИВЕТСТВИЕ В ГРУППЕ С ВЫДЕЛЕНИЕМ ВЛАДЕЛЬЦА =====
@dp.chat_member()
async def chat_member_update(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == 'member':
        user = event.new_chat_member.user
        
        if is_owner(user.id):
            # ОСОБОЕ ПРИВЕТСТВИЕ ДЛЯ ВЛАДЕЛЬЦА
            await event.answer(
                f"🔱 **ВНИМАНИЕ! ВЛАДЕЛЕЦ БОТА ЗАШЁЛ В ЧАТ!** \n\n"
                f"👑 **{user.full_name}** присоединился к нам!\n\n"
                f"Это создатель бота — относитесь с уважением! 💎"
            )
            # Автоматически добавляем как owner
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
    print("✅ БОТ ЗАПУЩЕН! Всё работает! ")
    print(f" Владелец: {OWNER_ID}")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
