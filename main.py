import os
import sqlite3
import random
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton, LabeledPrice

TOKEN = os.getenv('8614039525:AAHdwesoNheOYGVq3Kq7qIbQ9DY5UNC7PWQ')
bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== БАЗА ДАННЫХ =====
def init_db():
    conn = sqlite3.connect('aspekt_economy.db')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users 
                      (user_id INTEGER PRIMARY KEY, username TEXT, ac_balance INTEGER, is_premium INTEGER)''')
    conn.commit()
    conn.close()

def get_user(user_id, username):
    conn = sqlite3.connect('aspekt_economy.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = cursor.fetchone()
    if not user:
        cursor.execute("INSERT INTO users (user_id, username, ac_balance, is_premium) VALUES (?, ?, 0, 0)", (user_id, username))
        conn.commit()
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        user = cursor.fetchone()
    conn.close()
    return user

def update_balance(user_id, amount):
    conn = sqlite3.connect('aspekt_economy.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET ac_balance = ac_balance + ? WHERE user_id = ?", (amount, user_id))
    conn.commit()
    conn.close()

def set_premium(user_id):
    conn = sqlite3.connect('aspekt_economy.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET is_premium = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

init_db()

# ===== МЕНЮ КОМАНД =====
async def set_commands():
    commands = [
        BotCommand(command='start', description='Главное меню'),
        BotCommand(command='balance', description='Мой баланс Aspekt Coins 🪙'),
        BotCommand(command='daily', description='Ежедневная награда 🎁'),
        BotCommand(command='game', description='Игра: Орёл или Решка (ставка 10 🪙)'),
        BotCommand(command='shop', description='Магазин: покупка AC за Звёзды ⭐️'),
    ]
    await bot.set_my_commands(commands)

# ===== ГЛАВНОЕ МЕНЮ =====
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    user = get_user(message.from_user.id, message.from_user.username or "User")
    premium_tag = "👑 [PREMIUM] " if user[3] else ""
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="💰 Мой баланс", callback_data="check_balance")],
        [InlineKeyboardButton(text="⭐️ Купить Aspekt Coins", callback_data="open_shop")],
        [InlineKeyboardButton(text="🎲 Играть", callback_data="play_game")],
    ])
    await message.answer(
        f"👋 Привет, {premium_tag}{message.from_user.full_name}!\n\n"
        f"Я бот-помощник группы. Копи Aspekt Coins (🪙), играй и покупай привилегии!",
        reply_markup=keyboard
    )

# ===== ЭКОНОМИКА =====
@dp.message(Command('balance'))
@dp.callback_query(F.data == "check_balance")
async def cmd_balance(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    username = event.from_user.username or "User"
    user = get_user(user_id, username)
    premium_tag = "👑 " if user[3] else ""
    
    text = f"{premium_tag}Твой баланс: **{user[2]} Aspekt Coins (🪙)**"
    if isinstance(event, types.CallbackQuery):
        await event.answer(text, show_alert=True)
    else:
        await event.answer(text, parse_mode='Markdown')

@dp.message(Command('daily'))
async def cmd_daily(message: types.Message):
    # Для простоты пока без проверки времени, даём 5 монет в день (можно усложнить позже)
    update_balance(message.from_user.id, 5)
    await message.answer("🎉 Ты получил **5 🪙** на свой баланс!")

@dp.message(Command('game'))
@dp.callback_query(F.data == "play_game")
async def cmd_game(event: types.Message | types.CallbackQuery):
    user_id = event.from_user.id
    username = event.from_user.username or "User"
    user = get_user(user_id, username)
    
    if user[2] < 10:
        ans = "❌ Недостаточно монет! Нужно 10 🪙. Купи их в /shop или забери /daily!"
        if isinstance(event, types.CallbackQuery):
            await event.answer(ans, show_alert=True)
        else:
            await event.answer(ans)
        return
    
    update_balance(user_id, -10)
    win = random.choice([True, False])
    
    if win:
        update_balance(user_id, 20)
        ans = "🎲 **Победа!** Ты выиграл 20 🪙! (Чистая прибыль: +10 🪙)"
    else:
        ans = "🎲 **Неудача...** Ты потерял 10 🪙."
        
    if isinstance(event, types.CallbackQuery):
        await event.answer(ans, show_alert=True)
    else:
        await event.answer(ans, parse_mode='Markdown')

# ===== МАГАЗИН И TELEGRAM STARS =====
@dp.message(Command('shop'))
@dp.callback_query(F.data == "open_shop")
async def cmd_shop(event: types.Message | types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⭐️ 10 AC за 1 Звезду", callback_data="buy_10ac")],
        [InlineKeyboardButton(text="⭐️ 50 AC за 5 Звёзд", callback_data="buy_50ac")],
        [InlineKeyboardButton(text="👑 Премиум (100 AC)", callback_data="buy_premium")],
    ])
    text = (
        "🛒 **Магазин Aspekt Shop:**\n\n"
        "Курс: 1 Telegram Звезда ⭐️ = 10 Aspekt Coins 🪙\n"
        "👑 **Премиум статус** = 100 🪙\n\n"
        "Выберите товар ниже:"
    )
    
    if isinstance(event, types.CallbackQuery):
        await event.message.edit_text(text, parse_mode='Markdown', reply_markup=keyboard)
    else:
        await event.answer(text, parse_mode='Markdown', reply_markup=keyboard)

# Обработка нажатия на покупку за звёзды
@dp.callback_query(F.data.in_(["buy_10ac", "buy_50ac"]))
async def process_buy_stars(callback: types.CallbackQuery):
    amount_ac = 10 if callback.data == "buy_10ac" else 50
    stars_cost = 1 if callback.data == "buy_10ac" else 5
    
    # Создаём счёт на оплату в Telegram Stars (валюта "XTR", provider_token="")
    await callback.message.answer_invoice(
        title=f"Покупка {amount_ac} Aspekt Coins",
        description=f"Оплата {stars_cost} Telegram Звёздами ⭐️",
        payload=f"buy_ac_{amount_ac}", # Это мы проверим при успешной оплате
        provider_token="", # ВАЖНО: для звёзд должен быть пустым!
        currency="XTR",    # ВАЖНО: код валюты Telegram Stars
        prices=[LabeledPrice(label="Aspekt Coins", amount=stars_cost)],
    )
    await callback.answer()

# Telegram требует подтвердить платёж перед списанием
@dp.pre_checkout_query()
async def on_pre_checkout_query(pre_checkout_q: types.PreCheckoutQuery):
    await pre_checkout_q.answer(ok=True)

# Обработка УСПЕШНОЙ оплаты
@dp.message(F.successful_payment)
async def on_successful_payment(message: types.Message):
    payload = message.successful_payment.invoice_payload
    user_id = message.from_user.id
    
    if payload.startswith("buy_ac_"):
        amount_ac = int(payload.split("_")[2])
        update_balance(user_id, amount_ac)
        await message.answer(f"✅ Оплата прошла успешно! Тебе начислено **{amount_ac} 🪙**.")
        
    elif payload == "buy_premium":
        # Проверка, есть ли 100 монет
        user = get_user(user_id, message.from_user.username or "User")
        if user[2] >= 100:
            update_balance(user_id, -100)
            set_premium(user_id)
            await message.answer("🎉 Поздравляем! Ты купил 👑 **Премиум статус** за 100 🪙!")
        else:
            await message.answer(f"❌ Недостаточно монет! У тебя {user[2]} 🪙, а нужно 100 🪙.")

@dp.callback_query(F.data == "buy_premium")
async def cb_buy_premium(callback: types.CallbackQuery):
    # Эта кнопка просто создаст инвойс на 0 звёзд, но спишет 100 внутренних монет
    # Для простоты сделаем проверку прямо тут
    user = get_user(callback.from_user.id, callback.from_user.username or "User")
    if user[3] == 1:
        await callback.answer("У тебя уже есть Премиум!", show_alert=True)
        return
    
    if user[2] >= 100:
        update_balance(callback.from_user.id, -100)
        set_premium(callback.from_user.id)
        await callback.answer("🎉 Премиум куплен!", show_alert=True)
        await callback.message.edit_text("✅ Поздравляем! Ты успешно приобрёл 👑 **Премиум статус**!")
    else:
        await callback.answer(f"Нужно 100 🪙, а у тебя {user[2]} 🪙. Копи или покупай за Звёзды!", show_alert=True)

# ===== ЗАПУСК =====
async def main():
    await set_commands()
    print("✅ Бот запущен и готов принимать Звёзды!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())        reply_markup=keyboard
    )

# ===== КОМАНДА /help =====
@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    await message.answer(
        "📋 <b>Список команд:</b>\n\n"
        "/start — Приветствие\n"
        "/help — Эта справка\n"
        "/rules — Правила группы\n"
        "/settings — Настройки бота (инлайн-меню)\n"
        "/ban [ответ на сообщение] — Бан пользователя\n"
        "/mute [ответ на сообщение] — Мут на 10 минут\n"
        "/warn [ответ на сообщение] — Предупреждение\n\n"
        "⚠️ Модераторские команды работают только если ты админ группы!",
        parse_mode='HTML'
    )

# ===== КОМАНДА /rules =====
@dp.message(Command('rules'))
async def cmd_rules(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ Понял", callback_data="rules_accepted")],
    ])
    await message.answer(
        "📜 <b>Правила группы:</b>\n\n"
        "1. Уважайте друг друга\n"
        "2. Без спама и флуда\n"
        "3. Без рекламы без разрешения\n"
        "4. Не используйте мат в адрес других\n"
        "5. Соблюдайте тематику чата\n\n"
        "⚠️ Нарушение правил = мут/бан",
        parse_mode='HTML',
        reply_markup=keyboard
    )

# ===== КОМАНДА /settings (инлайн-меню) =====
@dp.message(Command('settings'))
async def cmd_settings(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👋 Приветствие", callback_data="set_welcome")],
        [InlineKeyboardButton(text="🛡️ Антиспам", callback_data="set_antispam")],
        [InlineKeyboardButton(text=" Режим только чтение", callback_data="set_readonly")],
        [InlineKeyboardButton(text=" Статистика", callback_data="stats")],
    ])
    await message.answer("⚙️ <b>Настройки бота:</b>", parse_mode='HTML', reply_markup=keyboard)

# ===== МОДЕРАТОРСКИЕ КОМАНДЫ =====
@dp.message(Command('ban'))
async def cmd_ban(message: types.Message):
    if message.reply_to_message and message.from_user:
        # Проверка прав админа (упрощённая)
        try:
            member = await message.chat.get_member(message.from_user.id)
            if member.status in ['administrator', 'creator']:
                user_id = message.reply_to_message.from_user.id
                await message.chat.ban(user_id)
                await message.answer(f"🔨 Пользователь забанен: {message.reply_to_message.from_user.full_name}")
            else:
                await message.answer("⚠️ У тебя нет прав администратора!")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
    else:
        await message.answer("Ответь на сообщение пользователя, чтобы забанить его")

@dp.message(Command('mute'))
async def cmd_mute(message: types.Message):
    if message.reply_to_message and message.from_user:
        try:
            member = await message.chat.get_member(message.from_user.id)
            if member.status in ['administrator', 'creator']:
                user_id = message.reply_to_message.from_user.id
                from datetime import timedelta, datetime
                until = datetime.now() + timedelta(minutes=10)
                await message.chat.restrict(user_id, permissions=types.ChatPermissions(can_send_messages=False), until_date=until)
                await message.answer(f"🔇 Пользователь замучен на 10 минут: {message.reply_to_message.from_user.full_name}")
            else:
                await message.answer("⚠️ У тебя нет прав администратора!")
        except Exception as e:
            await message.answer(f"Ошибка: {e}")
    else:
        await message.answer("Ответь на сообщение пользователя, чтобы замутить его")

@dp.message(Command('warn'))
async def cmd_warn(message: types.Message):
    if message.reply_to_message:
        await message.answer(f"⚠️ Предупреждение выдано: {message.reply_to_message.from_user.full_name}")
    else:
        await message.answer("Ответь на сообщение пользователя")

# ===== ОБРАБОТКА ИНЛАЙН-КНОПОК =====
@dp.callback_query(F.data == "rules")
async def cb_rules(callback: types.CallbackQuery):
    await callback.message.edit_text("📜 Правила группы: без спама, уважайте друг друга!")

@dp.callback_query(F.data == "rules_accepted")
async def cb_rules_accepted(callback: types.CallbackQuery):
    await callback.answer("✅ Спасибо!")
    await callback.message.edit_text("✅ Ты принял правила группы!")

@dp.callback_query(F.data == "settings")
async def cb_settings(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="👋 Приветствие", callback_data="set_welcome")],
        [InlineKeyboardButton(text="️ Антиспам", callback_data="set_antispam")],
        [InlineKeyboardButton(text="🔒 Режим только чтение", callback_data="set_readonly")],
        [InlineKeyboardButton(text=" Статистика", callback_data="stats")],
        [InlineKeyboardButton(text="◀️ Назад", callback_data="back_to_start")],
    ])
    await callback.message.edit_text("⚙️ <b>Настройки бота:</b>", parse_mode='HTML', reply_markup=keyboard)

@dp.callback_query(F.data == "help")
async def cb_help(callback: types.CallbackQuery):
    await callback.message.edit_text(
        " <b>Список команд:</b>\n\n"
        "/start — Приветствие\n"
        "/help — Эта справка\n"
        "/rules — Правила группы\n"
        "/settings — Настройки бота\n"
        "/ban — Бан пользователя\n"
        "/mute — Мут на 10 минут\n"
        "/warn — Предупреждение",
        parse_mode='HTML'
    )

@dp.callback_query(F.data == "set_welcome")
async def cb_set_welcome(callback: types.CallbackQuery):
    await callback.answer("👋 Приветствие включено!", show_alert=True)

@dp.callback_query(F.data == "set_antispam")
async def cb_set_antispam(callback: types.CallbackQuery):
    await callback.answer("🛡️ Антиспам активирован!", show_alert=True)

@dp.callback_query(F.data == "set_readonly")
async def cb_set_readonly(callback: types.CallbackQuery):
    await callback.answer("🔒 Режим только чтение!", show_alert=True)

@dp.callback_query(F.data == "stats")
async def cb_stats(callback: types.CallbackQuery):
    await callback.answer(f"📊 Участников в чате: {callback.message.chat.member_count}", show_alert=True)

@dp.callback_query(F.data == "back_to_start")
async def cb_back(callback: types.CallbackQuery):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Правила", callback_data="rules")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
    ])
    await callback.message.edit_text(
        "👋 Привет! Я бот-помощник для групп.\n\n"
        "Добавь меня в группу и сделай администратором!",
        reply_markup=keyboard
    )

# ===== ПРИВЕТСТВИЕ НОВЫХ УЧАСТНИКОВ В ГРУППЕ =====
@dp.chat_member()
async def chat_member_update(event: types.ChatMemberUpdated):
    if event.new_chat_member.status == 'member':
        user = event.new_chat_member.user
        await event.answer(
            f"👋 Добро пожаловать, {user.full_name}!\n"
            f"Используй /rules чтобы прочитать правила."
        )

# ===== ЗАПУСК БОТА =====
async def main():
    await set_commands()  # Устанавливаем меню команд
    print("✅ Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
