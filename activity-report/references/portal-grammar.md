# The portal grammar and the portal row

The body of a report is plain text in a tiny grammar. It is stored as-is in the
Bloodbank event (`report.raw`), in the client portal's `portal_project_updates`
row (`body`), and it is what `render` turns into markdown and HTML. The grammar
is the one the portal's `UpdateBody.tsx` parses, mirrored line for line in
`scripts/ar/render.py`, so the three readers see the same blocks.

## Blocks

Lines are trimmed; blank lines are skipped. Each non-blank line is tested in
this order and the first match wins:

| line | block | merges with the previous line's block? |
|---|---|---|
| `## Heading` | heading | no |
| `- item` or `* item` | bullet list | yes |
| `\| label \| value \|` | metric row | yes |
| `HH:MM text` (1 or 2 digit hour) | timeline entry | yes |
| anything else | paragraph | no |

Consequences worth knowing:

- `# title` inside the body is a paragraph that starts with a hash. The title
  is line 1 of `raw.txt` only; `render.split_raw` removes it.
- A metric row needs exactly two cells; three cells is a paragraph.
- A line that starts with a clock (`09:30 Deployed`) is a timeline entry even
  in the middle of prose. Write `At 09:30 ...` when you mean a sentence.
- Two bullet lists separated only by a blank line are one list.

## Inline

`**bold**` is the only inline form, in bullets, timeline entries and
paragraphs. Headings and metric cells are literal. An unbalanced `**` stays as
text (a half-written body reads badly rather than short); an empty `****` is
dropped. Everything else is literal: no links, no code spans, no HTML. The
lint warns on anything shaped like a tag.

## How each block renders

| block | portal | HTML (`render`) | markdown |
|---|---|---|---|
| heading | `h4` | a new `<section>` with an `h2` | `## Heading` |
| bullets | `ul` | `<ul>` | `- item` |
| metrics | `dl` label/value | tiles when the section is only metrics, `<dl class="kv">` otherwise | a `\| Metric \| Value \|` table |
| timeline | `ol` with clock and dot | `<ol class="timeline">` | `- **HH:MM** text` |
| paragraph | `p` | `<p>` | the line |

The HTML is one self-contained document: `<!doctype html>`, charset and viewport
metas, `<title>`, the stylesheet from `assets/report.css` inlined, no script, no
external asset, no storage. Every string from the report goes through
`html.escape`. The masthead shows the project, `Client update` or
`Internal update`, the title, an audience pill, the window range and its
duration. The internal footer shows the generated time, the window and the run
id; the external footer shows only `Updated <date>`.

## Caps

| | cap | where it comes from |
|---|---|---|
| title | 2 to 180 characters | the portal's `upsertUpdateInputSchema` (`min(2).max(180)`) and the event schema (`maxLength 180`) |
| body | 5000 characters | the portal's `upsertUpdateInputSchema` (`max(5000)`) and the event schema (`report.raw maxLength 5000`) |

A row written past the cap cannot be edited in the admin console. Cut the least
load-bearing detail; never raise the cap.

## The portal row

Adapter `automatic-ai` (`activity_report.portal.kind`), the AutomaticAI client
portal, one D1 table:

```
portal_project_updates (id, project_id, kind, title, body, pinned,
                        visible_to_client, occurred_at, created_at, updated_at)
```

| column | value |
|---|---|
| `id` | `uuid5(NAMESPACE, "<project_id>:<window.end>:<client\|internal>")`, `NAMESPACE = 6f9b1f1e-5d2a-4a3b-9c8d-1a2b3c4d5e6f` |
| `project_id` | `activity_report.portal.project_id` (the portal's project uuid, not the pjangler slug) |
| `kind` | `status` |
| `title`, `body` | `report.title`, `report.raw` (the body only; the title line is not in it) |
| `pinned` | `0` |
| `visible_to_client` | `1` for external, `0` for internal |
| `occurred_at` | `window.end` as epoch milliseconds |
| `created_at`, `updated_at` | now, epoch milliseconds |

The id is deterministic on purpose: a re-run of the same window (a
`Persistent=true` catch-up, a manual re-write after lint refused) overwrites the
row instead of adding a second one. The write is an upsert on `id`, followed by
a read-back that asserts `visible_to_client` is what the audience intended; the
server withholds internal rows from the client, the UI does not, so the flag is
the whole boundary.

Access is the Cloudflare global key over the D1 REST query endpoint
(`X-Auth-Email` + `X-Auth-Key`, resolved from `op://DeLoSecrets/Cloudflare/*`
at call time, never on disk). Both scoped tokens fail (one is IP-locked, the
other has no D1 scope), and Cloudflare refuses urllib's default `User-Agent`.

`activity-report portal EVENT --dry-run` builds the row, prints it (body
summarised), and runs one read-only `SELECT` for the id to prove the access
path. `portal: null` in the project config prints `no portal configured` and
exits 0, which is what `run.sh` relies on for projects without a portal.
