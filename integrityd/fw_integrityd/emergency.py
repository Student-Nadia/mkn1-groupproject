"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-6 Целостность
Модуль:      emergency
Назначение:  режим аварийной поддержки: блокировка трафика, E40, M08; выход из режима, E41 (FR-48, FR-49)
Методы:
  - is_active — включён ли режим аварийной поддержки
  - enter — войти в режим: traffic.block и state.clear в ПС-1, emergency.enter в ПС-3/ПС-4, E40
  - leave — выйти из режима: traffic.unblock в ПС-1, emergency.exit в ПС-3/ПС-4, E41
  - log_event — отправить событие log.write.event в ПС-2
"""

EVENT_QUEUE_MAX = 1000  # очередь событий при недоступной ПС-2
EVENT_RETRY_SEC = 5

_active = False


def is_active() -> bool:
    """Вернуть True, если МЭ в режиме аварийной поддержки."""
    raise NotImplementedError("emergency.is_active")


def enter(violations: list) -> None:
    """Заблокировать трафик, очистить таблицу состояний, перевести ПС-3 и ПС-4 в режим аварийной поддержки, E40 (FR-48)."""
    raise NotImplementedError("emergency.enter")


def leave() -> None:
    """После успешной повторной проверки снять блокировку, вернуть штатный режим, E41."""
    raise NotImplementedError("emergency.leave")


def log_event(code: str, result: bool, details: dict = None, command: str = None,
              actor_id: str = "integrityd", actor_ip: str = None, error_code: str = None) -> None:
    """Отправить log.write.event в ПС-2 (поля таблицы events).
    Если ПС-2 недоступна — хранить в очереди (до EVENT_QUEUE_MAX), повторять каждые EVENT_RETRY_SEC."""
    raise NotImplementedError("emergency.log_event")
