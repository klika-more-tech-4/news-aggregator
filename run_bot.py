from aiogram import executor

from bot.bot import dp

if __name__ == "__main__":
    executor.start_polling(dp)
