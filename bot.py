import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, Column, Integer, String, Text, BigInteger
from sqlalchemy.orm import declarative_base, sessionmaker
import app.models
from app.database import Base
load_dotenv()
bot = telebot.TeleBot(token=os.getenv("BOT_TOKEN"))

login_2fa_tg = InlineKeyboardMarkup(row_width=1)
login_2fa_tg.add(InlineKeyboardButton(
                    text="Подтвердить вход",
                    callback_data='allow'
                    ),
                    InlineKeyboardButton(
                    text="Это был не я",
                    callback_data="forbid"
                    )
)

def setup_handlers():
    @bot.message_handler(commands=['start'])
    def start(message):
        print(message.text)
        parts = message.text.split()
        if len(parts)>1:
            type = parts[1].split("_")
            if type[0] == "reg":
                code = type[1]
                db = SessionLocal()

                user = db.query(User).filter(User.telegram_id == str(message.from_user.id)).first()
                if user.email:
                    bot.reply_to(message, "⚠️ Этот Telegram аккаунт уже привязан к другой учетной записи.")
                    return

                user.telegram_id = message.from_user.id
                user.auth_tg_code = None
                db.commit()
                bot.reply_to(message, f"✅ Ваш Telegram успешно привязан к аккаунту {user.email}!")

    @bot.callback_query_handler(func=lambda call:True)
    def callback_query(call: CallbackQuery):
        req = call.data.split('_')
        if req[0] == "allow":
            print("Да")
        elif req[0] == "forbid":
            print("Нет")
        bot.answer_callback_query(call.id)
def send_login_2fa_buttons(user_id):
    bot.send_message(user_id, "Для доступа к личному кабинету подтвердите вход кнопкой ниже", reply_markup = login_2fa_tg)


def run_bot():
    setup_handlers()
    bot.infinity_polling()
