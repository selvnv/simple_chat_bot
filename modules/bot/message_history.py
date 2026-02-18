import json
from pathlib import Path
from utils.file_operations import FileFormat, utils_save_file
from modules.bot.config import _get_username, _get_message_history, _get_message_history_ids

# Функция для сохранения истории сообщений
def _save_message_history() -> bool:
    username = _get_username()
    message_history = _get_message_history()
    message_history_ids = _get_message_history_ids()

    try:
        if message_history is None:
            print("[ERROR] Не задана история сообщений для сохранения")
            return False
        elif message_history_ids is None:
            print("[ERROR] Не задан список идентификаторов для сопоставления истории сообщений с сохранением")
            return False
        elif len(message_history) == 0:
            print("[WARN] История сообщений пуста. Сохранение не будет выполнено")
            return False
        elif username is None:
            print("[ERROR] Пользователь для сохранения истории сообщений не известен")
            return False
    except Exception as ex:
        print("[ERROR] Ошибка при сохранении истории сообщений", ex)

    message_history_object = {}

    path = Path(f"data/history/{username}.json")

    if (path.exists()):
        # Если уже есть сохраненные сообщения, нужно вычитать их в память и выполнить дозапись
        with path.open("r", encoding="utf-8") as file:
            message_history_object = json.load(file)

            if "message_history_ids" not in message_history_object:
                print("[ERROR] В файле с сохраненной историей сообщений некорректная структура. Отсутствует поле 'message_history_ids'")
                return False

            if "message_history" not in message_history_object:
                print("[ERROR] В файле с сохраненной историей сообщений некорректная структура. Отсутствует поле 'message_history'")
                return False

            for index, id in enumerate(message_history_ids):

                # Пропустить добавление элементов, которые уже есть в файле
                if id in message_history_object.get("message_history_ids"):
                    continue

                # Добавить элементы истории сообщений на запись
                message_history_object["message_history_ids"].append(id)
                message_history_object["message_history"].append(message_history[index])
    else:
        # Если файла с данными нет, все элементы истории сообщений пойдут в запись
        message_history_object["message_history_ids"] = message_history_ids
        message_history_object["message_history"] = message_history

    utils_save_file(path, FileFormat.JSON, message_history_object)

    return True