from pathlib import Path
import json
from modules.bot.config import _set_context, _set_context_prompt, _get_context_prompt
from modules.bot.llm import _make_system_request
# from utils.file_operations import utils_save_file, FileFormat


# Функция для генерации контекста на основе предыдущих сообщений
def _generate_context(message_history: list = None):

    context_prompt = _get_context_prompt()

    if context_prompt is None:
        print("[ERROR] Промпт для генерации контекста не задан")
        return False

    response_message = _make_system_request(context_prompt, message_context=message_history)

    if response_message is not None:
        _set_context(response_message.get("message"))
    else:
        return False

    return True


# Функция для сохранения контекста в отдельный файл
# def _save_context():
#     path = Path(f"data/context/{_username}")

#     if _context is not None:
#         utils_save_file(path=path, format=FileFormat.TEXT, data=_context)
#     else:
#         print("[WARN] Контекст пуст, сохранение не будет произведено")


# Функция для загрузки промпта для генерации контекста из файла
def _load_context_prompt(context_path="conf/app/context_prompt"):

    path = Path(context_path)

    if path.exists():
        with path.open("r", encoding="utf-8") as file:
            data = file.read()

            if data:
                _set_context_prompt(data)
                return True
            else:
                print("[ERROR] Файл промпта для генерации контекста пуст. Промпт генерации контекста не задан")
                return False
    else:
        print(f"[ERROR] Указанный путь к файлу контекста не существует ({path})")
        return False