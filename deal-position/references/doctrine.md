# AutomaticAI deal doctrine

These are the standing rules for how AutomaticAI deals with clients. A position is checked against them in its `## Doctrine check` section. They outrank any analysis in a single run.

**Tune it here.** When the operator corrects a judgement, edit the rule, add a dated line to the changelog at the bottom, and bump the skill's `metadata.version`.

## D1. Every request lands in one of three bins

- **Bug**: something live is broken. We fix it, at no charge.
- **Blocks use**: something live can't be used as it was meant to be. We fix it, at no charge.
- **New feature**: anything else. It goes on a list we price with the client before building.

Answer every request within one business day and say which bin it's in ("fixed, that was a bug" / "on the list").

## D2. Requests go to both partners

The client sends requests to Jarad and Damian together, so nothing falls through and no one person becomes the free help desk. This is a reminder, not a reprimand.

## D3. Roles

- **Damian** reviews everything before it reaches a client. He leads money conversations: offers, options, agreements and collections.
- **Jarad** leads the product: demos, cutover plans, and product news.
- **One sender per message.** No double sends, and no two versions of the same offer.

## D4. Clarity, not guilt

- No apologies, in any client text.
- No family, health or personal finances in front of a client. Let the price carry the need.
- Never present our own sacrifices as weight the client must carry.

## D5. Money mechanics

- **Payment before building.** New work starts when a priced page is signed and the first payment has cleared.
- **Pass-through costs at actual cost, with receipts.** No markup, ever. That is in the contracts.
- **Bill tokens from upstream invoices** (OpenRouter and similar), **never from the gateway ledger.** The ledger carries a group ratio.
- **Pay by automatic ACH or card on file.** Money comes up at package boundaries, not in every product call.
- **Prefer the client's own card on vendor accounts** when a pass-through can be moved.

## D6. Price shape

- **Fixed packages tied to an outcome and a date** beat open retainers when the client's scope keeps moving.
- **A care (maintenance) floor** applies to anything live: running costs plus a monthly fee. Below the floor, hand off cleanly instead of running it for free.
- **Never trade cash price against equity percentage** in the same conversation.
- **Ask for their number once.** Options go out on schedule either way. Don't get into a staring contest.

## D7. Equity and ownership

- **AutomaticAI owns the software it builds**, unless a signed page says otherwise. The client owns their data and customers.
- **No profit share in a client's operating company.** It is unauditable, and it reaches into what they are protecting.
- **Equity in a new platform company is upside only.** It never buys down a cash floor, and we never sign the code over.
- **Contract terms are clarity, not weapons.** Offer licence gaps as something to write down, never as a threat.

## D8. Friendship is a term of the deal

- Every boundary line is said warmly and is backed by a mechanism (a page, a date, an ACH), so it never depends on a mood.
- Walking away is allowed and planned for: a clean handoff, a runbook, the bills moved to the client's card, 30 days' notice. "If we walk away, we walk away as friends."
- **Never discourage requests.** A client who stops asking is leaving.

## D9. Privacy

The position doc is internal. These never appear in client text:

- our floors and BATNAs;
- internal splits and our read of the client;
- strategist memos;
- gateway ratios and internal cost multipliers;
- the partners' personal circumstances;
- the client's private financial statements made in confidence;
- valuations someone floated.

Each engagement row in `engagements.md` can extend this list.

## D10. Evidence

- Measured beats estimated. Live state beats docs. Docs beat memory.
- A number in a client email must trace to a bill, an invoice or a measurement in the position's ledger.

## Changelog

- 2026-11-10: v0.1.0. Doctrine distilled from the James Brennan 11-09 alignment meeting, the partners' boundaries call, and three strategist memos (cash, relationship, asset).
