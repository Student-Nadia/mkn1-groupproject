"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-3 CLI
Модуль:      core
Назначение:  ядро управления, общее для CLI и web: проверка прав и режима по
             таблице команд, выполнение команд через ПС-1, ПС-2, ПС-5, ПС-6 и
             ОС, регистрация E50 / E43 и событий команд, рабочая копия
             политики доступа (rule add/edit/del -> rule.replace с путём к
             подготовленному policy.json) и конфигурации (config save).
Методы:
  - access_error — код отказа по роли и режиму: None, M03 или M10
  - Result — результат команды: код сообщения и/или данные для вывода
  - execute — выполнить разобранную команду от имени сеанса
"""
from dataclasses import dataclass, field


def access_error(spec, role, emergency):
    """Отказ по таблице 7: M10 — недоступна в аварийном режиме, M03 — нужна роль rw.

    Режим проверяется первым: в аварийном режиме изменяющая команда отклоняется
    с M10 для любой роли. При M03 вызывающий регистрирует E50 (FR-37b).
    """
    if emergency and not spec.emergency:
        return "M10"
    if spec.rw and role != "rw":
        return "M03"
    return None


@dataclass
class Result:
    code: str = None                          # M09, M13, ... или None
    columns: list = field(default_factory=list)
    rows: list = field(default_factory=list)
    text: str = None


def execute(cmd, session, run_dir="/run/fw", confirm=None):
    """Выполнить команду: проверка прав, подтверждение (confirm() -> bool), вызов подсистем."""
    raise NotImplementedError("core.execute")
