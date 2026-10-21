# ПС-5 Авторизация (fw-authd)

- **Язык:** Python 3
- **Пользователь ОС:** `fw-auth`
- **Требования:** FR-30 – FR-37
- **Команда:** Волнухина, Карцев (вместе с ПС-6: Митяев, Цыбукова)
- **Сокет:** `/run/fw/authd.sock` (права доступа 0600, владелец `fw-auth`)

---

## 1. Назначение и реализуемые требования

Подсистема **ПС-5 Авторизация** предназначена для управления учётными записями администраторов, аутентификации, поддержания сеансов работы и разграничения прав доступа к командам управления ПО межсетевого экрана (ПО МЭ).

### Реализуемые требования спецификации:
- **FR-30 (ТЗ 4.1):** Аутентификация администратора по идентификатору и паролю в CLI и web-интерфейсе. При неверных данных возвращается `M02` и регистрируется событие `E03`. Без аутентификации функции управления недоступны.
- **FR-31:** После 5 неудачных попыток входа подряд идентификатор блокируется на 60 секунд: возвращается `M12`, регистрируется `E06`.
- **FR-32 (ТЗ 4.2):** Роли «чтение/запись» (`rw`) и «только чтение» (`ro`). Перед выполнением изменяющей команды проверяется роль: при роли `ro` команда отклоняется с `M03`, регистрируется событие `E50`.
- **FR-33 (ТЗ 4.3):** Предустановленный администратор `admin` с ролью `rw`. Удаление учётной записи `admin` и изменение его роли блокируются с ошибкой `M05`. Смена пароля разрешена.
- **FR-34 (ТЗ 4.4):** При наличии активного сеанса с ролью `rw` права второго одновременно входящего администратора с ролью `rw` автоматически понижаются до `ro`: возвращается предупреждение `M04`, регистрируется событие `E04`. Автоматическое повышение прав запрещено.
- **FR-35 (ТЗ 5.9):** Сеанс завершается при выходе (`E02`), при сбросе другим администратором (`E05`), при удалении учётной записи пользователя или по таймауту бездействия 15 минут (900 с, `E07`). При принудительном завершении возвращается `M15`.
- **FR-36 (ТЗ 5.9):** Валидация учётных записей: идентификатор от 3 до 32 символов (латиница, цифры, подчёркивание `^[A-Za-z0-9_]+$`, уникальный); пароль не менее 8 символов (до 128); роль — `rw` или `ro`. Некорректные параметры отклоняются с `M06`.
- **FR-37:** Пароли хранятся и сверяются исключительно в виде хэша с солью (PBKDF2-HMAC-SHA-256, 200 000 итераций). Пароли и хэши никогда не передаются в интерфейсы и не пишутся в журналы.
- **FR-37a:** CLI взаимодействует с ПС-5 при входе один раз для аутентификации и периодически отправляет уведомления активности (`auth.ping`) для контроля таймаута бездействия.
- **FR-37b:** При попытке выполнения команды без необходимых прав возвращается `M03` и пишется событие `E50` с именем команды.

---

## 2. Структура подсистемы и модули

```text
authd/
├── README.md                  # Данное описание подсистемы и интерфейсов
└── fw_authd/
    ├── __init__.py            # Пакет fw_authd
    ├── __main__.py            # Сервер Unix-сокета, маршрутизация и диспетчеризация команд
    ├── accounts.py            # Учётные записи, accounts.json, PBKDF2-HMAC-SHA-256, валидация
    ├── auth.py                # Аутентификация, счётчики попыток и блокировка на 60 с
    ├── roles.py               # Ролевая модель rw / ro, категоризация команд и проверка прав
    └── sessions.py            # Сеансы, контроль одновременных RW-сессий, таймаут 15 мин
```

### Модули и функции-заглушки

#### `accounts.py`
Управление файлом учётных записей (`/etc/fw/accounts.json`), криптографическое хэширование и валидация.
- **Константы:** `ID_MIN_LEN = 3`, `ID_MAX_LEN = 32`, `PWD_MIN_LEN = 8`, `PWD_MAX_LEN = 128`, `DEFAULT_HASH_ITERATIONS = 200000`, `BUILTIN_ADMIN_ID = "admin"`.
- `validate_username(username: str) -> Tuple[bool, Optional[str]]` — проверка длины и символов логина (FR-36).
- `validate_password(password: str) -> Tuple[bool, Optional[str]]` — проверка длины пароля (FR-36).
- `validate_role(role: str) -> Tuple[bool, Optional[str]]` — проверка допустимости роли (`rw`, `ro`).
- `hash_password(password: str, salt_hex: Optional[str] = None, iterations: int = 200000) -> Tuple[str, str]` — генерация случайной соли и вычисление хэша PBKDF2-HMAC-SHA-256 (FR-37).
- `verify_password(password: str, stored_hash_hex: str, salt_hex: str, iterations: int = 200000) -> bool` — безопасная сверка пароля без утечки информации по времени (`hmac.compare_digest`).
- `load_accounts(path: str) -> Dict[str, Dict[str, Any]]` — загрузка `accounts.json`.
- `save_accounts(accounts: dict, path: str) -> None` — атомарная запись `accounts.json`.
- `get_user(username: str, path: str) -> Optional[Dict[str, Any]]` — получение записи пользователя.
- `list_users(path: str) -> List[Dict[str, str]]` — возврат списка `{id, role}` без хэшей и солей (FR-37).
- `add_user(username: str, password: str, role: str, path: str) -> Tuple[bool, Optional[str]]` — добавление новой учётной записи.
- `edit_user(username: str, new_password: Optional[str], new_role: Optional[str], path: str) -> Tuple[bool, Optional[str]]` — изменение роли или пароля (защита `admin` по FR-33).
- `delete_user(username: str, path: str) -> Tuple[bool, Optional[str]]` — удаление учётной записи (запрет удаления `admin` с `M05`).

#### `auth.py`
Логика аутентификации и защиты от перебора паролей.
- **Константы:** `LOGIN_MAX_ATTEMPTS = 5`, `LOGIN_BLOCK_SEC = 60`.
- `is_locked(username: str) -> bool` — проверка нахождения логина под временной блокировкой.
- `get_lock_remaining_time(username: str) -> int` — остаток времени блокировки в секундах.
- `record_failure(username: str) -> Tuple[int, bool]` — инкремент счётчика неудач и взвод блокировки при 5 попытках (FR-31).
- `reset_failures(username: str) -> None` — сброс счётчика при успешном входе.
- `clear_lockouts() -> None` — сброс состояния блокировок (для тестов/стенда).
- `authenticate(username: str, password: str, source: str, accounts_path: str) -> Tuple[bool, Optional[dict], Optional[str], Optional[str]]` — проверка логина/пароля, блокировок и инициализация сеанса.
- `logout(session_id: str) -> Tuple[bool, Optional[str]]` — завершение сеанса.

#### `sessions.py`
Управление активными сеансами администраторов.
- **Константы:** `SESSION_TIMEOUT_SEC = 900` (15 минут), `ROLE_RW = "rw"`, `ROLE_RO = "ro"`.
- `create_session(username: str, role: str, source: str) -> Tuple[dict, Optional[str], Optional[str]]` — создание сеанса с автоматическим понижением прав до `ro` при наличии активного `rw`-сеанса (FR-34, `M04`, `E04`).
- `get_session(session_id: str) -> Optional[dict]` — проверка валидности и получение сеанса.
- `touch_session(session_id: str) -> bool` — продление активности по сигналу `auth.ping` (FR-37a).
- `close_session(session_id: str, reason: str) -> Tuple[bool, Optional[str]]` — штатное закрытие сеанса (`E02`).
- `kill_session(session_id: str, killer_username: Optional[str]) -> Tuple[bool, Optional[str], Optional[str]]` — принудительный сброс сеанса (`E05`, `M15`).
- `close_sessions_for_user(username: str, reason: str) -> List[str]` — сброс всех сессий удалённого пользователя (`E07`).
- `list_active_sessions() -> List[dict]` — получение списка активных сессий.
- `cleanup_expired_sessions(timeout_sec: int) -> List[dict]` — очистка сеансов с бездействием > 15 минут (`E07`).
- `has_active_rw_session() -> bool` — проверка наличия активной сессии с эффективной ролью `rw`.

#### `roles.py`
Проверка прав доступа к командам и разграничение ролей.
- **Списки команд:** `MODIFYING_COMMANDS` (изменяющие команды: `user.*`, `rule.add/edit/delete`, `state.clear`, `integrity.restore`, `config.save` и др.) и `READ_ONLY_COMMANDS`.
- `is_modifying_cmd(cmd: str) -> bool` — определение типа команды.
- `is_read_only_cmd(cmd: str) -> bool` — проверка команды только для чтения.
- `check_permission(role: str, cmd: str) -> Tuple[bool, Optional[str], Optional[str]]` — проверка прав роли: при попытке вызова изменяющей команды пользователем `ro` возвращает `(False, "M03", "E50")` (FR-32, FR-37b).
- `check_session_permission(session: Any, cmd: str) -> Tuple[bool, Optional[str], Optional[str]]` — проверка прав сеанса.
- `validate_role_transition(username: str, current_role: str, new_role: str) -> Tuple[bool, Optional[str]]` — запрет смены роли предустановленного `admin` (`M05`, FR-33).
- `get_role_permissions(role: str) -> dict` — описание прав роли.

#### `__main__.py`
Точка входа службы `fw-authd`.
- `dispatch_request(msg: dict) -> Tuple[str, dict, Optional[str], Optional[str]]` — маршрутизация запросов к обработчикам.
- `emit_event(code: str, details: Optional[dict]) -> None` — асинхронная отправка событий в ПС-2 с локальной очередью до 1000 записей (FR-28).
- `notify_integrity() -> None` — вызов `integrity.update_baseline` в ПС-6 при изменении учётных записей.
- Обработчики входящих команд: `handle_auth_login`, `handle_auth_logout`, `handle_auth_ping`, `handle_auth_check`, `handle_user_list`, `handle_user_add`, `handle_user_edit`, `handle_user_delete`, `handle_session_list`, `handle_session_kill`.
- `start_server(socket_path: str)` — запуск Unix-сервера на `/run/fw/authd.sock`.

---

## 3. Спецификация команд протокола (JSON по Unix-сокету)

Все сообщения передаются в конвертах по стандарту `common/PROTOCOL.md`.

### 3.1. `auth.login` — Аутентификация и создание сеанса
- **Запрос (`payload`):**
  ```json
  {"id": "admin", "password": "SecretPassword123", "source": "cli"}
  ```
- **Успешный ответ (первый RW-сеанс):**
  ```json
  {"status": "ok", "payload": {"session_id": "a9f4...", "username": "admin", "role": "rw", "downgraded": false}}
  ```
- **Успешный ответ (второй одновременный RW-сеанс, понижение до RO по FR-34):**
  ```json
  {
    "status": "ok",
    "payload": {
      "session_id": "b1e2...",
      "username": "admin",
      "role": "ro",
      "downgraded": true,
      "warning": "M04",
      "warning_message": "Внимание: права понижены до «только чтение», так как активен другой администратор с правами «чтение/запись»"
    }
  }
  ```
- **Ответ при неверном пароле (FR-30):**
  ```json
  {"status": "error", "error_code": "M02", "error_message": "Ошибка: неверный идентификатор или пароль", "payload": {}}
  ```
- **Ответ при блокировке после 5 неудач (FR-31):**
  ```json
  {"status": "error", "error_code": "M12", "error_message": "Ошибка: вход временно заблокирован. Повторите через 60 с", "payload": {}}
  ```

### 3.2. `auth.logout` — Завершение сеанса
- **Запрос (`payload`):** `{"session_id": "a9f4..."}`
- **Ответ:** `{"status": "ok", "payload": {"status": "logged_out"}}` (регистрируется `E02`).

### 3.3. `auth.ping` — Продление активности сеанса
- **Запрос (`payload`):** `{"session_id": "a9f4..."}`
- **Ответ:** `{"status": "ok", "payload": {"status": "pong"}}`
- При просроченном сеансе: `status="error"`, `error_code="M15"`.

### 3.4. `auth.check` — Проверка прав сеанса или роли
- **Запрос (`payload`):** `{"session_id": "a9f4...", "cmd": "rule.add"}`
- **Ответ (доступ разрешён):** `{"status": "ok", "payload": {"allowed": true}}`
- **Ответ (доступ запрещён по роли `ro`, FR-32):**
  `{"status": "error", "error_code": "M03", "error_message": "Ошибка: недостаточно прав. Режим «только чтение»", "payload": {"allowed": false}}` (регистрируется `E50`).

### 3.5. `user.list` — Список пользователей
- **Запрос (`payload`):** `{"session_id": "..."}`
- **Ответ:**
  ```json
  {
    "status": "ok",
    "payload": {
      "users": [
        {"id": "admin", "role": "rw"},
        {"id": "operator", "role": "ro"}
      ]
    }
  }
  ```

### 3.6. `user.add` / `user.edit` / `user.delete` — Управление учётными записями
- `user.add`: `{"session_id": "...", "id": "...", "password": "...", "role": "rw|ro"}`
- `user.edit`: `{"session_id": "...", "id": "...", "password": "...", "role": "rw|ro"}` (попытка изменить роль `admin` возвращает `M05`).
- `user.delete`: `{"session_id": "...", "id": "..."}` (попытка удалить `admin` возвращает `M05`). При удалении пользователя все его сеансы сбрасываются с `E07`.
- При успешном выполнении регистрируется `E32` и в ПС-6 отправляется `integrity.update_baseline`.

### 3.7. `session.list` / `session.kill` — Управление сеансами
- `session.list`: `{"session_id": "..."}` -> список сеансов с временем активности и флагом `downgraded`.
- `session.kill`: `{"session_id": "...", "target_session_id": "..."}` -> сброс сеанса с событием `E05` и сообщением `M15`.

---

## 4. Регистрируемые события аудита (в ПС-2 logd)

| Код | Описание события |
|---|---|
| **E01** | Вход администратора |
| **E02** | Выход администратора |
| **E03** | Неуспешная попытка входа |
| **E04** | Понижение прав администратора до «только чтение» (FR-34) |
| **E05** | Сброс сеанса администратора другим администратором (FR-35) |
| **E06** | Блокировка входа после 5 неудачных попыток (FR-31) |
| **E07** | Завершение сеанса по бездействию 15 мин или удалению учётной записи (FR-35) |
| **E32** | Изменение учётной записи (`add`, `edit`, `delete`) |
| **E50** | Отказ в доступе: недостаточно прав роли для выполнения команды (FR-32, FR-37b) |

---

## 5. Запуск и тестирование

### Запуск службы
```bash
# Прямой запуск модуля в Debian 12:
PYTHONPATH=common:authd python3 -m fw_authd

# Через systemd:
sudo systemctl start fw-authd.service
```

### Запуск unit-тестов
```bash
# Запуск тестов ПС-5:
PYTHONPATH=common:authd python3 -m unittest discover -s tests/unit/authd -v
```
