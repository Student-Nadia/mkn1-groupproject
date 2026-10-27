"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-2 Регистрация
Модуль:      query
Назначение:  выборки по FR-39, постраничный вывод, валидация фильтров
Методы:
  - events: поиск и выборка событий безопасности с проверкой фильтров
  - packets: поиск и выборка сетевых пакетов с проверкой сетевых форматов
"""

import json
import logging
import re
from datetime import datetime
from typing import Dict, Any, Tuple, List

# Инициализация логгера подсистемы ПС-2 Регистрация (fw-logd)
logger = logging.getLogger("fw_logd.query")

# Пути к общим ресурсам проекта
MESSAGES_PATH = "common/messages.json"
VALIDATION_PATH = "common/validation.json"


def _load_error(error_code: str) -> Dict[str, Any]:
    """Безопасная загрузка сообщения об ошибке из common/messages.json."""
    try:
        with open(MESSAGES_PATH, "r", encoding="utf-8") as f:
            messages = json.load(f)
            message_text = messages.get(error_code, "Неизвестная ошибка системы")
    except Exception as e:
        logger.error(f"Не удалось прочитать {MESSAGES_PATH}: {str(e)}")
        message_text = "Ошибка конфигурации системы сообщений"
    return {"status": "error", "code": error_code, "message": message_text}


def _load_regex_patterns() -> Dict[str, str]:
    """Загрузка регулярных выражений для IP и MAC адресов из common/validation.json."""
    try:
        with open(VALIDATION_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Извлекаем паттерны (или используем надежные дефолты, если файл пуст)
            return {
                "ip": data.get("ip_pattern", r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$"),
                "mac": data.get("mac_pattern", r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$")
            }
    except Exception as e:
        logger.warning(f"Не удалось загрузить паттерны из {VALIDATION_PATH}, применены встроенные: {str(e)}")
        return {
            "ip": r"^(?:[0-9]{1,3}\.){3}[0-9]{1,3}$",
            "mac": r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
        }


def _validate_filters(filters: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Валидация бизнес-логики фильтров:
    1. Проверка временных периодов (начало не позже конца).
    2. Проверка форматов IP, MAC и портов на базе конфигурации.
    """
    if not isinstance(filters, dict):
        return False, "ERR_INVALID_FILTERS_FORMAT"

    # 1. Проверка временного периода
    time_start = filters.get("time_start")
    time_end = filters.get("time_end")
    
    if time_start and time_end:
        try:
            # Формат ISO 8601 (например: 2026-10-27T10:00:00Z)
            start_dt = datetime.fromisoformat(time_start.replace("Z", "+00:00"))
            end_dt = datetime.fromisoformat(time_end.replace("Z", "+00:00"))
            if start_dt > end_dt:
                return False, "ERR_TIME_PERIOD_INVALID"  # Начало периода позже конца
        except ValueError:
            return False, "ERR_INVALID_DATE_FORMAT"

    # 2. Проверка сетевых параметров (IP, MAC, Порты)
    patterns = _load_regex_patterns()
    
    # Проверка IP-адресов (отправитель / получатель / админ)
    for ip_field in ["ip_src", "ip_dst", "admin_ip"]:
        ip_val = filters.get(ip_field)
        if ip_val and not re.match(patterns["ip"], str(ip_val)):
            return False, "ERR_INVALID_IP_FORMAT"

    # Проверка MAC-адресов
    for mac_field in ["mac_src", "mac_dst"]:
        mac_val = filters.get(mac_field)
        if mac_val and not re.match(patterns["mac"], str(mac_val)):
            return False, "ERR_INVALID_MAC_FORMAT"

    # Проверка портов (должны быть в диапазоне 1 - 65535)
    for port_field in ["port_src", "port_dst"]:
        port_val = filters.get(port_field)
        if port_val is not None:
            try:
                port_num = int(port_val)
                if not (1 <= port_num <= 65535):
                    return False, "ERR_INVALID_PORT_RANGE"
            except (ValueError, TypeError):
                return False, "ERR_INVALID_PORT_FORMAT"

    return True, ""


def _validate_pagination(request_data: Dict[str, Any]) -> Tuple[bool, int, int]:
    """Проверка корректности параметров постраничного вывода (FR-39)."""
    page = request_data.get("page", 1)
    page_size = request_data.get("page_size", 20)
    try:
        page_num = int(page)
        size_num = int(page_size)
        if page_num < 1 or size_num < 1 or size_num > 100:
            return False, 0, 0
        return True, page_num, size_num
    except (ValueError, TypeError):
        return False, 0, 0


def events(request_data: Any) -> Dict[str, Any]:
    """Выборка событий из логов с применением фильтрации и пагинации."""
    try:
        if not isinstance(request_data, dict):
            return _load_error("ERR_INVALID_REQUEST")

        # Проверка пагинации
        is_pag_valid, page, page_size = _validate_pagination(request_data)
        if not is_pag_valid:
            return _load_error("ERR_INVALID_PAGINATION")

        # Валидация фильтров
        filters = request_data.get("filters", {})
        is_filt_valid, error_code = _validate_filters(filters)
        if not is_filt_valid:
            return _load_error(error_code)

        # Здесь происходит чтение файла / БД логов (эмуляция успешного поиска под фильтр)
        mock_items = [
            {
                "datetime": "2026-10-27T10:00:00Z",
                "event_code": filters.get("event_code", "EVT_ADMIN_LOGIN"),
                "description": "Успешная обработка запроса поиска событий",
                "initiator_id": "admin_main",
                "admin_ip": filters.get("admin_ip", "192.168.1.100")
            }
        ]

        return {
            "status": "success",
            "result": {
                "items": mock_items,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_items": len(mock_items),
                    "total_pages": 1
                }
            }
        }
    except Exception as exc:
        logger.critical(f"Исключение в log.query.events: {str(exc)}", exc_info=True)
        return _load_error("ERR_INTERNAL_SERVER_ERROR")


def packets(request_data: Any) -> Dict[str, Any]:
    """Выборка сетевых пакетов из логов с применением фильтрации и пагинации."""
    try:
        if not isinstance(request_data, dict):
            return _load_error("ERR_INVALID_REQUEST")

        is_pag_valid, page, page_size = _validate_pagination(request_data)
        if not is_pag_valid:
            return _load_error("ERR_INVALID_PAGINATION")

        filters = request_data.get("filters", {})
        is_filt_valid, error_code = _validate_filters(filters)
        if not is_filt_valid:
            return _load_error(error_code)

        mock_items = [
            {
                "datetime": "2026-10-27T10:14:02Z",
                "action": "DROP",
                "rule_number": 12,
                "interface_in": "eth0",
                "interface_out": "eth1",
                "protocol": filters.get("protocol", "TCP"),
                "mac_src": filters.get("mac_src", "00:0C:29:AB:CD:EF"),
                "mac_dst": filters.get("mac_dst", "00:0C:29:12:34:56"),
                "ip_src": filters.get("ip_src", "192.168.1.50"),
                "ip_dst": filters.get("ip_dst", "10.0.0.1"),
                "port_src": filters.get("port_src", 49152),
                "port_dst": filters.get("port_dst", 80),
                "icmp_type": None,
                "icmp_code": None
            }
        ]

        return {
            "status": "success",
            "result": {
                "items": mock_items,
                "pagination": {
                    "current_page": page,
                    "page_size": page_size,
                    "total_items": len(mock_items),
                    "total_pages": 1
                }
            }
        }
    except Exception as exc:
        logger.critical(f"Исключение в log.query.packets: {str(exc)}", exc_info=True)
        return _load_error("ERR_INTERNAL_SERVER_ERROR")
