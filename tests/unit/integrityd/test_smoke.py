import importlib
import unittest


class SmokeTest(unittest.TestCase):
    def test_import(self):
        for m in ['hasher', 'checker', 'emergency', 'restore']:
            importlib.import_module("fw_integrityd." + m)


if __name__ == "__main__":
    unittest.main()
