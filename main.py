import asyncio
import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.filters import CommandStart
from aiogram.types import Message
from aiogram import F
from config import TOKEN, HOLIDAYS_API_KEY

# Инициализация бота
bot = Bot(token=TOKEN)

# Создание Dispatcher
dp = Dispatcher()

user_data = {}

async def get_holidays(country: str, year: str, month: str, day: str):
    url = "https://holidays.abstractapi.com/v1/"
    params = {
        "api_key": HOLIDAYS_API_KEY,
        "country": country,
        "year": year,
        "month": month,
        "day": day
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as response:
                response.raise_for_status()  # Проверка на HTTP ошибки
                return await response.json()
    except aiohttp.ClientError as e:
        print(f"Ошибка при получении данных о праздниках: {e}")
        return []

# Регистрация обработчиков
@dp.message(CommandStart())
async def start(message: Message):
    user_data[message.from_user.id] = {"state": "country"}
    await message.answer(
        'Привет! Чтобы узнать про праздники, введите двухбуквенный код страны (например, US для США).'
    )

@dp.message(F.text.func(lambda text: len(text) == 2 and text.isalpha()))
async def get_country_code(message: Message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]["state"] == "country":
        country_code = message.text.upper()
        user_data[user_id] = {"country": country_code, "state": "year"}
        await message.answer("Введите год, за который хотите узнать праздники (например, 2023):")

@dp.message(F.text.func(lambda text: text.isdigit() and len(text) == 4))
async def get_year(message: Message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]["state"] == "year":
        user_data[user_id]["year"] = message.text
        user_data[user_id]["state"] = "month"
        await message.answer("Введите месяц в формате числа (например, 1 для Января):")

@dp.message(F.text.func(lambda text: text.isdigit() and 1 <= int(text) <= 12))
async def get_month(message: Message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]["state"] == "month":
        user_data[user_id]["month"] = message.text
        user_data[user_id]["state"] = "day"
        await message.answer("Введите день (число от 1 до 31):")

@dp.message(F.text.func(lambda text: text.isdigit() and 1 <= int(text) <= 31))
async def get_day(message: Message):
    user_id = message.from_user.id
    if user_id in user_data and user_data[user_id]["state"] == "day":
        user_data[user_id]["day"] = message.text
        data = user_data[user_id]
        holidays = await get_holidays(data["country"], data["year"], data["month"], data["day"])
        if holidays:
            response_text = "Вот праздники, которые я нашел:\n\n"
            for holiday in holidays:
                response_text += f"{holiday['date']}: {holiday['name']} ({holiday['type']})\n"
        else:
            response_text = "Я не смог найти праздники для этой даты. Попробуйте другой запрос."
        await message.answer(response_text)
        del user_data[user_id]

# Обработчик для любых других сообщений
@dp.message()
async def handle_other_messages(message: Message):
    user_id = message.from_user.id
    if user_id in user_data:
        state = user_data[user_id]["state"]
        if state == "country":
            await message.answer("Пожалуйста, введите двухбуквенный код страны (например, US для США).")
        elif state == "year":
            await message.answer("Пожалуйста, введите год в формате YYYY (например, 2023).")
        elif state == "month":
            await message.answer("Пожалуйста, введите месяц в формате числа от 1 до 12.")
        elif state == "day":
            await message.answer("Пожалуйста, введите день в формате числа от 1 до 31.")
    else:
        await message.answer("Пожалуйста, начните с команды /start")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
    asyncio.run(main())