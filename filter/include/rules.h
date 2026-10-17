/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  ПС-1 Фильтрация
 * Модуль:      rules
 * Назначение:  движок правил
 * Методы:
 *   - rules_init — инициализация
 *   - rules_replace — атомарная подмена таблицы
 *   - rules_match — найти решение для пакета
 */
#ifndef FW_RULES_H
#define FW_RULES_H

int rules_init(void);

#endif
