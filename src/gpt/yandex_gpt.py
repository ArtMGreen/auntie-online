from .base_yandex_gpt import BaseYandexGPTBot
from .prompt_validation import Validator


class YandexGPTBot(BaseYandexGPTBot):
    def __init__(self, config):
        super().__init__(config)
        self.validator = Validator(config)

    def unsafe_ask_gpt(self, question: str, user_id: int = None):
        raise AttributeError("'YandexGPTBot' object has no attribute 'unsafe_ask_gpt'")

    def ask_gpt(self, question: str, user_id: int) -> str:
        """Задать вопрос GPT с валидацией и историей пользователя"""
        is_valid_prompt = self.validator.check_prompt(question)
        if not is_valid_prompt:
            return (
                "Ваш вопрос был удален, "
                "поскольку он может нарушать правила использования бота"
            )

        return super().unsafe_ask_gpt(question, user_id)

    def reset_user_history(self, user_id: int):
        """Сбросить историю пользователя"""
        self.clear_history(user_id)
