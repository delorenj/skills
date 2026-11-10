import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).parents[1] / 'scripts/env-op-resolve.py'
spec = importlib.util.spec_from_file_location('env_op_resolve', SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

REF_A = 'op://DeLoSecrets/Some Item/credential'
REF_B = 'op://DeLoSecrets/other-item/notes/Field'
KEY_A = mod.derive_key(REF_A)
KEY_B = mod.derive_key(REF_B)
MULTILINE = 'line-one\nline "two" \\ trailer\nline-three'


class DeriveKeyTests(unittest.TestCase):
    def test_deterministic_and_prefixed(self):
        self.assertEqual(KEY_A, 'OP_DELOSECRETS_SOME_ITEM_CREDENTIAL')
        self.assertEqual(KEY_B, 'OP_DELOSECRETS_OTHER_ITEM_NOTES_FIELD')

    def test_rejects_non_ref(self):
        with self.assertRaises(mod.FailClosed):
            mod.derive_key('https://example.com/x/y')


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        d = Path(self.tmp.name)
        self.store = d / 'secrets.env'
        self.refmap = d / 'refmap.tsv'
        self.envop = d / '.env.op'
        escaped = MULTILINE.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        self.store.write_text('# store\n%s="%s"\n%s=plain-value\n' % (KEY_A, escaped, KEY_B))
        self.refmap.write_text('# ref<TAB>key\n%s\t%s\n%s\t%s\n' % (REF_A, KEY_A, REF_B, KEY_B))

    def tearDown(self):
        self.tmp.cleanup()

    def run_cli(self, *argv, cwd=None):
        return subprocess.run(
            [sys.executable, str(SCRIPT), '--store', str(self.store), '--refmap', str(self.refmap), *argv],
            capture_output=True, text=True, cwd=cwd or self.tmp.name,
        )


class RenderTests(Base):
    def test_render_roundtrip_multiline_and_mode(self):
        self.envop.write_text('A_KEY=%s\nB_KEY="%s"\n' % (REF_A, REF_B))
        out = Path(self.tmp.name) / '.env'
        r = self.run_cli('render', str(self.envop), str(out))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(oct(out.stat().st_mode & 0o777), '0o600')
        parsed = dict(mod._parse_env_lines(out.read_text(), 'rendered', allow_export=False))
        self.assertEqual(parsed['A_KEY'], MULTILINE)
        self.assertEqual(parsed['B_KEY'], 'plain-value')

    def test_render_refuses_unknown_ref(self):
        self.envop.write_text('X=op://DeLoSecrets/NotMapped/field\n')
        r = self.run_cli('render', str(self.envop))
        self.assertEqual(r.returncode, 2)
        self.assertIn('not in the refmap', r.stderr)
        self.assertFalse((Path(self.tmp.name) / '.env').exists())

    def test_render_refuses_missing_store_key(self):
        self.store.write_text('# empty\n')
        self.envop.write_text('A_KEY=%s\n' % REF_A)
        r = self.run_cli('render', str(self.envop))
        self.assertEqual(r.returncode, 2)
        self.assertIn('no value in the store', r.stderr)

    def test_render_refuses_duplicate_keys(self):
        self.envop.write_text('A=%s\nA=%s\n' % (REF_A, REF_B))
        r = self.run_cli('render', str(self.envop))
        self.assertEqual(r.returncode, 2)
        self.assertIn('duplicate key', r.stderr)

    def test_render_refuses_embedded_ref(self):
        self.envop.write_text('X=prefix op://DeLoSecrets/Some Item/credential suffix\n')
        r = self.run_cli('render', str(self.envop))
        self.assertEqual(r.returncode, 2)

    def test_refmap_disagreement_fails(self):
        self.refmap.write_text('%s\tWRONG_KEY\n' % REF_A)
        self.envop.write_text('A=%s\n' % REF_A)
        r = self.run_cli('render', str(self.envop))
        self.assertEqual(r.returncode, 2)
        self.assertIn('disagrees', r.stderr)

    def test_refmap_duplicate_key_fails(self):
        # both refs derive to the same store key
        twin = 'op://DeLoSecrets/Some-Item/credential'
        self.refmap.write_text('%s\t%s\n%s\t%s\n' % (REF_A, KEY_A, twin, KEY_A))
        r = self.run_cli('render', str(self.envop))
        self.assertEqual(r.returncode, 2)
        self.assertIn('maps two different refs', r.stderr)

    def test_stderr_never_contains_values(self):
        self.envop.write_text('X=op://DeLoSecrets/NotMapped/field\n')
        r = self.run_cli('render', str(self.envop))
        self.assertNotIn(MULTILINE.split('\n')[0], r.stderr)
        self.assertNotIn('plain-value', r.stderr)


class ExecTests(Base):
    def test_exec_injects_exact_bytes(self):
        self.envop.write_text('A_KEY=%s\n' % REF_A)
        probe = (
            'import os,hashlib;'
            'print(hashlib.sha256(os.environ["A_KEY"].encode()).hexdigest())'
        )
        r = self.run_cli('exec', '--env-file', str(self.envop), '--',
                         sys.executable, '-c', probe)
        self.assertEqual(r.returncode, 0, r.stderr)
        import hashlib
        self.assertEqual(r.stdout.strip(), hashlib.sha256(MULTILINE.encode()).hexdigest())

    def test_exec_file_overrides_inherited_env(self):
        self.envop.write_text('B_KEY=%s\n' % REF_B)
        env = dict(os.environ, B_KEY='inherited-loses')
        r = subprocess.run(
            [sys.executable, str(SCRIPT), '--store', str(self.store), '--refmap', str(self.refmap),
             'exec', '--env-file', str(self.envop), '--',
             sys.executable, '-c', 'import os;print(os.environ["B_KEY"])'],
            capture_output=True, text=True, env=env,
        )
        self.assertEqual(r.stdout.strip(), 'plain-value')


if __name__ == '__main__':
    unittest.main()
