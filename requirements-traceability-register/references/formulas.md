# Formulas

Copy-paste formulas for the derived sheets. Two dialects: **Google Sheets** (the workbook's native target) and **Excel 365** (also what the scaffolder bakes into `.xlsx`). Column letters follow [schema.md](./schema.md) (Priority = `I`, Status = `J`, Phase = `D`, Workstream = `F`, Acceptance Criteria = `M`). Assumes 3 phase registers named `P1 Requirements`, `P2 Requirements`, `P3 Requirements` — extend the pattern for more.

## All Requirements — aggregation (cell `A2`)

Stacks every phase register and drops blank rows. Put it in `A2` only; it spills.

**Google Sheets:**
```
=QUERY({'P1 Requirements'!A2:U; 'P2 Requirements'!A2:U; 'P3 Requirements'!A2:U}, "select * where Col1 is not null", 0)
```
The `{ … ; … }` stacks ranges vertically; `where Col1 is not null` removes empty rows. Open-ended `A2:U` (no bottom bound) grows automatically.

**Excel 365 / the `.xlsx` scaffold:**
```
=FILTER(VSTACK('P1 Requirements'!A2:U1000,'P2 Requirements'!A2:U1000,'P3 Requirements'!A2:U1000), VSTACK('P1 Requirements'!A2:A1000,'P2 Requirements'!A2:A1000,'P3 Requirements'!A2:A1000)<>"")
```
Excel has no open-ended ranges, so bound them (e.g. `1000`). In the raw `.xlsx`, openpyxl writes these as `_xlfn.VSTACK` / `_xlfn._xlws.FILTER`; Excel and Google Sheets resolve the prefixes on open.

## Traceability — pull selected columns (cell `A2`)

**Google Sheets** — reorder columns straight from the master with `QUERY`:
```
=QUERY('All Requirements'!A2:U, "select Col1, Col4, Col6, Col2, Col3, Col9, Col10, Col14 where Col1 is not null", 0)
```
(Col1=Requirement ID, Col4=Phase, Col6=Workstream, Col2=Ticket Key, Col3=Ticket Title, Col9=Priority, Col10=Status, Col14=Dependencies). Add `Test Case ID` (Col19), `Bug Link(s)` (Col18), `Source Document` (Col16), `Source Location` (Col17) as needed.

**AC Count** (per row, in the `AC Count` column) — counts newline-separated criteria in the master's `M` column:
```
=IF('All Requirements'!M2="",0,LEN('All Requirements'!M2)-LEN(SUBSTITUTE('All Requirements'!M2,CHAR(10),""))+1)
```
Wrap in `ARRAYFORMULA(...)` over `M2:M` in Sheets to fill the column from one cell.

## Acceptance Matrix — expand criteria to rows

Seed `Requirement ID` + `Acceptance Criteria` from the master, then split the newline-separated AC cell into one row per criterion.

**Google Sheets** (split one requirement's ACs down the rows):
```
=TRANSPOSE(SPLIT('All Requirements'!M2, CHAR(10)))
```
For a full auto-expansion across all requirements, keep it simple: filter `All Requirements` into the matrix, then split each AC cell — or fill `AC ID` (`REQID-AC-01`, `-02`…) by hand as tests are authored. The matrix is where QA adds `Test Method` and `Evidence Expected`.

## Dashboard — metric cards

All over `All Requirements` (`I` = Priority, `J` = Status). `COUNTIFS`/`COUNTIF`/`COUNTA` are classic functions — no dialect differences.

| Card | Formula |
|---|---|
| Total Requirements | `=COUNTA('All Requirements'!A2:A)` |
| Open (not Done) | `=COUNTIFS('All Requirements'!A2:A,"<>",'All Requirements'!J2:J,"<>Done")` |
| Done | `=COUNTIF('All Requirements'!J2:J,"Done")` |
| Blocked | `=COUNTIF('All Requirements'!J2:J,"Blocked")` |
| P0 / P1 / P2 / P3 | `=COUNTIF('All Requirements'!I2:I,"P0")` (swap the label) |
| Rows in phase P1 | `=COUNTIF('All Requirements'!D2:D,"P1")` |
| Acceptance criteria total | `=COUNTA('Acceptance Matrix'!A2:A)` |

In Excel, replace open-ended `A2:A` with a bounded range (`A2:A1000`).

## Gotchas

- **Spill needs empty space.** The aggregation and any array formula error with `#SPILL!` / `#REF!` if cells below the anchor already hold data. Keep downstream sheets empty except the anchor cell.
- **Anchor at `A2`, not `A1`.** Row 1 is headers; the formula fills from row 2 down.
- **Absolute refs for validation.** Data-validation list ranges must be absolute (`Lists!$A$2:$A$8`) or they drift when copied.
- **Blank-row filtering is mandatory.** Without `where Col1 is not null` / the `<>""` include array, empty register rows pollute counts and pivots.
- **Newline is the AC delimiter.** `AC Count`, `SPLIT`, and the matrix all assume `CHAR(10)`-separated criteria in one cell. Enter line breaks with Alt+Enter (Excel) / Ctrl+Enter (Sheets).
- **Excel ≠ open-ended ranges.** Sheets accepts `A2:U`; Excel needs a bottom bound. The scaffolder uses `1000`.
