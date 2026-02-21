import os
import asyncio
import aiohttp
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from aiohttp import web

from config import BOT_TOKEN
import storage
from texts import texts

bot = Bot(BOT_TOKEN)
dp = Dispatcher(bot)

def get_chat_id(msg):
    return msg.chat.id

def main_keyboard():
    kb = InlineKeyboardMarkup(row_width=2)
    kb.add(
        InlineKeyboardButton("📋 ToDo", callback_data="todo"),
        InlineKeyboardButton("🤖 AI", callback_data="ai"),
        InlineKeyboardButton("🇷🇺 RU", callback_data="lang_ru"),
        InlineKeyboardButton("🇬🇧 EN", callback_data="lang_en"),
    )
    return kb

@dp.message_handler(commands=["start"])
async def start(msg: types.Message):
    chat_id = get_chat_id(msg)
    lang = storage.get_lang(chat_id)
    await msg.reply(
        texts[lang]["start"] + "\n\n✅ Бот работает в группе",
        reply_markup=main_keyboard()
    )

@dp.callback_query_handler(lambda c: c.data.startswith("lang_"))
async def change_lang(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    lang = c.data.split("_")[1]
    storage.set_lang(chat_id, lang)
    await c.answer(texts[lang]["lang"])
    await c.message.edit_text(
        texts[lang]["start"],
        reply_markup=main_keyboard()
    )

@dp.callback_query_handler(text="todo")
async def todo(c: types.CallbackQuery):
    chat_id = c.message.chat.id
    lang = storage.get_lang(chat_id)
    tasks = storage.get_tasks(chat_id)
    if not tasks:
        await c.message.reply(texts[lang]["todo_empty"])
    else:
        text = "📋 ToDo (группа):\n"
        for i, t in enumerate(tasks):
            text += f"{i+1}. {t}\n"
        await c.message.reply(text)
    await c.answer()

@dp.message_handler(commands=["add"])
async def add_task(msg: types.Message):
    chat_id = get_chat_id(msg)
    text = msg.get_args()
    if not text:
        return await msg.reply("❗ /add текст задачи")
    storage.add_task(chat_id, text)
    await msg.reply("✅ Задача добавлена в общий список")

@dp.callback_query_handler(text="ai")
async def ai_start(c: types.CallbackQuery):
    lang = storage.get_lang(c.from_user.id)
    await c.message.answer(texts[lang]["ai"])
    await c.answer()

@dp.message_handler()
async def ai_chat(msg: types.Message):
    if msg.chat.type in ["group", "supergroup"]:
        if not msg.text or not msg.text.startswith(f"@{(await bot.me).username}"):
            return
        text = msg.text.replace(f"@{(await bot.me).username}", "").strip()
    else:
        text = msg.text

    if not text:
        return

    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://api.affiliateplus.xyz/api/chatbot",
            params={
                "message": text,
                "botname": "GroupBot",
                "ownername": "Chat"
            }
        ) as r:
            data = await r.json()
            await msg.reply(data.get("message", "🤖 ..."))

async def web_server():
    app = web.Application()
    app.router.add_get("/", lambda r: web.Response(text="Bot running"))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(
        runner,
        "0.0.0.0",
        int(os.environ.get("PORT", 10000))
    )
    await site.start()

async def main():
    await web_server()
    executor.start_polling(dp, skip_updates=True)

if __name__ == "__main__":
    asyncio.run(main())
