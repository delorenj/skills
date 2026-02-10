# Letta - Messages

**Pages:** 29

---

## Preview Model Request

**URL:** llms-txt#preview-model-request

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.letta.com/v1/agents/{agent_id}/messages/preview-raw-payload
Content-Type: application/json

Inspect the raw LLM request payload without sending it.

This endpoint processes the message through the agent loop up until
the LLM request, then returns the raw request payload that would
be sent to the LLM provider. Useful for debugging and inspection.

Reference: https://docs.letta.com/api-reference/agents/messages/preview

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Preview Model Request
  version: endpoint_agents/messages.preview
paths:
  /v1/agents/{agent_id}/messages/preview-raw-payload:
    post:
      operationId: preview
      summary: Preview Model Request
      description: |-
        Inspect the raw LLM request payload without sending it.

        This endpoint processes the message through the agent loop up until
        the LLM request, then returns the raw request payload that would
        be sent to the LLM provider. Useful for debugging and inspection.
      tags:
        - - subpackage_agents
          - subpackage_agents/messages
      parameters:
        - name: agent_id
          in: path
          description: The ID of the agent in the format 'agent-<uuid4>'
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                type: object
                additionalProperties:
                  description: Any type
        '422':
          description: Validation Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/agents_messages_preview_Request'
components:
  schemas:
    MessageCreateRole:
      type: string
      enum:
        - value: user
        - value: system
        - value: assistant
    TextContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: text
        text:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - text
    UrlImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: url
        url:
          type: string
      required:
        - url
    Base64Image:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: base64
        media_type:
          type: string
        data:
          type: string
        detail:
          type:
            - string
            - 'null'
      required:
        - media_type
        - data
    LettaImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: letta
        file_id:
          type: string
        media_type:
          type:
            - string
            - 'null'
        data:
          type:
            - string
            - 'null'
        detail:
          type:
            - string
            - 'null'
      required:
        - file_id
    ImageContentSource:
      oneOf:
        - $ref: '#/components/schemas/UrlImage'
        - $ref: '#/components/schemas/Base64Image'
        - $ref: '#/components/schemas/LettaImage'
    ImageContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: image
        source:
          $ref: '#/components/schemas/ImageContentSource'
      required:
        - source
    ToolCallContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_call
        id:
          type: string
        name:
          type: string
        input:
          type: object
          additionalProperties:
            description: Any type
        signature:
          type:
            - string
            - 'null'
      required:
        - id
        - name
        - input
    ToolReturnContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_return
        tool_call_id:
          type: string
        content:
          type: string
        is_error:
          type: boolean
      required:
        - tool_call_id
        - content
        - is_error
    ReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: reasoning
        is_native:
          type: boolean
        reasoning:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - is_native
        - reasoning
    RedactedReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: redacted_reasoning
        data:
          type: string
      required:
        - data
    OmittedReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: omitted_reasoning
        signature:
          type:
            - string
            - 'null'
    LettaMessageContentUnion:
      oneOf:
        - $ref: '#/components/schemas/TextContent'
        - $ref: '#/components/schemas/ImageContent'
        - $ref: '#/components/schemas/ToolCallContent'
        - $ref: '#/components/schemas/ToolReturnContent'
        - $ref: '#/components/schemas/ReasoningContent'
        - $ref: '#/components/schemas/RedactedReasoningContent'
        - $ref: '#/components/schemas/OmittedReasoningContent'
    MessageCreateContent0:
      type: array
      items:
        $ref: '#/components/schemas/LettaMessageContentUnion'
    MessageCreateContent:
      oneOf:
        - $ref: '#/components/schemas/MessageCreateContent0'
        - type: string
    MessageCreate:
      type: object
      properties:
        type:
          type:
            - string
            - 'null'
          enum:
            - type: stringLiteral
              value: message
        role:
          $ref: '#/components/schemas/MessageCreateRole'
        content:
          $ref: '#/components/schemas/MessageCreateContent'
        name:
          type:
            - string
            - 'null'
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        batch_item_id:
          type:
            - string
            - 'null'
        group_id:
          type:
            - string
            - 'null'
      required:
        - role
        - content
    ApprovalReturn:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: approval
        tool_call_id:
          type: string
        approve:
          type: boolean
        reason:
          type:
            - string
            - 'null'
      required:
        - tool_call_id
        - approve
    LettaSchemasLettaMessageToolReturnStatus:
      type: string
      enum:
        - value: success
        - value: error
    letta__schemas__letta_message__ToolReturn:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: tool
        tool_return:
          type: string
        status:
          $ref: '#/components/schemas/LettaSchemasLettaMessageToolReturnStatus'
        tool_call_id:
          type: string
        stdout:
          type:
            - array
            - 'null'
          items:
            type: string
        stderr:
          type:
            - array
            - 'null'
          items:
            type: string
      required:
        - tool_return
        - status
        - tool_call_id
    ApprovalCreateApprovalsItems:
      oneOf:
        - $ref: '#/components/schemas/ApprovalReturn'
        - $ref: '#/components/schemas/letta__schemas__letta_message__ToolReturn'
    ApprovalCreate:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: approval
        approvals:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/ApprovalCreateApprovalsItems'
        approve:
          type:
            - boolean
            - 'null'
        approval_request_id:
          type:
            - string
            - 'null'
        reason:
          type:
            - string
            - 'null'
    LettaRequestMessagesItems:
      oneOf:
        - $ref: '#/components/schemas/MessageCreate'
        - $ref: '#/components/schemas/ApprovalCreate'
    MessageType:
      type: string
      enum:
        - value: system_message
        - value: user_message
        - value: assistant_message
        - value: reasoning_message
        - value: hidden_reasoning_message
        - value: tool_call_message
        - value: tool_return_message
        - value: approval_request_message
        - value: approval_response_message
    LettaRequest:
      type: object
      properties:
        messages:
          type: array
          items:
            $ref: '#/components/schemas/LettaRequestMessagesItems'
        max_steps:
          type: integer
        use_assistant_message:
          type: boolean
        assistant_message_tool_name:
          type: string
        assistant_message_tool_kwarg:
          type: string
        include_return_message_types:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/MessageType'
        enable_thinking:
          type: string
      required:
        - messages
    LettaStreamingRequestMessagesItems:
      oneOf:
        - $ref: '#/components/schemas/MessageCreate'
        - $ref: '#/components/schemas/ApprovalCreate'
    LettaStreamingRequest:
      type: object
      properties:
        messages:
          type: array
          items:
            $ref: '#/components/schemas/LettaStreamingRequestMessagesItems'
        max_steps:
          type: integer
        use_assistant_message:
          type: boolean
        assistant_message_tool_name:
          type: string
        assistant_message_tool_kwarg:
          type: string
        include_return_message_types:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/MessageType'
        enable_thinking:
          type: string
        stream_tokens:
          type: boolean
        include_pings:
          type: boolean
        background:
          type: boolean
      required:
        - messages
    agents_messages_preview_Request:
      oneOf:
        - $ref: '#/components/schemas/LettaRequest'
        - $ref: '#/components/schemas/LettaStreamingRequest'
```

Example 2 (python):
```python
from letta_client import Letta, LettaRequest, MessageCreate, TextContent

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.agents.messages.preview(
    agent_id="agent-123e4567-e89b-42d3-8456-426614174000",
    request=LettaRequest(
        messages=[
            MessageCreate(
                role="user",
                content=[
                    TextContent(
                        text="text",
                    )
                ],
            )
        ],
    ),
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.agents.messages.preview("agent-123e4567-e89b-42d3-8456-426614174000", {
    messages: [{
            role: "user",
            content: [{
                    type: "text",
                    text: "text"
                }]
        }]
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/agents/agent_id/messages/preview-raw-payload"

	payload := strings.NewReader("{\n  \"messages\": [\n    {}\n  ]\n}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Monitoring

**URL:** llms-txt#monitoring

**Contents:**
- <Icon icon="fa-sharp fa-light fa-chart-simple" /> Overview
- <Icon icon="fa-sharp fa-light fa-chart-line" /> Activity & Usage
- <Icon icon="fa-sharp fa-light fa-tachometer-alt-fast" /> Performance
- <Icon icon="fa-sharp fa-light fa-triangle-exclamation" /> Errors

> Track your agent's performance and usage metrics

<img src="file:df814989-4c54-4224-b5cf-be2c8c189505" />

<img src="file:95abe412-fddf-4e7e-ad7b-fc4f9809a0b2" />

Monitor your agents across four key dashboards:

## <Icon icon="fa-sharp fa-light fa-chart-simple" /> Overview

Get a high-level view of your agent's health with essential metrics: total messages sent, API and tool error counts, plus LLM and tool latency averages. This dashboard gives you immediate visibility into system performance and reliability.

## <Icon icon="fa-sharp fa-light fa-chart-line" /> Activity & Usage

Track usage patterns including request frequency and peak traffic times. Monitor token consumption for cost optimization and see which features are used most. View breakdown by user/application to understand demand patterns.

## <Icon icon="fa-sharp fa-light fa-tachometer-alt-fast" /> Performance

Analyze response times with percentiles (average, median, 95th) broken down by model type. Monitor individual tool execution times, especially for external API calls. Track overall throughput (messages/second) and success rates to identify bottlenecks.

## <Icon icon="fa-sharp fa-light fa-triangle-exclamation" /> Errors

Categorize errors between API failures (LLM error, rate limits) and tool failures (timeouts, external APIs). View error frequency trends over time with detailed stack traces and request context for debugging. See how errors impact overall system performance.

---

## No need to send previous messages

**URL:** llms-txt#no-need-to-send-previous-messages

**Contents:**
- Agents as Services
- Persistence by Default
- Self-Editing Memory
- Agents vs Threads
- LLM OS
- Beyond Model Size
- Next Steps

POST /agents/{agent_id}/messages
mermaid
%%{init: {'flowchart': {'rankDir': 'LR'}}}%%
flowchart LR
    subgraph Traditional["Thread-Based Agents"]
        direction TB
        llm1[LLM] --> thread1["Thread 1
        --------
        Ephemeral
        Session"]
        llm1 --> thread2["Thread 2
        --------
        Ephemeral
        Session"]
        llm1 --> thread3["Thread 3
        --------
        Ephemeral
        Session"]
    end

Traditional ~~~ Letta

subgraph Letta["Letta Stateful Agents"]
        direction TB
        llm2[LLM] --> agent["Single Agent
        --------
        Persistent Memory"]
        agent --> db[(PostgreSQL)]
        db -->|"Learn & Update"| agent
    end

class thread1,thread2,thread3 session
    class agent agent
```

**Why no threads?** Letta is built on the principle that **all interactions should be part of persistent memory**, not ephemeral sessions. This enables:

* Continuous learning across all conversations
* True long-term memory and relationships
* No context loss when "starting a new thread"

For multi-user applications, we recommend **creating one agent per user**. Each agent maintains its own persistent memory about that specific user.

If you need conversation templates or starting points, use [agent templates](/guides/cloud/templates) to create new agents with pre-configured state.

The **LLM Operating System** is the infrastructure layer that manages agent execution, state, and memory. This includes:

* **Agent runtime** - Manages tool execution and the reasoning loop
* **Memory layer** - Handles context window management and persistence
* **Stateful layer** - Coordinates state across database, cache, and execution

Letta's architecture is inspired by the [MemGPT research paper](https://arxiv.org/abs/2310.08560), which introduced these concepts.

The path to more capable AI systems isn't just about larger models or longer context windows. Stateful agents represent a fundamental shift: agents that learn through accumulated experience, build lasting relationships with users, and continuously improve without retraining.

With stateful agents, you can build:

* **Personalized assistants** that adapt to individual users over time
* **Learning systems** that improve from feedback and interactions
* **Long-term relationships** where agents develop deep context about users and tasks
* **Autonomous services** that operate independently and maintain their own knowledge

This architectural shift—from stateless function calls to stateful agent services—enables a new class of AI applications that weren't possible with traditional LLM APIs.

<CardGroup cols={2}>
  <Card title="Build Your First Agent" href="/quickstart">
    Create a stateful agent with the Letta API
  </Card>

<Card title="Understanding Memory" href="/guides/agents/memory">
    Learn how agents manage their memory
  </Card>

<Card title="Agent Overview" href="/guides/agents/overview">
    Deep dive into Letta's agent architecture
  </Card>

<Card title="MemGPT Research" href="/concepts/memgpt">
    Read about the research behind Letta
  </Card>
</CardGroup>

**Examples:**

Example 1 (unknown):
```unknown
## Agents as Services

**Letta treats agents as persistent services, not ephemeral library calls.**

In traditional frameworks, agents are objects that live in your application's memory and disappear when your app stops. In Letta, agents are **independent services** that:

* Continue to exist when your application isn't running
* Maintain state in a database
* Can be accessed from multiple applications simultaneously
* Run autonomously on the server

You interact with Letta agents through REST APIs:
```

Example 2 (unknown):
```unknown
This architecture enables:

* **Multi-user applications** - Each user gets their own persistent agent
* **Agent-to-agent communication** - Agents can message each other
* **Background processing** - Agents can continue working while your app is offline
* **Deployment flexibility** - Scale agents independently from your application

## Persistence by Default

In Letta, **all state is persisted automatically**:

* Agent memory (both memory blocks and archival)
* Message history
* Tool configurations
* Agent state and context

Because everything is persisted:

* Agents can be paused and resumed at any time
* You can reload agents across different machines
* State is never lost due to application restarts
* Long conversations don't degrade performance

## Self-Editing Memory

Unlike RAG systems that passively retrieve documents, **Letta agents actively manage their own memory**. Agents use built-in tools to:

* Edit their memory blocks when learning new information
* Insert facts into archival memory for long-term storage
* Search their past conversations when context is needed

This enables agents to:

* Learn user preferences over time
* Maintain consistent personality across sessions
* Build long-term relationships with users
* Continuously improve from interactions

[Learn more about memory →](/guides/agents/memory)

## Agents vs Threads

Letta doesn't have the concept of **threads** or **sessions**. Instead, there are only **stateful agents** with a single perpetual message history.
```

---

## Extract response correctly

**URL:** llms-txt#extract-response-correctly

for msg in response.messages:
    if msg.message_type == "assistant_message":
        print(msg.content)
    elif msg.message_type == "reasoning_message":
        print(msg.reasoning)
    elif msg.message_type == "tool_call_message":
        print(msg.tool_call.name)
        print(msg.tool_call.arguments)
    elif msg.message_type == "tool_return_message":
        print(msg.tool_return)

---

## List Batches

**URL:** llms-txt#list-batches

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/messages/batches

Reference: https://docs.letta.com/api-reference/batches/list

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List Batches
  version: endpoint_batches.list
paths:
  /v1/messages/batches:
    get:
      operationId: list
      summary: List Batches
      description: List all batch runs.
      tags:
        - - subpackage_batches
      parameters:
        - name: before
          in: query
          description: >-
            Job ID cursor for pagination. Returns jobs that come before this job
            ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: after
          in: query
          description: >-
            Job ID cursor for pagination. Returns jobs that come after this job
            ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: limit
          in: query
          description: Maximum number of jobs to return
          required: false
          schema:
            type:
              - integer
              - 'null'
        - name: order
          in: query
          description: >-
            Sort order for jobs by creation time. 'asc' for oldest first, 'desc'
            for newest first
          required: false
          schema:
            $ref: '#/components/schemas/V1MessagesBatchesGetParametersOrder'
        - name: order_by
          in: query
          description: Field to sort by
          required: false
          schema:
            type: string
            enum:
              - type: stringLiteral
                value: created_at
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/BatchJob'
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    V1MessagesBatchesGetParametersOrder:
      type: string
      enum:
        - value: asc
        - value: desc
    JobStatus:
      type: string
      enum:
        - value: created
        - value: running
        - value: completed
        - value: failed
        - value: pending
        - value: cancelled
        - value: expired
    StopReasonType:
      type: string
      enum:
        - value: end_turn
        - value: error
        - value: llm_api_error
        - value: invalid_llm_response
        - value: invalid_tool_call
        - value: max_steps
        - value: no_tool_call
        - value: tool_rule
        - value: cancelled
        - value: requires_approval
    JobType:
      type: string
      enum:
        - value: job
        - value: run
        - value: batch
    BatchJob:
      type: object
      properties:
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
        created_at:
          type: string
          format: date-time
        updated_at:
          type:
            - string
            - 'null'
          format: date-time
        status:
          $ref: '#/components/schemas/JobStatus'
        completed_at:
          type:
            - string
            - 'null'
          format: date-time
        stop_reason:
          oneOf:
            - $ref: '#/components/schemas/StopReasonType'
            - type: 'null'
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        job_type:
          $ref: '#/components/schemas/JobType'
        background:
          type:
            - boolean
            - 'null'
        agent_id:
          type:
            - string
            - 'null'
        callback_url:
          type:
            - string
            - 'null'
        callback_sent_at:
          type:
            - string
            - 'null'
          format: date-time
        callback_status_code:
          type:
            - integer
            - 'null'
        callback_error:
          type:
            - string
            - 'null'
        ttft_ns:
          type:
            - integer
            - 'null'
        total_duration_ns:
          type:
            - integer
            - 'null'
        id:
          type: string
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.batches.list(
    before="before",
    after="after",
    limit=1,
    order="asc",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.batches.list({
    before: "before",
    after: "after",
    limit: 1,
    order: "asc",
    orderBy: "created_at"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/messages/batches"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Built-in Extractors

**URL:** llms-txt#built-in-extractors

**Contents:**
- Common Extractors
  - last\_assistant
  - first\_assistant
  - all\_assistant
  - pattern
  - tool\_arguments
  - tool\_output
  - memory\_block
  - after\_marker
- Next Steps

Letta Evals provides a set of built-in extractors that cover the most common extraction needs.

<Note>
  **What are extractors?** Extractors determine what part of an agent's response gets evaluated. They take the full conversation trajectory and extract just the piece you want to grade.
</Note>

Extracts the last assistant message content.

Extracts the first assistant message content.

Concatenates all assistant messages with a separator.

Extracts content matching a regex pattern.

Extracts arguments from a specific tool call.

Extracts the return value from a specific tool call.

Extracts content from a specific memory block.

<Warning>
  **Important**: This extractor requires the agent's final state, which adds overhead.
</Warning>

Extracts content after a specific marker string.

* [Custom Extractors](/evals/extractors/custom-extractors) - Write your own extractors
* [Extractors Concept](/evals/core-concepts/extractors) - Understanding extractors

**Examples:**

Example 1 (yaml):
```yaml
extractor: last_assistant  # Most common - gets final response
```

Example 2 (yaml):
```yaml
extractor: first_assistant
```

Example 3 (yaml):
```yaml
extractor: all_assistant
extractor_config:
  separator: "\n\n"  # Join messages with double newline
```

Example 4 (yaml):
```yaml
extractor: pattern
extractor_config:
  pattern: 'Result: (\d+)'  # Regex pattern to match
  group: 1  # Extract capture group 1
```

---

## List Messages For Run

**URL:** llms-txt#list-messages-for-run

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/runs/{run_id}/messages

Get response messages associated with a run.

Reference: https://docs.letta.com/api-reference/runs/messages/list

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List Messages For Run
  version: endpoint_runs/messages.list
paths:
  /v1/runs/{run_id}/messages:
    get:
      operationId: list
      summary: List Messages For Run
      description: Get response messages associated with a run.
      tags:
        - - subpackage_runs
          - subpackage_runs/messages
      parameters:
        - name: run_id
          in: path
          required: true
          schema:
            type: string
        - name: before
          in: query
          description: >-
            Message ID cursor for pagination. Returns messages that come before
            this message ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: after
          in: query
          description: >-
            Message ID cursor for pagination. Returns messages that come after
            this message ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: limit
          in: query
          description: Maximum number of messages to return
          required: false
          schema:
            type:
              - integer
              - 'null'
        - name: order
          in: query
          description: >-
            Sort order for messages by creation time. 'asc' for oldest first,
            'desc' for newest first
          required: false
          schema:
            $ref: '#/components/schemas/V1RunsRunIdMessagesGetParametersOrder'
        - name: order_by
          in: query
          description: Field to sort by
          required: false
          schema:
            type: string
            enum:
              - type: stringLiteral
                value: created_at
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/LettaMessageUnion'
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    V1RunsRunIdMessagesGetParametersOrder:
      type: string
      enum:
        - value: asc
        - value: desc
    SystemMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: system_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        content:
          type: string
      required:
        - id
        - date
        - content
    TextContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: text
        text:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - text
    UrlImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: url
        url:
          type: string
      required:
        - url
    Base64Image:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: base64
        media_type:
          type: string
        data:
          type: string
        detail:
          type:
            - string
            - 'null'
      required:
        - media_type
        - data
    LettaImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: letta
        file_id:
          type: string
        media_type:
          type:
            - string
            - 'null'
        data:
          type:
            - string
            - 'null'
        detail:
          type:
            - string
            - 'null'
      required:
        - file_id
    ImageContentSource:
      oneOf:
        - $ref: '#/components/schemas/UrlImage'
        - $ref: '#/components/schemas/Base64Image'
        - $ref: '#/components/schemas/LettaImage'
    ImageContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: image
        source:
          $ref: '#/components/schemas/ImageContentSource'
      required:
        - source
    LettaUserMessageContentUnion:
      oneOf:
        - $ref: '#/components/schemas/TextContent'
        - $ref: '#/components/schemas/ImageContent'
    UserMessageContent0:
      type: array
      items:
        $ref: '#/components/schemas/LettaUserMessageContentUnion'
    UserMessageContent:
      oneOf:
        - $ref: '#/components/schemas/UserMessageContent0'
        - type: string
    UserMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: user_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        content:
          $ref: '#/components/schemas/UserMessageContent'
      required:
        - id
        - date
        - content
    ReasoningMessageSource:
      type: string
      enum:
        - value: reasoner_model
        - value: non_reasoner_model
    ReasoningMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: reasoning_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        source:
          $ref: '#/components/schemas/ReasoningMessageSource'
        reasoning:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - id
        - date
        - reasoning
    HiddenReasoningMessageState:
      type: string
      enum:
        - value: redacted
        - value: omitted
    HiddenReasoningMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: hidden_reasoning_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        state:
          $ref: '#/components/schemas/HiddenReasoningMessageState'
        hidden_reasoning:
          type:
            - string
            - 'null'
      required:
        - id
        - date
        - state
    ToolCall:
      type: object
      properties:
        name:
          type: string
        arguments:
          type: string
        tool_call_id:
          type: string
      required:
        - name
        - arguments
        - tool_call_id
    ToolCallDelta:
      type: object
      properties:
        name:
          type:
            - string
            - 'null'
        arguments:
          type:
            - string
            - 'null'
        tool_call_id:
          type:
            - string
            - 'null'
    ToolCallMessageToolCall:
      oneOf:
        - $ref: '#/components/schemas/ToolCall'
        - $ref: '#/components/schemas/ToolCallDelta'
    ToolCallMessageToolCalls0:
      type: array
      items:
        $ref: '#/components/schemas/ToolCall'
    ToolCallMessageToolCalls:
      oneOf:
        - $ref: '#/components/schemas/ToolCallMessageToolCalls0'
        - $ref: '#/components/schemas/ToolCallDelta'
    ToolCallMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_call_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        tool_call:
          $ref: '#/components/schemas/ToolCallMessageToolCall'
        tool_calls:
          oneOf:
            - $ref: '#/components/schemas/ToolCallMessageToolCalls'
            - type: 'null'
      required:
        - id
        - date
        - tool_call
    ToolReturnMessageStatus:
      type: string
      enum:
        - value: success
        - value: error
    LettaSchemasLettaMessageToolReturnStatus:
      type: string
      enum:
        - value: success
        - value: error
    letta__schemas__letta_message__ToolReturn:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: tool
        tool_return:
          type: string
        status:
          $ref: '#/components/schemas/LettaSchemasLettaMessageToolReturnStatus'
        tool_call_id:
          type: string
        stdout:
          type:
            - array
            - 'null'
          items:
            type: string
        stderr:
          type:
            - array
            - 'null'
          items:
            type: string
      required:
        - tool_return
        - status
        - tool_call_id
    ToolReturnMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_return_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        tool_return:
          type: string
        status:
          $ref: '#/components/schemas/ToolReturnMessageStatus'
        tool_call_id:
          type: string
        stdout:
          type:
            - array
            - 'null'
          items:
            type: string
        stderr:
          type:
            - array
            - 'null'
          items:
            type: string
        tool_returns:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/letta__schemas__letta_message__ToolReturn'
      required:
        - id
        - date
        - tool_return
        - status
        - tool_call_id
    LettaAssistantMessageContentUnion:
      oneOf:
        - $ref: '#/components/schemas/TextContent'
    AssistantMessageContent0:
      type: array
      items:
        $ref: '#/components/schemas/LettaAssistantMessageContentUnion'
    AssistantMessageContent:
      oneOf:
        - $ref: '#/components/schemas/AssistantMessageContent0'
        - type: string
    AssistantMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: assistant_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        content:
          $ref: '#/components/schemas/AssistantMessageContent'
      required:
        - id
        - date
        - content
    ApprovalRequestMessageToolCall:
      oneOf:
        - $ref: '#/components/schemas/ToolCall'
        - $ref: '#/components/schemas/ToolCallDelta'
    ApprovalRequestMessageToolCalls0:
      type: array
      items:
        $ref: '#/components/schemas/ToolCall'
    ApprovalRequestMessageToolCalls:
      oneOf:
        - $ref: '#/components/schemas/ApprovalRequestMessageToolCalls0'
        - $ref: '#/components/schemas/ToolCallDelta'
    ApprovalRequestMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: approval_request_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        tool_call:
          $ref: '#/components/schemas/ApprovalRequestMessageToolCall'
        tool_calls:
          oneOf:
            - $ref: '#/components/schemas/ApprovalRequestMessageToolCalls'
            - type: 'null'
      required:
        - id
        - date
        - tool_call
    ApprovalReturn:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: approval
        tool_call_id:
          type: string
        approve:
          type: boolean
        reason:
          type:
            - string
            - 'null'
      required:
        - tool_call_id
        - approve
    ApprovalResponseMessageApprovalsItems:
      oneOf:
        - $ref: '#/components/schemas/ApprovalReturn'
        - $ref: '#/components/schemas/letta__schemas__letta_message__ToolReturn'
    ApprovalResponseMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: approval_response_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        approvals:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/ApprovalResponseMessageApprovalsItems'
        approve:
          type:
            - boolean
            - 'null'
        approval_request_id:
          type:
            - string
            - 'null'
        reason:
          type:
            - string
            - 'null'
      required:
        - id
        - date
    LettaMessageUnion:
      oneOf:
        - $ref: '#/components/schemas/SystemMessage'
        - $ref: '#/components/schemas/UserMessage'
        - $ref: '#/components/schemas/ReasoningMessage'
        - $ref: '#/components/schemas/HiddenReasoningMessage'
        - $ref: '#/components/schemas/ToolCallMessage'
        - $ref: '#/components/schemas/ToolReturnMessage'
        - $ref: '#/components/schemas/AssistantMessage'
        - $ref: '#/components/schemas/ApprovalRequestMessage'
        - $ref: '#/components/schemas/ApprovalResponseMessage'
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.runs.messages.list(
    run_id="run_id",
    before="before",
    after="after",
    limit=1,
    order="asc",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.runs.messages.list("run_id", {
    before: "before",
    after: "after",
    limit: 1,
    order: "asc",
    orderBy: "created_at"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/runs/run_id/messages"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Wednesday

**URL:** llms-txt#wednesday

**Contents:**
  - Handling Network Issues

You: Where did we leave off with the launch plan?
Agent: On Monday, we outlined the timeline and identified three key milestones...

You: [Sends message]
[No response for 30 seconds]

**Examples:**

Example 1 (unknown):
```unknown
### Handling Network Issues

**Edge Case:** Slow or interrupted connections.
```

---

## Reset Messages

**URL:** llms-txt#reset-messages

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.letta.com/v1/agents/{agent_id}/reset-messages
Content-Type: application/json

Resets the messages for an agent

Reference: https://docs.letta.com/api-reference/agents/messages/reset

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Reset Messages
  version: endpoint_agents/messages.reset
paths:
  /v1/agents/{agent_id}/reset-messages:
    patch:
      operationId: reset
      summary: Reset Messages
      description: Resets the messages for an agent
      tags:
        - - subpackage_agents
          - subpackage_agents/messages
      parameters:
        - name: agent_id
          in: path
          description: The ID of the agent in the format 'agent-<uuid4>'
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentState'
        '422':
          description: Validation Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/ResetMessagesRequest'
components:
  schemas:
    ResetMessagesRequest:
      type: object
      properties:
        add_default_initial_messages:
          type: boolean
    ToolCallNode:
      type: object
      properties:
        name:
          type: string
        args:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
      required:
        - name
    ChildToolRule:
      type: object
      properties:
        tool_name:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: constrain_child_tools
        prompt_template:
          type:
            - string
            - 'null'
        children:
          type: array
          items:
            type: string
        child_arg_nodes:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/ToolCallNode'
      required:
        - tool_name
        - children
    InitToolRule:
      type: object
      properties:
        tool_name:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: run_first
        prompt_template:
          type:
            - string
            - 'null'
        args:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
      required:
        - tool_name
    TerminalToolRule:
      type: object
      properties:
        tool_name:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: exit_loop
        prompt_template:
          type:
            - string
            - 'null'
      required:
        - tool_name
    ConditionalToolRule:
      type: object
      properties:
        tool_name:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: conditional
        prompt_template:
          type:
            - string
            - 'null'
        default_child:
          type:
            - string
            - 'null'
        child_output_mapping:
          type: object
          additionalProperties:
            type: string
        require_output_mapping:
          type: boolean
      required:
        - tool_name
        - child_output_mapping
    ContinueToolRule:
      type: object
      properties:
        tool_name:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: continue_loop
        prompt_template:
          type:
            - string
            - 'null'
      required:
        - tool_name
    RequiredBeforeExitToolRule:
      type: object
      properties:
        tool_name:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: required_before_exit
        prompt_template:
          type:
            - string
            - 'null'
      required:
        - tool_name
    MaxCountPerStepToolRule:
      type: object
      properties:
        tool_name:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: max_count_per_step
        prompt_template:
          type:
            - string
            - 'null'
        max_count_limit:
          type: integer
      required:
        - tool_name
        - max_count_limit
    ParentToolRule:
      type: object
      properties:
        tool_name:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: parent_last_tool
        prompt_template:
          type:
            - string
            - 'null'
        children:
          type: array
          items:
            type: string
      required:
        - tool_name
        - children
    RequiresApprovalToolRule:
      type: object
      properties:
        tool_name:
          type: string
        type:
          type: string
          enum:
            - type: stringLiteral
              value: requires_approval
        prompt_template:
          type:
            - string
            - 'null'
      required:
        - tool_name
    AgentStateToolRulesItems:
      oneOf:
        - $ref: '#/components/schemas/ChildToolRule'
        - $ref: '#/components/schemas/InitToolRule'
        - $ref: '#/components/schemas/TerminalToolRule'
        - $ref: '#/components/schemas/ConditionalToolRule'
        - $ref: '#/components/schemas/ContinueToolRule'
        - $ref: '#/components/schemas/RequiredBeforeExitToolRule'
        - $ref: '#/components/schemas/MaxCountPerStepToolRule'
        - $ref: '#/components/schemas/ParentToolRule'
        - $ref: '#/components/schemas/RequiresApprovalToolRule'
    AgentType:
      type: string
      enum:
        - value: memgpt_agent
        - value: memgpt_v2_agent
        - value: letta_v1_agent
        - value: react_agent
        - value: workflow_agent
        - value: split_thread_agent
        - value: sleeptime_agent
        - value: voice_convo_agent
        - value: voice_sleeptime_agent
    LlmConfigModelEndpointType:
      type: string
      enum:
        - value: openai
        - value: anthropic
        - value: google_ai
        - value: google_vertex
        - value: azure
        - value: groq
        - value: ollama
        - value: webui
        - value: webui-legacy
        - value: lmstudio
        - value: lmstudio-legacy
        - value: lmstudio-chatcompletions
        - value: llamacpp
        - value: koboldcpp
        - value: vllm
        - value: hugging-face
        - value: mistral
        - value: together
        - value: bedrock
        - value: deepseek
        - value: xai
    ProviderCategory:
      type: string
      enum:
        - value: base
        - value: byok
    LlmConfigReasoningEffort:
      type: string
      enum:
        - value: minimal
        - value: low
        - value: medium
        - value: high
    LlmConfigCompatibilityType:
      type: string
      enum:
        - value: gguf
        - value: mlx
    LlmConfigVerbosity:
      type: string
      enum:
        - value: low
        - value: medium
        - value: high
    LLMConfig:
      type: object
      properties:
        model:
          type: string
        display_name:
          type:
            - string
            - 'null'
        model_endpoint_type:
          $ref: '#/components/schemas/LlmConfigModelEndpointType'
        model_endpoint:
          type:
            - string
            - 'null'
        provider_name:
          type:
            - string
            - 'null'
        provider_category:
          oneOf:
            - $ref: '#/components/schemas/ProviderCategory'
            - type: 'null'
        model_wrapper:
          type:
            - string
            - 'null'
        context_window:
          type: integer
        put_inner_thoughts_in_kwargs:
          type:
            - boolean
            - 'null'
        handle:
          type:
            - string
            - 'null'
        temperature:
          type: number
          format: double
        max_tokens:
          type:
            - integer
            - 'null'
        enable_reasoner:
          type: boolean
        reasoning_effort:
          oneOf:
            - $ref: '#/components/schemas/LlmConfigReasoningEffort'
            - type: 'null'
        max_reasoning_tokens:
          type: integer
        frequency_penalty:
          type:
            - number
            - 'null'
          format: double
        compatibility_type:
          oneOf:
            - $ref: '#/components/schemas/LlmConfigCompatibilityType'
            - type: 'null'
        verbosity:
          oneOf:
            - $ref: '#/components/schemas/LlmConfigVerbosity'
            - type: 'null'
        tier:
          type:
            - string
            - 'null'
        parallel_tool_calls:
          type:
            - boolean
            - 'null'
      required:
        - model
        - model_endpoint_type
        - context_window
    EmbeddingConfigEmbeddingEndpointType:
      type: string
      enum:
        - value: openai
        - value: anthropic
        - value: bedrock
        - value: google_ai
        - value: google_vertex
        - value: azure
        - value: groq
        - value: ollama
        - value: webui
        - value: webui-legacy
        - value: lmstudio
        - value: lmstudio-legacy
        - value: llamacpp
        - value: koboldcpp
        - value: vllm
        - value: hugging-face
        - value: mistral
        - value: together
        - value: pinecone
    EmbeddingConfig:
      type: object
      properties:
        embedding_endpoint_type:
          $ref: '#/components/schemas/EmbeddingConfigEmbeddingEndpointType'
        embedding_endpoint:
          type:
            - string
            - 'null'
        embedding_model:
          type: string
        embedding_dim:
          type: integer
        embedding_chunk_size:
          type:
            - integer
            - 'null'
        handle:
          type:
            - string
            - 'null'
        batch_size:
          type: integer
        azure_endpoint:
          type:
            - string
            - 'null'
        azure_version:
          type:
            - string
            - 'null'
        azure_deployment:
          type:
            - string
            - 'null'
      required:
        - embedding_endpoint_type
        - embedding_model
        - embedding_dim
    TextResponseFormat:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: text
    JsonSchemaResponseFormat:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: json_schema
        json_schema:
          type: object
          additionalProperties:
            description: Any type
      required:
        - json_schema
    JsonObjectResponseFormat:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: json_object
    AgentStateResponseFormat:
      oneOf:
        - $ref: '#/components/schemas/TextResponseFormat'
        - $ref: '#/components/schemas/JsonSchemaResponseFormat'
        - $ref: '#/components/schemas/JsonObjectResponseFormat'
    MemoryAgentType:
      oneOf:
        - $ref: '#/components/schemas/AgentType'
        - type: string
    Block:
      type: object
      properties:
        value:
          type: string
        limit:
          type: integer
        project_id:
          type:
            - string
            - 'null'
        template_name:
          type:
            - string
            - 'null'
        is_template:
          type: boolean
        template_id:
          type:
            - string
            - 'null'
        base_template_id:
          type:
            - string
            - 'null'
        deployment_id:
          type:
            - string
            - 'null'
        entity_id:
          type:
            - string
            - 'null'
        preserve_on_migration:
          type:
            - boolean
            - 'null'
        label:
          type:
            - string
            - 'null'
        read_only:
          type: boolean
        description:
          type:
            - string
            - 'null'
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        hidden:
          type:
            - boolean
            - 'null'
        id:
          type: string
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
      required:
        - value
    FileBlock:
      type: object
      properties:
        value:
          type: string
        limit:
          type: integer
        project_id:
          type:
            - string
            - 'null'
        template_name:
          type:
            - string
            - 'null'
        is_template:
          type: boolean
        template_id:
          type:
            - string
            - 'null'
        base_template_id:
          type:
            - string
            - 'null'
        deployment_id:
          type:
            - string
            - 'null'
        entity_id:
          type:
            - string
            - 'null'
        preserve_on_migration:
          type:
            - boolean
            - 'null'
        label:
          type:
            - string
            - 'null'
        read_only:
          type: boolean
        description:
          type:
            - string
            - 'null'
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        hidden:
          type:
            - boolean
            - 'null'
        id:
          type: string
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
        file_id:
          type: string
        source_id:
          type: string
        is_open:
          type: boolean
        last_accessed_at:
          type:
            - string
            - 'null'
          format: date-time
      required:
        - value
        - file_id
        - source_id
        - is_open
    Memory:
      type: object
      properties:
        agent_type:
          oneOf:
            - $ref: '#/components/schemas/MemoryAgentType'
            - type: 'null'
        blocks:
          type: array
          items:
            $ref: '#/components/schemas/Block'
        file_blocks:
          type: array
          items:
            $ref: '#/components/schemas/FileBlock'
        prompt_template:
          type: string
      required:
        - blocks
    ToolType:
      type: string
      enum:
        - value: custom
        - value: letta_core
        - value: letta_memory_core
        - value: letta_multi_agent_core
        - value: letta_sleeptime_core
        - value: letta_voice_sleeptime_core
        - value: letta_builtin
        - value: letta_files_core
        - value: external_langchain
        - value: external_composio
        - value: external_mcp
    PipRequirement:
      type: object
      properties:
        name:
          type: string
        version:
          type:
            - string
            - 'null'
      required:
        - name
    NpmRequirement:
      type: object
      properties:
        name:
          type: string
        version:
          type:
            - string
            - 'null'
      required:
        - name
    Tool:
      type: object
      properties:
        id:
          type: string
        tool_type:
          $ref: '#/components/schemas/ToolType'
        description:
          type:
            - string
            - 'null'
        source_type:
          type:
            - string
            - 'null'
        name:
          type:
            - string
            - 'null'
        tags:
          type: array
          items:
            type: string
        source_code:
          type:
            - string
            - 'null'
        json_schema:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        args_json_schema:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        return_char_limit:
          type: integer
        pip_requirements:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/PipRequirement'
        npm_requirements:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/NpmRequirement'
        default_requires_approval:
          type:
            - boolean
            - 'null'
        enable_parallel_execution:
          type:
            - boolean
            - 'null'
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
        metadata_:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
    VectorDBProvider:
      type: string
      enum:
        - value: native
        - value: tpuf
        - value: pinecone
    Source:
      type: object
      properties:
        name:
          type: string
        description:
          type:
            - string
            - 'null'
        instructions:
          type:
            - string
            - 'null'
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        id:
          type: string
        embedding_config:
          $ref: '#/components/schemas/EmbeddingConfig'
        vector_db_provider:
          $ref: '#/components/schemas/VectorDBProvider'
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
        created_at:
          type:
            - string
            - 'null'
          format: date-time
        updated_at:
          type:
            - string
            - 'null'
          format: date-time
      required:
        - name
        - embedding_config
    AgentEnvironmentVariable:
      type: object
      properties:
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
        created_at:
          type:
            - string
            - 'null'
          format: date-time
        updated_at:
          type:
            - string
            - 'null'
          format: date-time
        id:
          type: string
        key:
          type: string
        value:
          type: string
        description:
          type:
            - string
            - 'null'
        value_enc:
          type:
            - string
            - 'null'
        agent_id:
          type: string
      required:
        - key
        - value
        - agent_id
    IdentityType:
      type: string
      enum:
        - value: org
        - value: user
        - value: other
    IdentityPropertyValue:
      oneOf:
        - type: string
        - type: integer
        - type: number
          format: double
        - type: boolean
        - type: object
          additionalProperties:
            description: Any type
    IdentityPropertyType:
      type: string
      enum:
        - value: string
        - value: number
        - value: boolean
        - value: json
    IdentityProperty:
      type: object
      properties:
        key:
          type: string
        value:
          $ref: '#/components/schemas/IdentityPropertyValue'
        type:
          $ref: '#/components/schemas/IdentityPropertyType'
      required:
        - key
        - value
        - type
    Identity:
      type: object
      properties:
        id:
          type: string
        identifier_key:
          type: string
        name:
          type: string
        identity_type:
          $ref: '#/components/schemas/IdentityType'
        project_id:
          type:
            - string
            - 'null'
        agent_ids:
          type: array
          items:
            type: string
        block_ids:
          type: array
          items:
            type: string
        properties:
          type: array
          items:
            $ref: '#/components/schemas/IdentityProperty'
      required:
        - identifier_key
        - name
        - identity_type
        - agent_ids
        - block_ids
    ManagerType:
      type: string
      enum:
        - value: round_robin
        - value: supervisor
        - value: dynamic
        - value: sleeptime
        - value: voice_sleeptime
        - value: swarm
    Group:
      type: object
      properties:
        id:
          type: string
        manager_type:
          $ref: '#/components/schemas/ManagerType'
        agent_ids:
          type: array
          items:
            type: string
        description:
          type: string
        project_id:
          type:
            - string
            - 'null'
        template_id:
          type:
            - string
            - 'null'
        base_template_id:
          type:
            - string
            - 'null'
        deployment_id:
          type:
            - string
            - 'null'
        shared_block_ids:
          type: array
          items:
            type: string
        manager_agent_id:
          type:
            - string
            - 'null'
        termination_token:
          type:
            - string
            - 'null'
        max_turns:
          type:
            - integer
            - 'null'
        sleeptime_agent_frequency:
          type:
            - integer
            - 'null'
        turns_counter:
          type:
            - integer
            - 'null'
        last_processed_message_id:
          type:
            - string
            - 'null'
        max_message_buffer_length:
          type:
            - integer
            - 'null'
        min_message_buffer_length:
          type:
            - integer
            - 'null'
        hidden:
          type:
            - boolean
            - 'null'
      required:
        - id
        - manager_type
        - agent_ids
        - description
    AgentState:
      type: object
      properties:
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
        created_at:
          type:
            - string
            - 'null'
          format: date-time
        updated_at:
          type:
            - string
            - 'null'
          format: date-time
        id:
          type: string
        name:
          type: string
        tool_rules:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/AgentStateToolRulesItems'
        message_ids:
          type:
            - array
            - 'null'
          items:
            type: string
        system:
          type: string
        agent_type:
          $ref: '#/components/schemas/AgentType'
        llm_config:
          $ref: '#/components/schemas/LLMConfig'
        embedding_config:
          $ref: '#/components/schemas/EmbeddingConfig'
        response_format:
          oneOf:
            - $ref: '#/components/schemas/AgentStateResponseFormat'
            - type: 'null'
        description:
          type:
            - string
            - 'null'
        metadata:
          type:
            - object
            - 'null'
          additionalProperties:
            description: Any type
        memory:
          $ref: '#/components/schemas/Memory'
        blocks:
          type: array
          items:
            $ref: '#/components/schemas/Block'
        tools:
          type: array
          items:
            $ref: '#/components/schemas/Tool'
        sources:
          type: array
          items:
            $ref: '#/components/schemas/Source'
        tags:
          type: array
          items:
            type: string
        tool_exec_environment_variables:
          type: array
          items:
            $ref: '#/components/schemas/AgentEnvironmentVariable'
        secrets:
          type: array
          items:
            $ref: '#/components/schemas/AgentEnvironmentVariable'
        project_id:
          type:
            - string
            - 'null'
        template_id:
          type:
            - string
            - 'null'
        base_template_id:
          type:
            - string
            - 'null'
        deployment_id:
          type:
            - string
            - 'null'
        entity_id:
          type:
            - string
            - 'null'
        identity_ids:
          type: array
          items:
            type: string
        identities:
          type: array
          items:
            $ref: '#/components/schemas/Identity'
        message_buffer_autoclear:
          type: boolean
        enable_sleeptime:
          type:
            - boolean
            - 'null'
        multi_agent_group:
          oneOf:
            - $ref: '#/components/schemas/Group'
            - type: 'null'
        managed_group:
          oneOf:
            - $ref: '#/components/schemas/Group'
            - type: 'null'
        last_run_completion:
          type:
            - string
            - 'null'
          format: date-time
        last_run_duration_ms:
          type:
            - integer
            - 'null'
        timezone:
          type:
            - string
            - 'null'
        max_files_open:
          type:
            - integer
            - 'null'
        per_file_view_window_char_limit:
          type:
            - integer
            - 'null'
        hidden:
          type:
            - boolean
            - 'null'
      required:
        - id
        - name
        - system
        - agent_type
        - llm_config
        - embedding_config
        - memory
        - blocks
        - tools
        - sources
        - tags
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.agents.messages.reset(
    agent_id="agent-123e4567-e89b-42d3-8456-426614174000",
    add_default_initial_messages=True,
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.agents.messages.reset("agent-123e4567-e89b-42d3-8456-426614174000", {
    addDefaultInitialMessages: true
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/agents/agent_id/reset-messages"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("PATCH", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## April 13, 2025

**URL:** llms-txt#april-13,-2025

**Contents:**
- New `reasoning_effort` field added to LLMConfig
- New `sender_id` parameter added to Message model

## New `reasoning_effort` field added to LLMConfig

The `reasoning_effort` field has been added to the `LLMConfig` object to control the amount of reasoning the model should perform, to support OpenAI's o1 and o3 reasoning models.

## New `sender_id` parameter added to Message model

The `Message` object now includes a `sender_id` field, which is the ID of the sender of the message, which can be either an identity ID or an agent ID. The `sender_id` is expected to be passed in at message creation time.

**Examples:**

Example 1 (unknown):
```unknown

```

---

## Cancel Batch

**URL:** llms-txt#cancel-batch

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.letta.com/v1/messages/batches/{batch_id}/cancel

Reference: https://docs.letta.com/api-reference/batches/cancel

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Cancel Batch
  version: endpoint_batches.cancel
paths:
  /v1/messages/batches/{batch_id}/cancel:
    patch:
      operationId: cancel
      summary: Cancel Batch
      description: Cancel a batch run.
      tags:
        - - subpackage_batches
      parameters:
        - name: batch_id
          in: path
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                description: Any type
        '422':
          description: Validation Error
          content: {}
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.batches.cancel(
    batch_id="batch_id",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.batches.cancel("batch_id");
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/messages/batches/batch_id/cancel"

	req, _ := http.NewRequest("PATCH", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## ... more chunks with same ID

**URL:** llms-txt#...-more-chunks-with-same-id

**Contents:**
- Implementation Tips
  - Universal Handling Pattern
  - SSE Format Notes
  - Handling Different LLM Providers

## Implementation Tips

### Universal Handling Pattern

The accumulator pattern shown above works for **both** streaming modes:

* **Step streaming**: Each message is complete (single chunk per ID)
* **Token streaming**: Multiple chunks per ID need accumulation

This means you can write your client code once to handle both cases.

All streaming responses follow the Server-Sent Events (SSE) format:

* Each event starts with `data: ` followed by JSON
* Stream ends with `data: [DONE]`
* Empty lines separate events

Learn more about SSE format [here](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events/Using_server-sent_events).

### Handling Different LLM Providers

If your Letta server connects to multiple LLM providers, some may not support token streaming. Your client code will still work - the server will fall back to step streaming automatically when token streaming isn't available.

---

## Send everything

**URL:** llms-txt#send-everything

response = openai.chat.completions.create(
    model="gpt-4",
    messages=messages  # ← Full history required
)

---

## Multi-modal (image inputs)

**URL:** llms-txt#multi-modal-(image-inputs)

**Contents:**
- Model Support
- ADE Support
- Usage Examples (SDK)
  - Sending an Image via URL
  - Sending an Image via Base64

> Send images to your agents

<Note>
  Multi-modal features require compatible language models. Ensure your agent is configured with a multi-modal capable model.
</Note>

Letta agents support image inputs, enabling richer conversations and more powerful agent capabilities.

Multi-modal capabilities depend on the underlying language model.
You can check which models from the API providers support image inputs by checking their individual model pages:

* **[OpenAI](https://platform.openai.com/docs/models)**: GPT-4.1, o1/3/4, GPT-4o
* **[Anthropic](https://docs.anthropic.com/en/docs/about-claude/models/overview)**: Claude Opus 4, Claude Sonnet 4
* **[Gemini](https://ai.google.dev/gemini-api/docs/models)**: Gemini 2.5 Pro, Gemini 2.5 Flash

If the provider you're using doesn't support image inputs, your images will still appear in the context window, but as a text message telling the agent that an image exists.

You can pass images to your agents by drag-and-dropping them into the chat window, or clicking the image icon to select a manual file upload.

<img src="file:0cca3f03-39eb-4acd-af41-9888f895e868" />

<img src="file:1320d16a-6c19-434a-aae3-946a4f986ed8" />

## Usage Examples (SDK)

### Sending an Image via URL

### Sending an Image via Base64

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown
</CodeGroup>

### Sending an Image via Base64

<CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## March 15, 2025

**URL:** llms-txt#march-15,-2025

**Contents:**
- Message `content` field extended to include Multi-modal content parts
  - Before:
  - After:

## Message `content` field extended to include Multi-modal content parts

The `content` field on `UserMessage` and `AssistantMessage` objects returned by our Messages endpoints has been extended to support multi-modal content parts, in anticipation of allowing you to send and receive messages with text, images, and other media.

**Examples:**

Example 1 (curl):
```curl
{
    "id": "message-dea2ceab-0863-44ea-86dc-70cf02c05946",
    "date": "2025-01-28T01:18:18+00:00",
    "message_type": "user_message",
    "content": "Hello, how are you?"
  }
```

Example 2 (curl):
```curl
{
    "id": "message-dea2ceab-0863-44ea-86dc-70cf02c05946",
    "date": "2025-01-28T01:18:18+00:00",
    "message_type": "user_message",
    "content": [
      {
        "type": "text",
        "text": "Hello, how are you?"
      }
    ]
  }
```

---

## You must send the entire conversation every time

**URL:** llms-txt#you-must-send-the-entire-conversation-every-time

messages = [
    {"role": "user", "content": "Hello, I'm Sarah"},
    {"role": "assistant", "content": "Hi Sarah!"},
    {"role": "user", "content": "What's my name?"},  # ← New message
]

---

## Search Messages

**URL:** llms-txt#search-messages

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.letta.com/v1/agents/messages/search
Content-Type: application/json

Search messages across the entire organization with optional project and template filtering. Returns messages with FTS/vector ranks and total RRF score.

This is a cloud-only feature.

Reference: https://docs.letta.com/api-reference/agents/messages/search

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Search Messages
  version: endpoint_agents/messages.search
paths:
  /v1/agents/messages/search:
    post:
      operationId: search
      summary: Search Messages
      description: >-
        Search messages across the entire organization with optional project and
        template filtering. Returns messages with FTS/vector ranks and total RRF
        score.


        This is a cloud-only feature.
      tags:
        - - subpackage_agents
          - subpackage_agents/messages
      parameters:
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/MessageSearchResult'
        '422':
          description: Validation Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/MessageSearchRequest'
components:
  schemas:
    MessageSearchRequestSearchMode:
      type: string
      enum:
        - value: vector
        - value: fts
        - value: hybrid
    MessageRole:
      type: string
      enum:
        - value: assistant
        - value: user
        - value: tool
        - value: function
        - value: system
        - value: approval
    MessageSearchRequest:
      type: object
      properties:
        query:
          type:
            - string
            - 'null'
        search_mode:
          $ref: '#/components/schemas/MessageSearchRequestSearchMode'
        roles:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/MessageRole'
        project_id:
          type:
            - string
            - 'null'
        template_id:
          type:
            - string
            - 'null'
        limit:
          type: integer
        start_date:
          type:
            - string
            - 'null'
          format: date-time
        end_date:
          type:
            - string
            - 'null'
          format: date-time
    TextContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: text
        text:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - text
    UrlImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: url
        url:
          type: string
      required:
        - url
    Base64Image:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: base64
        media_type:
          type: string
        data:
          type: string
        detail:
          type:
            - string
            - 'null'
      required:
        - media_type
        - data
    LettaImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: letta
        file_id:
          type: string
        media_type:
          type:
            - string
            - 'null'
        data:
          type:
            - string
            - 'null'
        detail:
          type:
            - string
            - 'null'
      required:
        - file_id
    ImageContentSource:
      oneOf:
        - $ref: '#/components/schemas/UrlImage'
        - $ref: '#/components/schemas/Base64Image'
        - $ref: '#/components/schemas/LettaImage'
    ImageContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: image
        source:
          $ref: '#/components/schemas/ImageContentSource'
      required:
        - source
    ToolCallContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_call
        id:
          type: string
        name:
          type: string
        input:
          type: object
          additionalProperties:
            description: Any type
        signature:
          type:
            - string
            - 'null'
      required:
        - id
        - name
        - input
    ToolReturnContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_return
        tool_call_id:
          type: string
        content:
          type: string
        is_error:
          type: boolean
      required:
        - tool_call_id
        - content
        - is_error
    ReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: reasoning
        is_native:
          type: boolean
        reasoning:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - is_native
        - reasoning
    RedactedReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: redacted_reasoning
        data:
          type: string
      required:
        - data
    OmittedReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: omitted_reasoning
        signature:
          type:
            - string
            - 'null'
    SummarizedReasoningContentPart:
      type: object
      properties:
        index:
          type: integer
        text:
          type: string
      required:
        - index
        - text
    SummarizedReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: summarized_reasoning
        id:
          type: string
        summary:
          type: array
          items:
            $ref: '#/components/schemas/SummarizedReasoningContentPart'
        encrypted_content:
          type: string
      required:
        - id
        - summary
    MessageContentItems:
      oneOf:
        - $ref: '#/components/schemas/TextContent'
        - $ref: '#/components/schemas/ImageContent'
        - $ref: '#/components/schemas/ToolCallContent'
        - $ref: '#/components/schemas/ToolReturnContent'
        - $ref: '#/components/schemas/ReasoningContent'
        - $ref: '#/components/schemas/RedactedReasoningContent'
        - $ref: '#/components/schemas/OmittedReasoningContent'
        - $ref: '#/components/schemas/SummarizedReasoningContent'
    Function-Output:
      type: object
      properties:
        arguments:
          type: string
        name:
          type: string
      required:
        - arguments
        - name
    ChatCompletionMessageFunctionToolCall-Output:
      type: object
      properties:
        id:
          type: string
        function:
          $ref: '#/components/schemas/Function-Output'
        type:
          type: string
          enum:
            - type: stringLiteral
              value: function
      required:
        - id
        - function
        - type
    LettaSchemasMessageToolReturnStatus:
      type: string
      enum:
        - value: success
        - value: error
    letta__schemas__message__ToolReturn:
      type: object
      properties:
        status:
          $ref: '#/components/schemas/LettaSchemasMessageToolReturnStatus'
        stdout:
          type:
            - array
            - 'null'
          items:
            type: string
        stderr:
          type:
            - array
            - 'null'
          items:
            type: string
        func_response:
          type:
            - string
            - 'null'
      required:
        - status
    ApprovalReturn:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: approval
        tool_call_id:
          type: string
        approve:
          type: boolean
        reason:
          type:
            - string
            - 'null'
      required:
        - tool_call_id
        - approve
    MessageApprovalsItems:
      oneOf:
        - $ref: '#/components/schemas/ApprovalReturn'
        - $ref: '#/components/schemas/letta__schemas__message__ToolReturn'
    Message:
      type: object
      properties:
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
        created_at:
          type: string
          format: date-time
        updated_at:
          type:
            - string
            - 'null'
          format: date-time
        id:
          type: string
        agent_id:
          type:
            - string
            - 'null'
        model:
          type:
            - string
            - 'null'
        role:
          $ref: '#/components/schemas/MessageRole'
        content:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/MessageContentItems'
        name:
          type:
            - string
            - 'null'
        tool_calls:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/ChatCompletionMessageFunctionToolCall-Output'
        tool_call_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        otid:
          type:
            - string
            - 'null'
        tool_returns:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/letta__schemas__message__ToolReturn'
        group_id:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        batch_item_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        approval_request_id:
          type:
            - string
            - 'null'
        approve:
          type:
            - boolean
            - 'null'
        denial_reason:
          type:
            - string
            - 'null'
        approvals:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/MessageApprovalsItems'
      required:
        - role
    MessageSearchResult:
      type: object
      properties:
        embedded_text:
          type: string
        message:
          $ref: '#/components/schemas/Message'
        fts_rank:
          type:
            - integer
            - 'null'
        vector_rank:
          type:
            - integer
            - 'null'
        rrf_score:
          type: number
          format: double
      required:
        - embedded_text
        - message
        - rrf_score
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.agents.messages.search()
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.agents.messages.search();
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/agents/messages/search"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## April 2, 2025

**URL:** llms-txt#april-2,-2025

**Contents:**
- New `strip_messages` field in Import Agent API

## New `strip_messages` field in Import Agent API

The `Import Agent` API now supports a new `strip_messages` field to remove messages from the agent's conversation history when importing a serialized agent file.

**Examples:**

Example 1 (unknown):
```unknown

```

---

## March 21, 2025

**URL:** llms-txt#march-21,-2025

**Contents:**
- Output messages added to Steps API
- Order parameter added to List Agents and List Passages APIs
- Filter parameters added List Passages API

## Output messages added to Steps API

The `Step` object returned by our Steps endpoints now includes a `steps_messages` field, which contains a list of messages generated by the step.

## Order parameter added to List Agents and List Passages APIs

The `List Agents` and `List Passages` endpoints now support an `ascending` parameter to sort the results based on creation timestamp.

## Filter parameters added List Passages API

The `List Passages` endpoint now supports filter parameters to filter the results including `after`, `before`, and `search` for filtering by text.

---

## Summarize Messages

**URL:** llms-txt#summarize-messages

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.letta.com/v1/agents/{agent_id}/summarize

Summarize an agent's conversation history.

Reference: https://docs.letta.com/api-reference/agents/messages/summarize

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Summarize Messages
  version: endpoint_agents/messages.summarize
paths:
  /v1/agents/{agent_id}/summarize:
    post:
      operationId: summarize
      summary: Summarize Messages
      description: Summarize an agent's conversation history.
      tags:
        - - subpackage_agents
          - subpackage_agents/messages
      parameters:
        - name: agent_id
          in: path
          description: The ID of the agent in the format 'agent-<uuid4>'
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '204':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/agents_messages_summarize_Response_204'
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    agents_messages_summarize_Response_204:
      type: object
      properties: {}
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.agents.messages.summarize(
    agent_id="agent-123e4567-e89b-42d3-8456-426614174000",
    max_message_length=1,
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.agents.messages.summarize("agent-123e4567-e89b-42d3-8456-426614174000", {
    maxMessageLength: 1
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/agents/agent_id/summarize"

	req, _ := http.NewRequest("POST", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Get user-facing messages only

**URL:** llms-txt#get-user-facing-messages-only

**Contents:**
  - 3. Track Tool Execution

display_messages = [
    msg for msg in messages
    if not is_internal_message(msg)
]
python

**Examples:**

Example 1 (unknown):
```unknown
### 3. Track Tool Execution

Match tool calls with their returns using `tool_call_id`:
```

---

## You must store and manage messages yourself

**URL:** llms-txt#you-must-store-and-manage-messages-yourself

messages.append(response.choices[0].message)
python

**Examples:**

Example 1 (unknown):
```unknown
**Stateful API (Letta):**
```

---

## Same ID across chunks of the same message

**URL:** llms-txt#same-id-across-chunks-of-the-same-message

data: {"id":"msg-abc","message_type":"assistant_message","content":"Why"}
data: {"id":"msg-abc","message_type":"assistant_message","content":" did"}
data: {"id":"msg-abc","message_type":"assistant_message","content":" the"}
data: {"id":"msg-abc","message_type":"assistant_message","content":" scarecrow"}
data: {"id":"msg-abc","message_type":"assistant_message","content":" win"}

---

## April 15, 2025

**URL:** llms-txt#april-15,-2025

**Contents:**
- New Batch message creation API

## New Batch message creation API

A series of new `Batch` endpoints has been introduced to support batch message creation, allowing you to perform multiple LLM requests in a single API call. These APIs leverage provider batch APIs under the hood, which can be more cost-effective than making multiple API calls.

New endpoints can be found here: [Batch Messages](https://docs.letta.com/api-reference/messages/batch)

---

## print the chunks coming back

**URL:** llms-txt#print-the-chunks-coming-back

for chunk in stream:
    if chunk.message_type == "assistant_message":
        print(chunk.content)
    elif chunk.message_type == "reasoning_message":
        print(chunk.reasoning)
    elif chunk.message_type == "tool_call_message":
        if chunk.tool_call.name:
            print(chunk.tool_call.name)
        if chunk.tool_call.arguments:
            print(chunk.tool_call.arguments)
    elif chunk.message_type == "tool_return_message":
        print(chunk.tool_return)
    elif chunk.message_type == "usage_statistics":
        print(chunk)
python
def my_custom_tool(query: str) -> str:
    """
    Search for information on a topic.

Args:
        query (str): The search query

Returns:
        str: Search results
    """
    return f"Results for: {query}"

**Examples:**

Example 1 (unknown):
```unknown
Creating custom tools (Python only):
```

---

## Reset Messages For Group

**URL:** llms-txt#reset-messages-for-group

**Contents:**
- OpenAPI Specification
- SDK Code Examples

PATCH https://api.letta.com/v1/groups/{group_id}/reset-messages

Delete the group messages for all agents that are part of the multi-agent group.

Reference: https://docs.letta.com/api-reference/groups/messages/reset

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Reset Messages For Group
  version: endpoint_groups/messages.reset
paths:
  /v1/groups/{group_id}/reset-messages:
    patch:
      operationId: reset
      summary: Reset Messages For Group
      description: >-
        Delete the group messages for all agents that are part of the
        multi-agent group.
      tags:
        - - subpackage_groups
          - subpackage_groups/messages
      parameters:
        - name: group_id
          in: path
          description: The ID of the group in the format 'group-<uuid4>'
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                description: Any type
        '422':
          description: Validation Error
          content: {}
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.groups.messages.reset(
    group_id="group-123e4567-e89b-42d3-8456-426614174000",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.groups.messages.reset("group-123e4567-e89b-42d3-8456-426614174000");
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/groups/group_id/reset-messages"

	req, _ := http.NewRequest("PATCH", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## Cancel Message

**URL:** llms-txt#cancel-message

**Contents:**
- OpenAPI Specification
- SDK Code Examples

POST https://api.letta.com/v1/agents/{agent_id}/messages/cancel
Content-Type: application/json

Cancel runs associated with an agent. If run_ids are passed in, cancel those in particular.

Note to cancel active runs associated with an agent, redis is required.

Reference: https://docs.letta.com/api-reference/agents/messages/cancel

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: Cancel Message
  version: endpoint_agents/messages.cancel
paths:
  /v1/agents/{agent_id}/messages/cancel:
    post:
      operationId: cancel
      summary: Cancel Message
      description: >-
        Cancel runs associated with an agent. If run_ids are passed in, cancel
        those in particular.


        Note to cancel active runs associated with an agent, redis is required.
      tags:
        - - subpackage_agents
          - subpackage_agents/messages
      parameters:
        - name: agent_id
          in: path
          description: The ID of the agent in the format 'agent-<uuid4>'
          required: true
          schema:
            type: string
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                type: object
                additionalProperties:
                  description: Any type
        '422':
          description: Validation Error
          content: {}
      requestBody:
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CancelAgentRunRequest'
components:
  schemas:
    CancelAgentRunRequest:
      type: object
      properties:
        run_ids:
          type:
            - array
            - 'null'
          items:
            type: string
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.agents.messages.cancel(
    agent_id="agent-123e4567-e89b-42d3-8456-426614174000",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.agents.messages.cancel("agent-123e4567-e89b-42d3-8456-426614174000");
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"strings"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/agents/agent_id/messages/cancel"

	payload := strings.NewReader("{}")

	req, _ := http.NewRequest("POST", url, payload)

	req.Header.Add("Authorization", "Bearer <token>")
	req.Header.Add("Content-Type", "application/json")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## List Messages For Batch

**URL:** llms-txt#list-messages-for-batch

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/messages/batches/{batch_id}/messages

Get response messages for a specific batch job.

Reference: https://docs.letta.com/api-reference/batches/messages/list

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List Messages For Batch
  version: endpoint_batches/messages.list
paths:
  /v1/messages/batches/{batch_id}/messages:
    get:
      operationId: list
      summary: List Messages For Batch
      description: Get response messages for a specific batch job.
      tags:
        - - subpackage_batches
          - subpackage_batches/messages
      parameters:
        - name: batch_id
          in: path
          required: true
          schema:
            type: string
        - name: before
          in: query
          description: >-
            Message ID cursor for pagination. Returns messages that come before
            this message ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: after
          in: query
          description: >-
            Message ID cursor for pagination. Returns messages that come after
            this message ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: limit
          in: query
          description: Maximum number of messages to return
          required: false
          schema:
            type:
              - integer
              - 'null'
        - name: order
          in: query
          description: >-
            Sort order for messages by creation time. 'asc' for oldest first,
            'desc' for newest first
          required: false
          schema:
            $ref: >-
              #/components/schemas/V1MessagesBatchesBatchIdMessagesGetParametersOrder
        - name: order_by
          in: query
          description: Field to sort by
          required: false
          schema:
            type: string
            enum:
              - type: stringLiteral
                value: created_at
        - name: agent_id
          in: query
          description: Filter messages by agent ID
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/LettaBatchMessages'
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    V1MessagesBatchesBatchIdMessagesGetParametersOrder:
      type: string
      enum:
        - value: asc
        - value: desc
    MessageRole:
      type: string
      enum:
        - value: assistant
        - value: user
        - value: tool
        - value: function
        - value: system
        - value: approval
    TextContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: text
        text:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - text
    UrlImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: url
        url:
          type: string
      required:
        - url
    Base64Image:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: base64
        media_type:
          type: string
        data:
          type: string
        detail:
          type:
            - string
            - 'null'
      required:
        - media_type
        - data
    LettaImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: letta
        file_id:
          type: string
        media_type:
          type:
            - string
            - 'null'
        data:
          type:
            - string
            - 'null'
        detail:
          type:
            - string
            - 'null'
      required:
        - file_id
    ImageContentSource:
      oneOf:
        - $ref: '#/components/schemas/UrlImage'
        - $ref: '#/components/schemas/Base64Image'
        - $ref: '#/components/schemas/LettaImage'
    ImageContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: image
        source:
          $ref: '#/components/schemas/ImageContentSource'
      required:
        - source
    ToolCallContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_call
        id:
          type: string
        name:
          type: string
        input:
          type: object
          additionalProperties:
            description: Any type
        signature:
          type:
            - string
            - 'null'
      required:
        - id
        - name
        - input
    ToolReturnContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_return
        tool_call_id:
          type: string
        content:
          type: string
        is_error:
          type: boolean
      required:
        - tool_call_id
        - content
        - is_error
    ReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: reasoning
        is_native:
          type: boolean
        reasoning:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - is_native
        - reasoning
    RedactedReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: redacted_reasoning
        data:
          type: string
      required:
        - data
    OmittedReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: omitted_reasoning
        signature:
          type:
            - string
            - 'null'
    SummarizedReasoningContentPart:
      type: object
      properties:
        index:
          type: integer
        text:
          type: string
      required:
        - index
        - text
    SummarizedReasoningContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: summarized_reasoning
        id:
          type: string
        summary:
          type: array
          items:
            $ref: '#/components/schemas/SummarizedReasoningContentPart'
        encrypted_content:
          type: string
      required:
        - id
        - summary
    MessageContentItems:
      oneOf:
        - $ref: '#/components/schemas/TextContent'
        - $ref: '#/components/schemas/ImageContent'
        - $ref: '#/components/schemas/ToolCallContent'
        - $ref: '#/components/schemas/ToolReturnContent'
        - $ref: '#/components/schemas/ReasoningContent'
        - $ref: '#/components/schemas/RedactedReasoningContent'
        - $ref: '#/components/schemas/OmittedReasoningContent'
        - $ref: '#/components/schemas/SummarizedReasoningContent'
    Function-Output:
      type: object
      properties:
        arguments:
          type: string
        name:
          type: string
      required:
        - arguments
        - name
    ChatCompletionMessageFunctionToolCall-Output:
      type: object
      properties:
        id:
          type: string
        function:
          $ref: '#/components/schemas/Function-Output'
        type:
          type: string
          enum:
            - type: stringLiteral
              value: function
      required:
        - id
        - function
        - type
    LettaSchemasMessageToolReturnStatus:
      type: string
      enum:
        - value: success
        - value: error
    letta__schemas__message__ToolReturn:
      type: object
      properties:
        status:
          $ref: '#/components/schemas/LettaSchemasMessageToolReturnStatus'
        stdout:
          type:
            - array
            - 'null'
          items:
            type: string
        stderr:
          type:
            - array
            - 'null'
          items:
            type: string
        func_response:
          type:
            - string
            - 'null'
      required:
        - status
    ApprovalReturn:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: approval
        tool_call_id:
          type: string
        approve:
          type: boolean
        reason:
          type:
            - string
            - 'null'
      required:
        - tool_call_id
        - approve
    MessageApprovalsItems:
      oneOf:
        - $ref: '#/components/schemas/ApprovalReturn'
        - $ref: '#/components/schemas/letta__schemas__message__ToolReturn'
    Message:
      type: object
      properties:
        created_by_id:
          type:
            - string
            - 'null'
        last_updated_by_id:
          type:
            - string
            - 'null'
        created_at:
          type: string
          format: date-time
        updated_at:
          type:
            - string
            - 'null'
          format: date-time
        id:
          type: string
        agent_id:
          type:
            - string
            - 'null'
        model:
          type:
            - string
            - 'null'
        role:
          $ref: '#/components/schemas/MessageRole'
        content:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/MessageContentItems'
        name:
          type:
            - string
            - 'null'
        tool_calls:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/ChatCompletionMessageFunctionToolCall-Output'
        tool_call_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        otid:
          type:
            - string
            - 'null'
        tool_returns:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/letta__schemas__message__ToolReturn'
        group_id:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        batch_item_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        approval_request_id:
          type:
            - string
            - 'null'
        approve:
          type:
            - boolean
            - 'null'
        denial_reason:
          type:
            - string
            - 'null'
        approvals:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/MessageApprovalsItems'
      required:
        - role
    LettaBatchMessages:
      type: object
      properties:
        messages:
          type: array
          items:
            $ref: '#/components/schemas/Message'
      required:
        - messages
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.batches.messages.list(
    batch_id="batch_id",
    before="before",
    after="after",
    limit=1,
    order="asc",
    agent_id="agent_id",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.batches.messages.list("batch_id", {
    before: "before",
    after: "after",
    limit: 1,
    order: "asc",
    orderBy: "created_at",
    agentId: "agent_id"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/messages/batches/batch_id/messages"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---

## List Messages For Step

**URL:** llms-txt#list-messages-for-step

**Contents:**
- OpenAPI Specification
- SDK Code Examples

GET https://api.letta.com/v1/steps/{step_id}/messages

List messages for a given step.

Reference: https://docs.letta.com/api-reference/steps/messages/list

## OpenAPI Specification

**Examples:**

Example 1 (yaml):
```yaml
openapi: 3.1.1
info:
  title: List Messages For Step
  version: endpoint_steps/messages.list
paths:
  /v1/steps/{step_id}/messages:
    get:
      operationId: list
      summary: List Messages For Step
      description: List messages for a given step.
      tags:
        - - subpackage_steps
          - subpackage_steps/messages
      parameters:
        - name: step_id
          in: path
          description: The ID of the step in the format 'step-<uuid4>'
          required: true
          schema:
            type: string
        - name: before
          in: query
          description: >-
            Message ID cursor for pagination. Returns messages that come before
            this message ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: after
          in: query
          description: >-
            Message ID cursor for pagination. Returns messages that come after
            this message ID in the specified sort order
          required: false
          schema:
            type:
              - string
              - 'null'
        - name: limit
          in: query
          description: Maximum number of messages to return
          required: false
          schema:
            type:
              - integer
              - 'null'
        - name: order
          in: query
          description: >-
            Sort order for messages by creation time. 'asc' for oldest first,
            'desc' for newest first
          required: false
          schema:
            $ref: '#/components/schemas/V1StepsStepIdMessagesGetParametersOrder'
        - name: order_by
          in: query
          description: Sort by field
          required: false
          schema:
            type: string
            enum:
              - type: stringLiteral
                value: created_at
        - name: Authorization
          in: header
          description: Header authentication of the form `Bearer <token>`
          required: true
          schema:
            type: string
      responses:
        '200':
          description: Successful Response
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: >-
                    #/components/schemas/V1StepsStepIdMessagesGetResponsesContentApplicationJsonSchemaItems
        '422':
          description: Validation Error
          content: {}
components:
  schemas:
    V1StepsStepIdMessagesGetParametersOrder:
      type: string
      enum:
        - value: asc
        - value: desc
    SystemMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: system_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        content:
          type: string
      required:
        - id
        - date
        - content
    TextContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: text
        text:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - text
    UrlImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: url
        url:
          type: string
      required:
        - url
    Base64Image:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: base64
        media_type:
          type: string
        data:
          type: string
        detail:
          type:
            - string
            - 'null'
      required:
        - media_type
        - data
    LettaImage:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: letta
        file_id:
          type: string
        media_type:
          type:
            - string
            - 'null'
        data:
          type:
            - string
            - 'null'
        detail:
          type:
            - string
            - 'null'
      required:
        - file_id
    ImageContentSource:
      oneOf:
        - $ref: '#/components/schemas/UrlImage'
        - $ref: '#/components/schemas/Base64Image'
        - $ref: '#/components/schemas/LettaImage'
    ImageContent:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: image
        source:
          $ref: '#/components/schemas/ImageContentSource'
      required:
        - source
    LettaUserMessageContentUnion:
      oneOf:
        - $ref: '#/components/schemas/TextContent'
        - $ref: '#/components/schemas/ImageContent'
    UserMessageContent0:
      type: array
      items:
        $ref: '#/components/schemas/LettaUserMessageContentUnion'
    UserMessageContent:
      oneOf:
        - $ref: '#/components/schemas/UserMessageContent0'
        - type: string
    UserMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: user_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        content:
          $ref: '#/components/schemas/UserMessageContent'
      required:
        - id
        - date
        - content
    ReasoningMessageSource:
      type: string
      enum:
        - value: reasoner_model
        - value: non_reasoner_model
    ReasoningMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: reasoning_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        source:
          $ref: '#/components/schemas/ReasoningMessageSource'
        reasoning:
          type: string
        signature:
          type:
            - string
            - 'null'
      required:
        - id
        - date
        - reasoning
    HiddenReasoningMessageState:
      type: string
      enum:
        - value: redacted
        - value: omitted
    HiddenReasoningMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: hidden_reasoning_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        state:
          $ref: '#/components/schemas/HiddenReasoningMessageState'
        hidden_reasoning:
          type:
            - string
            - 'null'
      required:
        - id
        - date
        - state
    ToolCall:
      type: object
      properties:
        name:
          type: string
        arguments:
          type: string
        tool_call_id:
          type: string
      required:
        - name
        - arguments
        - tool_call_id
    ToolCallDelta:
      type: object
      properties:
        name:
          type:
            - string
            - 'null'
        arguments:
          type:
            - string
            - 'null'
        tool_call_id:
          type:
            - string
            - 'null'
    ToolCallMessageToolCall:
      oneOf:
        - $ref: '#/components/schemas/ToolCall'
        - $ref: '#/components/schemas/ToolCallDelta'
    ToolCallMessageToolCalls0:
      type: array
      items:
        $ref: '#/components/schemas/ToolCall'
    ToolCallMessageToolCalls:
      oneOf:
        - $ref: '#/components/schemas/ToolCallMessageToolCalls0'
        - $ref: '#/components/schemas/ToolCallDelta'
    ToolCallMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_call_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        tool_call:
          $ref: '#/components/schemas/ToolCallMessageToolCall'
        tool_calls:
          oneOf:
            - $ref: '#/components/schemas/ToolCallMessageToolCalls'
            - type: 'null'
      required:
        - id
        - date
        - tool_call
    ToolReturnMessageStatus:
      type: string
      enum:
        - value: success
        - value: error
    LettaSchemasLettaMessageToolReturnStatus:
      type: string
      enum:
        - value: success
        - value: error
    letta__schemas__letta_message__ToolReturn:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: tool
        tool_return:
          type: string
        status:
          $ref: '#/components/schemas/LettaSchemasLettaMessageToolReturnStatus'
        tool_call_id:
          type: string
        stdout:
          type:
            - array
            - 'null'
          items:
            type: string
        stderr:
          type:
            - array
            - 'null'
          items:
            type: string
      required:
        - tool_return
        - status
        - tool_call_id
    ToolReturnMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: tool_return_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        tool_return:
          type: string
        status:
          $ref: '#/components/schemas/ToolReturnMessageStatus'
        tool_call_id:
          type: string
        stdout:
          type:
            - array
            - 'null'
          items:
            type: string
        stderr:
          type:
            - array
            - 'null'
          items:
            type: string
        tool_returns:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/letta__schemas__letta_message__ToolReturn'
      required:
        - id
        - date
        - tool_return
        - status
        - tool_call_id
    LettaAssistantMessageContentUnion:
      oneOf:
        - $ref: '#/components/schemas/TextContent'
    AssistantMessageContent0:
      type: array
      items:
        $ref: '#/components/schemas/LettaAssistantMessageContentUnion'
    AssistantMessageContent:
      oneOf:
        - $ref: '#/components/schemas/AssistantMessageContent0'
        - type: string
    AssistantMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: assistant_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        content:
          $ref: '#/components/schemas/AssistantMessageContent'
      required:
        - id
        - date
        - content
    ApprovalRequestMessageToolCall:
      oneOf:
        - $ref: '#/components/schemas/ToolCall'
        - $ref: '#/components/schemas/ToolCallDelta'
    ApprovalRequestMessageToolCalls0:
      type: array
      items:
        $ref: '#/components/schemas/ToolCall'
    ApprovalRequestMessageToolCalls:
      oneOf:
        - $ref: '#/components/schemas/ApprovalRequestMessageToolCalls0'
        - $ref: '#/components/schemas/ToolCallDelta'
    ApprovalRequestMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: approval_request_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        tool_call:
          $ref: '#/components/schemas/ApprovalRequestMessageToolCall'
        tool_calls:
          oneOf:
            - $ref: '#/components/schemas/ApprovalRequestMessageToolCalls'
            - type: 'null'
      required:
        - id
        - date
        - tool_call
    ApprovalReturn:
      type: object
      properties:
        type:
          type: string
          enum:
            - type: stringLiteral
              value: approval
        tool_call_id:
          type: string
        approve:
          type: boolean
        reason:
          type:
            - string
            - 'null'
      required:
        - tool_call_id
        - approve
    ApprovalResponseMessageApprovalsItems:
      oneOf:
        - $ref: '#/components/schemas/ApprovalReturn'
        - $ref: '#/components/schemas/letta__schemas__letta_message__ToolReturn'
    ApprovalResponseMessage:
      type: object
      properties:
        id:
          type: string
        date:
          type: string
          format: date-time
        name:
          type:
            - string
            - 'null'
        message_type:
          type: string
          enum:
            - type: stringLiteral
              value: approval_response_message
        otid:
          type:
            - string
            - 'null'
        sender_id:
          type:
            - string
            - 'null'
        step_id:
          type:
            - string
            - 'null'
        is_err:
          type:
            - boolean
            - 'null'
        seq_id:
          type:
            - integer
            - 'null'
        run_id:
          type:
            - string
            - 'null'
        approvals:
          type:
            - array
            - 'null'
          items:
            $ref: '#/components/schemas/ApprovalResponseMessageApprovalsItems'
        approve:
          type:
            - boolean
            - 'null'
        approval_request_id:
          type:
            - string
            - 'null'
        reason:
          type:
            - string
            - 'null'
      required:
        - id
        - date
    V1StepsStepIdMessagesGetResponsesContentApplicationJsonSchemaItems:
      oneOf:
        - $ref: '#/components/schemas/SystemMessage'
        - $ref: '#/components/schemas/UserMessage'
        - $ref: '#/components/schemas/ReasoningMessage'
        - $ref: '#/components/schemas/HiddenReasoningMessage'
        - $ref: '#/components/schemas/ToolCallMessage'
        - $ref: '#/components/schemas/ToolReturnMessage'
        - $ref: '#/components/schemas/AssistantMessage'
        - $ref: '#/components/schemas/ApprovalRequestMessage'
        - $ref: '#/components/schemas/ApprovalResponseMessage'
```

Example 2 (python):
```python
from letta_client import Letta

client = Letta(
    project="YOUR_PROJECT",
    token="YOUR_TOKEN",
)
client.steps.messages.list(
    step_id="step-123e4567-e89b-42d3-8456-426614174000",
    before="before",
    after="after",
    limit=1,
    order="asc",
)
```

Example 3 (typescript):
```typescript
import { LettaClient } from "@letta-ai/letta-client";

const client = new LettaClient({ token: "YOUR_TOKEN", project: "YOUR_PROJECT" });
await client.steps.messages.list("step-123e4567-e89b-42d3-8456-426614174000", {
    before: "before",
    after: "after",
    limit: 1,
    order: "asc",
    orderBy: "created_at"
});
```

Example 4 (go):
```go
package main

import (
	"fmt"
	"net/http"
	"io"
)

func main() {

	url := "https://api.letta.com/v1/steps/step_id/messages"

	req, _ := http.NewRequest("GET", url, nil)

	req.Header.Add("Authorization", "Bearer <token>")

	res, _ := http.DefaultClient.Do(req)

	defer res.Body.Close()
	body, _ := io.ReadAll(res.Body)

	fmt.Println(res)
	fmt.Println(string(body))

}
```

---
