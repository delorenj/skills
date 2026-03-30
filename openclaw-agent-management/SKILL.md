---
name: openclaw-agent-management
description: This skill codifies the standards and workflows for this machine's openclaw agent gateway configuration. Use this skill when provisioning new agents or managing existing ones. Trigger phrases are "add a new agent", "update [agent's name] identity"
---

# openclaw-agent-management

This skill helps define standards for the agents that live in this OpenClaw gateway instance.

> ![!IMPORTANT] MANDATORY RULE
> ONLY READ THE MINIMUM REQUIRED OF THIS SKILL IN ORDER TO SATISFY THE CURRENT TASK

## Main Router

Are you here to:

- Provision a new agent? see [Provisioning](./references/Provisioning.md)

## Agents 

- Each agent is a one-to-one mapping with an existing Triumph team member. i.e. Gershon Herczeg (team lead) --> GershonBot (main agent)

- An agent is one of two possible roles:
  1. Manager: Can delegate to other agents. Does not modify code
  2. Developer: Implements tickets and requests from managers by modifying code or spawning ephemeral subagents. Cannot delegate tasks to other team members/agents

