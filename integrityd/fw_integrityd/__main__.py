"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-6 Целостность
Модуль:      main
Назначение:  точка входа fw-integrityd
Методы:
  - main — запуск подсистемы
"""
import sys


def main():
    # TODO: чтение конфигурации из /etc/fw/, запуск сервера на /run/fw/*.sock
    print("fw-integrityd: skeleton, not implemented")
    return 0


if __name__ == "__main__":
    sys.exit(main())
