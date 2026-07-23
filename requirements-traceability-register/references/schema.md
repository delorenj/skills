# Register Schemas

Every column of every sheet. The phase-register schema is the source of truth; all other sheets derive from it. Column letters assume the first data column is `A`.

## Phase Register (P1/P2/P3 Requirements) — 21 columns

The only sheets a human types into. Identical schema across all phases.

| Col | Field | Group | Input | Example |
|---|---|---|---|---|
| A | Requirement ID | Identification | free (stable key) | `P1-ARCH-001` |
| B | Ticket Key | Identification | free | `ACME-123` |
| C | Ticket Title | Identification | free | `Provision auth service` |
| D | Phase | Categorization | dropdown → Phase | `P1` |
| E | Phase Gate | Categorization | dropdown → Phase Gate | `Not Started` |
| F | Workstream | Categorization | free | `Platform` |
| G | Category | Categorization | dropdown → Category | `Architecture` |
| H | Ticket Type | Categorization | dropdown → Ticket Type | `Story` |
| I | Priority | Triage | dropdown → Priority | `P0` |
| J | Status | Triage | dropdown → Status | `Proposed` |
| K | Owner Role | Triage | dropdown → Owner Role | `Backend` |
| L | Requirement Statement | Definition | free | `The system shall …` |
| M | Acceptance Criteria | Definition | free, newline-separated | `Invalid password shows error` ⏎ `SSO redirects correctly` |
| N | Dependencies | Traceability | free, comma-separated IDs | `P1-ARCH-002, P1-SEC-004` |
| O | Trace Tags | Traceability | free | `#login #oauth` |
| P | Source Document | Traceability | free | `Kickoff notes.pdf` |
| Q | Source Location | Traceability | free | `p.4 §2.1` |
| R | Bug Link(s) | Execution | free | `ACME-501` |
| S | Test Case ID | Execution | free | `TC-014` |
| T | Test Evidence | Execution | free | link/screenshot |
| U | Notes | Execution | free | — |

## Lists (validation source)

One column per dropdown; values start at row 2. The scaffolder also generates a `Phase` column (`P1`…`Pn`). Data validation on the phase registers points at these ranges (absolute refs).

| List | Values |
|---|---|
| Status | Proposed, In Progress, Blocked, In Review, Done, Deferred, Cancelled |
| Priority | P0, P1, P2, P3 |
| Owner Role | Product, Architecture, Backend, Frontend, QA, DevOps, Design, Data |
| Ticket Type | Epic, Story, Task, Spike, Bug |
| Category | Architecture, Feature, Infrastructure, Security, Performance, Documentation, Testing |
| Phase Gate | Not Started, In Progress, Passed, Failed |
| Phase | P1, P2, P3, … (one per register) |

Tune these to the project — they exist to prevent typos so Dashboard metrics stay correct.

## Source Map

Answers "why are we building this?" — one row per originating artifact.

`Source ID` · `Source File` · `Used For` · `Local Path` · `Notes`

## All Requirements (master, formula-only)

Same 21 columns as a phase register, populated by the aggregation formula (see [formulas.md](./formulas.md)). Never typed into. Search, filter, and pivot the whole project here.

## Traceability (formula-only)

Lifecycle view. `AC Count` is computed from the Acceptance Criteria cell.

`Requirement ID` · `Phase` · `Workstream` · `Ticket Key` · `Ticket Title` · `Priority` · `Status` · `Dependencies` · `AC Count` · `Test Case ID` · `Bug Link(s)` · `Source Document` · `Source Location`

## Acceptance Matrix (formula-seeded, then filled)

One row per **testable criterion** — the granular breakdown of each requirement's Acceptance Criteria cell.

`AC ID` · `Requirement ID` · `Phase` · `Workstream` · `Acceptance Criteria` · `Test Method` · `Evidence Expected` · `Status` · `Source Document` · `Source Location`

## Dashboard (formula-only)

Executive summary reading from `All Requirements` and `Acceptance Matrix`. Components:

- **Metric cards** — Total Requirements, Open (not Done), Done, Blocked.
- **Priority breakdown** — count of P0 / P1 / P2 / P3.
- **Per-phase summary** — row count and status mix per phase.
- **Navigation** — links to each tab.

Formulas for every card are in [formulas.md](./formulas.md).
