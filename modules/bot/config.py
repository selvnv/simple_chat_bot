import os
import uuid
import json
from pathlib import Path
from dotenv import load_dotenv
from requests import post
from requests.exceptions import JSONDecodeError
from datetime import datetime
from enum import Enum

# Обертка над os.environ.get для очистки переменной от возможных спецсимволов
def get_env_var(name: str = None):
    if name is None:
        return None

    var = os.environ.get(name)

    if var is None:
        return None

    return var.strip()

GIGACHAT_AUTH_URL = get_env_var("GIGACHAT_AUTH_URL")
GIGACHAT_AUTHORIZE_KEY = get_env_var("GIGACHAT_AUTHORIZE_KEY")
GIGACHAT_REQUEST_URL = get_env_var("GIGACHAT_REQUEST_URL")
GIGACHAT_MODEL = get_env_var("GIGACHAT_MODEL")

if not GIGACHAT_REQUEST_URL:
    raise ValueError("GIGACHAT_REQUEST_URL не установлена в окружении")

if not GIGACHAT_MODEL:
    raise ValueError("GIGACHAT_MODEL не установлена в окружении")

if not GIGACHAT_AUTH_URL:
    raise ValueError("GIGACHAT_AUTH_URL не установлен в окружении")

if not GIGACHAT_AUTHORIZE_KEY:
    raise ValueError("GIGACHAT_AUTHORIZE_KEY не установлен в окружении")

# Обновлять токен доступа, если до окончания действия осталось 60 секунд
REFRESH_ACCESS_TOKEN_BEFORE_S = 60

DISPLAY_MESSAGE_HISTORY_COUNT = 6

MESSAGE_HISTORY_DIR = "data/history/"

USER_SETTINGS_PATH = "conf/user_settings.json"

MESSAGE_HISTORY_LIMIT = 3


class Role(Enum):
    USER = "user"
    ASSISTANT = "assistant"

    @classmethod
    def values(cls):
        return [role.value for role in cls]

    @classmethod
    def has_value(cls, value):
        return value in cls.values()


class Context:
    def __init__(self):
        self._context = None
        self._context_prompt = None


    @property
    def context(self):
        return self._context


    @context.setter
    def context(self, context_value: str = None):
        if context_value is None:
            raise TypeError("context_value is None")

        if not isinstance(context_value, str):
            raise TypeError("context_value is not a string")

        self._context = context_value


    @property
    def context_prompt(self):
        return self._context_prompt


    @context_prompt.setter
    def context_prompt(self, context_prompt_value: str = None):
        if context_prompt_value is None:
            raise TypeError("context_prompt_value is None")

        if not isinstance(context_prompt_value, str):
            raise TypeError("context_prompt_value is not string")

        self._context_prompt = context_prompt_value


    def set_context_prompt_from_file(self, path: str = "conf/app/context_prompt"):
        filepath = Path(path)

        if filepath.exists():
            with filepath.open("r", encoding="utf-8") as file:
                data = file.read()

                if data:
                    self._context_prompt = data
                    return True
                else:
                    print("\033[1m\033[91m[ERROR] set_context_prompt_from_file >>>>\033[0m Файл промпта для генерации контекста пуст. Промпт генерации контекста не задан")
                    return False
        else:
            print(f"\033[1m\033[91m[ERROR] set_context_prompt_from_file >>>>\033[0m Указанный путь к файлу контекста не существует ({filepath})")
            return False


    def __str__(self):
        return self._context if self._context is not None else ""


def _refresh_access_token_if_expire(func):
        def wrapper(self, *args, **kwargs):
            # Если токен не задан - создать
            if self._access_token is None or self._access_token_expires is None:
                self._refresh_access_token()
            else:
                # Проверка действительности токена
                # Преобразование в секунды для корректной работы с datetime
                token_expire_time_s = self._access_token_expires / 1000.0
                token_expire_datetime = datetime.fromtimestamp(token_expire_time_s)
                # Остаток времени до истечения токена в секундах
                time_left_s = (token_expire_datetime - datetime.now()).total_seconds()

                # Если действие токена скоро закончится или уже закончилось - обновить
                if time_left_s < REFRESH_ACCESS_TOKEN_BEFORE_S:
                    print(
                        "Refreshing access token",
                        f"Expire datetime is: {token_expire_datetime}",
                        f"Seconds left: {time_left_s}"
                    )
                    self._refresh_access_token()

            return func(self, *args, **kwargs)

        return wrapper


class Chat:
    _access_token = None
    _access_token_expires = None

    def __init__(self):
        self._message_history = []
        self._message_history_ids = []

        self._username = None
        self._context = Context()

        self._message_count = 0


    @property
    def username(self):
        return self._username


    @username.setter
    def username(self, username: str = None):
        if username is None:
            raise TypeError("username is None")

        if not isinstance(username, str):
            raise TypeError("username is not string")

        self._username = username


    @property
    def context(self):
        return self._context


    @property
    def message_count(self):
        return self._message_count


    @property
    def message_history(self):
        return self._message_history.copy()


    @property
    def message_history_ids(self):
        return self._message_history_ids.copy()


    def add_message(self, role: Role = None, message: str = None):
        if message is None:
            raise TypeError("message is None")

        if not isinstance(message, str):
            raise TypeError("message is not str")

        if role is None:
            raise TypeError("role is None")

        if not isinstance(role, Role):
            raise TypeError("role is not Role instance")

        self._message_history.append(
            {
                "role": role.value,
                "content": message
            }
        )

        # Идентификаторы сообщений хранятся в отдельной структуре
        # согласовываются по индексу
        # _message_history[0] -> _message_history_ids[0]
        self._message_history_ids.append(str(uuid.uuid4()))

        # Ведение счетчика количества сообщений в истории чата
        self._message_count += 1


    def last_message(self) -> dict | None:
        """Get last message from the message history

        Returns:
            dict: {
                'role': 'rolename',
                'content': 'some content'
            }

            Return None if message history is empty

        """
        if self._message_count > 0:
            return self._message_history[-1]
        return None


    def clear_messages(self):
        if self._message_history is not None:
            self._message_history.clear()

        if self._message_history_ids is not None:
            self._message_history_ids.clear()

        self._message_count = 0


    def _refresh_access_token(self):
        """Refresh access_token for llm and set access_token_expires time

        Returns:
            Boolean:
                True if refresh is success
                False if token is not refreshed
        """

        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
            "RqUID": f"{uuid.uuid4()}",
            "Authorization": f"Basic {GIGACHAT_AUTHORIZE_KEY}"
        }

        payload = {
            "scope": "GIGACHAT_API_PERS"
        }

        try:
            response = post(
                url=GIGACHAT_AUTH_URL,
                headers=headers,
                data=payload
            )

            response_json = response.json()

            self._access_token = response_json.get("access_token")
            self._access_token_expires = response_json.get("expires_at")

            if self._access_token is None or self._access_token_expires is None:
                print("\033[1m\033[91m[ERROR] _refresh_access_token >>>>\033[0m Ошибка при выполнении запроса на обновление токена доступа",
                    "\nВ полученных данных отсутствуют 'access_token' или 'expires_at'",
                    f"\nОтвет сервиса: {response_json}")
                return False
        except JSONDecodeError as ex:
            print(f"\033[1m\033[91m[ERROR] _refresh_access_token >>>>\033[0m Ошибка при парсинге ответа от сервиса при выполнении запроса на обновление токена доступа\n{ex}")
            return False
        except Exception as ex:
            print(f"\033[1m\033[91m[ERROR] _refresh_access_token >>>>\033[0m Ошибка при выполнении запроса на обновление токена доступа\n{ex}")
            return False

        return True


    @_refresh_access_token_if_expire
    def make_request(self, messages: list = None) -> dict:
        """Make request to llm

        Args:
            messages (list): messages for request to llm (last message is request message, previous - history)

        Returns:
            dict: llm answer in format: {
                "role": "assistant",
                "content": assistant_message
            }

            None if something went wrong
        """

        if messages is None:
            print("\033[1m\033[91m[ERROR] make_request >>>>\033[0m Не заданы сообщения для отправки LLM")
            return None

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self._access_token}"
        }

        body = json.dumps({
            "model": GIGACHAT_MODEL,
            "messages": messages
        })

        try:
            response = post(
                url=GIGACHAT_REQUEST_URL,
                headers=headers,
                data=body
            )

            response.raise_for_status()

            response_json = response.json()

            # Разбор структуры из ответа
            choices = response_json.get("choices", [])
            if not choices:
                print("\033[1m\033[91m[ERROR] make_request >>>>\033[0m Нет choices в ответе")
                return None

            message = choices[0].get("message", {})
            assistant_message = message.get("content")
            if assistant_message is None:
                print("\033[1m\033[91m[ERROR] make_request >>>>\033[0m Нет content в ответе")
                return None

            # Вернуть ответ модели
            return {
                "role": "assistant",
                "content": assistant_message
            }
        except JSONDecodeError as ex:
            print(f"\033[1m\033[91m[ERROR] make_request >>>>\033[0m Ошибка при парсинге ответа от сервиса при выполнении запроса на обновление токена доступа\n{ex}")
            return None
        except Exception as ex:
            print("\033[1m\033[91m[ERROR] make_request >>>>\033[0m Ошибка при выполнении запроса к LLM", ex)
            return None
