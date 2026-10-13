"""Exercise bundle integrity failures using isolated copies, not model grading."""
import importlib.util
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('check_skills', ROOT / 'tools/check_skills.py')
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class SkillBundleTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for name in ('domains', 'references', 'prompts', 'evals', 'docs'):
            shutil.copytree(ROOT / name, self.root / name)
        for name in ('SKILL.md', 'README.md'):
            shutil.copyfile(ROOT / name, self.root / name)

    def test_complete_bundle(self):
        errors, counts = CHECK.check(self.root)
        self.assertEqual(errors, [])
        self.assertEqual(counts['skills'], 7)

    def test_missing_shared_dependency(self):
        (self.root / 'references/general-drafting-template.md').unlink()
        errors, _ = CHECK.check(self.root)
        self.assertTrue(any('broken link' in e for e in errors))

    def test_conflicting_case(self):
        path = self.root / 'evals/skill-routing-cases.yaml'
        data = CHECK.yaml.safe_load(path.read_text(encoding='utf-8'))
        data['cases'][0]['expected']['required'] = ['patent-software-ai']
        data['cases'][0]['expected']['avoid'] = ['patent-software-ai']
        path.write_text(CHECK.yaml.safe_dump(data), encoding='utf-8')
        self.assertTrue(any('conflicting' in e for e in CHECK.check(self.root)[0]))

    def test_undocumented_domain(self):
        path = self.root / 'references/domain-catalog.md'
        path.write_text('', encoding='utf-8')
        self.assertTrue(any('absent from catalog' in e for e in CHECK.check(self.root)[0]))

    def test_invalid_metadata(self):
        path = self.root / 'domains/patent-software-ai/SKILL.md'
        path.write_text('# No metadata', encoding='utf-8')
        self.assertTrue(any('frontmatter' in e for e in CHECK.check(self.root)[0]))


if __name__ == '__main__':
    unittest.main()
