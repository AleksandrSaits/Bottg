import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

TOKEN = os.getenv('8614039525:AAF2c9BWQqwFWxLQKCrBH-4-2YEA41w8z-A')
bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("Привет! Я работаю ✅")

@dp.message()
async def echo(message: types.Message):
    await message.answer("Я тебя слышу! Напиши /start")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
