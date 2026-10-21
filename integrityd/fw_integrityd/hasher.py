"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-6 Целостность
Модуль:      hasher
Назначение:  SHA-256 контролируемых файлов, файл эталонов под HMAC-SHA-256 (FR-46, FR-47)
Методы:
  - sha256_file — хэш SHA-256 файла
  - load_key — прочитать ключ HMAC
  - load_baseline — прочитать файл эталонов и проверить HMAC
  - save_baseline — записать файл эталонов с новым HMAC
"""


class BaselineError(Exception):
    """HMAC файла эталонов не совпал — нарушение целостности (FR-47)."""


def sha256_file(path: str) -> str:
    """Вернуть хэш SHA-256 файла (FR-46)."""
    raise NotImplementedError("hasher.sha256_file")


def load_key(path: str) -> bytes:
    """Прочитать ключ HMAC (/etc/fw/hmac.key, fw-integrity, 0400)."""
    raise NotImplementedError("hasher.load_key")


def load_baseline(path: str, key: bytes) -> dict:
    """Прочитать файл эталонов (путь файла и хэш SHA-256), проверить HMAC-SHA-256; вернуть {путь: хэш}.
    BaselineError — HMAC не совпал (FR-47)."""
    raise NotImplementedError("hasher.load_baseline")


def save_baseline(path: str, files: dict, key: bytes) -> None:
    """Записать файл эталонов {путь: хэш} с новым HMAC-SHA-256 (/var/lib/fw/baseline.json, fw-integrity, 0600)."""
    raise NotImplementedError("hasher.save_baseline")
