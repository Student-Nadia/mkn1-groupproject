/**
 * Система:     ПО межсетевого экрана (ПО МЭ)
 * Подсистема:  ПС-1 Фильтрация
 * Модуль:      conntrack
 * Назначение:  таблица состояний
 * Методы:
 *   - ct_init — инициализация
 *   - ct_lookup — поиск записи
 *   - ct_update — обновить состояние и таймер
 */
#ifndef FW_CONNTRACK_H
#define FW_CONNTRACK_H

int ct_init(void);

#endif
