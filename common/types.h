/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  общее
 * Модуль:      types
 * Назначение:  общие типы и константы ПО МЭ
 * Методы:
 *   - (добавить)
 */
#ifndef FW_COMMON_TYPES_H
#define FW_COMMON_TYPES_H

#include <stdint.h>

#define MIN_INTERFACES      1
#define MAX_INTERFACES      6
#define MAX_CONTROLLED_FILES 64
#define MAX_IFACE_NAME      16
#define MAX_RULES           65535
#define MAX_COMMENT_LEN     256
#define MAX_CMD_LEN         128
#define MAX_PATH_LEN        256

typedef uint16_t rule_id_t;
typedef uint32_t ip4_t;
typedef uint64_t mac_t;
typedef uint64_t timestamp_us_t;

typedef enum { ACTION_ACCEPT, ACTION_GOTO, ACTION_DROP } action_t;
typedef enum { ETH_PROTO_ANY, ETH_PROTO_ARP, ETH_PROTO_OTHER } eth_proto_t;
typedef enum { ROLE_RO, ROLE_RW } role_t;
typedef enum { RESULT_OK, RESULT_FAIL } result_t;

#endif /* FW_COMMON_TYPES_H */
