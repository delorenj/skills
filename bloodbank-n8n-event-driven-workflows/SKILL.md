---
name: bloodbank-event-system
description: Use this skill when facilitating communication between different systems in the 33GOD ecosystem. Every action in the pipeline is invoked by an event published by Bloodbank. Simiarly, every result is published as an event to be consumed by any system interested in it.
---

# Bloodbank Event System

Bloodbank is the event bus for the 33GOD ecosystem. It allows different systems to communicate with each other in an event-driven manner. It's designed to facilitate loose coupling between services, enabling scalability and flexibility.

## Architecture

- Each component in the pipeline is responsible for defining its own payload using Pydantic2 and adding the definitions to Bloodbank.
- Each event consists of a payload with optional metadata. The payload is wrapped in a common envelope that includes metadata such as event type, timestamp, and source.
- RabbitMQ is used as the event bus. It handles the routing of events between producers and consumers.
- Events are immutable messages that let us know something has happened in the system. Their key always follow the pattern `<eventType>.<entity>.<past-tense-action>`, for example, `github.pr.created`.
- Events that result in a mutation are Command events. Unlike basic events, they have their own exchange and are bound to the appropriate worker queue(s). Command events follow the naming convention `<eventType>.<entity>.<action>`, for example, `github.pr.merge`.

## Infrastructure

RabbitMQ is used as the event bus. It is

### Event Inventory

The number of events in the system is always growing as new features and integrations are added. You can get a complete list of events and their payload definitions by running the Bloodbank CLI command:

```bash
bloodbank list-events # Returns a list of all events in the system

# To only list commands you can use:
bloodbank list-events --type command

# or for convenience:
bloodbank list-commands

```

To print the schema for a specific event, use:

```bash
bloodbank show [event-key]
```
