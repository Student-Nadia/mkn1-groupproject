"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-2 Регистрация
Модуль:      query
Назначение:  выборки по FR-39 с постраничным выводом; проверка критериев на входе
Методы:
  - validate_event_filter — проверить критерии выборки событий (код, интервал времени)
  - validate_packet_filter — проверить критерии выборки пакетов (адреса, порты, интервал)
  - query_events — страница событий из SQLite
  - match_packet — подходит ли запись пакета под фильтр
  - query_packets — страница пакетов (линейный проход по журналу)
"""


def validate_event_filter(f: dict) -> None:
    """Критерии: event_code, from_ts, to_ts. Начало интервала не позже конца; иначе ValueError (M06)."""
    raise NotImplementedError("query.validate_event_filter")


def validate_packet_filter(f: dict) -> None:
    """Критерии: action, in_iface, out_iface, rule_id, smac, dmac, src_ip, dst_ip, sport, dport,
    from_ts, to_ts; форматы по common/validation.json. ValueError (M06) при ошибке."""
    raise NotImplementedError("query.validate_packet_filter")


def query_events(conn, f: dict, page: int, page_size: int) -> dict:
    """Вернуть {'items': [...], 'total': N}; пустая выборка — items=[] (клиент покажет M13)."""
    raise NotImplementedError("query.query_events")


def match_packet(rec: dict, f: dict) -> bool:
    """True, если запись удовлетворяет всем заданным критериям (критерии сочетаются по И)."""
    raise NotImplementedError("query.match_packet")


def query_packets(plog, f: dict, page: int, page_size: int) -> dict:
    """Вернуть {'items': [...], 'total': N} по журналу пакетов (файл + буфер)."""
    raise NotImplementedError("query.query_packets")
