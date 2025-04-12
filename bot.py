import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import User, ConfirmationCode, LoginSession
from app.database import Base
import logging
from datetime import datetime

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

bot = telebot.TeleBot(token=os.getenv("BOT_TOKEN"))

DB_URL = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASS')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
engine = create_engine(DB_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_login_confirmation_keyboard(session_token: str):
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton(
            "✅ Подтвердить",
            callback_data=f"confirm_{session_token}"
        ),
        InlineKeyboardButton(
            "❌ Отклонить",
            callback_data=f"reject_{session_token}"
        )
    )
    return keyboard

def setup_handlers():
    @bot.message_handler(commands=['start'])
    def start(message):
        try:
            logger.info(f"Received start command: {message.text}")
            parts = message.text.split()
            if len(parts) > 1:
                type_parts = parts[1].split("_")

                if type_parts[0] == "reg":
                    code = type_parts[1]
                    db = SessionLocal()

                    try:
                        confirmation = db.query(ConfirmationCode).filter(
                            ConfirmationCode.code == code
                        ).first()

                        if not confirmation:
                            bot.reply_to(message, "❌ Неверный код подтверждения")
                            return
                        existing_user = db.query(User).filter(
                            User.telegram_id == str(message.from_user.id)
                        ).first()

                        if existing_user:
                            bot.reply_to(message, "⚠️ Этот Telegram аккаунт уже привязан к другой учетной записи.")
                            return

                        user = db.query(User).filter(
                            User.email == confirmation.email
                        ).first()

                        if not user:
                            bot.reply_to(message, "❌ Пользователь не найден")
                            return

                        user.telegram_id = str(message.from_user.id)
                        confirmation.code = None
                        db.commit()

                        bot.reply_to(message, f"✅ Ваш Telegram успешно привязан к аккаунту {user.email}!")

                    except Exception as e:
                        db.rollback()
                        logger.error(f"Database error: {e}")
                        bot.reply_to(message, "❌ Произошла ошибка при обработке запроса")
                    finally:
                        db.close()

        except Exception as e:
            logger.error(f"Error in start handler: {e}")
            bot.reply_to(message, "❌ Произошла ошибка при обработке команды")

    @bot.callback_query_handler(func=lambda call: call.data.startswith(('confirm_', 'reject_')))
    def handle_login_confirmation(call: CallbackQuery):
        db = None
        try:
            action, session_token = call.data.split('_', 1)
            db = SessionLocal()

            login_session = db.query(LoginSession).filter(
                LoginSession.session_token == session_token,
                LoginSession.expires_at > datetime.now()
            ).first()

            if not login_session:
                bot.answer_callback_query(call.id, "❌ Сессия устарела")
                return
            if action == "confirm":
                login_session.is_confirmed = True
                db.commit()
                bot.answer_callback_query(call.id, "✅ Вход подтвержден")
                bot.send_message(
                    call.from_user.id,
                    "Вы успешно подтвердили вход в аккаунт."
                )
            else:
                db.delete(login_session)
                db.commit()
                bot.answer_callback_query(call.id, "❌ Вход отклонен")
                bot.send_message(
                    call.from_user.id,
                    "Вы отклонили попытку входа в аккаунт."
                )

        except Exception as e:
            logger.error(f"Error handling login confirmation: {e}")
            bot.answer_callback_query(call.id, "⚠️ Ошибка обработки запроса")
        finally:
            if db:
                db.close()

def send_login_2fa_buttons(telegram_id: str, session_token: str):
    try:
        bot.send_message(
            telegram_id,
            "🔐 Попытка входа в аккаунт\n\n"
            "Подтвердите вход:",
            reply_markup=create_login_confirmation_keyboard(session_token)
        )
    except Exception as e:
        logger.error(f"Error sending login confirmation: {e}")

def run_bot():
    try:
        logger.info("Starting bot...")
        setup_handlers()
        bot.infinity_polling()
    except Exception as e:
        logger.error(f"Bot crashed: {e}")

def run_bot():
    setup_handlers()
    bot.infinity_polling()
