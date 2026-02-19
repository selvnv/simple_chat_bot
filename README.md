# simple_chat_bot

### Установка сертификата Минцифры [для корректной работы запросов к API GigaChat](https://developers.sber.ru/docs/ru/gigachat/certificates)
```bash
curl -k "https://gu-st.ru/content/lending/russian_trusted_root_ca_pem.crt" -w "\n" >> "$(python -m certifi)"
```

### Установка переменных окружения

Некоторые данные, необходимые для работы программы, она получает из переменных окружения
Эти переменные можно задать в файле `.env`, который должен находиться в корне проекта
После чего выполнить скрипт `init.sh`, который возьмет данные из `.env` и установит переменные окружения

```bash
# Содержимое файла .env
GIGACHAT_SCOPE=GIGACHAT_API_PERS
GIGACHAT_AUTHORIZE_KEY=<YOUR_AUTHORIZATION_KEY>
GIGACHAT_AUTH_URL=https://ngw.devices.sberbank.ru:9443/api/v2/oauth
GIGACHAT_REQUEST_URL=https://gigachat.devices.sberbank.ru/api/v1/chat/completions
GIGACHAT_MODEL=GigaChat-2
```

Запуск скрипта для установки переменных окружения
```bash
source ./init.sh
```

### Запуск приложения

```bash
# Синхронизация окружения
uv sync

# Проверка окружения
uv pip list

# Создание файла окружения
# После создания необходимо заполнить
touch .env

# Установка переменных окружения
# Создание каталогов для хранения истории сообщений пользователя
source ./init.sh

# Запуск программы
uv run ./main.py
```

### TODO

- [x] Вывод истории сообщений в консоль
- [x] Сохранение истории сообщений при превышении лимита сообщений (например, 10)
- [x] Генерация контекста каждые N сообщений (например, 2)
- [x] Интерактивный режим для работы с пользователем
  - [x] Ввод имени пользователя
  - [x] Запрос и вывод ответа в CLI
- [x] Вывод истории сообщений в консоль
- [x] Классовая реализация бота (хранение и изменение состояния)

### Описание GigaChat

- [Получение токена доступа для авторизации запросов к API](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/post-token)
- [Запрос на генерацию ответа](https://developers.sber.ru/docs/ru/gigachat/api/reference/rest/post-chat)
- [Описание модели GigaChat 2 Lite](https://developers.sber.ru/docs/ru/gigachat/models/gigachat-2-lite)

