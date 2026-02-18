from modules.bot.config import _set_username, _get_username
from modules.bot.config_manager import _load_user_config, _save_user_config
from modules.bot.context import _load_context_prompt
from modules.bot.llm import bot_make_request
from modules.bot.message_history import _save_message_history
from modules.bot.display import show_last_message

chat_patterns = ["chat", "start", "begin", "старт", "начать"]
exit_patterns = ["quit", "q", "exit", "выход"]
submit_phrases = ["y", "yes", "true", "ok", "да"]

def _init_chat():
    _load_user_config()

    _load_context_prompt()


def _save_chat_state():
    # Сохранение конфигурации перед выходом (имя пользователя, контекст)
    _save_user_config()

    # Сохранение истории сообщений
    _save_message_history()


def start_chat():

    _init_chat()

    # Ввод имени пользователя, если конфиг пустой
    if _get_username() is None:
        input_username = ""

        while True:
            input_username = str(input("Введите ваше имя пользователя: ")).strip()

            if input_username == "":
                continue

            submit_username = str(input(f"Начать чат с именем {input_username} (y, n)? ")).strip()

            if submit_username.lower() in submit_phrases:
                break

        _set_username(input_username)


    while True:
        command = str(input("Введите команду (chat, q): ")).strip()

        if command in exit_patterns:
            _save_chat_state()
            print("Хорошего дня)")
            break

        if command in chat_patterns:
            while True:
                message = str(input("Введите запрос или команду выхода: ")).strip()

                if message == "":
                    continue

                if message in exit_patterns:
                    break

                # Выполнить запрос пользователя к LLM
                is_request_ok =  bot_make_request(message)
                if not is_request_ok:
                    print("[ERROR] Произошла ошибка при выполнении запроса")
                    continue

                # При успешном запросе, последнее сообщение в истории чата (ответ LLM) выводится в консоль
                show_last_message()




