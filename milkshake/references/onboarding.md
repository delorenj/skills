# Onboarding a client

A new client is data, never code (doctrine B1, Story 6.1). Nothing in `src/` names a client:
everything particular to one lives on the ledger (written by the commands below) or in its seed
files under `seeds/`, which are only ever the input of a command. Registering a client, its
vendor rows, its contract terms and its Mercury identity are **operator** steps (the authority
matrix in SKILL.md); an agent prepares the seed files and the plans, and runs the read-only
checks. Rules are recorded by an agent only with an operator's approval.

`$CLIENT` is the new client's kebab-case slug. Run everything through `mise run ms -- ...` so
`op run` supplies credentials.

## 1. The seed files (in the repo, reviewed like code)

Copy the templates and fill them in; they hold account ids, console URLs and credential
variable **names**, never a credential:

- `seeds/_template.vendors.json` to `seeds/$CLIENT.vendors.json`: one row per vendor scope the
  client uses (api rows name their reader; manual rows are recorded each month by hand). Each api
  row names its own credential variable in `options.credential_env`, shaped
  `MILKSHAKE_<NAME>_<FIELD>` and ending in the field the reader needs (`_API_KEY` for Deepgram
  and OpenRouter, `_AUTH_TOKEN` for Twilio, `_ACCESS_TOKEN` for the gateway, `_API_TOKEN` for
  Cloudflare), for example `MILKSHAKE_ACME_DEEPGRAM_API_KEY`. The name must also carry the row's
  reader: it ends in `_<READER>_<FIELD>` (a Deepgram row cannot name
  `MILKSHAKE_ACME_OPENROUTER_API_KEY`) or starts with that reader's own `MILKSHAKE_<READER>_`.
  It is never one of Milkshake's own settings unless that is the reader's own
  (`MILKSHAKE_TWILIO_STAGING_AUTH_TOKEN` for Twilio): `ms vendor register` refuses the Mercury
  key, the Farm token, the ledger password or another vendor's key (`VENDOR_ROW_INVALID`). AWS
  rows name an AWS profile instead. A gateway row carries its `group_ratio` (it prices inference
  sold at list). A row shared with other work before a date carries `dedicated_since`: earlier
  readings are AAI's.
- `seeds/_template.rules.json` is the default statement line catalog (D20: Telephony, Cloud
  Hosting, Platform, Inference, Development Costs), labels only, applied as is with `--client`
  ([statement-lines.md](statement-lines.md)).
- `seeds/$CLIENT.rules.json` holds the commercial terms, written exactly as the signed contract
  says: who bears which category (`bill_to`; anything without a client `bill_to` is AAI-borne
  by default), and what AAI earns (`margin`, `service_fee`, `retainer`), proposed from the
  pricing policy ([pricing.md](pricing.md)). Labels never name a vendor.
- Only for a client the legacy client portal billed: `seeds/_template.legacy.json` to
  `seeds/$CLIENT.legacy.json`, with the portal's client and project ids.

Add each credential's 1Password reference (by item UUID) to `.env.vendors.op` under the same
variable name the row names. It is resolved only into the `ms` process by `op run`.

## Before the second client: give every existing client its Mercury identity

While a client is alone, Milkshake matches its payments by amount against any untagged incoming
wire. Once a second client is registered, untagged cash is never a client's by amount any more
(it could be either's): only a reference match, the client's own Mercury identity or a
`revenue` tag attributes it, and `ms reconcile` and `ms yrd deliver` refuse while more than one
client names no identity (`MERCURY_CLIENT_FENCE`). So **before registering a new client**, an
operator gives every existing client its identity,
`ms client set $CLIENT --mercury-customer CUSTOMER_ID --revenue-counterparty "PAYER NAME"`,
and tags its historical revenue wires (`ms tx list --untagged`, then `ms tx tag` each one), or
its earlier statements read open again on the next `ms yrd payment`. Details:
[cash-books.md](cash-books.md).

## 2. The ordered commands

1. Register the client (**operator**). A client that forbids markup on pass-through cost names
   the clause of its own contract that says so (`CONTRACT_CLAUSE_REQUIRED` otherwise; never
   copy another client's clause):
   `ms client register --slug $CLIENT --legal-name "Legal Name LLC" --billing-contact "ap@example.com" --pass-through-markup forbidden --contract-clause "Services Agreement §4.2"`
   A contract that allows markup is registered `--pass-through-markup allowed` with no clause.
2. Register its vendor rows (**operator**): `ms vendor register --from-file seeds/$CLIENT.vendors.json`
3. Check every api row's credential (**you**; names only, never a value):
   `ms vendor check --client $CLIENT`. Every row should say `ready`; `missing` means the
   variable is not in `.env.vendors.op` (or not injected), `invalid` means an unresolved
   reference or a variable name that does not end in the field it supplies.
4. Add the line catalog, then the contract rules (**you, approved**):
   `ms rule add --from-file seeds/_template.rules.json --client $CLIENT`, then
   `ms rule add --from-file seeds/$CLIENT.rules.json`
5. Price it (**you**, read-only): `ms pricing policy show --client $CLIENT` for the defaults and
   any override, and `ms pricing suggest --client $CLIENT` for the forward-dated rules the policy
   implies (for a client that forbids markup, the contract change first). Once it has a few
   months of history, `ms pricing simulate --client $CLIENT --months 3` compares the models.
   Show them to an operator; record nothing on your own.
   A brand-new client has no complete month, so `suggest` proposes no retainer and `simulate`
   has nothing to price: squeeze and close the first month, then suggest again. Until then the
   operator picks a contract allowance (the fee amount is their business call) and the first
   `allowance_mis_sized` finding revisits it. A fee with an allowance is a retainer rule, in cents
   (**you, approved**): the command is in [pricing.md](pricing.md).
6. If the contract sells inference as AAI's product (**operator**):
   `ms client set $CLIENT --inference-pricing product --effective-from YYYY-MM-DD --contract-ref "REF"`
   and the llm `bill_to` rule that makes it client-borne ([pricing.md](pricing.md)).
7. Its own Mercury identity (**operator**):
   `ms client set $CLIENT --mercury-customer CUSTOMER_ID --revenue-counterparty "PAYER NAME"`
8. Record the tax treatment once the accountant has answered (**operator**):
   `ms client set $CLIENT --tax-treatment confirmed --tax-confirmed-by "Name"`
9. The letterhead is AAI's, shared by every client: `ms issuer show` should list nothing missing.
10. Plan the first squeeze and show it to an operator (**you**):
    `ms squeeze --client $CLIENT --period YYYY-MM`
11. Read what is still missing (**you**): `ms shakedown --client $CLIENT --period YYYY-MM`
12. Only for a client with legacy portal history (**operator** applies it; the plan is yours):
    `ms import legacy --client $CLIENT --source s3 --legacy-file seeds/$CLIENT.legacy.json`
13. The client portal: per-client Farm credentials and invoicer grants are Story 10.3, not built
    yet, so `ms farm push` still reads the one `MILKSHAKE_FARM_TOKEN`. Ask an operator before
    planning `ms farm push --client $CLIENT --period YYYY-MM` for a new client.

From here the client follows [month-close.md](month-close.md) like every other client.
