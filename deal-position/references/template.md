# POSITION.md template (schema automaticai.position/v1)

Copy this file and fill it in. Keep every heading, verbatim and in this order. A section with nothing new says `None this move.`. Text in `<angle brackets>` is an instruction: replace it.

```markdown
---
schema: automaticai.position/v1
engagement: <engagement id from engagements.md, e.g. james-brennan>
counterparty: <person (company)>
as_of: <ISO 8601 with offset, e.g. 2026-11-10T09:30:00-05:00>
move: <number of the last move in moves.md>
previous: <history/<as_of>.md, or "none">
to_move: <us | them>
initiative: <us | them | neither>
evaluation: <winning | better | slightly-better | equal | slightly-worse | worse | losing>
phase: <opening | middlegame | endgame>
next_move: <one line: the single most important next move, with an owner>
delta: <one line: what changed in the evaluation since the previous position, and why>
---

# The Position: <counterparty>, <date>

## Evaluation
<One paragraph, chess-style. Who holds the initiative. What the position favours and why. The single most important next move and who makes it. One sentence on what would change the evaluation.>

## Moves since last position
<Numbered moves applied this run. Each is copied into moves.md with the same number.>

## The board
<The verified material, as one table. Keep the columns in this order.>

| Area | Fact | As of | Source | Confidence |
|---|---|---|---|---|
| <money / contract / product / comms / operations / people> | <fact with units> | <date> | <file:line, command, transcript@timestamp> | <verified-live / verified-doc / inferred / stale-suspect> |

## Players
### <Name> (<role>)
- **Wants (stated):**
- **Wants (underlying):**
- **Fears:**
- **Constraints:**
- **Leverage:**
- **BATNA:**
- **Signals:** <verbatim quotes with file@timestamp>

<Repeat the block for every player: the counterparty first, then each of us.>

## The game
- **Type:** <repeated / one-shot, cooperative / competitive, information asymmetries>
- **ZOPA:** <the range, with numbers; our floor and their likely ceiling>
- **Anchors in play:** <numbers already on the table and who set them>
- **Commitment devices:** <deadlines, contracts, payments, public statements>
- **Relationship terms:** <how friendship and trust change the payoffs>

## Our line
- **Options on the table:** <each with what they get, what they pay, what we commit, and the risk to us>
- **Recommended line:**
- **Walk-away floor:**
- **Boundary language:** <the exact sentences we will use>

## Candidate moves
| Player | Move | Probability | Our best reply |
|---|---|---|---|

## Open loops
| Item | Owner | State | Due | Source |
|---|---|---|---|---|

## Threats
<A ranked list. Each threat: what it is, how likely, how bad, and the move that defuses it.>

## Doctrine check
<Each relevant rule from doctrine.md, marked holds or strained, with one line each. Any strain becomes a threat or an open loop.>

## Keep private
<What must never reach the counterparty from this position.>

## Sources
<Every file, transcript, command and URL this position relied on.>
```

## moves.md format

```markdown
# Move log: <counterparty>

1. 2026-07-27 · both · Signed pilot ($25K) and Rider · engagement/legal/ · game opens
2. ...
```

The rules for the move log:

- Each line is `N. YYYY-MM-DD · player · move · source · effect`.
- Numbers are contiguous and the log is append-only.
- Never renumber.
- A wrong move is corrected by a new move that says so.
