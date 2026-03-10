# Project Creation

Use this when creating a new 33GOD project or importing an existing repo.

> **Quick Start**: Run `pjangler init 33god` for automated setup.
> See `workflows/project-bootstrap-pjangler.md` for details.

## Required assets

- Plane project/board
- Repository
- Lead owner/agent
- Initial docs scaffold (README + GOD/BMAD as applicable)

## Checklist

1. Classify project type: platform infrastructure vs revenue product.
2. Create or clone repo in correct location.
3. Create/verify Plane project and initial backlog.
4. Add docs scaffold:
   - `README.md`
   - `GOD.md` or domain/component linkage
   - BMAD structure if this project uses BMAD
5. Seed first 3 executable tickets.
6. Confirm event contracts needed for the first milestone.

## Project kickoff template

```markdown
## Project: <name>
- Scope: <what it owns>
- Owner: <human/agent>
- Repo: <url/path>
- Plane project: <key/url>
- Initial milestone: <name>
- First 3 tickets:
  1. <ticket>
  2. <ticket>
  3. <ticket>
```
