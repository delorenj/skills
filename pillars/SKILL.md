---
name: pillars
description: Pillars are acceptance criteria for decisions. Use when making, recording or justifying a judgement call on Jarad's or a client's behalf (approach, scope, tool or vendor choice, trade-off), when authoring or reviewing PILLARS.md at global, repo or client scope, or when someone asks what a pillar is or how decisions get measured.
---

# Pillars: acceptance criteria for decisions

## The model

Picture the work as a graph. **Requirements (states) are nodes**, and acceptance
criteria are predicates on a node: you check after the fact whether you have
arrived. **Decisions are edges**, the move chosen from a node among several
possible ones. AC can't judge an edge, because several edges can reach a node
that passes. A **pillar** is the predicate on edges: it is checked before or at
the moment of choosing, and it is comparative ("given A and B, which does this
pillar prefer?").

| | Acceptance criteria | Pillars |
|---|---|---|
| Judges | a node (an outcome) | an edge (a choice) |
| When | after, as verification | before or during, as the basis of the choice |
| Shape | pass/fail on one artefact | a preference across alternatives |
| Evidence | a test or demo | a decision record that cites pillar slugs |

A single pillar does not have to be absolute: two can pull against each other.
Naming that tension and saying which pillar wins is the decision.

## Scopes and precedence

1. **Global**: `~/.agents/PILLARS.md`. Jarad's universal positions, for every
   agent and every project.
2. **Repo**: `<repo>/PILLARS.md` at the repo root. What this project is for.
   `.momo/pillars.md` is a legacy location; make it a symlink to `PILLARS.md`.
3. **Client**: a Genesis client's charter pillars (the client's own pillars plus
   AutomaticAI's pillars for that client). They govern decisions taken for that
   client.
4. **Role**: doctrine that travels with a skill, such as Momo's process pillars in
   `skills/momo/references/pillars.md`.

Narrower scope wins on product intent and scope. Wider scope wins on how Jarad
operates and on safety and honesty. A client pillar never overrides a client's
explicit instruction, and nothing overrides credential hygiene or "ask before an
outside effect" where a client pillar sets it.

## Format

Each pillar is a bullet with:

- a stable kebab-case **slug** (it is what decisions cite, so never rename one);
- a **statement**, in the owner's words where possible;
- a ***Test:*** line, a question you can hold two options against. If you can't
  write a test that separates realistic options, it isn't a pillar yet ("be
  excellent" fails).

Keep a scope to about 5 to 9 pillars. Too many and it stops working as a compass.
Never invent an owner's pillar. Propose one, mark it as a proposal, and cite the
source of anything you add.

## Using pillars in a decision

1. Name the decision in one line, and the realistic alternatives (at least two).
2. Load the pillars for every scope that applies. Pick the 1 to 3 that actually
   bear on this decision.
3. Run each one's test against the alternatives. If two disagree, say which wins
   and why, using the precedence above.
4. Act. Don't park a reversible decision waiting for sign-off.
5. Record it where the project records decisions, such as the commit message, a
   doc's decision note, or Momo's `record-decision.py --basis "<slugs>"`. A
   record is: decision, alternatives, chosen, basis (slugs), one line of
   reasoning.

A decision record with a basis is to a decision what a passing AC check is to a
requirement: the evidence that it met the bar.

## Maintaining

- Global pillars change only from Jarad's own statements. When he states a new
  universal position, add it with its source and a test, then commit and push
  `~/.agents`.
- When a decision turns out wrong, check whether a pillar was missing, too vague
  to test, or cited badly, and fix that pillar.
