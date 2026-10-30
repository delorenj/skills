# Cash books: Mercury transactions, tags and categories

Hand-written (doctrine B6, B8, B11, B12; decision D21 and its as-built notes; Amendment A6).
Milkshake records every movement of AAI's bank and card cash and owns what each one is. Cash
describes what happened in the bank; bois and rules decide what a client is charged. **The two
are never summed**: a tag never changes a charge, and a payment never changes a statement.
Flags and `--json` shapes: [commands.md](commands.md). The card conventions behind the feed:
[cards.md](cards.md).

Run every command here through `mise run ms -- ...` so `op run` injects the Mercury key
(`MILKSHAKE_MERCURY_API_KEY`), Jev's virtual key (`MILKSHAKE_JEV_TOKEN`), the category namer's
gateway token (`MILKSHAKE_CATEGORY_LLM_TOKEN`) and, for an operator's push, the write token
(`MILKSHAKE_MERCURY_WRITE_TOKEN`).

## The cycle, in order

| step | command | who |
| --- | --- | --- |
| 1. record the bank | `ms tx sync` (plan), then `ms tx sync --since YYYY-MM-DD --apply` | you, then you with approval |
| 2. the deterministic rules | `ms tx autotag --period YYYY-MM` (plan), then `ms tx autotag --period YYYY-MM --apply` | you, then you with approval |
| 3. Jev for the rest | `ms tx categorize --period YYYY-MM` (plan), then `ms tx categorize --period YYYY-MM --apply` | you, then you with approval |
| 4. what is left | `ms tx list --period YYYY-MM --untagged` | you |
| 5. tag by hand | `ms tx tag TX_ID --client $CLIENT --kind cogs --category speech --line Telephony --reason "REASON"` | you, with the operator's answer |
| 6. new categories | `ms category propose` (plan), then `ms category propose --apply`; `ms category list` | you, then you with approval |
| 7. accept a category | `ms category accept PROPOSAL --reason "REASON"` | operator |
| 8. cash against accrual | `ms reconcile --client $CLIENT --period YYYY-MM` | you |
| 9. write tags to Mercury | `ms tx push --period YYYY-MM` (plan), then `ms tx push --period YYYY-MM --apply` | you (the plan), operator (the apply) |

### 1. `ms tx sync`

The plan names the GETs and calls nothing. `--apply` reads `/accounts` and the all-accounts
`/transactions` feed (credit-card lines one by one) before the ledger transaction opens, and
appends one `tx.observed` per new or changed transaction: integer cents beside Mercury's
decimal text, and the raw JSON (with presigned attachment links dropped: they are bearer
tokens) as an evidence blob. An unchanged re-run appends nothing. `tx.observed` names no client
(it is AAI's bank) and is not announced on Bloodbank. `--since YYYY-MM-DD` limits the window (a creation date); autotag, categorize and push window
by `--period` instead, so the two spellings are not interchangeable.

### 2. `ms tx autotag`: the deterministic rules

The plan lists what the rules decide; `--apply` appends one `tx.tagged` (`source=rule`) per
untagged transaction they decide and never replaces a tag. The rules, in order:

1. money in from a client's own revenue counterparty (`ms client set`, below): that client's
   `revenue`, `client_payment`;
2. the card autopay (the IO card's one monthly lump): a `transfer`, `card_payment`;
3. Mercury's `internalTransfer`: a `transfer`, `internal_transfer`; an `externalTransfer`:
   `owner`, `owner_capital` in or `owner_draw` out;
4. Mercury fees: AAI `opex`, `bank_fees`;
5. the vendor map against the clients' vendor rows **active and dedicated on the transaction's
   UTC day**: one client, that client's `cogs`; none, AAI `opex`; several, an operator's choice.
   A vendor whose rows were registered, changed or retired after that day is left as an
   operator's choice (today's rows are not the ones that served it), so a backfill of a vendor
   registered late is tagged by hand;
6. operator vendors (AAI's own tooling): AAI `opex`, `tooling`.

Only a transaction that moved money needs a tag (not failed, cancelled, reversed or blocked).

### 3. `ms tx categorize`: Jev

Jev (`jev.delo.sh`, the `milkshake` virtual key) decides categories for what the rules say
nothing about; a rule-decided or several-owner transaction is never asked. The plan lists the
transactions it would ask (at most `MILKSHAKE_JEV_MAX_REQUESTS`, default 200), the question-set
version and the thresholds. `--apply` sends one System One request per transaction: what Jev
reads is the counterparty, the bank description, direction and size in cents, the payment and
account kind, the memo and the note (never an id or a card number), and two questions, a
`choice` over every active category with its description and a companion "does any listed
category fit".

| outcome | when | what is recorded |
| --- | --- | --- |
| tagged | the chosen category's probability is at least `MILKSHAKE_JEV_CHOICE_THRESHOLD_BPS` (8000, 80%) **and** the fit is at least `MILKSHAKE_JEV_FIT_THRESHOLD_BPS` (5000, 50%; a clear case answers about 60%) | one `tx.tagged`, `source=jev`: AAI's, the category's kind, the probability as `confidence_bps`, the question-set version and an evidence blob with the state, the exact reply and whether it came from the cache |
| `no_fit` | no listed category fits | one `tx.unfit`; the transaction stays untagged |
| `low_confidence` | Jev is not sure enough | one `tx.unfit`; stays untagged |
| `needs_owner` | the category's money is a person's call (`client_payment`, `refund`) | one `tx.unfit`; stays untagged |

A declined transaction is asked again only when the question set changes (a category added,
accepted or retired). A Jev failure is per transaction and records nothing for it; three in a
row stop the run; a sync or a tag never calls Jev, so Jev being down blocks nothing. Answers are
cached by the state's sha256 and the question set when Milkshake's Redis is configured.

### 4 and 5. What is left, and tagging by hand

`ms tx list --period YYYY-MM --untagged` lists every untagged transaction that moved money as a
`tx_untagged` warning with its exact `ms tx tag` command and, after Jev declined it, why
(`jev: no listed category fits`, `not sure enough`, or the owner needs a person). It is cash
only: it never blocks a statement and is never raised by `ms shakedown`.

Fill the command's UPPER-CASE blanks with the operator's answer and run it:

- a client's cost: `ms tx tag TX_ID --client $CLIENT --kind cogs --category speech --line Telephony --reason "REASON"`
- a client's payment: `ms tx tag TX_ID --client $CLIENT --kind revenue --category client_payment --reason "REASON"`
- AAI's own: `ms tx tag TX_ID --aai --kind opex --category tooling --reason "REASON"`

Exactly one owner (`--client $CLIENT` or `--aai`; `--client ''` is refused, never read as AAI).
Kinds: `revenue`, `cogs`, `opex`, `owner`, `transfer`. The category must be in the catalog
(`CATEGORY_UNKNOWN` otherwise) and the kind must fit it (`TX_TAG_INVALID`): `opex` and `cogs`
fit each other (the same cost, kept by AAI or serving a client), `owner` and `transfer` entries
fit only themselves, and an entry with no kind (`client_payment`, `refund`) fits any. The
newest tag of a transaction wins; the same tag again appends nothing. `--line` is free text
naming the statement line the cash relates to.

### 6 and 7. Categories

The catalog is the built-in categories (the statement categories, `infrastructure`, `telephony`,
`speech`, `llm`, `analytics`, `platform`, `development`, `other`, plus the cash ones
`client_payment`, `owner_capital`, `owner_draw`, `card_payment`, `internal_transfer`,
`bank_fees`, `tooling`, `refund`) overlaid with accepted and retired ones. `ms category list`
shows it, with every open proposal and its accept command; `--all` adds retired categories and
closed proposals.

Jev cannot name a new category. When at least `MILKSHAKE_CATEGORY_PROPOSE_MIN` (default 3)
no-fit transactions of one counterparty have no open or rejected proposal, `ms category propose`
plans a proposal; `--apply` asks the AAI gateway (its own consumer token) to name it and appends
`category.proposed` (`p<seq>`), at most 5 groups per run. Proposing never creates a category.
Only an operator does:

- `ms category accept PROPOSAL --reason "REASON"` (optionally `--name`, `--description`,
  `--kind` to correct the proposal) creates it;
- `ms category reject PROPOSAL --reason "REASON"` closes the proposal;
- `ms category retire NAME --reason "REASON"` takes one off the list;
- `ms category add --name NAME --kind opex --description "DESCRIPTION" --reason "REASON"`
  creates one directly, with no proposal, when a person already knows it is needed.

Names are lowercase words joined by single underscores. Each change makes a new question set,
so the transactions Jev declined are asked again.

### 8. Attribution: whose cash is it

A client's own Mercury identity is an operator's decision:
`ms client set $CLIENT --mercury-customer CUSTOMER_ID --revenue-counterparty "PAYER NAME"`.
One customer id and one payer name belong to one client; a name that contains, or is contained
in, another client's (`Acme` and `Acme Labs`) is `MERCURY_ATTRIBUTION_CONFLICT`.

- **An attributed client** (one that names either): `ms yrd payment` matches its statements by
  amount only to a credit its own payer sent, `ms yrd deliver` raises the AR invoice for its own
  customer, and `ms reconcile` counts only its own cash (what the ledger tags as its revenue,
  plus untagged money in from a payer only its counterparties name).
- **A client that names nothing** keeps the one-customer fence: only AR customers no other
  client claims count, and cash tagged as another client's, or sent by another client's payer,
  is left out.
- **The second-client caveat.** While a client is alone, Milkshake matches its payments by
  amount against any untagged incoming wire. Once any other client is registered, untagged money
  in is never a client's by amount any more: only a reference match (the statement number in the
  memo, always the strongest), the client's own identity, or a `revenue` tag with that client
  attributes it. And while more than one client names no Mercury identity, `ms reconcile` and
  `ms yrd deliver` refuse (`MERCURY_CLIENT_FENCE`). So **before a second client is registered**,
  an operator gives every existing client its identity and tags its historical revenue wires
  (`ms tx list --untagged`, then `ms tx tag`), or its earlier statements read open again on the
  next `ms yrd payment`.
- Only a `revenue` tag with a client pays a statement by amount; a credit tagged as anything else
  (a vendor refund, a transfer) never does (a reference in the memo still does).

`ms reconcile --client $CLIENT --period YYYY-MM` compares Mercury cash with accrued bois per
vendor and reports the gaps (AWS is invisible to Mercury, the card's opaque lump, prepaid
top-ups, declined retries). It appends nothing and **never sums cash with accrual**: the
buckets are a report and change no accrual figure.

### 9. `ms tx push`: write the tags back to Mercury (operator)

The plan (you may run it) lists, per tagged transaction whose newest tag is not on Mercury yet,
the exact `PATCH /transaction/{id}`: Mercury's custom category for the tag (named in words,
`Client Payment`) and the structured note
`<what a person wrote> | ms:client=<slug|aai> kind=<kind> [line=<line>] tag=<seq>`, plus the
categories Mercury lacks. `--apply` is an operator's (`MILKSHAKE_MERCURY_WRITE_TOKEN`, a token
value of its own, never the read key's): it creates the missing categories, reads each
transaction's current note from Mercury just before its PATCH (a person's words are kept as
Mercury holds them, never cut, and our trailing segment is replaced, not doubled), and records
each confirmed write as `tx.pushed`, so a re-run sends only changed tags. A note too long to
keep is refused for that transaction (`MERCURY_WRITE_FAILED`, exit 3, the others go on). A write
whose outcome is unknown (no answer, a 5xx or 408, a created category without an id) is
`MERCURY_WRITE_UNCONFIRMED`, exit 5: stop, an operator looks in Mercury. Only `ms tx push --apply`
ever writes to Mercury's transactions.
