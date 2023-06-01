import random
import requests
import logging
import sqlite3
from aiogram import Bot, Dispatcher, types, executor

API_TOKEN = '6297165368:AAHhVEqdCLKex9UOI4OXNVy08Trc5nGPEYc'  # Укажите здесь свой токен API
logging.basicConfig(level=logging.INFO)
# Создаем подключение к базе данных SQLite
conn = sqlite3.connect('polzovateli.db')
cursor = conn.cursor()

# Создаем таблицу users, если она не существует
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        easter_eggs INTEGER DEFAULT 0
    )
''')
conn.commit()

# Создаем экземпляр бота
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


def get_crypto_price(symbol):
    url = f'https://api.coingecko.com/api/v3/simple/price?ids={symbol}&vs_currencies=usd,eur,uah,rub'
    response = requests.get(url)
    data = response.json()
    return data[symbol]


def get_market_cap():
    url = 'https://api.coingecko.com/api/v3/global'
    response = requests.get(url)
    data = response.json()
    market_cap = data['data']['total_market_cap']['usd']
    return market_cap


def get_user_easter_eggs(user_id):
    cursor.execute('SELECT easter_eggs FROM users WHERE id=?', (user_id,))
    result = cursor.fetchone()
    if result is not None:
        return result[0]
    return 0


@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name

    # Добавляем пользователя в базу данных
    cursor.execute('''
        INSERT OR IGNORE INTO users (id, first_name)
        VALUES (?, ?)
    ''', (user_id, first_name))
    conn.commit()

    username = message.from_user.username
    cursor.execute('UPDATE users SET username=?, first_name=? WHERE id=?', (username, first_name, user_id))
    conn.commit()

    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    button_stats = types.KeyboardButton('📊 Крипто статистика')
    button_profile = types.KeyboardButton('👤 Профиль')
    button_easter_eggs = types.KeyboardButton('🐰 Пасхалки')
    keyboard.add(button_stats, button_profile, button_easter_eggs)

    start_text = f"🤖 Привет! Я бот для осмотра крипто рынка.\n🚀 Доступные команды:\n/id - получить ID чата\n/updinf - информация о версиях\n/donate - донат на работу хостинга"

    await message.reply(start_text, reply_markup=keyboard)


@dp.message_handler(commands=['id'])
async def get_chat_id(message: types.Message):
    await message.reply(f"Chat ID: {message.chat.id}")


@dp.message_handler(commands=['updinf'])
async def show_update_info(message: types.Message):
    update_info = f"Версия 1.0: добавлен обычный функционал на 3 криптовалюты\nВерсия 1.1.0: попытка сделать админ панель безуспешно\nВерсия 1.2.0: добавлено /info\nВерсия 1.3.0: заменено aiohttp на requests\nВерсия 1.3.1: удален aiohttp, так как ничего не изменилось\nВерсия 1.3.2: добавлено больше криптовалют и кнопка для отображения общего рыночного капитала, удалено /info\n1.3.3: добавлена команда /donate, профиль,пасхалки, улучшенный дизайн и бд пользователей\nВ планах: рассмотрение возможности создания криптокошелька с использованием базы данных"

    await message.reply(update_info)


@dp.message_handler(text='📊 Крипто статистика')
async def show_crypto_stats(message: types.Message):
    market_cap = get_market_cap()
    crypto_symbols = ['bitcoin', 'ethereum', 'litecoin', 'bitcoin-cash', 'ripple', 'stellar', 'cardano', 'eos',
                      'tezos', 'chainlink', 'polkadot', 'tron']

    stats_text = "Криптовалюты:\n"

    for symbol in crypto_symbols:
        crypto_price = get_crypto_price(symbol)
        stats_text += f"{symbol.capitalize()}: {format_price(crypto_price)}\n"

    stats_text += f"Общий рыночный капитал крипторынка: ${market_cap}"

    await message.reply(stats_text)


@dp.message_handler(commands=['donate'])
async def donate(message: types.Message):
    await message.reply(
        f"💰 Спасибо, что хотите задонатить!\n"
        f"Вы можете сделать пожертвование на следующие адреса:\n"
        f"BTC: <code>bc1qvdkm9t0fyep5t2e7cyejnhddwmzf77xu3l0j8n</code>\n"
        f"ETH: <code>0x606dfAf553f6C93Cc95CE321DBdC0923bf92623c</code>\n"
        f"TRX: <code>TEvrCSUHSignbKic3xLHxemKgCJCLNB8H5</code>\n"
        f"BCH: <code>qzlpz9es5dqxd7tpurlxfcvvjgp564p9vvcw5hsevq</code>\n"
        f"Благодарим вас за вашу поддержку! 🙏",
        parse_mode='html'
    )


@dp.message_handler(text='👤 Профиль')
async def show_profile(message: types.Message):
    user_id = message.from_user.id
    first_name = message.from_user.first_name
    username = message.from_user.username

    cursor.execute('UPDATE users SET username=?, first_name=? WHERE id=?', (username, first_name, user_id))
    conn.commit()

    easter_eggs_found = get_user_easter_eggs(user_id)

    keyboard = types.InlineKeyboardMarkup()
    button_ladybug = types.InlineKeyboardButton('🐞', callback_data='ladybug')

    if random.random() < 0.01:
        keyboard.add(button_ladybug)

    profile_text = f"Имя: {first_name}\nАйди: {user_id}\n\nНайденные пасхалки: {easter_eggs_found}"

    await message.reply(profile_text, reply_markup=keyboard)


@dp.callback_query_handler(lambda c: c.data == 'ladybug')
async def ladybug_found(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    first_name = callback_query.from_user.first_name

    easter_eggs_found = get_user_easter_eggs(user_id)

    await bot.answer_callback_query(callback_query.id, text="Вы нашли пасхалку!")
    await bot.send_message(callback_query.from_user.id, f"Поздравляем, {first_name}! Вы нашли пасхалку!")

    cursor.execute('UPDATE users SET easter_eggs=? WHERE id=?', (easter_eggs_found + 1, user_id))
    conn.commit()


@dp.message_handler(text='🐰 Пасхалки')
async def show_easter_eggs(message: types.Message):
    easter_eggs_found = get_user_easter_eggs(message.from_user.id)
    total_easter_eggs = 10  # Укажите общее количество пасхалок
    progress = easter_eggs_found / total_easter_eggs

    easter_eggs_text = f"Найденные пасхалки: {easter_eggs_found}/{total_easter_eggs} ({progress:.0%})"

    await message.reply(easter_eggs_text)


def format_price(price_data):
    price_usd = price_data['usd']
    price_eur = price_data['eur']
    price_uah = price_data['uah']
    price_rub = price_data['rub']

    return f"{price_usd}$, {price_eur}€, {price_uah}₴, {price_rub}₽"


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
