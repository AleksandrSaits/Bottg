from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart

# ВСТАВЛЯЮ ТОКЕН НАПРЯМУЮ!
TOKEN = "8614039525:AAF2c9BWQqwFWxLQKCrBH-4-2YEA41w8z-A"  # ← ВСТАВЬ СЮДА СВОЙ ПОЛНЫЙ ТОКЕН!

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer("✅ ПРИВЕТ! Я РАБОТАЮ! Наконец-то!")

@dp.message()
async def echo(message: types.Message):
    await message.answer("Напиши /start")

async def main():
    print("🚀 Бот запущен!")
    await dp.start_polling(bot)

if __name__ == '__main__':
    import asyncio
    asyncio.run(main())
