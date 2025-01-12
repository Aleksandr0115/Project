import logging
import asyncio
import json
import random
from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import CommandStart
from aiogram import F

# Токен бота
API_TOKEN = '7833196735:AAEMkQ8h-Z-pL5MuYxtMhJCk16CBOdDO9Nc'

# Логирование
logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Файл для сохранения данных
DATA_FILE = "users_data.json"


# Загрузка данных пользователей из файла
def load_users():
    try:
        with open(DATA_FILE, "r") as file:
            return json.load(file)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logging.error(f"Ошибка загрузки данных пользователей: {e}")
        return {}


# Сохранение данных пользователей в файл
def save_users():
    try:
        with open(DATA_FILE, "w") as file:
            json.dump(users, file, indent=4)
    except Exception as e:
        logging.error(f"Ошибка сохранения данных пользователей: {e}")


# Инициализация словаря пользователей
users = load_users()

# Главное меню
main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Баланс'), KeyboardButton(text='Магазин')],
        [KeyboardButton(text='Рейтинг'), KeyboardButton(text='Помощь')],
        [KeyboardButton(text='Заработок')]
    ],
    resize_keyboard=True
)

# Меню магазина
shop_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Помидоры - 100'), KeyboardButton(text='Огурцы - 100')],
        [KeyboardButton(text='Торт - 200'), KeyboardButton(text='Добавить свой товар')],
        [KeyboardButton(text='Купить существующий товар'), KeyboardButton(text='Вернуться')]
    ],
    resize_keyboard=True
)

# Меню добавленных товаров
def generate_added_items_menu(user_id):
    if "added_items" not in users[user_id] or not users[user_id]["added_items"]:
        return ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text='Вернуться в магазин')]],
            resize_keyboard=True
        )
    buttons = [[KeyboardButton(text=f"{item} - {price}")] for item, price in users[user_id]["added_items"].items()]
    buttons.append([KeyboardButton(text='Вернуться в магазин')])
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# Меню заработка
earn_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text='Тык'), KeyboardButton(text='Вернуться в главное меню')]
    ],
    resize_keyboard=True
)


# Состояния для добавления товара
class AddItem(StatesGroup):
    waiting_for_item_name = State()


# /start
@dp.message(CommandStart())
async def start_command(message: types.Message):
    user_id = str(message.from_user.id)
    first_name = message.from_user.first_name or "Игрок"

    # Добавление пользователя в словарь, если его нет
    if user_id not in users:
        users[user_id] = {
            "name": first_name,
            "balance": 1000,
            "added_items": {}
        }
        save_users()

    await message.answer(f"Добро пожаловать в экономическую игру, {first_name}!", reply_markup=main_menu)


# Баланс
@dp.message(F.text == 'Баланс')
async def check_balance(message: types.Message):
    user_id = str(message.from_user.id)
    balance = users[user_id]["balance"]
    await message.answer(f"Ваш баланс: {balance} виртуальных монет.")


# Рейтинг
@dp.message(F.text == 'Рейтинг')
async def check_rating(message: types.Message):
    sorted_users = sorted(users.items(), key=lambda x: x[1]["balance"], reverse=True)
    rating = "\n".join(
        [f"{i + 1}. {user[1]['name']} - {user[1]['balance']} монет" for i, user in enumerate(sorted_users)]
    )
    await message.answer(f"Рейтинг игроков:\n{rating}")


# Помощь
@dp.message(F.text == 'Помощь')
async def help_menu(message: types.Message):
    await message.answer(
        "Команды бота:\n"
        "- Баланс: проверить баланс\n"
        "- Магазин: купить товары\n"
        "- Рейтинг: увидеть лучших игроков\n"
        "- Помощь: информация о командах\n"
        "- Заработок: заработать монеты"
    )


# Магазин
@dp.message(F.text == 'Магазин')
async def shop(message: types.Message):
    await message.answer("Добро пожаловать в магазин! Выберите действие:", reply_markup=shop_menu)


@dp.message(F.text == 'Добавить свой товар')
async def add_item_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название товара, который хотите добавить.")
    await state.set_state(AddItem.waiting_for_item_name)


@dp.message(AddItem.waiting_for_item_name)
async def save_custom_item(message: types.Message, state: FSMContext):
    user_id = str(message.from_user.id)
    item_name = message.text
    item_price = random.randint(1, 200)  # Случайная цена от 1 до 200
    logging.info(f"Добавление товара: {item_name} с ценой {item_price}")

    # Добавляем товар в список добавленных товаров пользователя
    if "added_items" not in users[user_id]:
        users[user_id]["added_items"] = {}

    users[user_id]["added_items"][item_name] = item_price
    save_users()

    await message.answer(
        f"Товар '{item_name}' добавлен с ценой {item_price} монет. Вы можете купить его в разделе 'Купить существующий товар'.",
        reply_markup=shop_menu
    )
    await state.clear()


@dp.message(F.text == 'Купить существующий товар')
async def show_added_items(message: types.Message):
    user_id = str(message.from_user.id)
    added_items_menu = generate_added_items_menu(user_id)
    await message.answer("Ваши добавленные товары:", reply_markup=added_items_menu)


@dp.message(F.text == 'Вернуться в магазин')
async def back_to_shop(message: types.Message):
    await message.answer("Вы вернулись в магазин.", reply_markup=shop_menu)


@dp.message(F.text == 'Вернуться')
async def back_to_main(message: types.Message):
    await message.answer("Вы вернулись в главное меню.", reply_markup=main_menu)


# Заработок
@dp.message(F.text == 'Заработок')
async def earn_menu_command(message: types.Message):
    await message.answer("Вы перешли в меню заработка. Выберите действие:", reply_markup=earn_menu)


@dp.message(F.text == 'Тык')
async def clicker(message: types.Message):
    user_id = str(message.from_user.id)
    users[user_id]["balance"] += 1
    save_users()
    balance = users[user_id]["balance"]
    await message.answer(f"Вы заработали 1 монету! Ваш текущий баланс: {balance} монет.")


@dp.message(F.text == 'Вернуться в главное меню')
async def back_to_main_menu(message: types.Message):
    await message.answer("Вы вернулись в главное меню.", reply_markup=main_menu)


# Обработчики для покупки товаров
@dp.message(F.text == 'Помидоры - 100')
async def buy_tomatoes(message: types.Message):
    user_id = str(message.from_user.id)
    balance = users[user_id]["balance"]
    item_price = 100  # Цена помидоров

    if balance >= item_price:
        users[user_id]["balance"] -= item_price
        save_users()
        await message.answer(f"Вы купили Помидоры за 100 монет. Ваш новый баланс: {users[user_id]['balance']} монет.", reply_markup=shop_menu)
    else:
        await message.answer(f"У вас недостаточно монет для покупки Помидоров.", reply_markup=shop_menu)


@dp.message(F.text == 'Огурцы - 100')
async def buy_cucumbers(message: types.Message):
    user_id = str(message.from_user.id)
    balance = users[user_id]["balance"]
    item_price = 100  # Цена огурцов

    if balance >= item_price:
        users[user_id]["balance"] -= item_price
        save_users()
        await message.answer(f"Вы купили Огурцы за 100 монет. Ваш новый баланс: {users[user_id]['balance']} монет.", reply_markup=shop_menu)
    else:
        await message.answer(f"У вас недостаточно монет для покупки Огурцов.", reply_markup=shop_menu)


@dp.message(F.text == 'Торт - 200')
async def buy_cake(message: types.Message):
    user_id = str(message.from_user.id)
    balance = users[user_id]["balance"]
    item_price = 200  # Цена торта

    if balance >= item_price:
        users[user_id]["balance"] -= item_price
        save_users()
        await message.answer(f"Вы купили Торт за 200 монет. Ваш новый баланс: {users[user_id]['balance']} монет.", reply_markup=shop_menu)
    else:
        await message.answer(f"У вас недостаточно монет для покупки Торта.", reply_markup=shop_menu)


async def main():
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
