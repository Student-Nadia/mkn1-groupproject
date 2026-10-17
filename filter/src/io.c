/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  ПС-1 Фильтрация
 * Модуль:      io
 * Назначение:  приём и отправка кадров
 * Методы:
 *   - io_init — открыть AF_PACKET-сокеты на интерфейсах
 *   - io_recv — принять кадр
 *   - io_send — отправить кадр на интерфейс
 */
#include "io.h"

int io_init(void)
{
    /* TODO: AF_PACKET, TPACKET_V3, promiscuous mode */
    return 0;
}
