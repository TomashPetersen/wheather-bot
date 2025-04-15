from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application, CommandHandler, ContextTypes, MessageHandler,
    filters, ConversationHandler, CallbackQueryHandler
)
import aiohttp
import asyncio
import time

BOT_TOKEN = "8123994682:AAHLz7KbYUsr0pvfd49TCtfvRQaE-VzCpIA"
WEATHER_API_KEY = "1a3d1330bd4345b384f143116251404"

ASK_CITY = 1

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = context.user_data.get("tip_task")
    if task and not task.done():
        task.cancel()

    await update.message.reply_text(
        "Вы запустили Бот, который показывает погоду в городах России. Введите интересующий город:"
    )
    context.user_data["last_weather_time"] = time.time()

async def handle_city(update: Update, context: ContextTypes.DEFAULT_TYPE):
    city = update.message.text
    success, text = await get_weather_by_city(city)
    await update.message.reply_text(text)

    if success:
        context.user_data["last_weather_time"] = time.time()
        task = asyncio.create_task(delayed_tip(context, update.effective_chat.id))
        context.user_data["tip_task"] = task
    return ASK_CITY 

async def handle_city_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    city = query.data
    success, weather_text = await get_weather_by_city(city)
    await query.edit_message_text(text=weather_text)

    if success:
        context.user_data["last_weather_time"] = time.time()
        task = asyncio.create_task(delayed_tip(context, query.message.chat_id))
        context.user_data["tip_task"] = task

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = context.user_data.get("tip_task")
    if task and not task.done():
        task.cancel()

    await update.message.reply_text(
        "❌ Отмена. Если будет нужна актуальная погода — просто напишите /start"
    )
    return ConversationHandler.END

async def weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    task = context.user_data.get("tip_task")
    if task and not task.done():
        task.cancel()

    keyboard = [
        [InlineKeyboardButton("Москва", callback_data="Москва")],
        [InlineKeyboardButton("Санкт-Петербург", callback_data="Санкт-Петербург")],
        [InlineKeyboardButton("Новосибирск", callback_data="Новосибирск")],
        [InlineKeyboardButton("Екатеринбург", callback_data="Екатеринбург")],
        [InlineKeyboardButton("Казань", callback_data="Казань")],
        [InlineKeyboardButton("Нижний Новгород", callback_data="Нижний Новгород")],
        [InlineKeyboardButton("Челябинск", callback_data="Челябинск")],
        [InlineKeyboardButton("Самара", callback_data="Самара")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("📍 Выберите город:", reply_markup=reply_markup)

async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🛠 Что умеет бот:\n"
        "/start — запустить бота и ввести город вручную\n"
        "/weather — выбрать город из списка\n"
        "/cancel — остановить диалог\n"
        "/help — показать это сообщение"
    )

async def unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Пожалуйста, используйте команды или введите название города.\n"
        "Вот что я умею:\n"
        "/start — старт бота\n"
        "/weather — выбор города\n"
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
                if response.status == 400:
                    return False, "❗️Не удалось найти город. Проверьте название и попробуйте ещё раз."
                elif response.status != 200:
                    return False, "⚠️ Ошибка при получении данных о погоде."

                data = await response.json()
                name = data["location"]["name"]
                temp = data["current"]["temp_c"]
                wind = data["current"]["wind_kph"]
                condition = data["current"]["condition"]["text"]

                return True, (
                    f"📍 {name}\n"
                    f"🌡 Температура: {temp}°C\n"
                    f"💨 Ветер: {wind} км/ч\n"
                    f"🌤 Состояние: {condition}"
                )
    except Exception as e:
        return False, f"🚫 Ошибка: {e}"

async def delayed_tip(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    try:
        last_time = context.user_data.get("last_weather_time", 0)
        await asyncio.sleep(5)
        if context.user_data.get("last_weather_time", 0) == last_time:
            await context.bot.send_message(
                chat_id=chat_id,
                text="💡 Вы также можете ввести другой город или нажать /weather, чтобы выбрать из списка."
            )
    except asyncio.CancelledError:
        pass

def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))  # теперь глобально, всегда работает
    app.add_handler(CommandHandler("weather", weather))
    app.add_handler(CommandHandler("help", help))
    app.add_handler(CommandHandler("cancel", cancel))
    app.add_handler(CallbackQueryHandler(handle_city_button))

    # этот обработчик теперь сам переключает на ASK_CITY
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_city))

    app.run_polling()

if __name__ == "__main__":
    main()
    
    