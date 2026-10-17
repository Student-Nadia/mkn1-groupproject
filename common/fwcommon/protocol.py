"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  общее
Модуль:      protocol
Назначение:  обмен JSON-сообщениями по Unix-сокетам (конверт, клиент с повторами, сервер с дедупликацией)
Методы:
  - make_msg — собрать сообщение
  - request — запрос с тайм-аутом и повторами
  - serve — простой сервер: обработчик + кэш ответов по msg_id
"""
import itertools
import json
import os
import socket
import socketserver
import threading
import time
from datetime import datetime, timezone

TIMEOUT_SEC = 5
RETRIES = 2
_ids = itertools.count(1)


def now_iso():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def make_msg(type_, src, dst, cmd=None, payload=None, reply_to=None, msg_id=None, **extra):
    msg = {"msg_id": msg_id if msg_id is not None else next(_ids), "type": type_, "src": src, "dst": dst,
           "cmd": cmd, "ts": now_iso(), "payload": payload if payload is not None else {}, "reply_to": reply_to}
    msg.update(extra)
    return msg


def _exchange(path, msg, timeout):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as s:
        s.settimeout(timeout)
        s.connect(path)
        s.sendall((json.dumps(msg, ensure_ascii=False) + "\n").encode("utf-8"))
        buf = b""
        while b"\n" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                raise ConnectionError("connection closed")
            buf += chunk
        return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))


def request(path, src, dst, cmd, payload=None, timeout=TIMEOUT_SEC, retries=RETRIES):
    """Отправить запрос; при отсутствии ответа повторить с тем же msg_id. Исключение — подсистема не отвечает (M16)."""
    msg = make_msg("request", src, dst, cmd, payload)
    last = None
    for _ in range(retries + 1):
        try:
            return _exchange(path, msg, timeout)
        except (OSError, ValueError) as e:
            last = e
    raise ConnectionError("subsystem %s does not respond: %s" % (dst, last))


def serve(path, name, handler, cache_size=1024):
    """handler(msg) -> (status, payload, error_code, error_message). Повторный msg_id получает прежний ответ."""
    cache = {}
    order = []
    lock = threading.Lock()

    class H(socketserver.StreamRequestHandler):
        def handle(self):
            for line in self.rfile:
                try:
                    msg = json.loads(line.decode("utf-8"))
                except ValueError:
                    continue
                with lock:
                    resp = cache.get(msg.get("msg_id"))
                if resp is None:
                    try:
                        status, payload, ec, em = handler(msg)
                    except Exception as e:  # необработанные исключения не завершают процесс
                        status, payload, ec, em = "error", {}, None, str(e)
                    resp = make_msg("response", name, msg.get("src"), reply_to=msg.get("msg_id"),
                                    status=status, error_code=ec, error_message=em, payload=payload)
                    with lock:
                        cache[msg.get("msg_id")] = resp
                        order.append(msg.get("msg_id"))
                        if len(order) > cache_size:
                            cache.pop(order.pop(0), None)
                self.wfile.write((json.dumps(resp, ensure_ascii=False) + "\n").encode("utf-8"))

    if os.path.exists(path):
        os.unlink(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    srv = socketserver.ThreadingUnixStreamServer(path, H)
    os.chmod(path, 0o600)
    return srv
