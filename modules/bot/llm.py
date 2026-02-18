import uuid
import copy
import json

from requests import post
from requests.exceptions import JSONDecodeError

from datetime import datetime

from modules.bot.config import GIGACHAT_AUTH_URL, GIGACHAT_AUTHORIZE_KEY, GIGACHAT_REQUEST_URL, REFRESH_ACCESS_TOKEN_BEFORE_S, GIGACHAT_MODEL, MESSAGE_HISTORY_LIMIT
from modules.bot.config import _access_token, _access_token_expires
from modules.bot.config import _get_message_history, _get_message_history_ids, _get_context, _set_message_history, _set_message_history_ids, _set_context
from modules.bot.message_history import _save_message_history

def _refresh_access_token():
    """Refresh access_token for llm and set access_token_expires time

    Returns:
        Boolean:
            True if refresh is success
            False if token is not refreshed
    """

    global _access_token
    global _access_token_expires

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

        _access_token = response_json.get("access_token")
        _access_token_expires = response_json.get("expires_at")

        if _access_token is None or _access_token_expires is None:
            print("Ошибка при выполнении запроса на обновление токена доступа",
                  "\nВ полученных данных отсутствуют 'access_token' или 'expires_at'",
                  f"\nОтвет сервиса: {response_json}")
            return False
    except JSONDecodeError as ex:
        print(f"Ошибка при парсинге ответа от сервиса при выполнении запроса на обновление токена доступа\n{ex}")
        return False
    except Exception as ex:
        print(f"Ошибка при выполнении запроса на обновление токена доступа\n{ex}")
        return False

    return True


def _refresh_access_token_if_expire(func):
    def wrapper(*args, **kwargs):
        # Если токен не задан - создать
        if _access_token is None or _access_token_expires is None:
            _refresh_access_token()
        else:
            # Проверка действительности токена
            # Преобразование в секунды для корректной работы с datetime
            token_expire_time_s = _access_token_expires / 1000.0
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
                _refresh_access_token()

        return func(*args, **kwargs)

    return wrapper

@_refresh_access_token_if_expire
def _make_system_request(request_message: str, message_context: list = None) -> dict:
    """Make request to llm without user message history editing

    Args:
        request_message (str): request to llm
        _message_history (list, optional): previous messages to|from llm. Defaults to None. If need to use the messages for context

    Returns:
        dict: llm answer in format: {
            "role": "assistant",
            "message": assistant_message
        }

        None if something went wrong
    """
    if message_context is not None:
        request_messages = copy.deepcopy(message_context)
    else:
        request_messages = []

    # Т.к. системное сообщение может быть направлено только первым, запросы программы (не пользователя) также передаются под ролью user
    request_messages.append({
        "role": "user",
        "content": request_message
    })

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {_access_token}"
    }

    body = json.dumps({
        "model": GIGACHAT_MODEL,
        "messages": request_messages
    })

    try:
        response = post(
            url=GIGACHAT_REQUEST_URL,
            headers=headers,
            data=body
        )

        response_json = response.json()

        assistant_message = ((response_json.get("choices")[0]).get("message")).get("content")

        if assistant_message is None:
            print(f"[ERROR] В полученных данных отсутствует сообщение модели")
            return None

        # Вернуть ответ модели
        return {
            "role": "assistant",
            "message": assistant_message
        }
    except JSONDecodeError as ex:
        print(f"[ERROR] Ошибка при парсинге ответа от сервиса при выполнении запроса на обновление токена доступа\n{ex}")
        return None
    except Exception as ex:
        print("[ERROR] Ошибка при выполнении запроса к LLM", ex)
        return None

@_refresh_access_token_if_expire
def bot_make_request(request_message: str):
    from modules.bot.context import _generate_context

    message_history = _get_message_history()
    message_history_ids = _get_message_history_ids()

    # Действия при превышении объема истории сообщений заданного лимита
    if len(message_history) >= MESSAGE_HISTORY_LIMIT:
        # Сохранить сообщения по достижении лимита
        _save_message_history()
        # Сгенерировать контекст - он будет подставляться вместо истории сообщений при отправке к сервису LLM
        _generate_context(message_history)

        # Очистить предыдущую историю в памяти программы
        message_history.clear()
        message_history_ids.clear()

    message_history.append({
        "role": "user",
        "content": request_message
    })

    # Идентификаторы сообщений хранятся в отдельной структуре
    # согласовываются по индексу
    # _message_history[0] -> _message_history_ids[0]
    message_history_ids.append(str(uuid.uuid4()))

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Authorization": f"Bearer {_access_token}"
    }

    request_messages = []

    if _get_context() is None:
        request_messages = message_history
    else:
        request_messages = [{
            "role": "user",
            "content": f"Используй этот контекст истории общения для более точных ответов: {_get_context}"
        }]

        request_messages.extend(message_history)

    body = json.dumps({
        "model": GIGACHAT_MODEL,
        "messages": request_messages
    })

    try:
        response = post(
            url=GIGACHAT_REQUEST_URL,
            headers=headers,
            data=body
        )

        response_json = response.json()

        assistant_message = response_json.get("choices")[0].get("message").get("content")


        if assistant_message is None:
            print(f"[ERROR] В полученных данных отсутствует сообщение модели")
            return False

        # Добавить ответ модели в историю сообщений
        message_history.append({
            "role": "assistant",
            "content": assistant_message
        })

        # Сохранение идентификатора сообщения
        message_history_ids.append(str(uuid.uuid4()))
    except JSONDecodeError as ex:
        print(f"[ERROR] Ошибка при парсинге ответа от сервиса при выполнении запроса на обновление токена доступа\n{ex}")
        return False
    except Exception as ex:
        print("[ERROR] Ошибка при выполнении запроса к LLM", ex)
        return False

    return True