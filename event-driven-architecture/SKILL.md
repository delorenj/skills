---
name: event-driven-architecture
description: Kafka, RabbitMQ, SQS/SNS, event sourcing, CQRS, saga patterns, dead letter
  queues, and idempotency. Use when designing asynchronous systems, implementing message-driven
  workflows, or building event streaming pipelines.
metadata:
  pipeline-status: new
---

# Event-Driven Architecture

## Overview

This skill covers designing and implementing event-driven systems that decouple services through asynchronous message passing. It addresses message broker selection and integration (Kafka, RabbitMQ, SQS/SNS, NATS), event sourcing and CQRS patterns, saga orchestration for distributed transactions, dead letter queues for failure handling, idempotency patterns, event schema evolution, the transactional outbox pattern, and consumer group management.

Use this skill when building microservice architectures, implementing distributed workflows, decoupling services for independent deployment, handling eventual consistency, or replacing synchronous service-to-service calls with asynchronous events.

---

## Core Principles

1. **Events are facts, commands are requests** - Events describe something that happened (`OrderPlaced`, `PaymentReceived`). Commands request an action (`ProcessPayment`, `ShipOrder`). This distinction drives correct system design: events are broadcast, commands are point-to-point.
2. **Idempotency is not optional** - Messages will be delivered at least once (and sometimes more). Every consumer must handle duplicate messages gracefully. Use event IDs, version checks, or database constraints for deduplication.
3. **Schema evolution without breaking consumers** - Event schemas will change. Use backward-compatible evolution (add fields, never remove or rename). Version schemas explicitly and support multiple versions during migration.
4. **Dead letters are not garbage** - Messages that can't be processed go to dead letter queues. These represent bugs, data issues, or edge cases. Monitor DLQs, alert on growth, and build tooling to replay them.
5. **Local transactions, eventual consistency** - Each service owns its data and processes events within local transactions. Cross-service consistency is eventual, not immediate. Design UIs and workflows to handle this.

---

## Detailed procedures

Read [patterns](references/patterns.md) only for the
matching implementation or diagnosis.

## Message Broker Selection Guide

| Broker | Best For | Ordering | Throughput | Persistence |
|---|---|---|---|---|
| **Kafka** | High-throughput event streaming, log compaction | Per-partition | Very high (millions/sec) | Configurable retention |
| **RabbitMQ** | Task queues, routing, request-reply | Per-queue | High (100k/sec) | Optional |
| **SQS/SNS** | Serverless, AWS-native, low ops | Per-FIFO queue | High (3k/sec FIFO, unlimited standard) | 14-day retention |
| **NATS** | Low-latency, cloud-native, lightweight | JetStream | Very high | JetStream for persistence |

---

## Anti-Patterns

| Anti-Pattern | Why It's Bad | Better Approach |
|---|---|---|
| Dual writes (DB + event) without outbox | Data inconsistency when one write fails | Transactional outbox pattern |
| No idempotency in consumers | Duplicate processing on redelivery | Dedup by event ID in same transaction |
| Event payloads too large (> 1MB) | Slow processing, broker limits | Store data in a service, send reference (claim check) |
| Synchronous event handling | Defeats purpose of async architecture | Process events asynchronously with queues |
| No DLQ configured | Failed messages block queue or disappear | Always configure DLQ with alerting |
| Tightly coupled event schemas | Breaking consumers on schema changes | Backward-compatible evolution, explicit versioning |
| Publishing domain events from multiple places | Inconsistent event shapes, missed events | Single publish point (aggregate root / service layer) |

---

## Checklist

- [ ] Transactional outbox pattern for atomic DB + event writes
- [ ] Every consumer is idempotent (event ID deduplication)
- [ ] Dead letter queues configured with alerting and replay tooling
- [ ] Event schemas versioned with backward-compatible evolution
- [ ] Consumer groups configured for each service
- [ ] Retry policy with exponential backoff before DLQ
- [ ] Saga or choreography pattern for cross-service workflows
- [ ] Monitoring: consumer lag, DLQ depth, processing errors
- [ ] Event ordering preserved where required (partition keys)
- [ ] Message broker cluster is fault-tolerant (replication)

---

## Related Resources

- **Skills:** `monitoring-observability` (consumer lag monitoring), `serverless-development` (SQS/Lambda)
- **Skills:** `payment-integration` (payment event flows), `email-systems` (email as async event)
- **Rules:** `rules/stacks/fullstack-nextjs-nestjs.md` (NestJS CQRS modules)
