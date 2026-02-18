import json
from requests.exceptions import JSONDecodeError
from pathlib import Path

from modules.bot.config import _set_username, _set_context, _get_username, _get_context
from utils.file_operations import utils_save_file, FileFormat

def _load_user_config(config_path="conf/user_settings.json"):
    path = Path(config_path)

    if (path.exists()):
        try:
            with open(path, "r", encoding="utf-8") as settings_file:
                settings = json.load(settings_file)

                username = settings.get("username")

                if username is None:
                    print(f"[ERROR] Не удается найти имя пользователя в файле конфигурации {config_path} (username)")
                    return False

                _set_username(username)

                context = settings.get("context")
                if context is None:
                    print(f"[WARN] Не удается найти контекст в файле конфигурации {config_path} (context)")

                _set_context(context)

                return True
        except JSONDecodeError as ex:
            print("[ERROR] Ошибка при парсинге файла конфигурации в JSON", ex)
        except Exception as ex:
            print("[ERROR] Непредвиденная ошибка при чтении файла конфигурации", ex)
    else:
        print(f"[ERROR] Не удается найти файл конфигурации пользователя по пути {path}")
        return False


def _save_user_config(config_path="conf/user_settings.json"):
    path = Path(config_path)

    try:
        config_object = {
            "username": _get_username(),
            "context": _get_context()
        }

        utils_save_file(path, FileFormat.JSON, config_object)
    except Exception as ex:
        print("[ERROR] Ошибка при сохранении файла пользовательской конфигурации", ex)