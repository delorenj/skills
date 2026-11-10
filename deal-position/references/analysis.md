# Reading the position: an analysis checklist

Use this checklist when you fill in `## Players`, `## The game`, `## Candidate moves` and the evaluation. It is a checklist, not prose to copy into the doc.

## Evaluation scale (always from AutomaticAI's side)

| Value | Meaning |
|---|---|
| winning | The deal we want is signed or certain. Only execution risk remains. |
| better | We hold the initiative, and the most likely outcome is at or above our recommended line. |
| slightly-better | It leans our way, but one of their likely moves would cost us real value. |
| equal | Balanced. The outcome depends on the next exchange. |
| slightly-worse | Their likely outcome is below our recommended line but above our floor. |
| worse | The most likely outcome is near or below our floor. |
| losing | We are working unpaid or heading toward a handoff, and no move recovers it. |

**Initiative** belongs to whoever's next move forces the other to respond: a page sent with a date, a payment, an ultimatum. Silence hands the initiative to the other side.

## Players

For each player:

- **Stated vs underlying wants.** Quote the stated one. Infer the underlying one, and say what the inference rests on.
- **Fears.** Name the fear behind each objection. An objection to price from someone able to pay is usually about risk, not capacity.
- **Constraints.** Cash timing, other commitments, legal entities, deadlines.
- **Leverage.** What each side can withhold or grant: money, code, data, time, reputation, introductions.
- **BATNA.** The best alternative to a deal with us (or with them), concretely: another vendor, the incumbent tool, doing nothing, taking other work.
- **Signals.** Verbatim quotes with file@timestamp. A signal counts more when it costs the speaker something to say.

## The game

- **Type.** A repeated game with a friend has a long shadow of the future. Defection (unpaid work, a hard sell) costs more than it gains. Say so when it applies.
- **ZOPA.** Our floor (from `## Our line`) against their likely ceiling. If there's no overlap, say so plainly. Then the play is a smaller package, not a lower price.
- **Anchors.** List every number already said aloud and who said it. The first serious number anchors. Say whether a high one is helping us or scaring them.
- **Commitment devices.** Deadlines tied to their goals (a cutover date or an acquisition) beat deadlines we invent.
- **Information asymmetry.** What they know that we don't (their cash, their other options), and what we know that they don't (cost, effort, how close a feature is).
- **Focal points.** Numbers or shapes they have already accepted once (a past package price, a past payment schedule) are cheap to agree to again.

## Candidate moves

- List three to five plausible next moves for the counterparty, with probabilities summing to about 100%.
- Give each one our best reply, prepared in advance.
- Include the "nothing happens" move (silence, delay) every time. It is usually the most likely.
- List our own next moves in `## Our line`, not here. This table is for their moves.

## Threats

Rank threats by likelihood × damage. For each, give the trigger, the damage in money or days, and the defusing move with an owner. Operational risks that touch the deal belong here too: a lapsing vendor balance, a live line on someone's personal account, an outage near a decision date.

## Calibration

- When the operator later says what actually happened, add it as a move and compare it with the candidate-move table that predicted it.
- Note any repeated miss here as a dated line, for example "we keep over-estimating speed of reply".

### Calibration log

- None yet.
