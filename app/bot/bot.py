import asyncio

from aiogram import Bot, Dispatcher

from app.bot.handlers import router
from app.core.config import settings


async def main():
    bot = Bot(
        token=settings.telegram_bot_token,
    )

    dp = Dispatcher()
    dp.include_router(router)

    print("Bot started")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
