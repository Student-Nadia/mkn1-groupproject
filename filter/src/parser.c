/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  ПС-1 Фильтрация
 * Модуль:      parser
 * Назначение:  разбор заголовков
 * Методы:
 *   - parse_frame — разобрать Ethernet / IPv4 / TCP / UDP / ICMP / ARP
 */
#include "parser.h"

int parse_frame(const unsigned char *buf, unsigned len)
{
    (void)buf; (void)len;
    /* TODO: Ethernet / IPv4 / TCP / UDP / ICMP / ARP, FR-12 */
    return -1;
}
