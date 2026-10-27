"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-2 Регистрация
Модуль:      main
Назначение:  точка входа fw-logd
Методы:
  - main — запуск подсистемы
"""
import sys


def main():
    # TODO: чтение конфигурации из /etc/fw/, запуск сервера на /run/fw/*.sock
    print("fw-logd: skeleton, not implemented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
