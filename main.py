import os
import asyncio
import threading
from flask import Flask
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, MessageHandler, CallbackQueryHandler,
    ContextTypes, filters
)
import aiohttp

# Загрузка переменных окружения
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

# Константа для диалога
ASK_CITY = 1

# Flask для UptimeRobot
app_flask = Flask(__name__)

@app_flask.route('/')
def index():
    return "Бот работает!"

# Обработчики Telegram
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "\U0001F4CD Введите город, чтобы узнать погоду"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start — запустить бота\n"
        "/weather — выбрать город из списка\n"
        "/help — помощь"
    )

async def get_weather_by_city(city_name: str) -> tuple[bool, str]:
    url = "http://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHER_API_KEY,
        "q": city_name,
        "lang": "ru"
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                if response.status != 200:
                    return False, "Ошибка получения погоды."
                data = await response.json()
                location = data["location"]["name"]
                temp = data["current"]["temp_c"]
                condition = data["current"]["condition"]["text"]
                return True, f"\U0001F4CD {location}\n\u2600 Температура: {temp} C\n{condition}"
    except Exception as e:
        return False, f"Ошибка: {e}"

async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    success, message = await get_weather_by_city(city)
    await update.message.reply_text(message)

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Москва", callback_data="Москва")],
        [InlineKeyboardButton("Санкт-Петербург", callback_data="Санкт-Петербург")],
        [InlineKeyboardButton("Новосибирск", callback_data="Новосибирск")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("\U0001F3E0 Выберите город:", reply_markup=reply_markup)

async def handle_city_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    city = query.data
    success, message = await get_weather_by_city(city)
    await query.edit_message_text(message)

# Запуск Telegram-бота
async def run_telegram():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))
    app.add_handler(CallbackQueryHandler(handle_city_button))

    await app.run_polling()

# Поток для Telegram-бота
def start_bot():
    asyncio.run(run_telegram())

if __name__ == '__main__':
    threading.Thread(target=start_bot).start()
    app_flask.run(host='0.0.0.0', port=10000)
