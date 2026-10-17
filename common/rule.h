/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  общее
 * Модуль:      rule
 * Назначение:  структура правила фильтрации
 * Методы:
 *   - (добавить)
 */
#ifndef FW_COMMON_RULE_H
#define FW_COMMON_RULE_H

#include "types.h"

typedef struct {
    rule_id_t   id;                    /* 1..65535 */
    uint8_t     active;                /* 0/1 */
    uint8_t     log;                   /* 0/1 */

    /* Условия (0 = any) */
    int8_t      in_iface;              /* -1 = any, иначе индекс */
    mac_t       smac;                  /* 0 = any */
    mac_t       dmac;                  /* 0 = any */
    ip4_t       src;                   /* 0 = any */
    ip4_t       src_mask;              /* для CIDR; 0xFFFFFFFF по умолчанию */
    ip4_t       src_end;               /* для диапазона; == src если не диапазон */
    ip4_t       dst;
    ip4_t       dst_mask;
    ip4_t       dst_end;
    uint8_t     proto;                 /* 0 = any, иначе 1/6/17 */
    eth_proto_t eth_proto;             /* ANY | ARP | OTHER */
    uint16_t    sport;                 /* 0 = any */
    uint16_t    sport_end;
    uint16_t    dport;
    uint16_t    dport_end;
    uint8_t     icmp_type;             /* 255 = any */
    uint8_t     icmp_code;             /* 255 = any */

    /* Действие */
    action_t    action;                /* accept | goto | drop */
    int8_t      out_ifaces[MAX_INTERFACES]; /* -1 = терминатор */
    rule_id_t   to_rule;               /* для action=goto */
    uint8_t     conntrack;             /* 1 = контролировать состояние */

    char        comment[MAX_COMMENT_LEN];
    uint64_t    hits;                  /* счётчик срабатываний (ведёт ПС-1, в файл не сохраняется) */
} rule_t;

#endif /* FW_COMMON_RULE_H */
