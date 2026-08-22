import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

TOKEN = os.getenv('8614039525:AAF2c9BWQqwFWxLQKCrBH-4-2YEA41w8z-A')
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def cmd_start(message: types.Message):
    await message.answer("✅ БОТ РАБОТАЕТ! Я запущен на Bothost.")

async def main():
    print("✅ Бот запущен...")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
