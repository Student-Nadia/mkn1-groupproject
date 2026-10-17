/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  ПС-1 Фильтрация
 * Модуль:      main
 * Назначение:  точка входа fw-filter
 * Методы:
 *   - main — инициализация модулей и основной цикл
 */
#include <stdio.h>

#include "io.h"
#include "parser.h"
#include "rules.h"
#include "conntrack.h"
#include "pktlog_client.h"

int main(void)
{
    if (rules_init() || ct_init() || pktlog_init() || io_init()) {
        fprintf(stderr, "fw-filter: initialization failed\n");
        return 1;
    }
    /* TODO: основной поток (раздел «Основной поток (обработка пакета)» спецификации) */
    puts("fw-filter: skeleton, not implemented");
    return 0;
}
