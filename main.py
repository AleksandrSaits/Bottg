import os
import sqlite3
import random
from datetime import datetime
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice, FSInputFile
from aiogram.enums import ParseMode

# ТОКЕН (замени на свой полный!)
TOKEN = "8614039525:AAF2c9BWQqwFWxLQKCrBH-4-2YEA41w8z-A"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, ac_balance INTEGER, 
                       is_premium INTEGER, last_daily TEXT)''')
    conn.commit()
    conn.close()

def get_user(user_id, username):
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users VALUES (?, ?, 0, 0, '')", (user_id, username))
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

# ===== КАРТИНКИ (URL) =====
WELCOME_IMG = "https://i.imgur.com/your_welcome_image.jpg"  # Замени на свою картинку!
MENU_IMG = "https://i.imgur.com/your_menu_image.jpg"
SHOP_IMG = "https://i.imgur.com/your_shop_image.jpg"
RULES_IMG = "https://i.imgur.com/your_rules_image.jpg"

# ===== МЕНЮ КОМАНД =====
async def set_commands():
    commands = [
        BotCommand(command='start', description='🏠 Главное меню'),
        BotCommand(command='balance', description='💰 Мой баланс'),
        BotCommand(command='daily', description='🎁 Ежедневный бонус'),
        BotCommand(command='casino', description='🎰 Казино'),
        BotCommand(command='shop', description=' Магазин'),
    ]
    await bot.set_my_commands(commands)

# ===== ГЛАВНОЕ МЕНЮ =====
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username or "User")
    premium_badge = " **PREMIUM** | " if user[3] else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🎁 Daily", callback_data="daily"),
         InlineKeyboardButton(text="🎰 Казино", callback_data="casino")],
        [InlineKeyboardButton(text="⭐️ Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
    ])
    
    caption = (
        f"👋 {premium_badge}Добро пожаловать, **{message.from_user.full_name}**!\n\n"
        f"💎 **Aspekt Coins** — твоя валюта в нашем мире\n"
        f" **Баланс:** {user[2]} 💎\n\n"
        f"Выбирай, чем займёмся 👇"
    )
    
    try:
        await message.answer_photo(
            photo=WELCOME_IMG,
            caption=caption,
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=keyboard
        )
    except:
        await message.answer(caption + "\n\n*(Картинка не загрузилась)*", reply_markup=keyboard)

# ===== БАЛАНС =====
@dp.message(Command('balance'))
async def cmd_balance(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username or "User")
    premium_badge = "👑 " if user[3] else ""
    
    await message.answer(
        f"{premium_badge}💰 **Твой баланс:** {user[2]} 💎\n\n"
        f"Пополняй через /daily или выигрывай в казино!"
    )

@dp.callback_query(F.data == "balance")
async def cb_balance(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    premium_badge = "👑 " if user[3] else ""
    
    await callback.message.edit_text(
        f"{premium_badge}💰 **Твой баланс:** {user[2]} 💎\n\n"
        f"Пополняй через Daily или выигрывай в казино!",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== DAILY =====
@dp.message(Command('daily'))
async def cmd_daily(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username or "User")
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user[4] == today:
        await message.answer("⏳ Ты уже забрал награду сегодня!\n\nПриходи завтра 🌅")
        return
    
    reward = random.randint(50, 150)
    update_balance(message.from_user.id, reward)
    
    await message.answer(
        f"🎉 **Ежедневная награда!**\n\n"
        f"Ты получил **{reward} **\n\n"
        f"Новый баланс: {user[2] + reward} "
    )

@dp.callback_query(F.data == "daily")
async def cb_daily(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    today = datetime.now().strftime("%Y-%m-%d")
    
    if user[4] == today:
        await callback.answer(" Уже забрал сегодня!", show_alert=True)
        return
    
    reward = random.randint(50, 150)
    update_balance(callback.from_user.id, reward)
    
    conn = sqlite3.connect('aspekt.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET last_daily = ? WHERE user_id = ?", (today, callback.from_user.id))
    conn.commit()
    conn.close()
    
    await callback.message.edit_text(
        f"🎉 **Ежедневная награда!**\n\n"
        f"Ты получил **{reward} 💎**\n\n"
        f"Новый баланс: {user[2] + reward} 💎",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=" Ещё раз завтра", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== КАЗИНО (РУЛЕТКА) =====
@dp.message(Command('casino'))
async def cmd_casino(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔴 Красное (x2)", callback_data="bet_red"),
         InlineKeyboardButton(text="⚫ Чёрное (x2)", callback_data="bet_black")],
        [InlineKeyboardButton(text=" Зелёное (x14)", callback_data="bet_green")],
        [InlineKeyboardButton(text="🎲 Чёт/Нечёт", callback_data="bet_even_odd")],
    ])
    
    await message.answer(
        "🎰 **КАЗИНО**\n\n"
        "Выбери ставку:\n"
        " **Красное** — x2\n"
        "⚫ **Чёрное** — x2\n"
        "🟢 **Зелёное (0)** — x14\n\n"
        "Минимальная ставка: 10 💎",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.in_(["bet_red", "bet_black", "bet_green", "bet_even_odd"]))
async def process_bet(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    
    if user[2] < 10:
        await callback.answer(" Нужно минимум 10 💎", show_alert=True)
        return
    
    # Спрашиваем сумму ставки
    await callback.message.edit_text(
        "💰 **Введите сумму ставки:**\n\n"
        f"Твой баланс: {user[2]} 💎\n\n"
        "*(Напиши число в чат)*"
    )
    await callback.answer()

@dp.message()
async def handle_bet_amount(message: types.Message):
    if not message.text.isdigit():
        return
    
    bet_amount = int(message.text)
    user = get_user(message.from_user.id, message.from_user.username or "User")
    
    if bet_amount < 10:
        await message.answer("❌ Минимальная ставка: 10 💎")
        return
    
    if bet_amount > user[2]:
        await message.answer("❌ Недостаточно средств!")
        return
    
    # Сохраняем ставку в БД (упрощённо - через FSM или просто глобально)
    # Для простоты - сразу крутим рулетку
    update_balance(message.from_user.id, -bet_amount)
    
    # Рулетка: 0-14 (0=зелёное, 1-7=красное, 8-14=чёрное)
    result = random.randint(0, 14)
    
    if result == 0:
        color = "green"
        emoji = "🟢"
    elif result <= 7:
        color = "red"
        emoji = ""
    else:
        color = "black"
        emoji = "⚫"
    
    win = 0
    if color == "green":
        win = bet_amount * 14
    elif color == "red":
        win = bet_amount * 2
    else:
        win = bet_amount * 2
    
    if win > 0:
        update_balance(message.from_user.id, win)
        await message.answer(
            f"🎰 **Результат:** {emoji} {color.upper()}\n\n"
            f"🎉 **ТЫ ВЫИГРАЛ!** {win} 💎\n\n"
            f"Новый баланс: {user[2] - bet_amount + win} 💎"
        )
    else:
        await message.answer(
            f" **Результат:** {emoji} {color.upper()}\n\n"
            f"😔 Проигрыш: {bet_amount} 💎\n\n"
            f"Баланс: {user[2] - bet_amount} 💎"
        )

# ===== МАГАЗИН =====
@dp.message(Command('shop'))
async def cmd_shop(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ 100 💎 за 1 Звезду", callback_data="buy_100ac")],
        [InlineKeyboardButton(text="⭐️ 500 💎 за 5 Звёзд", callback_data="buy_500ac")],
        [InlineKeyboardButton(text="👑 PREMIUM (1000 💎)", callback_data="buy_premium")],
    ])
    
    await message.answer(
        "🛒 **МАГАЗИН ASPЕKT**\n\n"
        " **Курс:** 1 ⭐️ = 100 💎\n\n"
        "👑 **PREMIUM:** 1000 💎\n"
        "_Особый статус и привилегии_\n\n"
        "Выбирай:",
        reply_markup=keyboard
    )

@dp.callback_query(F.data.in_(["buy_100ac", "buy_500ac"]))
async def process_buy_stars(callback: types.CallbackQuery):
    amount_ac = 100 if callback.data == "buy_100ac" else 500
    stars_cost = 1 if callback.data == "buy_100ac" else 5
    
    await callback.message.answer_invoice(
        title=f"Покупка {amount_ac} Aspekt Coins",
        description=f"Оплата {stars_cost} Telegram Звёздами ⭐️",
        payload=f"buy_ac_{amount_ac}",
        provider_token="",
        currency="XTR",
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
        user = get_user(user_id, message.from_user.username or "User")
        await message.answer(
            f"✅ **Оплата прошла!**\n\n"
            f"Тебе начислено **{amount_ac} 💎**\n\n"
            f"Баланс: {user[2]} 💎"
        )

@dp.callback_query(F.data == "buy_premium")
async def cb_buy_premium(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    
    if user[3] == 1:
        await callback.answer("👑 У тебя уже есть PREMIUM!", show_alert=True)
        return
    
    if user[2] >= 1000:
        update_balance(callback.from_user.id, -1000)
        set_premium(callback.from_user.id)
        await callback.message.edit_text(
            "🎉 **ПОЗДРАВЛЯЕМ!**\n\n"
            " **PREMIUM статус** активирован!\n\n"
            "Теперь ты особенный! 💎"
        )
        await callback.answer()
    else:
        await callback.answer(f"❌ Нужно 1000 💎, у тебя {user[2]} 💎", show_alert=True)

# ===== ПРАВИЛА =====
@dp.callback_query(F.data == "rules")
async def cb_rules(callback: types.CallbackQuery):
    await callback.message.edit_text(
        "📜 **ПРАВИЛА СЕРВЕРА**\n\n"
        "1️ Уважай других участников\n"
        "2️⃣ Запрещён спам и флуд\n"
        "3️⃣ Никакой рекламы без разрешения\n"
        "4️⃣ Соблюдай тематику чата\n"
        "5️⃣ Читай закрепленные сообщения\n\n"
        "Нарушение = ️ предупреждение или 🔨 бан",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="✅ Понял", callback_data="back_to_menu")]
        ])
    )
    await callback.answer()

# ===== НАЗАД В МЕНЮ =====
@dp.callback_query(F.data == "back_to_menu")
async def cb_back_to_menu(callback: types.CallbackQuery):
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    premium_badge = "👑 **PREMIUM** | " if user[3] else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Баланс", callback_data="balance")],
        [InlineKeyboardButton(text="🎁 Daily", callback_data="daily"),
         InlineKeyboardButton(text=" Казино", callback_data="casino")],
        [InlineKeyboardButton(text="⭐️ Магазин", callback_data="shop")],
        [InlineKeyboardButton(text="📜 Правила", callback_data="rules")],
    ])
    
    await callback.message.edit_text(
        f"👋 {premium_badge}С возвращением, **{callback.from_user.full_name}**!\n\n"
        f"💎 **Баланс:** {user[2]} 💎\n\n"
        f"Выбирай действие:",
        reply_markup=keyboard
    )
    await callback.answer()

# ===== ПРИВЕТСТВИЕ В ГРУППЕ =====
@dp.chat_member()
async def chat_member_update(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == 'member':
        user = event.new_chat_member.user
        await event.answer(
            f"👋 **Добро пожаловать**, {user.full_name}!\n\n"
            f"Читай правила: /rules\n"
            f"Забирай бонус: /daily"
        )

# ===== ЗАПУСК =====
async def main():
    await set_commands()
    print("✅ БОТ ЗАПУЩЕН! Всё работает! 🔥")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
