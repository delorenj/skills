# Product Requirements Document: Bloodbank Event System

## 1. Introduction

This document outlines the product requirements for the Bloodbank Event System, a centralized event bus for the 33GOD ecosystem. Bloodbank facilitates communication between different systems in a decoupled, event-driven manner, enhancing scalability and flexibility.

## 2. Goals

*   To provide a reliable and scalable event-driven architecture for the 33GOD ecosystem.
*   To enable seamless communication between different services without creating tight couplings.
*   To offer a user-friendly Command Line Interface (CLI) for managing and inspecting events.

## 3. User Personas

*   **Software Engineer:** Developers who need to integrate new or existing services into the 33GOD ecosystem. They will use Bloodbank to publish and subscribe to events.
*   **DevOps Engineer:** Engineers responsible for maintaining the infrastructure of the 33GOD ecosystem. They will monitor the health and performance of the Bloodbank system.
*   **System Architect:** Architects who design the overall structure of the 33GOD ecosystem. They will leverage Bloodbank to design scalable and resilient systems.

## 4. Features

### 4.1. Event-Driven Architecture

*   **Event Bus:** Utilizes RabbitMQ as the underlying message broker for event routing.
*   **Event Envelope:** All events are wrapped in a common envelope containing metadata such as event type, timestamp, and source.
*   **Pydantic Integration:** Event payloads are defined using Pydantic V2, ensuring data validation and schema consistency.
*   **Event Naming Convention:** Events follow a standardized naming convention: `<eventType>.<entity>.<past-tense-action>`.
*   **Command Events:** Special events for mutations, with their own exchange and worker queues. Command events follow the naming convention `<eventType>.<entity>.<action>`.

### 4.2. Command Line Interface (CLI)

The Bloodbank CLI provides tools for interacting with the event system.

*   **`bloodbank list-events`**: Lists all available events in the system.
    *   `--type <type>`: Filters events by type (e.g., `command`).
*   **`bloodbank list-commands`**: A convenient alias for `bloodbank list-events --type command`.
*   **`bloodbank show <event-key>`**: Displays the schema definition for a specific event.

## 5. Technical Details

*   **Message Broker:** RabbitMQ
*   **Schema Definition:** Pydantic V2
*   **CLI:** To be implemented in Python (or another suitable language).

## 6. Future Considerations

*   **Event Replay:** The ability to replay historical events for debugging or recovery purposes.
*   **Event Analytics:** A dashboard for visualizing event flow and system performance.
*   **Schema Registry:** A centralized registry for managing event schemas.
