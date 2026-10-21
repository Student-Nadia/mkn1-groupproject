"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-2 Регистрация
Модуль:      event_log
Назначение:  журнал событий в SQLite (схема events, FR-24, FR-25, FR-27, FR-28)
Методы:
  - init_db — открыть/создать базу и таблицу events с индексами
  - write_event — добавить запись в журнал событий
  - count_events — число записей (для rotation)
  - delete_oldest — удалить n самых старых записей (E37)
"""
import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_us      INTEGER NOT NULL,
    event_code TEXT    NOT NULL,
    result     INTEGER NOT NULL,
    actor_type INTEGER NOT NULL,
    actor_id   TEXT,
    actor_ip   TEXT,
    command    TEXT,
    details    TEXT,
    error_code TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_ts    ON events(ts_us);
CREATE INDEX IF NOT EXISTS idx_events_code  ON events(event_code);
CREATE INDEX IF NOT EXISTS idx_events_actor ON events(actor_id);
"""


def init_db(path: str) -> sqlite3.Connection:
    """Открыть базу журнала событий, создать схему при первом запуске."""
    raise NotImplementedError("event_log.init_db")


def write_event(conn: sqlite3.Connection, event: dict) -> int:
    """Записать событие (поля как в таблице events, payload log.write.event).
    Проверить event_code (E01..E52) и result; вернуть id записи."""
    raise NotImplementedError("event_log.write_event")


def count_events(conn: sqlite3.Connection) -> int:
    """Вернуть число записей в журнале событий."""
    raise NotImplementedError("event_log.count_events")


def delete_oldest(conn: sqlite3.Connection, n: int) -> int:
    """Удалить n самых старых записей; вернуть число удалённых."""
    raise NotImplementedError("event_log.delete_oldest")
