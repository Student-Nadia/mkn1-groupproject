"""
Система:     ПО межсетевого экрана (ПО МЭ)
Подсистема:  ПС-3 CLI
Модуль:      test_shared
Назначение:  прогон общих сценариев tests/shared/*.json (шаги do=command)
             через разбор и проверку CLI; ПС-4 прогоняет те же сценарии
             и должна получать те же коды и поля
"""
import glob
import json
import os
import unittest

from fw_cli import parser, validation

_SHARED = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "shared")


def run_line(line, ifaces, rule_ids):
    """Строка команды -> {"ok": True} или {"message": код, "field": поле}."""
    try:
        cmd = parser.parse(line)
        validation.check_command(cmd, ifaces, rule_ids)
    except (parser.ParseError, validation.ValidationError) as e:
        out = {"message": e.code}
        if e.field is not None:
            out["field"] = e.field
        return out
    return {"ok": True}


class SharedScenariosTest(unittest.TestCase):
    def test_command_steps(self):
        total = 0
        for path in sorted(glob.glob(os.path.join(_SHARED, "*.json"))):
            with open(path, encoding="utf-8") as fh:
                sc = json.load(fh)
            for step in sc["steps"]:
                if step["do"] != "command":
                    continue
                total += 1
                with self.subTest(file=os.path.basename(path), line=step["line"]):
                    got = run_line(step["line"], sc.get("ifaces", []),
                                   set(sc.get("existing_rules", [])))
                    self.assertEqual(got, step["expect"])
        self.assertGreater(total, 0)


if __name__ == "__main__":
    unittest.main()
