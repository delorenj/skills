---
name: deal-position
description: Maintain "The Position", AutomaticAI's normalized, chess-style snapshot of a client deal. It covers the verified material (money, contracts, product, comms), each player's wants, fears, leverage and BATNA, the game (ZOPA, anchors, signals), the likely next moves and our replies, open loops, risks, and one evaluation with the single most important next move. It also keeps an append-only move log. Use for "run our position again", "update the position / state of play", "where do we stand with <client>", "account for these turn of events", "give me a handoff on the deal", or before any pricing, offer or boundary email to a client. Not for a client-facing update (activity-report) or for a single email draft. The position feeds those; it is never sent to the client.
metadata:
  version: "0.1.0"
  owner: AutomaticAI (Jarad + Damian)
---

# deal-position

**The Position** is the board snapshot of one client engagement. **The move log** is the game record behind it. Every run produces a new position in the same format:

- the previous position is archived;
- the new events are appended as moves;
- the document is linted, rendered, published and landed.

The format is the contract. Downstream agents read it instead of re-deriving the deal from transcripts.

## Files (per engagement)

Each engagement has a `position/` directory:

- `POSITION.md`: the current position (template: [references/template.md](references/template.md)).
- `moves.md`: an append-only move log. Each line is `N. date · player · move · source · effect`.
- `history/<as_of>.md`: every earlier position, never edited.
- `site/index.html`: the rendered page published to S3. It is generated, so `position/.gitignore` lists `site/` and it is never committed.

A new engagement starts with `python3 <skill>/scripts/position.py init <dir> --engagement <id> --counterparty "<Name (Co)>"`.

Where the directory lives, who the players are, and where the evidence lives for each client is in [references/engagements.md](references/engagements.md). A new client gets a row there before its first position.

## Run

0. **Load the context.** Load [references/engagements.md](references/engagements.md) for the engagement. Then read, in this order:
   - the current `POSITION.md`;
   - the tail of `moves.md`;
   - [references/doctrine.md](references/doctrine.md), AutomaticAI's standing rules. **The doctrine outranks a clever analysis.**
1. **Record the moves.**
   - Turn the operator's "turn of events" into numbered moves.
   - Add every other event found since the last `as_of`: new transcripts, emails sent or received, payments, tickets, deploys, offers.
   - A move has a player, a date, a source and its effect on the board.
   - Infer rather than ask. Mark an inferred move `(inferred)`.
2. **Refresh the board.** Re-verify each ledger row against live state where it can be checked: Gmail (read-only), the bank and billing facts the operator states, vendors, tickets, git.
   - Every row carries `source`, `as_of` and a confidence of `verified-live`, `verified-doc`, `inferred` or `stale-suspect`.
   - Live state beats docs. Docs beat memory.
   - A row you could not refresh keeps its old date and drops to `stale-suspect`.
3. **Re-read the players and the game** using [references/analysis.md](references/analysis.md).
   - Use the players' own words with timestamps.
   - Update the BATNAs, the zone of possible agreement (ZOPA) and the candidate moves, with probabilities.
4. **Review adversarially.** Do this before writing. Try to refute:
   - each changed evaluation;
   - each new probability;
   - each number.
   - Check every option and phrase against the doctrine and the private-material list.
   - With multi-agent orchestration available (ultracode, or the user asked), run it as a small workflow, three or four agents: a ledger auditor (structured output), a players-and-game analyst, then a skeptic over the draft. Without it, do the same passes inline.
5. **Write the position.**
   - `python3 <skill>/scripts/position.py snapshot <dir>` archives the current position.
   - Then **Write** the new `POSITION.md` from the template with the Write tool (`_bmad-output/` sidecars fire on Write) and append to `moves.md`.
   - Bump `move` to the last move number. Fill `delta` with what changed in the evaluation and why.
6. **Gate it.** Run `python3 <skill>/scripts/position.py lint <dir>/POSITION.md` and fix it until it passes. The lint checks the frontmatter, the section order, the evaluation and initiative vocabularies, the ledger columns, the move-log continuity, and that `as_of` advanced.
7. **Publish and land.**
   - Run `python3 <skill>/scripts/position.py render <dir>`, then publish `site/` with the `html-artifact-delivery` skill. The slug is `<engagement>-position-<as_of compact>`, a new slug per run.
   - Commit through the repo's normal flow (branch, PR, merge where main is protected).
   - Update the engagement's memory pointer to the new URL.
8. **Report** to the operator. Keep it short:
   - evaluation before → after, and why;
   - the moves applied;
   - the top threat;
   - the single most important next move;
   - open loops that changed owner or state;
   - the URL.

## Rules

- **Internal only.** The position holds private material, our floors and our read on people. Never paste it, or a link to it, into anything the counterparty sees. Client text is derived from it under the doctrine's privacy list.
- **Same sections, same order, every time.** Never drop a section. Write `None this move.` instead.
- **Numbers carry units, a date and a source.** Measured beats estimated, and the doc says which is which.
- **Quotes are verbatim, with file and timestamp.** Fix transcript speaker labels per the engagement row before quoting.
- **Probabilities are calibrated guesses.** They must sum to about 100% across a player's listed moves.
- **No apologies, no hedging prose.** This is a working document for operators and agents.

## Tuning

Every rule here is meant to be tuned to how AutomaticAI deals:

- **When the operator corrects a judgement** (a floor, a doctrine rule, a framing), change [references/doctrine.md](references/doctrine.md) or [references/analysis.md](references/analysis.md) in the same run. Date the change, record it in the doctrine changelog, and bump `metadata.version`.
- **Format changes** go in [references/template.md](references/template.md) and `scripts/position.py` together, and `schema` in the frontmatter is bumped (`automaticai.position/v1` → `v2`). Old positions keep their schema, and the lint accepts each version it knows.
