"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-3 CLI
Модуль:      repl
Назначение:  цикл чтения-выполнения: вход (M01, скрытый ввод пароля),
             приглашения admin@fw[rw|ro|EMERGENCY]>, подтверждение
             «Подтвердите (y/n):», help, вывод результатов, auth.ping.
Методы:
  - prompt — строка приглашения для сеанса и режима
  - is_confirmed — ответ на «Подтвердите (y/n):»: только «y» подтверждает
  - help_text — help и help группа по таблице команд
  - run — цикл чтения-выполнения до logout / exit / конца ввода
"""
from . import commands

CONFIRM_PROMPT = "Подтвердите (y/n): "


def prompt(username, role, emergency=False):
    """admin@fw[rw]> , admin@fw[ro]> или admin@fw[EMERGENCY]> ."""
    return "%s@fw[%s]> " % (username, "EMERGENCY" if emergency else role)


def is_confirmed(answer):
    """Любой ответ, кроме y, отменяет операцию без изменений и без события."""
    return answer.strip() == "y"


def help_text(group=None):
    """Без группы — список групп; с группой — синтаксис её команд; неизвестная группа — None."""
    if group is None:
        return "\n".join("%-10s %s" % (g, commands.GROUP_TITLES[g]) for g in commands.groups())
    specs = commands.by_group(group)
    if not specs:
        return None
    return "\n".join("%-22s %s" % (s.name, s.help) for s in specs)


def run(run_dir="/run/fw", stdin=None, stdout=None):
    """Цикл чтения-выполнения CLI."""
    raise NotImplementedError("repl.run")
