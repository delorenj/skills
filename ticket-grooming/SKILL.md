---
name: ticket-grooming
description: >-
  Use when grooming one Plane ticket in place for delegation.
---

# Ticket grooming

One existing ticket, improved in place. Never create, split, or decompose it;
never change its state; never do the ticket's work. `lifecycle:triaged` is the
pipeline's completion marker — add it LAST and only if the pass finished.

## Procedure

1. Read the repo's `.project.json` (board binding, any
   `activity_report.board.exposure_labels` declaration) and the board's own
   schema: `px schema export -f /tmp/<board>-schema.json --json` returns
   states, labels, modules and feature toggles.
2. Read the ticket and its neighbours: `px show <ref> --json` for the target,
   `px task list --json` plus targeted `px show` for the tickets around it.
   The groomed neighbours define the description shape (section headings),
   priority conventions and facet labels. Agree with the board rather than
   inventing a parallel vocabulary. An ungroomed ticket often arrives in a
   batch minted seconds apart — one review round files several follow-ups at
   once, and the batch-mates are as thin as the target. Take house conventions
   from the most recently *groomed* ticket on the board, never from the
   ungroomed siblings.
3. Ground the description in the repo. Before expanding a thin description,
   read the source, seed and config files the ticket names so the acceptance
   criteria state the mechanism the code actually implements — including what
   is explicitly out of scope, which the author's one-line summary usually
   omits. Keep the author's meaning; never infer a mechanism you did not read.
   Two fast grounding routes: review-filed tickets quote test names and
   assertion strings verbatim — grep the tree for those exact strings to find
   the failing sites; and when the ticket cites an artifacts directory
   (`artifacts/<round>/<ticket>/`), the review documents there are the primary
   evidence — cite their exact failure modes with file:line rather than
   paraphrasing the author's summary. When the ticket is one of a batch, name
   the sibling follow-ups in the description's boundaries so the delegate does
   not absorb their scope.
   If you genuinely cannot tell what the ticket means, comment asking for the
   detail you need instead of guessing.
4. Decide the fields against the board's own rules:
   - Facet labels (bare words such as `bug`, `feature`) only from the board's
     existing label set.
   - Exposure label only when `.project.json` declares the
     `activity_report.board.exposure_labels` axis AND the ticket genuinely
     belongs in front of that audience; most tickets get neither, and neither
     is the default.
   - Priority, module, cycle, start date: follow the board's rules and the
     neighbours' practice. Leave priority `none` and dates unset where the
     sibling tickets are unset.
5. Write the description (and any field updates) through the local
   plane-mcp-server stdio route: `workitem(action="update")` accepts
   `description_html`, `start_date`, `priority`, and `parent` in one call.
   Write the HTML to a temp file first, run it with the checkout's venv python
   under `env -u PYTHONPATH -u PYTHONHOME -u VIRTUAL_ENV`, and pass the bound
   board UUID as `project_id` on every call (see project-lifecycle).
6. Change labels one at a time via the same route
   (`workitem(action="manage_label")` with `add_label_id`/`remove_label_id`) —
   never rewrite the whole label list, and never touch `agent:working`.
7. Post the audit comment (`px comment <ref> -m ...`) before the completion
   marker. Shape: what was verified against the repo and artifacts (with
   file:line), the description shape applied, every convention applied WITH
   its rationale (label, priority, and each deliberate non-assignment — no
   exposure/cycle/module/start date), and what was left untouched (state,
   title, assignees, parent, `agent:working`). The next grooming pass on the
   board reads this comment to stay consistent, so the rationale matters more
   than the list.
8. Verify with the bound read (`px show <ref> --json`). Trust
   `description_html` length; `description_text` can come back empty even when
   the write landed.
9. Add `lifecycle:triaged` last. If you had to stop and ask a question instead,
   do not add it.

## Pitfalls

- The local server's `label(action="list", project_id=...)` returns a
  paginated `{"results": [...]}` object, not a bare list — iterate `results`,
  never the envelope, or the parser dies mid-pass.
- `agent:working` is the pipeline's lease: it appears while your turn runs and
  clears itself. Never add or remove it by hand.
- A board with no cycles, no modules and no exposure labels is normal. Do not
  invent any of them merely to complete a one-ticket pass.
