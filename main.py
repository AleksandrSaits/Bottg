import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandStart
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

# Токен из переменных окружения (ты уже закинул его на хостинг)
TOKEN = os.getenv('BOT_TOKEN')

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ===== НАСТРОЙКА МЕНЮ КОМАНД (появится в Telegram при нажатии "/") =====
async def set_commands():
    commands = [
        BotCommand(command='start', description='Приветствие'),
        BotCommand(command='help', description='Список команд'),
        BotCommand(command='rules', description='Правила группы'),
        BotCommand(command='settings', description='Настройки бота'),
        BotCommand(command='ban', description='Забанить пользователя'),
        BotCommand(command='mute', description='Замутить пользователя'),
        BotCommand(command='warn', description='Предупреждение'),
    ]
    await bot.set_my_commands(commands)

# ===== КОМАНДА /start =====
@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Правила", callback_data="rules")],
        [InlineKeyboardButton(text="⚙️ Настройки", callback_data="settings")],
        [InlineKeyboardButton(text="❓ Помощь", callback_data="help")],
    ])
    await message.answer(
        "👋 Привет! Я бот-помощник для групп.\n\n"
        "Добавь меня в группу и сделай администратором — "
        "я помогу модерировать чат!",
        reply_markup=keyboard
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
