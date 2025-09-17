import logging
import time
from dataclasses import dataclass

import jwt
import requests

from src.exceptions import YandexGptException


@dataclass
class YandexGPTConfig:
    """Configuration for Yandex GPT authentication"""
    service_account_id: str
    key_id: str
    private_key: str
    folder_id: str


class BaseYandexGPTBot:
    def __init__(self, config: YandexGPTConfig):
        logging.basicConfig(
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            level=logging.INFO
        )
        self.logger = logging.getLogger(__name__)

        self.iam_token = None
        self.config = config

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
                'iss': self.config.service_account_id,
                'iat': now,
                'exp': now + 360
            }

            encoded_token = jwt.encode(
                payload,
                self.config.private_key,
                algorithm='PS256',
                headers={'kid': self.config.key_id}
            )

            response = requests.post(
                'https://iam.api.cloud.yandex.net/iam/v1/tokens',
                json={'jwt': encoded_token},
                timeout=10
            )

            if response.status_code != 200:
                raise YandexGptException(f"Ошибка генерации токена: {response.text}")

            token_data = response.json()
            self.iam_token = token_data['iamToken']
            self.token_expires = now + 3500  # На 100 секунд меньше срока действия

            self.logger.info("IAM token generated successfully")
            return self.iam_token

        except Exception as e:
            self.logger.error("Error generating IAM token: %s", str(e))
            raise

    def unsafe_ask_gpt(self, question):
        """Запрос к Yandex GPT API"""
        try:
            iam_token = self.get_iam_token()

            headers = {
                'Content-Type': 'application/json',
                'Authorization': f'Bearer {iam_token}',
                'x-folder-id': self.config.folder_id
            }

            self.history.append(f"Пользователь: {question}")
            data = {
                "modelUri": f"gpt://{self.config.folder_id}/yandexgpt-lite",
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
                self.logger.error("Yandex GPT API error: %s", response.text)
                raise YandexGptException(f"Ошибка API: {response.status_code}")

            answer = response.json()['result']['alternatives'][0]['message']['text']
            self.history.append(f"Ты: {answer}")
            self.logger.info("dialog info:\nquestion: %s\nanswer: %s",
                             question[:min(100, len(answer))],
                             answer[:min(len(answer), 100)])
            return answer

        except Exception as e:
            self.logger.error("Error in ask_gpt: %s", str(e))
            raise
