# Statement lines: the customer face

Hand-written policy (doctrine B15, decision D20, Amendment A5; discounts A1, adjustments A8).
What the client reads on a statement is a few category lines, never a vendor. This page says
which lines exist, how a cost reaches one, when two lines become one, what the label guard
refuses and where a true-up's adjustment lines land. Who bears a cost and what AAI earns on it
are different questions: [pricing.md](pricing.md).

## The catalog

Every client gets the same lines (Story 7.1). A line is a **label**: whatever produced the money
(a usage charge, a fee, an overage, a discount, an adjustment), the client sees the label and
its amount.

| line (label) | order | what lands on it | produced by |
| --- | --- | --- | --- |
| Telephony | 20 | `telephony` and `speech` (voice merges into it) | narrative rules from the seed |
| Cloud Hosting | 30 | `infrastructure` | narrative rule from the seed |
| Platform | 40 | the monthly fee (a retainer, or a `service_fee` labelled Platform) and `platform` usage | the retainer or fee rule; a narrative rule for the usage |
| Inference | 50 | `llm`; inference sold at the gateway list always bills here | narrative rule from the seed; the engine for `--inference-pricing product` |
| Development Costs | 60 | `development` (third-party tooling and compute bought to build the client's system), and one-off costs an operator files here | narrative rule from the seed; a one-off narrative |
| Usage above plan | after the fee lines | a retainer's overage at cost plus the category margin | the retainer rule (`--overage-label`) |
| Included in plan | after the fee lines | a negative line taking back the usage an itemized retainer includes | the retainer rule with `--itemize` |
| Annual prepay discount, Discount | after those | a negative line that reduces fee lines only (never usage, never below zero) | a `discount` rule (A1) |
| MONTH YEAR adjustment: LABEL | last | actual minus projected for one label of a projected month | `ms yrd true-up` (A8) |
| Services | 100 | a cost whose category no narrative rule maps | nothing: the neutral fallback, with an `unmapped_narrative` warning |

Customer lines come in this order: usage lines (by `order`, then label), fee lines (the
Platform fee), a retainer's `Usage above plan` or `Included in plan` line, discount lines, then
adjustment lines. A merged label (below) sits where its first part would. The lines always add
up to the total exactly.

## How a cost reaches a line: narrative rules

A `narrative` rule names the customer line of the bois it matches. Each boi gets at most one
winning narrative: the most specific match (scope, then vendor, then category, then
environment), ties to the newer rule; a revoked rule is ignored. With no winner the boi is
billed on `Services` and `ms shakedown` warns `unmapped_narrative` with the exact command to
add one (an operator picks the label):

- `ms rule add narrative --client $CLIENT --category speech --label Telephony --order 20 --reason "REASON"`
- `ms rule add narrative --client $CLIENT --category development --label "Development Costs" --order 60 --reason "REASON"`
- A single cost filed under another line for one month, as James Brennan's October
  re-transcription loop was filed under Development Costs: a one-off pinned to its scope,
  `ms rule add narrative --client $CLIENT --scope SCOPE_KEY --timing one-off --period YYYY-MM --label "Development Costs" --reason "REASON"`
  (`ms item list --client $CLIENT --period YYYY-MM` gives the scope key).

Timing decides which periods a label change reaches. The seed's rules are `retroactive` (a new
client has nothing issued). For a client that already has issued statements, date the change
forward, or every statement it touches reads `stale_issued` and an operator must supersede it:
`ms rule add narrative --client $CLIENT --category telephony --label Telephony --order 20 --timing forward --effective-from YYYY-MM-DD --reason "REASON"`.
A narrative changes the label only; it never changes who bears a cost or the margin.

Inference sold as AAI's product (`--inference-pricing product`, [pricing.md](pricing.md)) always
bills on `Inference`, whatever narrative matches it, at the catalog order (or the matching
narrative's order).

## The seed template

`seeds/_template.rules.json` holds the catalog's narrative rules and nothing else (Story 7.1):
labels only. Apply it once when a client is onboarded:
`ms rule add --from-file seeds/_template.rules.json --client $CLIENT`.
Bill-to, split, margin, fee and retainer rules are commercial terms and go in the client's own
`seeds/$CLIENT.rules.json`, written from the signed contract ([onboarding.md](onboarding.md)).
A retainer adds `Platform` and `Usage above plan` by itself; nothing in the seed is needed for
them.

## Merging: one label, one line

Usage is grouped by label, so two vendors' Telephony is one line. And a label that more than
one kind of line produces (usage, fee, overage, included, discount) is one customer line too,
whatever produced it (D20, Story 7.1): `platform` usage beside the Platform fee reads as one
amount, at its first part's position. Lines of one kind keep their parts (a fee line per month
of a range, a line per discount), because merging those would change statements already built
and the evidence pack's per-rule attribution.

- The customer view (`ms invoice create --client $CLIENT --period YYYY-MM`) shows the merged line.
- The operator view (`ms yrd build --client $CLIENT --period YYYY-MM --operator`) keeps every
  part, with its boi, rules and arithmetic: internal only, it names vendors and margins.
- The evidence pack (`ms yrd evidence NUMBER --out DIR`) lists a merged line's `parts`.
- Staleness (`stale_issued`) compares summed label totals, so a regrouping that leaves every
  label's total unchanged does not make an issued statement stale.

## The label guard

A customer label never names a vendor (doctrine B15, AD-17). `ms rule add narrative`,
`ms rule add service_fee` and a retainer's labels are refused with
`NARRATIVE_LABEL_LEAKS_VENDOR` when the label contains a registered vendor name or reader slug,
and `ms vendor register` is refused when a new vendor would make an active label leak. A label
that leaks anyway (registered before the guard) is the always-blocking `label_leaks_vendor`
item: an operator revokes the rule and you propose a neutral narrative in its place. Neutral
labels are the catalog's: Telephony, Cloud Hosting, Inference, Development Costs, Platform.

Vendor detail lives in three tiers, never on the statement: the statement (labels only), the
evidence pack on request (`ms yrd evidence`, where the contract requires it; its
`operator.html` is internal and never sent), and the subprocessor inventory (a separate
document).

## Adjustment lines from a true-up

A projected statement ([month-close.md](month-close.md), step 5) is settled after the close by
`ms yrd true-up NUMBER --reason "REASON"` (a plan; an operator applies it). The settlement is
actual minus projected **per customer label**, exactly; a negative line is a credit. Each label
that moved becomes one adjustment line, named for the period it settles and the label it moves:
`October 2026 adjustment: Telephony`. Never a vendor: the label was already guarded.

- `--into next` (the default) carries the lines into the client's first calendar month after
  the period with no active statement; that month's draft (`ms yrd build`) shows them at once.
  A credit larger than that statement is its `NEGATIVE_TOTAL`.
- `--into one-off` issues a separate statement `NUMBER-TU` holding only the adjustment lines
  (never negative: a credit goes `--into next`).
- A settlement whose figures move later (`settlement_drift`) is settled again on top of
  everything already billed; a second one-off is `NUMBER-TU2`.
- An adjustment line is the difference of two priced figures (the actual line minus the line
  billed), so it carries no margin or fee of its own. In `ms portfolio` an adjustment is
  client-borne cost of the period it adjusts, never kept profit.
