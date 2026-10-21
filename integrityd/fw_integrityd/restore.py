"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-6 Целостность
Модуль:      restore
Назначение:  восстановление файлов из резервных копий с проверкой эталона (FR-49, FR-50)
Методы:
  - verify_backup — сверить резервную копию с эталоном
  - restore_file — восстановить файл из резервной копии
  - update_backup — обновить резервную копию после штатного изменения
"""


class RestoreError(Exception):
    """Копия не совпала с эталоном или восстановление не выполнено."""


def verify_backup(backup_dir: str, path: str, baseline: dict) -> bool:
    """True, если SHA-256 резервной копии файла совпадает с эталоном."""
    raise NotImplementedError("restore.verify_backup")


def restore_file(backup_dir: str, path: str, baseline: dict) -> None:
    """Сверить копию с эталоном и заменить файл через sudo.
    Копия с несовпадающей контрольной суммой не используется (FR-49)."""
    raise NotImplementedError("restore.restore_file")


def update_backup(backup_dir: str, path: str) -> None:
    """Обновить резервную копию файла (/var/lib/fw/backup/, fw-integrity, 0700) после штатного изменения (FR-50)."""
    raise NotImplementedError("restore.update_backup")
