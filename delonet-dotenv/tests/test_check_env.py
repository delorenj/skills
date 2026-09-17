import contextlib
import importlib.util
import io
import os
from pathlib import Path
import unittest
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('check_env', Path(__file__).parents[1] / 'scripts/check-env.py')
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


class PresenceTests(unittest.TestCase):
    def run_check(self, values, names):
        output = io.StringIO()
        with patch.dict(os.environ, values, clear=True), contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            status = check.main(names)
        return status, output.getvalue()

    def test_resolved_value_is_never_printed(self):
        status, output = self.run_check({'DEMO': 'synthetic-private-value'}, ['DEMO'])
        self.assertEqual(status, 0)
        self.assertNotIn('synthetic-private-value', output)

    def test_missing_empty_and_unresolved_values_fail_without_values(self):
        status, output = self.run_check({'EMPTY': '', 'REF': 'prefix-op://example/item/field'}, ['ABSENT', 'EMPTY', 'REF'])
        self.assertEqual(status, 1)
        self.assertIn('ABSENT, EMPTY, REF', output)
        self.assertNotIn('example/item', output)

    def test_invalid_argument_is_not_echoed(self):
        status, output = self.run_check({}, ['NAME=private-value'])
        self.assertEqual(status, 2)
        self.assertNotIn('private-value', output)

    def test_no_names_is_not_false_success(self):
        self.assertEqual(self.run_check({}, [])[0], 2)


if __name__ == '__main__':
    unittest.main()
