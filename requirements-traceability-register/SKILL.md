---
name: requirements-traceability-register
description: Scaffold and populate a Requirements Management & Traceability Register — a multi-sheet spreadsheet that tracks project requirements from scoping through execution to acceptance and testing. Use when the user wants a requirements tracker, traceability register or matrix (RTM), acceptance matrix, phase-based requirements workbook, or a requirements dashboard in Google Sheets or Excel — built from a Lists validation tab, per-phase registers (P1/P2/P3) on a shared 21-column schema, an aggregated All Requirements master (VSTACK/QUERY), Traceability and Acceptance Matrix views, and COUNTIFS metric cards. Triggers include requirements traceability matrix, requirements register, acceptance criteria matrix, requirement ID, trace tags, phase gate, requirements dashboard, requirement statement. Do NOT use to author a PRD (use bmad-create-prd), run a Plane/Trello ticket board (use project-lifecycle or momo), or build a Gantt/timeline (use html-timeline-roadmap).
---

# Requirements Management & Traceability Register

Build a spreadsheet that carries requirements from scoping (registers) through execution (tickets/phases) to validation (acceptance/testing), with a live master view and an executive dashboard. Targets Google Sheets and Excel.

## Operating Principle

**Silo data entry by phase; aggregate automatically for reporting.** Each phase register (P1/P2/P3) is a hand-edited sheet on one shared 21-column schema. Every downstream view — All Requirements, Traceability, Acceptance Matrix, Dashboard — reads *from* those registers via formulas and is never hand-edited. This keeps entry fast and readable while reporting stays consistent and scalable. Dropdowns come from one `Lists` tab so metrics never break on typos.

## Quick Navigation

| Your goal | Do this |
|---|---|
| Generate the whole workbook now | Run the scaffolder (below), then open the `.xlsx` or import the CSVs |
| Know the exact columns for any sheet | Read [references/schema.md](./references/schema.md) |
| Get the aggregation / dashboard formulas | Read [references/formulas.md](./references/formulas.md) |
| Adapt lists, phases, or roles | Edit `LISTS` / `--phases` in the scaffolder, or the `Lists` tab |
| Understand the four zones | See "Workbook Map" below |

## Workbook Map

Four zones, in data-flow order:

1. **Foundation** — `Lists` (dropdown values: Status, Priority, Owner Role, Ticket Type, Category, Phase, Phase Gate) and `Source Map` (where each requirement originated: Source ID, Source File, Used For, Local Path, Notes).
2. **Data entry** — `P1 Requirements`, `P2 Requirements`, `P3 Requirements`. Identical 21-column schema; the only sheets a human types into. One sheet per delivery phase keeps each fast and uncluttered.
3. **Consolidation** — `All Requirements` stacks every phase register into one filterable/pivotable master via a single aggregation formula (blank rows removed).
4. **QA + reporting** — `Traceability` (lifecycle view + AC count), `Acceptance Matrix` (one row per testable criterion), and `Dashboard` (COUNTIFS metric cards: totals, open vs. done, priority breakdown, per-phase counts).

## Scaffold It

The scaffolder is the fastest path to a working register. It writes one CSV per tab (dependency-free) and, with `--xlsx`, a single workbook with dropdown validation, the live aggregation, and the dashboard already wired:

```bash
# CSV bundle — import each tab into Sheets/Excel (see IMPORT_ORDER.txt)
scripts/scaffold_register.py --out ./req-register --phases 3 --title "Acme Rebuild"

# Fully wired .xlsx (dropdowns + formulas). Needs openpyxl:
uv run --with openpyxl scripts/scaffold_register.py --out ./req-register --phases 3 --title "Acme Rebuild" --xlsx
```

`--phases N` sets how many phase registers to create; `--title` names the project (used on the Dashboard and in the file name).

## Build By Hand

When scaffolding is not an option (locked-down Sheet, bespoke schema), build in this order — later sheets depend on earlier ones:

1. **`Lists` first.** Define Status, Priority, Owner Role, Ticket Type, Category, Phase, Phase Gate (see [references/schema.md](./references/schema.md)).
2. **One phase register.** Lay down the 21 columns, then attach data validation on the dropdown columns to the `Lists` ranges.
3. **Duplicate** it once per phase (`P1`/`P2`/`P3 Requirements`).
4. **`All Requirements`.** Paste the aggregation formula in `A2` (Google Sheets `QUERY` or Excel `VSTACK`+`FILTER`) — see [references/formulas.md](./references/formulas.md).
5. **`Traceability` + `Acceptance Matrix`.** Pull `Requirement ID` and friends from `All Requirements`; compute AC Count from the newline-separated Acceptance Criteria cell.
6. **`Dashboard` last.** COUNTIFS/COUNTA cards over `All Requirements`, plus a navigation list to the other tabs.

## Conventions

- **Requirement ID** encodes phase + workstream + sequence, e.g. `P1-ARCH-001`. Keep it stable — every other sheet traces back to it.
- **Acceptance Criteria** lives in one cell as newline-separated bullets; `AC Count` and the Acceptance Matrix derive from it.
- **Dependencies** holds other Requirement IDs, comma-separated.
- Downstream sheets are **formula-only**. If you find yourself typing into `All Requirements`, `Traceability`, or `Dashboard`, the wiring is wrong.

## Out of Scope

- **Authoring the requirements themselves** (the PRD, epics, user stories) — use `bmad-create-prd` / `bmad-create-epics-and-stories`. This skill builds the *register*, not the requirement content.
- **Running a live ticket board** (Plane, Trello, Linear, Jira execution) — use `project-lifecycle` or `momo`. The register tracks and traces; it is not the system of record for ticket workflow.
- **Timeline / Gantt / roadmap visuals** — use `html-timeline-roadmap`. The register is tabular, not time-axis.
- **Generic spreadsheet formula help** unrelated to this register structure — answer directly; no skill needed.
