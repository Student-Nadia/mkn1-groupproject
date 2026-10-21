"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-2 Регистрация
Модуль:      rotation
Назначение:  ограничение размера журналов: E36 (пакеты), E37 (события); очистка пакетов E34 (FR-29, FR-40)
Методы:
  - enforce_event_limit — удалить старые события при превышении предела
  - enforce_packet_limit — зафиксировать переполнение кольца пакетов
  - clear_packets — очистить журнал пакетов и зарегистрировать E34
"""


def enforce_event_limit(conn, limit_bytes: int, emit_event) -> int:
    """При превышении предела (по умолчанию 50 МБ) удалить самые старые записи и вызвать emit_event('E37')."""
    raise NotImplementedError("rotation.enforce_event_limit")


def enforce_packet_limit(plog, emit_event) -> bool:
    """Если кольцо перезаписывает старые записи — вызвать emit_event('E36'); вернуть True при переполнении."""
    raise NotImplementedError("rotation.enforce_packet_limit")


def clear_packets(plog, actor: dict, emit_event) -> None:
    """Очистить журнал пакетов (только роль rw — проверяет вызывающий) и зарегистрировать E34."""
    raise NotImplementedError("rotation.clear_packets")
