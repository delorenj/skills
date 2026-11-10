"""Tests for position.py — run: python3 -m unittest discover -s scripts -p 'test_*.py'"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import position  # noqa: E402

GOOD = """---
schema: automaticai.position/v1
engagement: acme
counterparty: Pat (Acme)
as_of: 2026-11-10T09:00:00-05:00
move: 2
previous: none
to_move: them
initiative: us
evaluation: slightly-better
phase: middlegame
next_move: Damian sends the options page by Fri
delta: first position
---

# The Position: Pat (Acme), 2026-11-10

## Evaluation
We hold the initiative.

## Moves since last position
1. Pilot signed. 2. Final payment landed.

## The board
| Area | Fact | As of | Source | Confidence |
|---|---|---|---|---|
| money | Pilot $25K paid | 2026-11-10 | bank, operator | verified-live |

## Players
### Pat (client)
- **Wants (stated):** off the old CRM

## The game
- **ZOPA:** $20K-$30K

## Our line
- **Recommended line:** package

## Candidate moves
| Player | Move | Probability | Our best reply |
|---|---|---|---|
| Pat | silence | 50% | one nudge |

## Open loops
| Item | Owner | State | Due | Source |
|---|---|---|---|---|
| options page | Damian | drafting | 11-13 | deal page |

## Threats
1. Vendor balance lapses.

## Doctrine check
D5 holds.

## Keep private
Our floor.

## Sources
- deal page
"""

MOVES = """# Move log: Pat (Acme)

1. 2026-07-27 · both · Signed pilot · contract · game opens
2. 2026-11-10 · Pat · Paid final $7,500 · operator · pilot closed
"""


class LintTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.d = Path(self.tmp.name)
        (self.d / "POSITION.md").write_text(GOOD)
        (self.d / "moves.md").write_text(MOVES)

    def tearDown(self):
        self.tmp.cleanup()

    def lint(self):
        return position.lint(self.d / "POSITION.md")

    def test_good_passes(self):
        self.assertEqual(self.lint(), [])

    def test_section_order(self):
        text = GOOD.replace("## Threats", "## TMP").replace("## Open loops", "## Threats").replace("## TMP", "## Open loops")
        (self.d / "POSITION.md").write_text(text)
        self.assertTrue(any("sections" in e for e in self.lint()))

    def test_bad_enum_and_confidence(self):
        text = GOOD.replace("slightly-better", "great").replace("verified-live", "sure")
        (self.d / "POSITION.md").write_text(text)
        errs = self.lint()
        self.assertTrue(any("evaluation" in e for e in errs))
        self.assertTrue(any("confidence" in e for e in errs))

    def test_move_gap(self):
        (self.d / "moves.md").write_text(MOVES.replace("2. 2026", "3. 2026"))
        self.assertTrue(any("contiguous" in e for e in self.lint()))

    def test_placeholder(self):
        (self.d / "POSITION.md").write_text(GOOD.replace("Our floor.", "<What must never reach the counterparty>"))
        self.assertTrue(any("placeholder" in e for e in self.lint()))

    def test_snapshot_and_monotonic(self):
        self.assertEqual(position.main(["snapshot", str(self.d)]), 0)
        hist = next((self.d / "history").glob("*.md"))
        text = GOOD.replace("previous: none", f"previous: history/{hist.name}")
        (self.d / "POSITION.md").write_text(text)  # same as_of -> must fail
        self.assertTrue(any("does not advance" in e for e in self.lint()))
        (self.d / "POSITION.md").write_text(text.replace("09:00:00", "10:00:00"))
        self.assertEqual(self.lint(), [])

    def test_render(self):
        self.assertEqual(position.main(["render", str(self.d)]), 0)
        page = (self.d / "site" / "index.html").read_text()
        self.assertIn("INTERNAL", page)
        self.assertIn("slightly-better", page)

    def test_template_init_is_lint_shaped(self):
        d = self.d / "fresh"
        self.assertEqual(position.main(["init", str(d), "--engagement", "x", "--counterparty", "Y (Z)"]), 0)
        names = [h for h, _ in position.h2_sections(position.split_frontmatter((d / "POSITION.md").read_text())[1])]
        self.assertEqual(names, position.SECTIONS_V1)


if __name__ == "__main__":
    unittest.main()
