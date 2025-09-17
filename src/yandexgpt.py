import logging
import time
import requests
import jwt

from src.prompt_validation import Validator


class YandexGPTBot:
    def __init__(
        self,
        service_account_id,
        key_id,
        private_key,
        folder_id,
    ):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

        self.validator = Validator(
            service_account_id,
            key_id,
            private_key,
            folder_id
        )

        self.iam_token = None
        self.service_account_id = service_account_id
        self.key_id = key_id
        self.private_key = private_key
        self.folder_id = folder_id

        self.token_expires = 0
        self.history = []

    def get_iam_token(self):
        """Получение IAM-токена (с кэшированием на 1 час)"""
        if self.iam_token and time.time() < self.token_expires:
            return self.iam_token

        try:
            now = int(time.time())
            payload = {
                'aud': 'https://iam.api.cloud.yandex.net/iam/v1/tokens',
                'iss': self.service_account_id,
                'iat': now,
                'exp': now + 360
            }

            encoded_token = jwt.encode(
                payload,
                self.private_key,
                algorithm='PS256',
                headers={'kid': self.key_id}
            )

            response = requests.post(
                'https://iam.api.cloud.yandex.net/iam/v1/tokens',
                json={'jwt': encoded_token},
                timeout=10
            )

            if response.status_code != 200:
                raise Exception(f"Ошибка генерации токена: {response.text}")

            token_data = response.json()
            self.iam_token = token_data['iamToken']
            self.token_expires = now + 3500  # На 100 секунд меньше срока действия

            self.logger.info("IAM token generated successfully")
            return self.iam_token

        except Exception as e:
            self.logger.error(f"Error generating IAM token: {str(e)}")
            raise

    def ask_gpt(self, question):
        """Запрос к Yandex GPT API"""
        try:
            is_valid_prompt = self.validator.check_prompt(question)
            if not is_valid_prompt:
                return "Ваш вопрос был удален, поскольку он может нарушать правила использования бота"

            iam_token = self.get_iam_token()

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {iam_token}',
                'x-folder-id': self.folder_id
            }

            self.history.append(f"Пользователь: {question}")
            data = {
                "modelUri": f"gpt://{self.folder_id}/yandexgpt-lite",
                "completionOptions": {
                    "stream": False,
                    "temperature": 0.6,
                    "maxTokens": 2000
                },
                "messages": [
                    {
                        "role": "user",
                        "text": "\n".join(self.history)
                    }
                ]
            }

            response = requests.post(
                'https://llm.api.cloud.yandex.net/foundationModels/v1/completion',
                headers=headers,
                json=data,
                timeout=30
            )

            if response.status_code != 200:
                self.logger.error(f"Yandex GPT API error: {response.text}")
                raise Exception(f"Ошибка API: {response.status_code}")

            answer = response.json()['result']['alternatives'][0]['message']['text']
            self.history.append(f"Ты: {answer}")
            self.logger.info(f"dialog info:\nquestion: {question[:min(100, len(answer))]}\nanswer: {answer[:min(len(answer), 100)]}")
            return answer

        except Exception as e:
            self.logger.error(f"Error in ask_gpt: {str(e)}")
            raise
