/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  ПС-1 Фильтрация
 * Модуль:      pktlog_client
 * Назначение:  передача записей пакетов в ПС-2
 * Методы:
 *   - pktlog_init — открыть соединение с ПС-2
 *   - pktlog_write — передать запись packet_record_t
 */
#ifndef FW_PKTLOG_CLIENT_H
#define FW_PKTLOG_CLIENT_H

int pktlog_init(void);

#endif
