"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-5 Авторизация
Модуль:      main
Назначение:  точка входа fw-authd
Методы:
  - main — запуск подсистемы
"""
import sys


def main():
    # TODO: чтение конфигурации из /etc/fw/, запуск сервера на /run/fw/*.sock
    print("fw-authd: skeleton, not implemented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
