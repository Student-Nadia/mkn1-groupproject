/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  ПС-1 Фильтрация
 * Модуль:      pktlog_client
 * Назначение:  передача записей пакетов в ПС-2
 * Методы:
 *   - pktlog_init — открыть соединение с ПС-2
 *   - pktlog_write — передать запись packet_record_t
 */
#include "pktlog_client.h"

int pktlog_init(void)
{
    /* TODO: сокет /run/fw/logd.sock, бинарный формат packet_record_t */
    return 0;
}
