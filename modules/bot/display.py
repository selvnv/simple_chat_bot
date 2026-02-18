import copy
import json

from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme

from pathlib import Path

from modules.bot.config import DISPLAY_MESSAGE_HISTORY_COUNT
from modules.bot.config import _username, _message_history, _message_history_ids

def _print_markdown_message(message: str = ""):
    if len(message) == 0:
        print("[WARN] Нет данных для отображения")

    console = Console(theme=Theme({
        "markdown.h1": "bold bright_magenta",
        "markdown.h2": "bold bright_cyan",
        "markdown.h3": "bold bright_green",
        "markdown.h4": "bold bright_yellow",
        "markdown.h5": "bold bright_blue",
        "markdown.h6": "bold bright_red",
        "markdown.strong": "bold bright_white",
        "markdown.emphasis": "italic bright_cyan",
        "markdown.strike": "strike bright_black",
        "markdown.code": "bright_green on grey11",
        "markdown.code_block": "bright_yellow on grey0",
        "markdown.link": "underline bright_blue",
        "markdown.link_url": "italic bright_cyan",
        "markdown.block_quote": "dim bright_magenta",
    }))

    markdown_text = Markdown(message)

    console.print(markdown_text)


def _print_message_history(message_history: list = None, show_last: int = 10):
    """Show 'show_last' messages of message history

    Args:
        message_history (list, optional): list of messages with content. Defaults to None.
        show_last (int, optional): sets how many messages to display. Defaults to 10.
    """
    if message_history is None or len(message_history) == 0:
        print("[WARN] История сообщений пуста")

    for message_item in message_history[-show_last:]:
        if message_item.get("role") == "user":
            print(f"\033[1m\033[34m======{_username if _username is not None else "Пользователь"}======\033[0m")

        if message_item.get("role") == "assistant":
            print("\033[1m\033[92m======Model======\033[0m")

        if "content" in message_item:
            _print_markdown_message(message_item.get("content"))

def show_last_message():
    if len(_message_history) == 0:
        print("\nНет сообщений для отображения")
    else:
        print("\n\033[1m\033[96m============================================================\033[0m\n")
        _print_markdown_message(_message_history[-1]["content"])
        print("\n\033[1m\033[96m============================================================\033[0m\n")

def show_message_history():
    # Создание дубликата истории сообщений, т.к. возможна мутация
    messages_to_display = copy.deepcopy(_message_history)
    messages_to_display_count = len(messages_to_display)

    # Если в памяти мало сообщений для отображения
    if messages_to_display_count < DISPLAY_MESSAGE_HISTORY_COUNT:
        path_to_message_history_file = Path(f"data/history/{_username}.json")

        is_history_file_exists = path_to_message_history_file.exists()
        # История пуста, файл с историей отсутствует
        if messages_to_display_count == 0:
            if not is_history_file_exists:
                print("[WARN] История сообщений пуста")
                return

        if is_history_file_exists:
            # Догрузить сообщения из файла с сохранениями
            with path_to_message_history_file.open("r", encoding="utf-8") as file:
                message_history_object = json.load(file)

                if "message_history_ids" not in message_history_object:
                    print("[ERROR] В файле с сохраненной историей сообщений некорректная структура. Отсутствует поле 'message_history_ids'")
                    return

                if "message_history" not in message_history_object:
                    print("[ERROR] В файле с сохраненной историей сообщений некорректная структура. Отсутствует поле 'message_history'")
                    return

                file_message_histody_len = len(message_history_object["message_history"])
                # Обход списка истории сообщений в обратном порядке
                for shift, message_id in enumerate(reversed(message_history_object["message_history_ids"])):
                    print(shift, message_id)
                    # Если message_id сообщения уже есть в памяти, загрузка такого сообщения не требуется
                    if message_id in _message_history_ids:
                        continue

                    # Вставка сообщений в начало истории сообщений в памяти (сообщения в файле старее, чем сообщения в памяти)
                    messages_to_display.insert(0, message_history_object["message_history"][file_message_histody_len - 1 - shift])

                    # При доборе сообщений до нужного количества, завершить обход
                    if len(messages_to_display) >= DISPLAY_MESSAGE_HISTORY_COUNT:
                        break
        elif messages_to_display_count == 0:
            print("[WARN] История сообщений пуста")

    _print_message_history(messages_to_display, DISPLAY_MESSAGE_HISTORY_COUNT)