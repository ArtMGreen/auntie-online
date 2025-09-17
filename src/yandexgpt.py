from src.prompt_validation import Validator
from src.baseyandexgpt import BaseYandexGPTBot


class YandexGPTBot(BaseYandexGPTBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.validator = Validator(
            self.service_account_id,
            self.key_id,
            self.private_key,
            self.folder_id
        )

    def ask_gpt(self, question) -> str:
        is_valid_prompt = self.validator.check_prompt(question)
        if not is_valid_prompt:
            return ("Ваш вопрос был удален, "
                    "поскольку он может нарушать правила использования бота")

        return super().unsafe_ask_gpt(question)
