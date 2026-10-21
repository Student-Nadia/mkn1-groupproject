import importlib
import unittest


class SmokeTest(unittest.TestCase):
    def test_import(self):
        for m in ['hasher', 'checker', 'emergency', 'restore', '__main__']:
            importlib.import_module("fw_integrityd." + m)

    def test_commands(self):
        main = importlib.import_module("fw_integrityd.__main__")
        self.assertEqual(set(main.COMMANDS), set(main.ALLOWED_SRC))

    def test_stubs_not_implemented(self):
        from fw_integrityd import hasher
        with self.assertRaises(NotImplementedError):
            hasher.sha256_file("/nonexistent")


if __name__ == "__main__":
    unittest.main()
