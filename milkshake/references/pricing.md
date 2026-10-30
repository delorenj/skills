# Pricing: how AutomaticAI bills

Hand-written policy (doctrine B14-B17, decisions D18-D20 and D24, Amendment A5). It tells you
what to **propose**; every pricing rule is an operator's decision recorded with a reason, and the
contract guard (`pass_through_markup`) always wins over this page. What the client reads (the
lines) is [statement-lines.md](statement-lines.md).

## The stance

- We bill to make money, not just to recover cost. A client at cost is a recorded decision with a
  reason, never a default you accept silently.
- For every client-month ask "is AAI earning a defensible margin on each line?" and, when it is
  not, propose the rule that fixes it, with the policy row and its source as the reason.
- Justify a margin from the bands below and lean to AAI's side of the band. Never invent a number
  outside a band; quote the band.
- Proposals reach forward only. A rule that changes a period already billed makes every
  statement it touches `stale_issued`; the policy never asks for that.

## Default markups (on cost), approved 2026-10-27

| policy row (`--category`) | covers | default | band | evidence |
| --- | --- | --- | --- | --- |
| Telephony (`telephony`) | `telephony`, `speech` | 35% (3500 bps) | 25-50% | White-label VoIP resellers report 50-75% gross margin (skyswitch.com, viirtue.com); voice-AI agencies sell "retainer including 1,000 minutes" at about 73% gross margin (callsupplai.com) |
| Cloud Hosting (`cloud_hosting`) | `infrastructure` | 20% (2000 bps) | 15-25% | Managed AWS is priced at 10-25% of monthly spend (opsiocloud.com, cloudbolt.io); we operate the environment, not just resell it |
| Inference (`inference`) | `llm` | 100% (10000 bps) | 50-100% | Our gateway's 2.0 group ratio; AI product guidance targets about 70% gross margin, price = cost / (1 - margin) (getlago.com); OpenRouter's 5.5% is the floor for pure pass-through with no service |
| Development Costs (`development`) | `development` | 20% (2000 bps) | 15-25% | Agencies mark up software and platform fees 20-30% (sidekickaccounting.co.uk) |
| Handling fee (`handling_fee`) | itemized reimbursables | 15% (1500 bps) | 10-20% | Agencies charge 10-20% on pass-through (getholdings.com, agencyacquisitions.io); government cost-plus caps at 10% (15% R&D), the conservative floor |

Basis points are what `--bps` (`ms rule add margin`) and `--margin-bps` (`ms adjust item`) take.
`analytics`, `platform` and `other` have no policy row.

## Choosing the model

1. **Preferred: the hybrid retainer.** A flat monthly **Platform** fee (it pays for monitoring,
   tuning, support, gateway access and vendor administration) that includes a pooled **usage
   allowance** at AAI cost. Usage above the allowance is **overage**, billed at cost times
   (1 + the category markup). Unused allowance is AAI's: no rollover, no credit. The face is the
   Platform line and, when there is one, `Usage above plan`; line items on request through the
   evidence pack (`--itemize` shows them on the statement instead). Options: a 12-month minimum
   term or the annual-prepay discount (a `discount` rule, Amendment A1); a price-adjustment
   clause for vendor increases over 10%.
2. **Fallback, for a client that insists on itemized at-cost billing:** the Platform fee plus the
   15% handling fee on reimbursables. Never stack the handling fee on charges the Platform fee
   already covers, and never stack it with the category markups (one margin per charge).
3. **Flat:** one monthly amount that includes every client-borne charge (a retainer whose
   allowance covers everything). Only when the usage is small and steady.
4. **Inference is a product**, priced at the gateway list in every model (below).

Choose on real numbers, never on a guess: `ms pricing simulate` prices the client's real months
under each model and reports AAI's margin. Size an allowance from `average_usage_cents`.

## The mechanics

**Policy (Story 7.2).** `ms pricing policy show --client $CLIENT` prints every row above with its
sources and the client's overrides. An override is
`ms pricing policy set --client $CLIENT --category telephony --bps 4000 --reason "REASON"`
(`pricing.policy_set`; `--category` takes a policy row or a boi category it prices, such as
`speech` or `llm`); a value outside the band also needs `--outside-band "REASON"`
(`PRICING_OUTSIDE_BAND` otherwise). The same bps again records nothing, even with a new reason.
**A policy changes no charge: rules do.**

**Margins.** One per charge, the most specific matching rule winning; never stacked:
`ms rule add margin --client $CLIENT --category speech --bps 3500 --timing forward --effective-from YYYY-MM-DD --reason "REASON"`.
The handling fee is a client-wide margin:
`ms rule add margin --client $CLIENT --bps 1500 --timing forward --effective-from YYYY-MM-DD --reason "REASON"`.
For one boi only, `ms adjust item --id BOI_ID --margin-bps 2000 --reason "REASON"` (an operator's
price: the audit leaves it alone).

**A Platform fee without an allowance** is a `service_fee`:
`ms rule add service_fee --client $CLIENT --label Platform --amount-cents 50000 --timing forward --effective-from YYYY-MM-DD --contract-ref "REF" --reason "REASON"`.

**The retainer (Story 7.3).**
`ms rule add retainer --client $CLIENT --amount 50000 --allowance 25000 --timing forward --effective-from YYYY-MM-DD --contract-ref "REF" --reason "REASON"`
(cents: USD 500.00 a month including USD 250.00 of usage; add `--itemize` for line items on the
statement). Per calendar month the Yrd fully covers:

- the `Platform` line (a fee line, so a `discount` reduces it);
- matched client-borne usage is absorbed at cost up to the allowance, in `(period_start,
  scope_key)` order; the rest is overage at cost plus the category margin on one
  `Usage above plan` line (the guard suppresses that margin where markup is forbidden; inference
  sold at list is overage at list);
- **credits**: a client-borne credit (a vendor refund, a negative base) first reduces what the
  allowance absorbed. A month absorbs `min(allowance, net matched usage)` and its overage is
  `max(net - allowance, 0)`, priced on the month's netted overage, so net usage inside the
  allowance never takes the client below the Platform fee (no rollover, no credit);
- a part-month build has neither the Platform line nor an allowance;
- **resizing** is one new forward retainer with the same match: it supersedes the older one in
  the months it charges in, and the months before it (and every statement issued for them) keep
  the old terms. Never revoke the old one to resize: that reprices issued statements;
- among retainers with different matches, the most specific absorbs a charge, then the newest.

**Inference is a product (Story 7.5).** Inference runs through our gateway and is priced at its
list (the client's group ratio); the upstream provider cost is COGS in the operator view, never a
customer line, and the providers behind the gateway are never billable rows (D11). An operator
records it with
`ms client set $CLIENT --inference-pricing product --effective-from YYYY-MM-DD --contract-ref "REF"`
(`--contract-ref` is required while the client forbids markup: `CONTRACT_REF_REQUIRED`). From that
date, per boi period, a client-borne llm charge read through a gateway row bills at the
gateway's billed amount (upstream times ratio, to the cent) on the `Inference` line, outside the
guard; no margin rule applies to it. Selling inference also needs it client-borne:
`ms rule add bill_to --client $CLIENT --category llm --to client --timing forward --effective-from YYYY-MM-DD --reason "REASON"`.
Earlier periods, `pass_through` clients and AAI-borne inference are unchanged; inside a retainer's
allowance inference is at cost, overage at list; a projected issue bills the list of the
projected amount. A setting recorded without `--contract-ref` while markup was allowed never
sells inference in a period the client later forbids markup in (the engine bills it at cost
there and the manifest says `uncontracted_product: pass_through`), and the flip to `forbidden`
over such a setting is refused unless it ends it in the same command
(`--inference-pricing pass_through`). `ms client show $CLIENT` lists the setting's history.

## Simulate and suggest (read-only)

- `ms pricing simulate --client $CLIENT --months YYYY-MM..YYYY-MM --model current --model itemized+fee:1500 --model retainer:50000/25000 --model flat:50000`
  prices real months under each model in memory: per model and month the client total, AAI cost
  (client-borne and AAI-borne), AAI margin and margin percent; nothing is recorded. Models:
  `current`, `itemized`, `itemized+policy`, `itemized+fee:BPS`, `itemized+platform:CENTS`,
  `retainer:CENTS/ALLOWANCE`, `flat:CENTS`. The guard is reported (`guard_refuses`,
  `contract_needs`), not applied, so a post-contract model can be priced.
  `average_usage_cents` counts complete months only: a month with a client-borne reading still
  pending (missing, unknown, an estimate, partial or stale) is in `incomplete_months`, never
  counted as low usage.
- `ms pricing suggest --client $CLIENT` lists the commands the policy implies and runs none. Every
  rule it proposes is dated forward (`--timing forward --effective-from D`) and never reaches
  back: for an allowed client D is the first month no active statement covers, never earlier
  than the date markup was allowed; for a forbidden client the contract change comes first and D
  is the first period after the signed instrument (fill it in). For client-borne llm on an
  allowed client it proposes `--inference-pricing product`, not a 100% margin. A retainer sized
  over incomplete months is `provisional` (resolve them with `ms shakedown`, then suggest again);
  with no complete month it proposes none.

## The audit argues our side (Story 7.6)

`ms audit --client $CLIENT --period YYYY-MM` raises `margin_below_policy` when a client-borne
charge earns less than the policy on its billed line (Development Costs is judged at 20% even
when its category is `speech`), with the exact forward `ms rule add margin` per policy line and
the shortfall in cents; for a client that forbids markup it raises one finding naming the
operator's contract change. Inference below policy proposes the product setting, never a margin,
and a price an operator pinned to one boi is left alone. `allowance_mis_sized` flags a retainer
over or under its allowance three closed months running and proposes one forward retainer at the
average. Findings are advice: show them, never run them yourself.

## Contracts decide

- A margin on a client whose contract forbids markup is refused (`GUARD_MARKUP_FORBIDDEN`). Do
  not route around it: no fee in disguise, no second client, no other number. Propose the
  contract change; an operator records it after a signed instrument (or, as for James Brennan,
  a recorded decision), dated the first period after signature:
  `ms client set $CLIENT --pass-through-markup allowed --effective-from YYYY-MM-DD`.
  The flip is its own ledger event; it covers periods starting on that date or later.
- A fee or a retainer for a forbidden client needs `--contract-ref` naming the signed clause.
- The guard is read per boi period: a change never reaches back into periods before it, and a
  superseding version of an earlier period still forbids markup. A margin dated back across the
  flip is therefore suppressed in the earlier periods (the `margin_suppressed_by_guard` item) and can only
  make their issued statements stale; it never re-bills them. Reaching back fails twice.

## James Brennan today (D24)

James Brennan is the dogfood client, priced like any other. His signed pilot terms (Agreement
3.4, SOW 5.2) still read at cost, but Jarad decided on 2026-10-27, on the strength of the
understanding with Jim, that he is billed at the doctrine's markups from 2026-10-01: markup
allowed (seq 4513), Telephony 35% (r4516, r4517) and Cloud Hosting 20% (r4518) margins, October's
re-transcription loop at 20% under Development Costs (r4514, one-off), llm client-borne (r4519)
and sold at the gateway list (`inference_pricing=product`, seq 4515). No Platform fee or retainer
exists yet (Agreement 7, SOW 9). Nothing before October changed.

The recommended next step (decisions Open item 1) is the Managed Platform Agreement: USD 500 a
month Platform fee including a pooled allowance sized with `ms pricing simulate`, overage at the
default markups, inference at list, category-level statements with vendor evidence on request,
effective the first full month after the correction period. That is Jarad's business call; your
job is to have the numbers ready.
