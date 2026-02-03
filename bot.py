import os
import asyncio
import aiohttp

from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import CommandStart
from aiogram.types import Message


TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")


if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("Missing env var TELEGRAM_BOT_TOKEN")
if not OPENAI_API_KEY:
    raise RuntimeError("Missing env var OPENAI_API_KEY")


router = Router()


async def ask_openai(user_text: str) -> str:
    url = "https://api.openai.com/v1/responses"
    headers = {
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": OPENAI_MODEL,
        "input": user_text,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload, timeout=60) as resp:
            data = await resp.json()

    # Responses API возвращает текст по-разному в зависимости от формата,
    # самый частый вариант — data["output"][...]["content"][...]["text"]
    try:
        out = data["output"]
        chunks = []
        for item in out:
            if item.get("type") == "message":
                for c in item.get("content", []):
                    if c.get("type") == "output_text":
                        chunks.append(c.get("text", ""))
        text = "\n".join([t for t in chunks if t]).strip()
        return text if text else "Пустой ответ от модели."
    except Exception:
        return f"Не смог разобрать ответ OpenAI: {data}"


@router.message(CommandStart())
async def start(message: Message):
    await message.answer("Привет! Напиши сообщение — я отвечу через OpenAI.")


@router.message(F.text)
async def handle_text(message: Message):
    await message.answer("Думаю…")
    reply = await ask_openai(message.text)
    await message.answer(reply)


async def main():
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
