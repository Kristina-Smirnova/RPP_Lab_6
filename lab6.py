from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext
from aiogram.contrib.middlewares.logging import LoggingMiddleware
import math
from aiogram.types import KeyboardButton, BotCommand, ReplyKeyboardMarkup, BotCommandScopeChat, BotCommandScopeDefault

import os
import logging

import psycopg2


def get_currency_rates():
    conn = psycopg2.connect(
        host="localhost",
        database="postgres",
        user="postgres",
        password="postgres"
    )
    cursor = conn.cursor()
    cursor.execute("SELECT currency_name, rate FROM currencies")
    rows = cursor.fetchall()
    conn.close()
    return rows

# Создание курсора для выполнения SQL-запросов
# cur = conn.cursor()

# Закрытие соединения с базой данных PostgreSQL
# conn.close()


# Активация системы логирования
logging.basicConfig(level=logging.INFO)

# Получение токена из переменных окружения
bot_token = os.getenv('API_TOKEN')

# Создание бота с токеном, который выдал в BotFather при регистрации бота
bot = Bot(token=bot_token)

# Инициализация диспетчера команд
dp = Dispatcher(bot, storage=MemoryStorage())

saved_state_global = {}


class Step1(StatesGroup):
    currency_name = State()
    rate = State()


class Step2(StatesGroup):
    currency_name2 = State()
    amount = State()


# Получение чат-id пользователя, который прислал сообщение
@dp.message_handler(commands=['start'])
async def add_chat_id(message: types.Message):
    await message.reply("Добро пожаловать в бота")
    chat_id = message.chat.id


def add_chat_id(chat_id):
    conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="postgres"
        )
    cursor = conn.cursor()
    cursor.execute("""insert into admin (id, chat_id) VALUES  (:id, :chat_id) """,
                   {"id": id, "chat_id": chat_id})


@dp.message_handler(commands=['get_currencies'])
async def viewing_recorded_currencies(message: types.Message):
    currencies = get_currency_rates()
    if currencies:
        response = "Курсы валют к рублю:\n"
        for rate in currencies:
            response += f"{rate[0]}: {rate[1]} руб.\n"
    else:
        response = "Курсы валют не найдены"
    bot.send_message(message.chat.id, response)


# Команды для админов
admin_commands = [
    BotCommand(command="/start", description="START"),
    BotCommand(command="/manage_currency", description="MANAGE CURRENCY"),
    BotCommand(command="/get_currencies", description="GET CURRENCIES"),
    BotCommand(command="/convert", description="CONVERT")
]

# Команды для всех пользователей
user_commands = [
    BotCommand(command="/start", description="START"),
    BotCommand(command="/get_currencies", description="GET CURRENCIES"),
    BotCommand(command="/convert", description="CONVERT")
]

ADMIN_ID = ["5278277671"]


async def setup_bot_commands(arg):
    await bot.set_my_commands(user_commands, scope=BotCommandScopeDefault())

    for admin in ADMIN_ID:
        await bot.set_my_commands(admin_commands, scope=BotCommandScopeChat(chat_id=admin))


# Кнопки
add_currency = KeyboardButton('Добавить валюту')
delete_currency = KeyboardButton('Удалить валюту')
change_rate = KeyboardButton('Изменить курс валюты')

markup = ReplyKeyboardMarkup().row(add_currency, delete_currency, change_rate)


# Обработчик команды /add_currency
@dp.message_handler(commands=['add_currency'])
async def add_currency_command(message: types.Message):
    await Step1.currency_name.set()
    await message.reply("Введите название валюты")


# Здесь были обработчики для удаления валюты и изменения курса


# Обработка
@dp.message_handler(state=Step1.currency_name)
async def process_currency(message: types.Message, state: FSMContext):
    await state.update_data(currency_name=message.text)
    user_data = await state.get_data()
    await Step1.rate.set()
    await message.reply("Введите курс валюты к рублю")


def add_currency_in_database(currency_name):
    conn = psycopg2.connect(
            host="localhost",
            database="postgres",
            user="postgres",
            password="postgres"
        )
    cursor = conn.cursor()
    cursor.execute("""insert into currencies (id, currency_name, rate) VALUES  (:id, :currency_name, :rate) """,
                   {"id": id, "currency_name": Step1.currency_name, "rate": Step1.rate})


@dp.message_handler(state=Step1.rate)
async def process_rate(message: types.Message, state: FSMContext):
    await state.update_data(rate=message.text)
    user_data = await state.get_data()
    saved_state_global['step1'] = user_data
    await state.finish()
    await message.reply("Курс валюты сохранен")


@dp.message_handler(commands=['convert'])
async def start_command2(message: types.Message):
    await Step2.currency_name2.set()
    await message.reply("Введите название валюты")


@dp.message_handler(state=Step2.currency_name2)
async def process_currency2(message: types.Message, state: FSMContext):
    await state.update_data(currency_name2=message.text)
    user_data = await state.get_data()
    await Step2.amount.set()
    await message.reply("Введите сумму в указанной валюте")


@dp.message_handler(state=Step2.amount)
async def process_convert(message: types.Message, state: FSMContext):
    await state.update_data(amount=message.text)
    user_data = await state.get_data()
    await message.reply(math.floor(int(user_data['amount']) * int(saved_state_global['step1']['rate'])))


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    dp.middleware.setup(LoggingMiddleware())
    executor.start_polling(dp, skip_updates=True)
