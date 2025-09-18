import logging
import os

from dotenv import load_dotenv
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from src.gpt.base_yandex_gpt import YandexGPTConfig
from src.gpt.yandex_gpt import YandexGPTBot
from src.rag import rag

load_dotenv()

SERVICE_ACCOUNT_ID = os.environ["ACCOUNT_ID"]
KEY_ID = os.environ["KEY_ID"]
PRIVATE_KEY = os.environ["PRIVATE_KEY"]
FOLDER_ID = os.environ["FOLDER_ID"]
TELEGRAM_TOKEN = os.environ["BOT_TOKEN"]

s3_cfg = {
    "endpoint": os.environ["S3_ENDPOINT"],
    "access_key": os.environ["S3_ACCESS_KEY"],
    "secret_key": os.environ["S3_SECRET_KEY"],
    "bucket": os.environ["S3_BUCKET"],
    "prefix": os.environ.get("S3_PREFIX", ""),
}
global_vector_store = rag.prepare_index(s3_cfg)

yandex_bot = YandexGPTBot(
    YandexGPTConfig(SERVICE_ACCOUNT_ID, KEY_ID, PRIVATE_KEY, FOLDER_ID)
)
logger = logging.getLogger(__name__)


async def start(update: Update, _context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Я бот для работы с Yandex GPT.\n"
        "Просто напиши мне свой вопрос.\n\n"
        "Доступные команды:\n"
        "/start - показать это сообщение\n"
        "/reset - очистить историю диалога\n"
        "/history - показать количество сообщений в истории\n"
        "/rag XXX - искать текст XXX в документации Julia и дать ответ от ИИ на этот ХХХ"
    )


async def reset_history(update: Update):
    """Обработчик команды /reset - сброс истории диалога"""
    user_id = update.effective_user.id
    yandex_bot.reset_user_history(user_id)
    await update.message.reply_text(
        "✅ История диалога успешно очищена. Начинаем новый диалог!"
    )


async def show_history_info(update: Update):
    """Показать информацию об истории диалога"""
    user_id = update.effective_user.id
    history = yandex_bot.get_user_history(user_id)

    if not history:
        await update.message.reply_text("📭 История диалога пуста")
    else:
        user_messages = sum(1 for msg in history if msg.role == "user")
        assistant_messages = sum(1 for msg in history if msg.role == "assistant")

        await update.message.reply_text(
            f"📚 История диалога:\n"
            f"Ваших сообщений: {user_messages}\n"
            f"Ответов бота: {assistant_messages}\n"
            f"Всего сообщений: {len(history)}\n\n"
            f"Используйте /reset для очистки истории"
        )


async def rag_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка команды /rag"""
    user_message = " ".join(context.args)

    if not user_message.strip():
        await update.message.reply_text("Пожалуйста, введите вопрос после команды /rag")
        return

    try:
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )

        response = rag.rag_answer(
            global_vector_store, yandex_bot, user_message, update.effective_user.id
        )
        await update.message.reply_text(response)

    except Exception as e:
        logger.error("Error handling /rag command: %s", str(e))
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже."
        )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_message = update.message.text
    user_id = update.effective_user.id
    username = update.effective_user.username or f"user_{user_id}"

    if not user_message.strip():
        await update.message.reply_text("Пожалуйста, введите вопрос")
        return

    try:
        logger.info(
            "Processing message from %s (ID: %s): %s...",
            username,
            user_id,
            user_message[:50],
        )

        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )

        response = yandex_bot.ask_gpt(user_message, user_id)
        await update.message.reply_text(response)

    except Exception as e:
        logger.error("Error handling message from %s: %s", username, str(e))
        await update.message.reply_text(
            "Извините, произошла ошибка при обработке вашего запроса. "
            "Пожалуйста, попробуйте позже."
        )


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error("Update %s caused error %s", update, context.error)
    if update and update.effective_message:
        await update.effective_message.reply_text(
            "Произошла ошибка. Пожалуйста, попробуйте позже."
        )


def main():
    """Основная функция"""
    try:
        yandex_bot.get_iam_token()
        logger.info("IAM token test successful")

        application = Application.builder().token(TELEGRAM_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("reset", reset_history))
        application.add_handler(CommandHandler("history", show_history_info))
        application.add_handler(CommandHandler("rag", rag_command))

        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)
        )

        application.add_error_handler(error_handler)

        logger.info("Бот запускается...")
        application.run_polling()

    except Exception as e:
        logger.error("Failed to start bot: %s", str(e))


if __name__ == "__main__":
    main()
