import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import CommandStart
from aiogram.types import BotCommand, InlineKeyboardMarkup, InlineKeyboardButton

TOKEN = os.getenv('8614039525:AAHdwesoNheOYGVq3Kq7qIbQ9DY5UNC7PWQ')
print(f"🔑 Токен получен: {TOKEN[:10]}..." if TOKEN else "❌ ТОКЕН НЕ НАЙДЕН!")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("✅ БОТ РАБОТАЕТ! Напиши /help")

@dp.message(Command('help'))
async def cmd_help(message: types.Message):
    await message.answer("👋 Привет! Это тестовый бот.")

async def main():
    print("✅ Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
