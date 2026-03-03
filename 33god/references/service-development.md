# Service Development

Use this for new event-consumer/producer services and service registration.

## Core principles

- Event-driven, schema-first, single responsibility
- FastStream consumers preferred for RabbitMQ event handling
- Service registration must be updated in the registry source of truth

## Standard flow

1. Define/confirm schema contracts.
2. Scaffold service structure.
3. Implement consumer/producer handlers.
4. Register service + routing in registry.
5. Add tests and run local verification.
6. Validate end-to-end event flow.

If schema contract work is the main task, load:
- `event-command-lifecycle.md`

## Required output

- Service code scaffold + implementation
- Registry entry updates
- Test evidence
- Brief runbook for operations

## Deep references

If needed, load the standalone specialist skill:
- `33god-service-development` (compatibility shim → this reference)
