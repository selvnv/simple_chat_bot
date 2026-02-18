import json
from pathlib import Path
from enum import Enum

class FileFormat(Enum):
    JSON = "json"
    TEXT = "txt"

# Функция для сохранения файла
def utils_save_file(path: Path, format: str, data) -> bool:
    print(path)
    if not path.exists():
        print("[WARN] Путь к файлу не существует. Попытка создать файл")
        try:
            path.touch()
        except Exception as ex:
            print("[ERROR] Ошибка при создании файла", ex)
            return False


    if format == FileFormat.JSON:
        try:
            with path.open("w", encoding="utf-8") as file:
                json.dump(data, file, indent=4, ensure_ascii=False)
        except Exception as ex:
            print("[ERROR] Ошибка при сохранении JSON файла")
            return False
    elif format == FileFormat.TEXT:
        try:
            with path.open("w", encoding="utf-8") as file:
                file.write(str(data))
        except Exception as ex:
            print("[ERROR] Ошибка при сохранении текстового файла")
            return False
    else:
        print("[ERROR] Неизвестный формат файла. Сохранение не будет выполнено")

    return True