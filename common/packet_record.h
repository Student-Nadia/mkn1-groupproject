/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  общее
 * Модуль:      packet_record
 * Назначение:  запись журнала пакетов (двоичная, фиксированной длины)
 * Методы:
 *   - (добавить)
 */
#ifndef FW_COMMON_PACKET_RECORD_H
#define FW_COMMON_PACKET_RECORD_H

#include "types.h"

#pragma pack(push, 1)
typedef struct {
    timestamp_us_t ts_us;              /* 8 */
    uint8_t        action;             /* 1: 0=accept, 1=drop */
    uint8_t        in_iface;           /* 1 */
    uint8_t        out_count;          /* 1 */
    uint8_t        out_ifaces[6];      /* 6 (0xFF = пусто) */
    rule_id_t      rule_id;            /* 2 */
    uint32_t       conn_id;            /* 4: ID записи таблицы состояний, 0 = вне соединения */
    uint8_t        eth_proto;          /* 1: 0=IPv4, 1=ARP, 2=other */
    uint8_t        ip_proto;           /* 1: 6=TCP, 17=UDP, 1=ICMP */
    mac_t          smac;               /* 8 */
    mac_t          dmac;               /* 8 */
    ip4_t          src_ip;             /* 4 */
    ip4_t          dst_ip;             /* 4 */
    uint16_t       sport;              /* 2 */
    uint16_t       dport;              /* 2 */
    uint8_t        icmp_type;          /* 1 */
    uint8_t        icmp_code;          /* 1 */
} packet_record_t;                     /* итого 55 байт */
#pragma pack(pop)

_Static_assert(sizeof(packet_record_t) == 55, "packet_record_t must be 55 bytes");

#endif /* FW_COMMON_PACKET_RECORD_H */
