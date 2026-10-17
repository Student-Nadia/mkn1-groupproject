"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  общее
Модуль:      codes
Назначение:  загрузка кодов событий (E..) и сообщений (M..) из JSON
Методы:
  - event_text — описание события по коду
  - message_text — текст сообщения по коду
"""
import json
import os

_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load(name):
    with open(os.path.join(_DIR, name), encoding="utf-8") as f:
        return json.load(f)


EVENTS = _load("events.json")
MESSAGES = _load("messages.json")


def event_text(code):
    return EVENTS[code]


def message_text(code, **kw):
    return MESSAGES[code].format(**kw) if kw else MESSAGES[code]
