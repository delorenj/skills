# Provisioning Agents

## Workflow: Add agent workspace to git

Agent workspaces are tracked in git. Follow this standard procedure (as demoed for agent `Gershon` in workspace `workspace-gershon`):

```sh
gh repo create YIC-Triumph/agent-oc-gershon --private -d "GershonBot agent, OpenClaw Runtime Implementation"
cp ~/.openclaw/workspace.gitignore .gitignore
git add -A
git commit -am "Initial commit"
git remote add origin git@github.com:YIC-Triumph/agent-oc-gershon.git
git push -u origin main
```
```
