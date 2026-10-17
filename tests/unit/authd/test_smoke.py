import importlib
import unittest


class SmokeTest(unittest.TestCase):
    def test_import(self):
        for m in ['accounts', 'auth', 'sessions', 'roles']:
            importlib.import_module("fw_authd." + m)


if __name__ == "__main__":
    unittest.main()
