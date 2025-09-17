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

from src.base_yandex_gpt import YandexGPTConfig
from src.yandex_gpt import YandexGPTBot
from src import rag

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


async def start(update: Update):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Я бот для работы с Yandex GPT. Просто напиши мне свой вопрос"
    )


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка текстовых сообщений"""
    user_message = update.message.text

    if not user_message.strip():
        await update.message.reply_text("Пожалуйста, введите вопрос")
        return

    try:
        # Показываем статус "печатает"
        await context.bot.send_chat_action(
            chat_id=update.effective_chat.id, action="typing"
        )

        response = rag.rag_answer(global_vector_store, yandex_bot, user_message)
        await update.message.reply_text(response)

    except Exception as e:
        logger.error("Error handling message: %s", str(e))
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
        # Проверяем возможность генерации токена при запуске
        yandex_bot.get_iam_token()
        logger.info("IAM token test successful")

        application = Application.builder().token(TELEGRAM_TOKEN).build()

        application.add_handler(CommandHandler("start", start))
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
