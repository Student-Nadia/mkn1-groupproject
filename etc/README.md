# etc/

- `default/config.json`, `default/policy.json` — конфигурация и политика по умолчанию (политика пустая: все пакеты IPv4 удаляются, FR-08).
- `systemd/fw-*.service` — службы подсистем, каждая от своего пользователя ОС.
- `sudoers.d/fw` — **шаблон**: фиксированный список команд sudo (ip, route, timedatectl, systemctl). Установка с правами root, права 0440.
- `nginx/fw-web.conf` — HTTPS для ПС-4 (самоподписанный сертификат создаётся при установке).