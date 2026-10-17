import importlib
import unittest


class SmokeTest(unittest.TestCase):
    def test_import(self):
        for m in ['event_log', 'packet_log', 'query', 'rotation']:
            importlib.import_module("fw_logd." + m)


if __name__ == "__main__":
    unittest.main()
