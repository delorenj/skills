---
pipeline-status: new
---
# Worked example — JobHunting (the first live domain)

The reference deployment. Lives in the DeLoDocs vault:
`Projects/JobHunting/.curator/{taxonomy.yaml,TRIAGE.md}` + Hindsight bank `jobhunting`.

## The domain

- **Entity = company/opportunity.** Folders are one-per-opportunity (`Asana/`, `Closure/`,
  `Citi-AI-Lead-SVP/`, …) plus a `Recruiters/<Agency>/` subtree and a `_triage/` intake lane.
- **Types (folder-curator categories):** `invites` (calendar/scheduling), `correspondence` (email
  threads + call transcripts), `application` (posting/brief/resume/cover-letter/answers/outreach),
  `intel` (company research + interview prep), `dropbox` (ingest/review).
- **Sub-rule = recruiter vs in-house.** The tell is textual: an in-house rep speaks as *"we / here at
  <Company> / we're hiring"*; a recruiter references *"my client"* or names an agency (Talener, 680
  Partners). Recruiter comms route under `Recruiters/<Agency>/`; in-house comms into `<Company>/`.

## Entity detection order (Layer 2)

1. Exact match to a known folder/alias in `domain.entities`.
2. Sender/attendee mapped via `domain.contacts` (e.g. *Landon Marder → Asana*, *Andrew → Talener → Flow*).
3. LLM read of the content (subject line, letterhead, who is speaking).
4. Unknown → park in `_triage/` at `confidence: low`. **Never guess a company.**

First contact from a new company opens a new `<Company>/` folder (e.g. Babylist, Anthropic, Wonder
were created this way from tailored-resume drops).

## Worked signals

- `Asana/…intro-call.md` — transcript; **Landon Marder**: *"we're hiring here at Asana"* →
  `company: Asana, contact-type: in-house-hr, kind: transcript` → `Asana/`.
- `Flow/Gmail - Andrew at Talener…pdf` — **Andrew @ Talener** (agency) prepping the **Flow** role →
  `company: Flow, contact-type: recruiter` → `Recruiters/Talener/` (label `company: Flow`).
- A screening-call transcript where the hiring company is never named → **parked** in `_triage/` as
  `company: unknown, contact-type: recruiter, needs-company-id` — the honest-park behavior, not a guess.

## Recency in action

The bank carries: *"a burst of captures tied to one company = an active interview pipeline there."*
Recalling it before typing a new Asana-linked file biases detection toward Asana and flags it as likely
interview logistics/prep — narrowing the field before the file is even read. This is why the domain has
its own bank rather than relying on a generic one.

## Known deployment note

folder-curator's `plan` is reliable on the PDF filenames; it currently crashes on `.md` files whose
frontmatter carries a date (see gotchas). For those, Layer 2 classifies from content directly — the
agent path the domain uses anyway.
