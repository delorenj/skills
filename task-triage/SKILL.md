---
name: task-triage
description: Scope explicitly requested backlog work or handle a verified Plane task-ingress event. Use for triage or story creation; ordinary nontrivial tasks do not trigger ticket creation.
---
# Task triage

Resolve the project, requested outcome, and current task before decomposing it.
For an event handler, verify `bloodbank.repo.task.created` provenance, including
`data.provider_event_type=plane.ticket.created`, board ID, and repository identity.
Creation alone does not establish the ticket's current lane. Board mapping comes
from `.project.json` enrollment (the pjangler registry, which wins) merged with
the shared Hermes registry. See `bloodbank-integration` for transport and
`board-taxonomy` for state and labels.

Keep a small task whole. Split only independently deliverable outcomes or a
concrete dependency boundary; stop when acceptance is executable. Do not recurse
to an arbitrary depth or produce a generic subtask document for every request.

If ticket creation is requested, check duplicates and use `project-lifecycle`
for bounded writes and readback. Create with `px task create`; never publish the
`repo.task.created` fact yourself, the Plane webhook does. A request for analysis returns analysis unless
creation is already authorized. Use `momo` only for requested board execution.
