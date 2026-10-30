# Card and cash conventions (carried over from the james-brennan `billing` skill)

Policy content carried over from the james-brennan `billing` skill, retired in Story 10.4 (the
Mercury operating policy that predates Milkshake; its `billing/v1` push and ledger scripts went
with it), kept here because it decides what the readings mean
and what an operator should do about them. `ms` never moves money and never changes a card:
these are the rules the people who run Mercury follow, and what you check when a figure looks
wrong. Mercury is **cash truth with holes**: it has no AWS line (AWS goes through AutomaticAI's
org payer), the IO credit card is one opaque monthly autopay, and a declined charge counts
retry attempts rather than debts. Milkshake's accrual (bois) and Mercury's cash are always
reported side by side (`ms reconcile`) and never summed.

## Virtual cards: one merchant-locked card per recurring vendor

- Name it `<scope>-<vendor>-<phase>`: client-serving as `jimb-deepgram-ops`, internal as
  `aa-github-dev`. The card name is then a self-describing label in the Mercury dashboard and
  in any card-level drill-down.
- Merchant-lock it to that vendor. A locked card makes a mis-charge structurally impossible: a
  Telnyx charge attempted on the Cloudflare-locked card failed correctly, and that is the
  system working, not an incident to fix.
- Set the spend limit at three times the vendor's peak monthly spend or more, and revisit it
  after any month that came within 20% of the limit. A limit that protects against a runaway
  key must not bite on legitimate monthly volume (the OpenRouter declines of USD 21.10, twice,
  were limit bites).
- Per-vendor cards keep per-vendor granularity in the checking feed. A vendor on its own debit
  card means the feed stays attributable and the opaque-autopay problem cannot grow.

## Credit versus debit

- Client-serving operational vendors go on **debit virtual cards only**. Their per-vendor lines
  are the raw material of the margin and of `ms reconcile`; on the IO card they would sink into
  one monthly `Mercury Credit` autopay nobody can decompose.
- The IO credit card is for **operator and development spend only**, where one monthly autopay
  line is acceptable granularity. Pay it in full every month: interest on a carried balance is
  not a cost anyone wants to explain.
- Owner funding in and draws out are equity movements, never revenue or cost.

## What a Mercury reading in `ms` means

- `ms reconcile` shows cash settled against accrued bois per vendor and flags the gaps: AWS
  invisible to Mercury, the IO-card lump, prepaid top-ups (an OpenRouter or Deepgram balance
  recharge is a payment, not a month's usage), and declined retries.
- **A refused charge is an incident, not a footnote.** A vendor that cannot collect cuts
  service (Deepgram retried seven times against USD 5.14 in October before anyone looked).
  Tell an operator the same day; a declined count is attempts, so check the vendor's own invoice
  before concluding it was owed twice.
- Keep the checking balance at or above one month of committed operating cost plus any
  refused-unpaid balance.
- Payment of a statement is read from Mercury **cash** (`ms yrd payment`): a settled incoming
  credit that names the number, or a wire from the client for exactly the total after the issue
  date. The Mercury AR invoice's own status is never the source (`ms yrd deliver` raises that
  AR sidecar, by an operator only).

## Who raises the invoice

The statement is raised monthly by a **human**: `ms yrd issue --client $CLIENT --period YYYY-MM --apply`,
and if an AR sidecar is wanted `ms yrd deliver NUMBER --rail mercury --apply`, `--send-email` only
as a deliberate act. Never a timer, a cron job or an agent: creating a real invoice to the client
is a deliberate act. Daily figures (squeeze, the audit) keep the close from being a surprise; the
statement itself is monthly because the fee is monthly.
