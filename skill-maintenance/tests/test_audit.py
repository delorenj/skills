import importlib.util
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('audit', Path(__file__).parents[1] / 'scripts/audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class InventoryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir='/tmp')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def skill(self, folder, name, body=''):
        p = self.root / folder / 'SKILL.md'
        p.parent.mkdir(parents=True)
        p.write_text(f'---\nname: {name}\ndescription: Scoped example\n---\n{body}')
        return p

    def test_divergent_duplicates_not_hidden_by_hash_or_link_target(self):
        self.skill('one', 'same', 'first')
        self.skill('synced/bucket/two', 'same', 'second')
        result = audit.inventory(self.root)
        self.assertEqual(2, result['entrypoints'])
        self.assertEqual('DUPLICATE_NAME', result['findings'][0]['code'])
        self.assertNotEqual(result['entries'][0]['sha256'], result['entries'][1]['sha256'])

    def test_examples_urls_and_placeholders_are_not_missing_dependencies(self):
        self.skill('one', 'one', '```md\n[x](missing.md)\n```\n[x](https://example.test)\n[x](<project>/file.md)\n[x](#here)\n[x](real-missing.md)')
        findings = audit.inventory(self.root)['findings']
        self.assertEqual(['real-missing.md'], [x['target'] for x in findings])

    def test_cycle_and_broken_symlink_are_bounded(self):
        (self.root / 'cycle').symlink_to(self.root, target_is_directory=True)
        (self.root / 'broken').symlink_to(self.root / 'absent')
        self.assertEqual({'DIRECTORY_CYCLE', 'BROKEN_PATH'}, {x['code'] for x in audit.inventory(self.root)['findings']})

    def test_external_canonical_link_is_counted(self):
        self.skill('catalog/one', 'one')
        activation = self.root / 'activation';activation.mkdir()
        (activation / 'one').symlink_to(self.root / 'catalog/one')
        self.assertEqual(1, audit.inventory(activation)['entrypoints'])

    def test_invalid_metadata_does_not_echo_body(self):
        p = self.root / 'bad';p.mkdir();(p / 'SKILL.md').write_text('private-example-value')
        result = audit.inventory(self.root)
        self.assertEqual('INVALID_ENTRYPOINT', result['findings'][0]['code'])
        self.assertNotIn('private-example-value', str(result))

    def test_system_and_synced_are_included_but_skill_assets_are_not(self):
        self.skill('.system/core', 'core')
        self.skill('synced/bucket/imported', 'imported')
        self.skill('synced/bucket/imported/assets/example', 'not-a-skill')
        self.assertEqual({'core', 'imported'}, {e['name'] for e in audit.inventory(self.root)['entries']})


if __name__ == '__main__':
    unittest.main()
