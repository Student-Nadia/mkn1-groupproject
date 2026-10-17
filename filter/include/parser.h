/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  ПС-1 Фильтрация
 * Модуль:      parser
 * Назначение:  разбор заголовков
 * Методы:
 *   - parse_frame — разобрать Ethernet / IPv4 / TCP / UDP / ICMP / ARP
 */
#ifndef FW_PARSER_H
#define FW_PARSER_H

int parse_frame(const unsigned char *buf, unsigned len);

#endif
