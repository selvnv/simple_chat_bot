import os
import copy
from dotenv import load_dotenv

load_dotenv('.env')

GIGACHAT_AUTH_URL = os.environ.get("GIGACHAT_AUTH_URL")
GIGACHAT_AUTHORIZE_KEY = os.environ.get("GIGACHAT_AUTHORIZE_KEY")
GIGACHAT_REQUEST_URL = os.environ.get("GIGACHAT_REQUEST_URL")
GIGACHAT_MODEL = os.environ.get("GIGACHAT_MODEL")
MESSAGE_HISTORY_LIMIT = 10

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

_access_token = None
_access_token_expires = None

_message_history = []
_message_history_ids = []

_username = None

_context = None
_context_prompt = None

def _set_username(username: str = None):
    global _username
    _username = username

def _get_username():
    return _username

def _set_context(context: str = None):
    global _context
    _context = context

def _get_context():
    return _context

def _set_context_prompt(context_prompt: str = None):
    global _context_prompt
    _context_prompt = context_prompt

def _get_context_prompt():
    return _context_prompt

def _set_message_history(message_history: list = None):
    global _message_history
    _message_history = message_history

def _get_message_history():
    return _message_history

def _set_message_history_ids(message_history_ids: list = None):
    global _message_history_ids
    _message_history_ids = message_history_ids

def _get_message_history_ids():
    return _message_history_ids