# The column contract

Twenty-five columns. Each one exists because a specific way of being wrong about
infrastructure cost is only visible when that column is filled in.

| column | vocabulary | why it earns its place |
|---|---|---|
| `component_id` | slug, unique | the upsert key; `add` and `set` address rows by it |
| `provider` | `aws` `cloudflare` `twilio` `clerk` `gorilladesk` `openai` `resend` `1password` `homelab` | "the cloud bill" is never one bill |
| `account` | free | one provider is several accounts, and only one of them is the project's |
| `service` | free, but stable per provider | the unit the provider actually prices, which is rarely the unit a human names |
| `resource_id` | provider identifier | what `verify` looks up; without it a row cannot be refreshed, only re-read |
| `region` | free | price varies by region and the ledger must not silently mix them |
| `purpose` | one sentence | the thing a reader needs to decide whether it may go |
| `owner` | `automaticai` `client` `shared-operator-tooling` `undetermined` | stops somebody quoting the organization's bill as the engagement's cost |
| `status` | `live` `rollback-only` `deprecated` `idle` | `rollback-only` is the state that has no natural end unless something says so |
| `monthly_usd` | number or empty | the figure that sums. Empty means "not ours to state", never "zero" |
| `monthly_usd_max` | number or empty | **the Aurora column.** What the row costs when the condition holding it down stops holding |
| `cost_basis` | see below | what *kind* of figure this is. A measured $44 and a configured $0 were the same cell before this column existed |
| `unit_rate` | free | the rate and quantity, so the figure can be re-derived rather than trusted |
| `cost_source` | free | the exact API call or bill line behind it |
| `billing_key` | provider usage types, `;`-separated | the provider's own string, so reconciliation is machine-checkable in both directions |
| `cost_window` | free | *which period* a measured figure covers. A "measured" number over nine hours is not a month |
| `last_verified` | ISO date | when a machine last confirmed the row |
| `verified_by` | free | which command wrote it — a hand-edited row and a machine-verified one must be distinguishable |
| `review_by` | ISO date | when a **human** must re-decide. A row past this alarms |
| `introduced_by` | ticket / ADR / "predates …" | which decision created it; a component with no origin is one nobody owns |
| `evidence` | repo path | where that decision was written down |
| `depends_on` | `component_id`s, `;`-separated | teardown ordering, and what else falls over |
| `teardown` | command or a sentence saying why there is none | recorded, **never executed** |
| `teardown_risk` | `safe` `destructive` `blocked` | stops a teardown command reading like an invitation |
| `notes` | free | the sentence a future reader needs and no column can hold |

## `cost_basis`

| value | means |
|---|---|
| `measured` | a bill or a live meter said so; `billing_key` should name the line |
| `list-price` | a measured quantity times a published rate, with no charge posted yet |
| `free-tier` | inside a free allowance, and `unit_rate` names the allowance |
| `included-in-plan` | covered by a subscription this row does not itself pay for |
| `estimated` | modelled, labelled as modelled, with the model named in `cost_source` |
| `client-billed` | a term of the client's own contract; the figure is theirs |
| `out-of-scope` | billed to someone else on a contract this engagement does not hold |

`measured` and `list-price` are deliberately different. A rate read from the
Pricing API multiplied by a duration read from the API is a good number and is
still not a charge anyone has been billed for, and the day those two disagree is
the day the distinction pays for itself.

## `status`

| value | means |
|---|---|
| `live` | serving its purpose right now |
| `rollback-only` | kept solely so a migration can be reversed. **Requires a `review_by`** |
| `deprecated` | superseded, awaiting removal |
| `idle` | provisioned and wired but not carrying traffic |

## The total

Only `owner=automaticai` rows sum. Everything else keeps its figure in its own
row and stays out of the number that gets quoted.

Two totals are always reported: the run-rate (`monthly_usd`) and the ceiling
(`monthly_usd_max`, falling back to `monthly_usd`). The gap between them is the
conditional part of the bill, and the audit names every row that widens it.
