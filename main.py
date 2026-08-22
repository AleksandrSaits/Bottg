import os
import sqlite3
import random
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

# ТОКЕН НАПРЯМУЮ (замени на свой полный токен!)
TOKEN = "8614039525:AAF2c9BWQqwFWxLQKCrBH-4-2YEA41w8z-A"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, ac_balance INTEGER, 
                       is_premium INTEGER, last_daily TEXT, warn_count INTEGER)''')
    conn.commit()
    conn.close()

def get_user(user_id, username):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users VALUES (?, ?, 0, 0, '', 0)", (user_id, username))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    conn.close()
    return user

def update_balance(user_id, amount):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET ac_balance = ac_balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def set_premium(user_id):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

init_db()

# ===== МЕНЮ КОМАНД =====
async def set_commands():
    commands = [
        BotCommand(command='start', description='Главное меню'),
        BotCommand(command='balance', description='Мой баланс 🪙'),
        BotCommand(command='daily', description='Ежедневная награда 🎁'),
        BotCommand(command='game', description='Игра 50/50 🎲'),
        BotCommand(command='shop', description='Магазин за Звёзды ⭐️'),
        BotCommand(command='rules', description='Правила группы 📜'),
    ]
    await bot.set_my_commands(commands)

# ===== ГЛАВНОЕ МЕНЮ =====
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username or "User")
    premium_tag = " [PREMIUM] " if user[3] else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text=" Daily", callback_data="daily"),
         InlineKeyboardButton(text="🎲 Игра", callback_data="game")],
        [InlineKeyboardButton(text="⭐️ Магазин", callback_data="shop")],
        [InlineKeyboardButton(text=" Правила", callback_data="rules")],
    ])
    
    await message.answer(
        f"👋 {premium_tag}Привет, {message.from_user.full_name}!\n\n"
        f"💰 Твой баланс: {user[2]} Aspekt Coins (🪙)\n\n"
        f"Выбери действие ниже 👇",
        reply_markup=keyboard
    )

# ===== ЭКОНОМИКА =====
@dp.message(Command('balance'))
@dp.callback_query(F.data == "balance")
async def cmd_balance(event: types.Message | types.CallbackQuery):
    user = get_user(event.from_user.id, event.from_user.username or "User")
    premium_tag = "👑 " if user[3] else ""
    text = f"{premium_tag}Твой баланс: **{user[2]} 🪙**"
    
    if isinstance(event, types.CallbackQuery):
        await event.answer(text, show_alert=True)
    else:
        await event.answer(text, parse_mode='Markdown')

@dp.message(Command('daily'))
@dp.callback_query(F.data == "daily")
async def cmd_daily(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    username = event.from_user.username or "User"
    user = get_user(user_id, username)
    
    today = datetime.now().strftime("%Y-%m-%d")
    if user[4] == today:
        ans = "⏳ Ты уже забрал награду сегодня. Возвращайся завтра!"
        if isinstance(event, types.CallbackQuery):
            await event.answer(ans, show_alert=True)
        else:
            await event.answer(ans)
        return
    
    reward = random.randint(15, 50)
    update_balance(user_id, reward)
    
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (today, user_id))
    conn.commit()
    conn.close()
    
    ans = f"🎉 Ты получил **{reward} 🪙**!"
    if isinstance(event, types.CallbackQuery):
        await event.answer(ans, show_alert=True)
    else:
        await event.answer(ans, parse_mode='Markdown')

@dp.message(Command('game'))
@dp.callback_query(F.data == "game")
async def cmd_game(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    username = event.from_user.username or "User"
    user = get_user(user_id, username)
    
    if user[2] < 20:
        ans = "❌ Нужно минимум 20 🪙 для игры. Забери /daily!"
        if isinstance(event, types.CallbackQuery):
            await event.answer(ans, show_alert=True)
        else:
            await event.answer(ans)
        return
    
    update_balance(user_id, -20)
    win = random.choice([True, False])
    
    if win:
        update_balance(user_id, 40)
        ans = "🎲 **ПОБЕДА!** +40 🪙 (чистая прибыль: +20 🪙)"
    else:
        ans = "🎲 **Проигрыш...** -20 🪙"
    
    if isinstance(event, types.CallbackQuery):
        await event.answer(ans, show_alert=True, parse_mode='Markdown')
    else:
        await event.answer(ans, parse_mode='Markdown')

# ===== МАГАЗИН С TELEGRAM STARS =====
@dp.message(Command('shop'))
@dp.callback_query(F.data == "shop")
async def cmd_shop(event: types.Message | types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ 10 🪙 за 1 Звезду", callback_data="buy_10ac")],
        [InlineKeyboardButton(text="⭐️ 50 🪙 за 5 Звёзд", callback_data="buy_50ac")],
        [InlineKeyboardButton(text="👑 Premium (100 🪙)", callback_data="buy_premium")],
    ])
    
    text = ("🛒 **МАГАЗИН:**\n\n"
            "Курс: 1 ⭐️ = 10 🪙\n"
            " Premium = 100 🪙\n\n"
            "Выбери товар:")
    
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await event.answer(text, parse_mode='Markdown', reply_markup=keyboard)

@dp.callback_query(F.data.in_(["buy_10ac", "buy_50ac"]))
async def process_buy_stars(callback: types.CallbackQuery):
    amount_ac = 10 if callback.data == "buy_10ac" else 50
    stars_cost = 1 if callback.data == "buy_10ac" else 5
    
    await callback.message.answer_invoice(
        title=f"Покупка {amount_ac} Aspekt Coins",
        description=f"Оплата {stars_cost} Telegram Звёздами",
        payload=f"buy_ac_{amount_ac}",
        provider_token="",  # Для звёзд пустой!
        currency="XTR",     # Код валюты Telegram Stars
        prices=[LabeledPrice(label="Aspekt Coins", amount=stars_cost)],
    )
    await callback.answer()

@dp.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)

@dp.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    
    if payload.startswith("buy_ac_"):
        amount_ac = int(payload.split("_")[2])
        update_balance(user_id, amount_ac)
        await message.answer(f"✅ Оплата прошла! Тебе начислено **{amount_ac} 🪙**", parse_mode='Markdown')

@dp.callback_query(F.data == "buy_premium")
async def cb_buy_premium(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    
    if user[3] == 1:
        await callback.answer("У тебя уже есть Premium!", show_alert=True)
        return
    
    if user[2] >= 100:
        update_balance(callback.from_user.id, -100)
        set_premium(callback.from_user.id)
        await callback.answer(" Premium куплен!", show_alert=True)
        await callback.message.edit_text("✅ Поздравляем! 👑 **Premium статус** активирован!")
    else:
        await callback.answer(f"Нужно 100 , у тебя {user[2]} ", show_alert=True)

# ===== ПРАВИЛА =====
@dp.callback_query(F.data == "rules")
async def cb_rules(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📜 **ПРАВИЛА:**\n\n"
        "1. Уважайте друг друга\n"
        "2. Без спама\n"
        "3. Без рекламы\n"
        "4. Соблюдайте тематику"
    )

# ===== ПРИВЕТСТВИЕ В ГРУППЕ =====
@dp.chat_member()
async def chat_member_update(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == 'member':
        user = event.new_chat_member.user
        await event.answer(f"👋 Добро пожаловать, {user.full_name}!")

# ===== ЗАПУСК =====
async def main():
    await set_commands()
    print("✅ БОТ ЗАПУЩЕН! Всё работает!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
