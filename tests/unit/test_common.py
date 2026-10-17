import json
import os
import sys
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "common"))

from fwcommon import codes, protocol  # noqa: E402


class CodesTest(unittest.TestCase):
    def test_codes(self):
        self.assertIn("E50", codes.EVENTS)
        self.assertEqual(len(codes.MESSAGES), 16)
        self.assertIn("5", codes.message_text("M11", n=5))


class ProtocolTest(unittest.TestCase):
    def test_roundtrip_and_dedup(self):
        import tempfile
        calls = []

        def handler(msg):
            calls.append(msg["msg_id"])
            return "ok", {"echo": msg["cmd"]}, None, None

        with tempfile.TemporaryDirectory() as d:
            path = os.path.join(d, "t.sock")
            srv = protocol.serve(path, "authd", handler)
            threading.Thread(target=srv.serve_forever, daemon=True).start()
            try:
                msg = protocol.make_msg("request", "cli", "authd", "auth.ping")
                r1 = protocol._exchange(path, msg, 2)
                r2 = protocol._exchange(path, msg, 2)  # повтор с тем же msg_id
                self.assertEqual(r1["status"], "ok")
                self.assertEqual(r1, r2)
                self.assertEqual(len(calls), 1)  # команда выполнена один раз
                r3 = protocol.request(path, "cli", "authd", "auth.check")
                self.assertEqual(r3["payload"]["echo"], "auth.check")
            finally:
                srv.shutdown()
                srv.server_close()


class ValidationFileTest(unittest.TestCase):
    def test_json_valid(self):
        base = os.path.join(os.path.dirname(__file__), "..", "..", "common")
        with open(os.path.join(base, "validation.json"), encoding="utf-8") as f:
            v = json.load(f)
        self.assertIn("rule", v)


if __name__ == "__main__":
    unittest.main()
