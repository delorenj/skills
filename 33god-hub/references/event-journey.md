# Event journey routing

Use the root architecture package for the system view:

- `~/code/33GOD/docs/event-journey.md` — authority, live/target distinction,
  event and command traces, verification evidence, and diagram index.
- `~/code/33GOD/docs/diagrams/33god-event-pipeline.excalidraw` — editable
  Excalidraw source with platform context, focused Plane ingress, event trace,
  and command trace frames.

Then route to the owning skill:

| Boundary | Skill | Canonical reference |
|---|---|---|
| Plane raw-body HMAC and n8n node topology | `delonet-n8n-architecture` | `references/plane-webhook-ingress.md` |
| Bloodbank subjects, schemas, streams, producers, consumers | `bloodbank-integration` | `references/event-journey.md` |
| Project/board identity projection | `33god-projects` | `references/agent-hooks.md` |
| Fleet command routing and Hermes profiles | `agent-fleet-operations` | `SKILL.md` full command journey |
| Plane CRUD and its automatic event side effect | `project-lifecycle` | `SKILL.md` event-side-effect section |
| Provider-neutral task-created triage | `task-triage` | `SKILL.md` canonical event ingress |
| Judgment events beyond mechanical Plane facts | `momo` | `references/decisions.md` |

Do not copy transport details into unrelated skills. Route to the owner so one
contract change does not create a dozen subtly different diagrams.
