import logging
import os

from dotenv import load_dotenv
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from bot.bot import BotHandlers
from gpt.base_yandex_gpt import YandexGPTConfig
from gpt.yandex_gpt import YandexGPTBot
from rag import rag

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()

SERVICE_ACCOUNT_ID = os.environ["ACCOUNT_ID"]
KEY_ID = os.environ["KEY_ID"]
PRIVATE_KEY = os.environ["PRIVATE_KEY"].replace("\\n", "\n")
FOLDER_ID = os.environ["FOLDER_ID"]
TELEGRAM_TOKEN = os.environ["BOT_TOKEN"]

s3_cfg = {
    "endpoint": os.environ["S3_ENDPOINT"],
    "access_key": os.environ["S3_ACCESS_KEY"],
    "secret_key": os.environ["S3_SECRET_KEY"],
    "bucket": os.environ["S3_BUCKET"],
    "prefix": os.environ.get("S3_PREFIX", ""),
}


def main():
    """Основная функция"""
    try:
        logger.info("Инициализация компонентов...")

        global_vector_store = rag.prepare_index(s3_cfg)

        yandex_bot = YandexGPTBot(
            YandexGPTConfig(SERVICE_ACCOUNT_ID, KEY_ID, PRIVATE_KEY, FOLDER_ID)
        )

        yandex_bot.get_iam_token()
        logger.info("IAM token test successful")

        handlers = BotHandlers(yandex_bot, global_vector_store)

        application = Application.builder().token(TELEGRAM_TOKEN).build()

        application.add_handler(CommandHandler("start", handlers.start))
        application.add_handler(CommandHandler("reset", handlers.reset_history))
        application.add_handler(CommandHandler("history", handlers.show_history_info))
        application.add_handler(CommandHandler("rag", handlers.rag_command))

        application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, handlers.handle_message)
        )

        application.add_error_handler(BotHandlers.error_handler)

        logger.info("Бот запускается...")
        application.run_polling()

    except KeyError as e:
        logger.error("Отсутствует необходимая переменная окружения: %s", str(e))
    except Exception as e:
        logger.error("Failed to start bot: %s", str(e))


if __name__ == "__main__":
    main()
