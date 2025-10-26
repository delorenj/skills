# Agno - Getting Started

**Pages:** 28

---

## Agent Infra AWS

**URL:** llms-txt#agent-infra-aws

**Contents:**
- Next

Source: https://docs.agno.com/templates/agent-infra-aws/introduction

The Agent Infra AWS template provides a simple AWS infrastructure for running AgentOS. It contains:

* An AgentOS instance, serving Agents, Teams, Workflows and utilities using FastAPI.
* A PostgreSQL database for storing sessions, memories and knowledge.

You can run your Agent Infra AWS locally as well as on AWS. This guide goes over the local setup first.

<Snippet file="setup.mdx" />

<Snippet file="create-agent-infra-aws-codebase.mdx" />

<Snippet file="run-agent-infra-aws-local.mdx" />

Congratulations on running your Agent Infra AWS locally. Next Steps:

* Read how to [update infra settings](/templates/infra-management/infra-settings)
* Read how to [create a git repository for your workspace](/templates/infra-management/git-repo)
* Read how to [manage the development application](/templates/infra-management/development-app)
* Read how to [format and validate your code](/templates/infra-management/format-and-validate)
* Read how to [add python libraries](/templates/infra-management/install)
* Chat with us on [discord](https://agno.link/discord)

---

## What is Agno?

**URL:** llms-txt#what-is-agno?

Source: https://docs.agno.com/introduction

**Agno is an incredibly fast multi-agent framework, runtime and control plane.**

Use it to build multi-agent systems with memory, knowledge, human in the loop and MCP support. You can orchestrate agents as multi-agent teams (more autonomy) or step-based agentic workflows (more control).

Here’s an example of an Agent that connects to an MCP server, manages conversation state in a database, and is served using a FastAPI application that you can interact with using the [AgentOS UI](https://os.agno.com).

```python agno_agent.py lines theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.tools.mcp import MCPTools

---

## Install dependencies

**URL:** llms-txt#install-dependencies

pip install "agno[infra]" openai exa_py python-dotenv

4. Create a new project with [AgentOS](/agent-os/introduction):

```bash
ag infra create              # Choose: [1] agent-infra-docker (default)

---

## Ask the agent to process web content

**URL:** llms-txt#ask-the-agent-to-process-web-content

**Contents:**
  - 3. Google Places Crawler

agent.print_response("Summarize the content from https://docs.agno.com/introduction", markdown=True)
python  theme={null}
from agno.agent import Agent
from agno.tools.apify import ApifyTools

agent = Agent(
    tools=[
        ApifyTools(actors=["compass/crawler-google-places"])
    ]
)

**Examples:**

Example 1 (unknown):
```unknown
### 3. Google Places Crawler

The [Google Places Crawler](https://apify.com/compass/crawler-google-places) extracts data about businesses from Google Maps and Google Places.
```

---

## Use the agent to get website content

**URL:** llms-txt#use-the-agent-to-get-website-content

**Contents:**
- Available Apify Tools
  - 1. RAG Web Browser

agent.print_response("What information can you find on https://docs.agno.com/introduction ?", markdown=True)
python  theme={null}
from agno.agent import Agent
from agno.tools.apify import ApifyTools

agent = Agent(
    tools=[
        ApifyTools(actors=["apify/rag-web-browser"])
    ],
        markdown=True
)

**Examples:**

Example 1 (unknown):
```unknown
## Available Apify Tools

You can easily integrate any Apify Actor as a tool. Here are some examples:

### 1. RAG Web Browser

The [RAG Web Browser](https://apify.com/apify/rag-web-browser) Actor is specifically designed for AI and LLM applications. It searches the web for a query or processes a URL, then cleans and formats the content for your agent. This tool is enabled by default.
```

---

## A2A

**URL:** llms-txt#a2a

**Contents:**
- Setup

Source: https://docs.agno.com/agent-os/interfaces/a2a/introduction

Expose your Agno Agent via the A2A protocol

Google's [Agent-to-Agent Protocol (A2A)](https://a2a-protocol.org/latest/topics/what-is-a2a/) aims at creating a standard way for Agents to communicate with each other.

Agno integrates seamlessly with A2A, allowing you to expose your Agno Agent and Teams in a A2A compatible way.

This is done with our `A2A` interface, which you can use with our [AgentOS](/agent-os/introduction) runtime.

You just need to set `a2a_interface=True` when creating your `AgentOS` instance and serve it as normal:

By default all the Agents, Teams and Workflows in the AgentOS will be exposed via `A2A`.

You can also specify which Agents, Teams and Workflows to expose:

```python a2a-interface-initialization.py theme={null}
from agno.agent import Agent
from agno.os import AgentOS
from agno.os.interfaces.a2a import A2A

agent = Agent(name="My Agno Agent")

**Examples:**

Example 1 (unknown):
```unknown
By default all the Agents, Teams and Workflows in the AgentOS will be exposed via `A2A`.

You can also specify which Agents, Teams and Workflows to expose:
```

---

## Introduction to Knowledge

**URL:** llms-txt#introduction-to-knowledge

**Contents:**
- The Problem with Knowledge-Free Agents
- Real-World Impact
  - Intelligent Text-to-SQL Agents
  - Customer Support Excellence
  - Internal Knowledge Assistant
- Ready to Get Started?

Source: https://docs.agno.com/concepts/knowledge/overview

Understand why Knowledge is essential for building intelligent, context-aware AI agents that provide accurate, relevant responses.

Imagine asking an AI agent about your company's HR policies, and instead of generic advice, it gives you precise answers based on your actual employee handbook. Or picture a customer support agent that knows your specific product details, pricing, and troubleshooting guides. This is the power of Knowledge in Agno.

## The Problem with Knowledge-Free Agents

Without access to specific information, AI agents can only rely on their general training data. This leads to:

* **Generic responses** that don't match your specific context
* **Outdated information** from training data that's months or years old
* **Hallucinations** when the agent guesses at facts it doesn't actually know
* **Limited usefulness** for domain-specific tasks or company-specific workflows

### Intelligent Text-to-SQL Agents

Build agents that know your exact database schema, column names, and common query patterns. Instead of guessing at table structures, they retrieve the specific schema information needed for each query, ensuring accurate SQL generation.

### Customer Support Excellence

Create a support agent with access to your complete product documentation, FAQ database, and troubleshooting guides. Customers get accurate answers instantly, without waiting for human agents to look up information.

### Internal Knowledge Assistant

Deploy an agent that knows your company's processes, policies, and institutional knowledge. New employees can get onboarding help, and existing team members can quickly find answers to complex procedural questions.

## Ready to Get Started?

Transform your agents from generic assistants to domain experts:

<CardGroup cols={2}>
  <Card title="Learn How It Works" icon="book-open" href="/concepts/knowledge/how-it-works">
    Understand the simple RAG pipeline behind intelligent knowledge retrieval
  </Card>

<Card title="Build Your First Agent" icon="rocket" href="/concepts/knowledge/getting-started">
    Follow our quick tutorial to create a knowledge-powered agent in minutes
  </Card>
</CardGroup>

---

## Getting Help

**URL:** llms-txt#getting-help

**Contents:**
- Need help?
- Building with Agno?
- Looking for dedicated support?

Source: https://docs.agno.com/introduction/getting-help

Connect with builders, get support, and explore Agent Engineering.

Head over to our [community forum](https://agno.link/community) for help and insights from the team.

## Building with Agno?

Share what you're building on [X](https://agno.link/x), [LinkedIn](https://www.linkedin.com/company/agno-agi) or join our [Discord](https://agno.link/discord) to connect with other builders.

## Looking for dedicated support?

We've helped many companies turn ideas into AI products. [Book a call](https://cal.com/team/agno/intro) to get started.

---

## Introduction

**URL:** llms-txt#introduction

**Contents:**
- Setup
- Examples

Source: https://docs.agno.com/examples/getting-started/introduction

This guide walks through the basics of building Agents with Agno.

The examples build on each other, introducing new concepts and capabilities progressively. Each example contains detailed comments, example prompts, and required dependencies.

Create a virtual environment:

Install the required dependencies:

Export your OpenAI API key:

<CardGroup cols={3}>
  <Card title="Basic Agent" icon="robot" iconType="duotone" href="./01-basic-agent">
    Build a news reporter with a vibrant personality. This Agent only shows basic LLM inference.
  </Card>

<Card title="Agent with Tools" icon="toolbox" iconType="duotone" href="./02-agent-with-tools">
    Add web search capabilities using DuckDuckGo for real-time information gathering.
  </Card>

<Card title="Agent with Knowledge" icon="brain" iconType="duotone" href="./03-agent-with-knowledge">
    Add a vector database to your agent to store and search knowledge.
  </Card>

<Card title="Agent with Storage" icon="database" iconType="duotone" href="./06-agent-with-storage">
    Add persistence to your agents with session management and history capabilities.
  </Card>

<Card title="Agent Team" icon="users" iconType="duotone" href="./17-agent-team">
    Create an agent team specializing in market research and financial analysis.
  </Card>

<Card title="Structured Output" icon="code" iconType="duotone" href="./05-structured-output">
    Generate a structured output using a Pydantic model.
  </Card>

<Card title="Custom Tools" icon="wrench" iconType="duotone" href="./04-write-your-own-tool">
    Create and integrate custom tools with your agent.
  </Card>

<Card title="Research Agent" icon="magnifying-glass" iconType="duotone" href="./18-research-agent-exa">
    Build an AI research agent using Exa with controlled output steering.
  </Card>

<Card title="Research Workflow" icon="diagram-project" iconType="duotone" href="./19-blog-generator-workflow">
    Create a research workflow combining web searches and content scraping.
  </Card>

<Card title="Image Agent" icon="image" iconType="duotone" href="./13-image-agent">
    Create an agent that can understand images.
  </Card>

<Card title="Image Generation" icon="paintbrush" iconType="duotone" href="./14-image-generation">
    Create an Agent that can generate images using DALL-E.
  </Card>

<Card title="Video Generation" icon="video" iconType="duotone" href="./15-video-generation">
    Create an Agent that can generate videos using ModelsLabs.
  </Card>

<Card title="Audio Agent" icon="microphone" iconType="duotone" href="./16-audio-agent">
    Create an Agent that can process audio input and generate responses.
  </Card>

<Card title="Agent with State" icon="database" iconType="duotone" href="./07-agent-state">
    Create an Agent with session state management.
  </Card>

<Card title="Agent Context" icon="sitemap" iconType="duotone" href="./08-agent-context">
    Evaluate dependencies at agent.run and inject them into the instructions.
  </Card>

<Card title="Agent Session" icon="clock-rotate-left" iconType="duotone" href="./09-agent-session">
    Create an Agent with persistent session memory across conversations.
  </Card>

<Card title="User Memories" icon="memory" iconType="duotone" href="./10-user-memories-and-summaries">
    Create an Agent that stores user memories and summaries.
  </Card>

<Card title="Function Retries" icon="rotate" iconType="duotone" href="./11-retry-function-call">
    Handle function retries for failed or unsatisfactory outputs.
  </Card>

<Card title="Human in the Loop" icon="user-check" iconType="duotone" href="./12-human-in-the-loop">
    Add user confirmation and safety checks for interactive agent control.
  </Card>
</CardGroup>

Each example includes runnable code and detailed explanations. We recommend following them in order, as concepts build upon previous examples.

**Examples:**

Example 1 (unknown):
```unknown
Install the required dependencies:
```

Example 2 (unknown):
```unknown
Export your OpenAI API key:
```

---

## Examples Gallery

**URL:** llms-txt#examples-gallery

**Contents:**
- Getting Started
- Use Cases
- Agent Concepts
- Models

Source: https://docs.agno.com/examples/introduction

Explore Agno's example gallery showcasing everything from single-agent tasks to sophisticated multi-agent workflows.

Welcome to Agno's example gallery! Here you'll discover examples showcasing everything from **single-agent tasks** to sophisticated **multi-agent workflows**. You can either:

* Run the examples individually
* Clone the entire [Agno cookbook](https://github.com/agno-agi/agno/tree/main/cookbook)

Have an interesting example to share? Please consider [contributing](https://github.com/agno-agi/agno-docs) to our growing collection.

If you're just getting started, follow the [Getting Started](/examples/getting-started) guide for a step-by-step tutorial. The examples build on each other, introducing new concepts and capabilities progressively.

Build real-world applications with Agno.

<CardGroup cols={3}>
  <Card title="Simple Agents" icon="user-astronaut" iconType="duotone" href="/examples/use-cases/agents">
    Simple agents for web scraping, data processing, financial analysis, etc.
  </Card>

<Card title="Multi-Agent Teams" icon="people-group" iconType="duotone" href="/examples/use-cases/teams/">
    Multi-agent teams that collaborate to solve tasks.
  </Card>

<Card title="Advanced Workflows" icon="diagram-project" iconType="duotone" href="/examples/use-cases/workflows/">
    Advanced workflows for creating blog posts, investment reports, etc.
  </Card>
</CardGroup>

Explore Agent concepts with detailed examples.

<CardGroup cols={3}>
  <Card title="Multimodal" icon="image" iconType="duotone" href="/examples/concepts/multimodal">
    Learn how to use multimodal Agents
  </Card>

<Card title="Knowledge" icon="brain-circuit" iconType="duotone" href="/examples/concepts/knowledge">
    Add domain-specific knowledge to your Agents
  </Card>

<Card title="RAG" icon="book-bookmark" iconType="duotone" href="/examples/concepts/knowledge/rag">
    Learn how to use Agentic RAG
  </Card>

<Card title="Hybrid search" icon="magnifying-glass-plus" iconType="duotone" href="/examples/concepts/knowledge/search_type/hybrid-search">
    Combine semantic and keyword search
  </Card>

<Card title="Memory" icon="database" iconType="duotone" href="/examples/concepts/memory">
    Let Agents remember past conversations
  </Card>

<Card title="Tools" icon="screwdriver-wrench" iconType="duotone" href="/examples/concepts/tools">
    Extend your Agents with 100s or tools
  </Card>

<Card title="Storage" icon="hard-drive" iconType="duotone" href="/examples/concepts/db">
    Store Agents sessions in a database
  </Card>

<Card title="Vector Databases" icon="database" iconType="duotone" href="/examples/concepts/vectordb">
    Store Knowledge in Vector Databases
  </Card>

<Card title="Embedders" icon="database" iconType="duotone" href="/examples/concepts/knowledge/embedders">
    Convert text to embeddings to store in VectorDbs
  </Card>
</CardGroup>

Explore different models with Agno.

<CardGroup cols={3}>
  <Card title="OpenAI" icon="network-wired" iconType="duotone" href="/examples/models/openai">
    Examples using OpenAI GPT models
  </Card>

<Card title="Ollama" icon="laptop-code" iconType="duotone" href="/examples/models/ollama">
    Examples using Ollama models locally
  </Card>

<Card title="Anthropic" icon="network-wired" iconType="duotone" href="/examples/models/anthropic">
    Examples using Anthropic models like Claude
  </Card>

<Card title="Cohere" icon="brain-circuit" iconType="duotone" href="/examples/models/cohere">
    Examples using Cohere command models
  </Card>

<Card title="DeepSeek" icon="circle-nodes" iconType="duotone" href="/examples/models/deepseek">
    Examples using DeepSeek models
  </Card>

<Card title="Gemini" icon="google" iconType="duotone" href="/examples/models/gemini">
    Examples using Google Gemini models
  </Card>

<Card title="Groq" icon="bolt" iconType="duotone" href="/examples/models/groq">
    Examples using Groq's fast inference
  </Card>

<Card title="Mistral" icon="wind" iconType="duotone" href="/examples/models/mistral">
    Examples using Mistral models
  </Card>

<Card title="Azure" icon="microsoft" iconType="duotone" href="/examples/models/azure">
    Examples using Azure OpenAI
  </Card>

<Card title="Fireworks" icon="sparkles" iconType="duotone" href="/examples/models/fireworks">
    Examples using Fireworks models
  </Card>

<Card title="AWS" icon="aws" iconType="duotone" href="/examples/models/aws">
    Examples using Amazon Bedrock
  </Card>

<Card title="Hugging Face" icon="face-awesome" iconType="duotone" href="/examples/models/huggingface">
    Examples using Hugging Face models
  </Card>

<Card title="NVIDIA" icon="microchip" iconType="duotone" href="/examples/models/nvidia">
    Examples using NVIDIA models
  </Card>

<Card title="Nebius" icon="people-group" iconType="duotone" href="/examples/models/nebius">
    Examples using Nebius AI models
  </Card>

<Card title="Together" icon="people-group" iconType="duotone" href="/examples/models/together">
    Examples using Together AI models
  </Card>

<Card title="xAI" icon="brain-circuit" iconType="duotone" href="/examples/models/xai">
    Examples using xAI models
  </Card>

<Card title="LangDB" icon="rust" iconType="duotone" href="/examples/models/langdb">
    Examples using LangDB AI Gateway.
  </Card>
</CardGroup>

---

## Designed for Agent Engineering

**URL:** llms-txt#designed-for-agent-engineering

**Contents:**
  - Core Intelligence
  - Memory, Knowledge, and Persistence
  - Execution & Control
  - Runtime & Evaluation
  - Security & Privacy

Source: https://docs.agno.com/introduction/features

Agno is built for real-world **Agent Engineering**, helping engineers build, deploy, and scale multi-agent systems in production. Here are some key features that make Agno stand out:

### Core Intelligence

* **Model Agnostic**: Works with any model provider so you can use your favorite LLMs.

* **Type Safe**: Enforce structured I/O through `input_schema` and `output_schema` for predictable, composable behavior.

* **Dynamic Context Engineering**: Inject variables, state, and retrieved data on the fly into context. Perfect for dependency-driven agents.

### Memory, Knowledge, and Persistence

* **Persistent Storage**: Give your Agents, Teams, and Workflows a database to persist session history, state, and messages.

* **User Memory**: Built-in memory system that allows Agents to recall user-specific context across sessions.

* **Agentic RAG**: Connect to 20+ vector stores (called **Knowledge** in Agno) with hybrid search + reranking out of the box.

* **Culture (Collective Memory)**: Shared knowledge that compounds across agents and time.

### Execution & Control

* **Human-in-the-Loop**: Native support for confirmations, manual overrides, and external tool execution.

* **Guardrails**: Built-in safeguards for validation, security, and prompt protection.

* **Agent Lifecycle Hooks**: Pre- and post-hooks to validate or transform inputs and outputs.

* **MCP Integration**: First-class support for the Model Context Protocol (MCP) to connect Agents with external systems.

* **Toolkits**: 113+ built-in toolkits with thousands of tools — ready for use across domains like data, code, web, and enterprise APIs.

### Runtime & Evaluation

* **Runtime**: Pre-built FastAPI based runtime with SSE compatible endpoints, ready for production on day 1.

* **Control Plane (UI)**: Integrated interface to visualize, monitor, and debug agent activity in real time.

* **Natively Multimodal**: Agents can process and generate text, images, audio, video, and files.

* **Evals**: Measure your Agents' Accuracy, Performance, and Reliability.

### Security & Privacy

* **Private by Design**: Runs entirely in your cloud. The UI connects directly to your AgentOS from your browser — no data is ever sent externally.

* **Data Governance**: Your data lives securely in your Agent database, with no external data sharing or vendor lock-in.

* **Access Control**: Role-based access (RBAC) and per-agent permissions to protect sensitive contexts and tools.

Every part of Agno is built for real-world deployment, where developer experience meets production performance.

---

## Singlestore

**URL:** llms-txt#singlestore

**Contents:**
- Usage

Source: https://docs.agno.com/concepts/db/singlestore

Learn to use Singlestore as a database for your Agents

Agno supports using [Singlestore](https://www.singlestore.com/) as a database with the `SingleStoreDb` class.

You can get started with Singlestore following their [documentation](https://docs.singlestore.com/db/v9.0/introduction/).

```python singlestore_for_agent.py theme={null}
from os import getenv

from agno.agent import Agent
from agno.db.singlestore import SingleStoreDb

---

## The agent will first search for relevant URLs, then analyze their content in detail

**URL:** llms-txt#the-agent-will-first-search-for-relevant-urls,-then-analyze-their-content-in-detail

**Contents:**
- Usage

agent.print_response(
    "Analyze the content of the following URL: https://docs.agno.com/introduction and also give me latest updates on AI agents"
)
bash  theme={null}
    export GOOGLE_API_KEY=xxx
    bash  theme={null}
    pip install -U google-genai agno
    bash Mac theme={null}
      python cookbook/models/google/gemini/url_context_with_search.py
      bash Windows theme={null}
      python cookbook/models/google/gemini/url_context_with_search.py
      ```
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set your API key">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## AG-UI

**URL:** llms-txt#ag-ui

**Contents:**
- Example usage
- Custom Events
- Core Components
- `AGUI` interface
  - Initialization Parameters
  - Key Method
- Endpoints
- Serving your AgentOS
  - Parameters

Source: https://docs.agno.com/agent-os/interfaces/ag-ui/introduction

Expose your Agno Agent via the AG-UI protocol

AG-UI, the [Agent-User Interaction Protocol](https://github.com/ag-ui-protocol/ag-ui), standardizes how AI agents connect to front-end applications.

<Note>
  **Migration from Apps**: If you're migrating from `AGUIApp`, see the [v2 migration guide](/how-to/v2-migration#7-apps-interfaces) for complete steps.
</Note>

<Steps>
  <Step title="Install backend dependencies">
    
  </Step>

<Step title="Run the backend">
    Expose an Agno Agent through the AG-UI interface using `AgentOS` and `AGUI`.

<Step title="Run the frontend">
    Use Dojo (`ag-ui`'s frontend) as an advanced, customizable interface for AG-UI agents.

1. Clone: `git clone https://github.com/ag-ui-protocol/ag-ui.git`
    2. Install dependencies in `/ag-ui/typescript-sdk`: `pnpm install`
    3. Build the Agno package in `/ag-ui/integrations/agno`: `pnpm run build`
    4. Start Dojo following the instructions in the repository.
  </Step>

<Step title="Chat with your Agno Agent">
    With Dojo running, open `http://localhost:3000` and select your Agno agent.
  </Step>
</Steps>

You can see more in our [cookbook examples](https://github.com/agno-agi/agno/tree/main/cookbook/agent_os/interfaces/agui/).

Custom events you create in your tools are automatically delivered to AG-UI in the AG-UI custom event format.

**Creating custom events:**

**Yielding from tools:**

Custom events are streamed in real-time to the AG-UI frontend.

See [Custom Events documentation](/concepts/agents/running-agents#custom-events) for more details.

* `AGUI` (interface): Wraps an Agno `Agent` or `Team` into an AG-UI compatible FastAPI router.
* `AgentOS.serve`: Serves your FastAPI app (including the AGUI router) with Uvicorn.

`AGUI` mounts protocol-compliant routes on your app.

Main entry point for AG-UI exposure.

### Initialization Parameters

| Parameter | Type              | Default | Description            |
| --------- | ----------------- | ------- | ---------------------- |
| `agent`   | `Optional[Agent]` | `None`  | Agno `Agent` instance. |
| `team`    | `Optional[Team]`  | `None`  | Agno `Team` instance.  |

Provide `agent` or `team`.

| Method       | Parameters               | Return Type | Description                                              |
| ------------ | ------------------------ | ----------- | -------------------------------------------------------- |
| `get_router` | `use_async: bool = True` | `APIRouter` | Returns the AG-UI FastAPI router and attaches endpoints. |

Mounted at the interface's route prefix (root by default):

* `POST /agui`: Main entrypoint. Accepts `RunAgentInput` from `ag-ui-protocol`. Streams AG-UI events.
* `GET /status`: Health/status endpoint for the interface.

Refer to `ag-ui-protocol` docs for payload details.

## Serving your AgentOS

Use `AgentOS.serve` to run your app with Uvicorn.

| Parameter | Type                  | Default       | Description                            |
| --------- | --------------------- | ------------- | -------------------------------------- |
| `app`     | `Union[str, FastAPI]` | required      | FastAPI app instance or import string. |
| `host`    | `str`                 | `"localhost"` | Host to bind.                          |
| `port`    | `int`                 | `7777`        | Port to bind.                          |
| `reload`  | `bool`                | `False`       | Enable auto-reload for development.    |

See [cookbook examples](https://github.com/agno-agi/agno/tree/main/cookbook/agent_os/interfaces/agui/) for updated interface patterns.

**Examples:**

Example 1 (unknown):
```unknown
</Step>

  <Step title="Run the backend">
    Expose an Agno Agent through the AG-UI interface using `AgentOS` and `AGUI`.
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run the frontend">
    Use Dojo (`ag-ui`'s frontend) as an advanced, customizable interface for AG-UI agents.

    1. Clone: `git clone https://github.com/ag-ui-protocol/ag-ui.git`
    2. Install dependencies in `/ag-ui/typescript-sdk`: `pnpm install`
    3. Build the Agno package in `/ag-ui/integrations/agno`: `pnpm run build`
    4. Start Dojo following the instructions in the repository.
  </Step>

  <Step title="Chat with your Agno Agent">
    With Dojo running, open `http://localhost:3000` and select your Agno agent.
  </Step>
</Steps>

You can see more in our [cookbook examples](https://github.com/agno-agi/agno/tree/main/cookbook/agent_os/interfaces/agui/).

## Custom Events

Custom events you create in your tools are automatically delivered to AG-UI in the AG-UI custom event format.

**Creating custom events:**
```

Example 3 (unknown):
```unknown
**Yielding from tools:**
```

---

## MCP Toolbox

**URL:** llms-txt#mcp-toolbox

**Contents:**
- Prerequisites
- Quick Start

Source: https://docs.agno.com/concepts/tools/mcp/mcp-toolbox

Learn how to use MCPToolbox with Agno to connect to MCP Toolbox for Databases with tool filtering capabilities.

**MCPToolbox** enables Agents to connect to Google's [MCP Toolbox for Databases](https://googleapis.github.io/genai-toolbox/getting-started/introduction/) with advanced filtering capabilities. It extends Agno's `MCPTools` functionality to filter tools by toolset or tool name, allowing agents to load only the specific database tools they need.

You'll need the following to use MCPToolbox:

Our default setup will also require you to have Docker or Podman installed, to run the MCP Toolbox server and database for the examples.

Get started with MCPToolbox instantly using our fully functional demo.

```bash  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
Our default setup will also require you to have Docker or Podman installed, to run the MCP Toolbox server and database for the examples.

## Quick Start

Get started with MCPToolbox instantly using our fully functional demo.
```

---

## Parallel and custom function step streaming on AgentOS

**URL:** llms-txt#parallel-and-custom-function-step-streaming-on-agentos

Source: https://docs.agno.com/examples/concepts/workflows/04-workflows-parallel-execution/parallel_and_custom_function_step_streaming_agentos

This example demonstrates how to use parallel steps with custom function executors and streaming on AgentOS.

This example demonstrates how to use using steps with custom function
executors, and how to stream their responses using the [AgentOS](/agent-os/introduction).

The agents and teams running inside the custom function step in `Parallel` will also stream their results to the AgentOS.

```python parallel_and_custom_function_step_streaming_agentos.py theme={null}
from typing import AsyncIterator, Union

from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.run.workflow import WorkflowRunOutputEvent
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.parallel import Parallel
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## What is AgentOS?

**URL:** llms-txt#what-is-agentos?

**Contents:**
- Overview
- Getting Started
- Security & Privacy First
  - Complete Data Ownership
- Next Steps

Source: https://docs.agno.com/agent-os/introduction

The production runtime and control plane for your agentic systems

AgentOS is Agno's production-ready runtime that runs entirely within your own infrastructure, ensuring complete data privacy and control of your agentic system.
Agno also provides a beautiful web interface for managing, monitoring, and interacting with your AgentOS, with no data ever being persisted outside of your environment.

<Check>
  Behind the scenes, AgentOS is a FastAPI app that you can run locally or in your cloud. It is designed to be easy to deploy and scale.
</Check>

Ready to get started with AgentOS? Here's what you need to do:

<CardGroup cols={2}>
  <Card title="Create Your First OS" icon="plus" href="/agent-os/creating-your-first-os">
    Set up a new AgentOS instance from scratch using our templates
  </Card>

<Card title="Connect Your AgentOS" icon="link" href="/agent-os/connecting-your-os">
    Learn how to connect your local development environment to the platform
  </Card>
</CardGroup>

## Security & Privacy First

AgentOS is designed with enterprise security and data privacy as foundational principles, not afterthoughts.

<Frame>
  <img src="https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-secure-infra-illustration.png?fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=b13db5d4b3c25eb5508752f7d3474b51" alt="AgentOS Security and Privacy Architecture" style={{ borderRadius: "0.5rem" }} data-og-width="3258" width="3258" data-og-height="1938" height="1938" data-path="images/agentos-secure-infra-illustration.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-secure-infra-illustration.png?w=280&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=c548641b352030a8fee914cd49919417 280w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-secure-infra-illustration.png?w=560&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=9640bb14a9d22619973e7efb20ab1be5 560w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-secure-infra-illustration.png?w=840&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=82645dfaae8f0155bc3912cdfaf656cc 840w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-secure-infra-illustration.png?w=1100&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=ba5cf9921c1b389d58216ba71ef38515 1100w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-secure-infra-illustration.png?w=1650&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=d7ca28c6e75259c18b08783224c1a2e4 1650w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-secure-infra-illustration.png?w=2500&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=122528a3dc3ecf7789fb1b076be48f08 2500w" />
</Frame>

### Complete Data Ownership

* **Your Infrastructure, Your Data**: AgentOS runs entirely within your cloud environment
* **Zero Data Transmission**: No conversations, logs, or metrics are sent to external services
* **Private by Default**: All processing, storage, and analytics happen locally

To learn more about AgentOS Security, check out the [AgentOS Security](/agent-os/security) page.

<CardGroup cols={2}>
  <Card title="Control Plane" icon="desktop" href="/agent-os/control-plane">
    Learn how to use the AgentOS control plane to manage and monitor your OSs
  </Card>

<Card title="Create Your First OS" icon="rocket" href="/agent-os/creating-your-first-os">
    Get started by creating your first AgentOS instance
  </Card>
</CardGroup>

---

## Quickstart

**URL:** llms-txt#quickstart

**Contents:**
- Build your first Agent

Source: https://docs.agno.com/introduction/quickstart

Build and run your first Agent using Agno.

**Agents are AI programs where a language model controls the flow of execution.**

In 10 lines of code, we can build an Agent that uses tools to achieve a task.

## Build your first Agent

Instead of a toy demo, let's build an Agent that you can extend and build upon. We'll connect our agent to the Agno MCP server, and give it a database to store conversation history and state.

**This is a simple yet complete example that you can extend by connecting to any MCP server**.

```python agno_agent.py lines theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.tools.mcp import MCPTools

**Examples:**

Example 1 (unknown):
```unknown
## Build your first Agent

Instead of a toy demo, let's build an Agent that you can extend and build upon. We'll connect our agent to the Agno MCP server, and give it a database to store conversation history and state.

**This is a simple yet complete example that you can extend by connecting to any MCP server**.
```

---

## Add documentation content

**URL:** llms-txt#add-documentation-content

knowledge.add_contents(urls=["https://docs.agno.com/introduction/agents.md"])

---

## Deploy your AgentOS

**URL:** llms-txt#deploy-your-agentos

**Contents:**
- Overview
- What is A Template?
- Here's How They Work

Source: https://docs.agno.com/deploy/introduction

How to take your AgentOS to production

You can build, test, and improve your AgentOS locally, but to run it in production you’ll need to deploy it to your own infrastructure. Because it’s pure Python code, you’re free to deploy AgentOS anywhere. To make things easier, we’ve also put together a set of ready to use templates - standardized codebases you can use to quickly deploy AgentOS to your own infrastructure.

Currently supported templates:

Docker Template: [agent-infra-docker](https://github.com/agno-agi/agent-infra-docker)
AWS Template: [agent-infra-aws](https://github.com/agno-agi/agent-infra-aws)

* Modal Template
* Railway Template
* Render Template
* GCP Template

## What is A Template?

A template is a standardized codebase for a production AgentOS. It contains:

* An AgentOS instance using FastAPI.
* A Database for storing Sessions, Memories, Knowledge and Evals.

They are setup to run locally using docker and on cloud providers. They're a fantastic starting point and exactly what we use for our customers. You'll definitely need to customize them to fit your specific needs, but they'll get you started much faster.

## Here's How They Work

**Step 1**: Create your codebase using: `ag infra create` and choose a template.

This will clone one of our templates and give you a starting point.

**Step 2**: `cd` into your codebase and run locally using docker: `ag infra up`

This will start your AgentOS instance and PostgreSQL database locally using docker.

**Step 3 (For AWS template)**: Run on AWS: `ag infra up prd:aws`

This will start your AgentOS instance and PostgreSQL database on AWS.

We recommend starting with the `agent-infra-docker` template and taking it from there.

<CardGroup cols={2}>
  <Card title="Agent Infra Docker " icon="server" href="/templates/agent-infra-docker">
    An AgentOS template with a docker compose file.
  </Card>

<Card title="Agent Infra AWS" icon="server" href="/templates/agent-infra-aws">
    An AgentOS template with a AWS infrastructure.
  </Card>
</CardGroup>

---

## Cancelling a Run

**URL:** llms-txt#cancelling-a-run

Source: https://docs.agno.com/concepts/teams/run-cancel

Learn how to cancel a team run.

You can cancel a run by using the `cancel_run` function on the Team.

Below is a basic example that starts an team run in a thread and cancels it from another thread, simulating how it can be done via an API. This is supported via [AgentOS](/agent-os/introduction) as well.

For a more complete example, see [Cancel a run](https://github.com/agno-agi/agno/tree/main/cookbook/teams/basic/team_cancel_a_run.py).

---

## Getting Started with Knowledge

**URL:** llms-txt#getting-started-with-knowledge

**Contents:**
- What You'll Build
- Prerequisites
- Step 1: Set Up Your Knowledge Base

Source: https://docs.agno.com/concepts/knowledge/getting-started

Build your first knowledge-powered agent in three simple steps with this hands-on tutorial.

Ready to build your first intelligent agent? This guide will walk you through creating a knowledge-powered agent that can answer questions about your documents in just a few minutes.

By the end of this tutorial, you'll have an agent that can:

* Read and understand your documents or website content
* Answer specific questions based on that information
* Provide sources for its responses
* Search intelligently without you having to specify what to look for

<Steps>
  <Step title="Install Agno">
    
  </Step>

<Step title="Set up your API key">

<Note>This tutorial uses OpenAI, but Agno supports [many other models](/concepts/models/overview).</Note>
  </Step>
</Steps>

## Step 1: Set Up Your Knowledge Base

First, let's create a knowledge base with a vector database to store your information:

```python knowledge_agent.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.models.openai import OpenAIChat

**Examples:**

Example 1 (unknown):
```unknown
</Step>

  <Step title="Set up your API key">
```

Example 2 (unknown):
```unknown
<Note>This tutorial uses OpenAI, but Agno supports [many other models](/concepts/models/overview).</Note>
  </Step>
</Steps>

## Step 1: Set Up Your Knowledge Base

First, let's create a knowledge base with a vector database to store your information:
```

---

## Performance

**URL:** llms-txt#performance

**Contents:**
- Agent Performance
  - Instantiation Time

Source: https://docs.agno.com/introduction/performance

Get extreme performance out of the box with Agno.

If you're building with Agno, you're guaranteed best-in-class performance by default. Our obsession with performance is necessary because even simple AI workflows can spawn hundreds of Agents and because many tasks are long-running -- stateless, horizontal scalability is key for success.

At Agno, we optimize performance across 3 dimensions:

1. **Agent performance:** We optimize static operations (instantiation, memory footprint) and runtime operations (tool calls, memory updates, history management).
2. **System performance:** The AgentOS API is async by default and has a minimal memory footprint. The system is stateless and horizontally scalable, with a focus on preventing memory leaks. It handles parallel and batch embedding generation during knowledge ingestion, metrics collection in background tasks, and other system-level optimizations.
3. **Agent reliability and accuracy:** Monitored through evals, which we’ll explore later.

Let's measure the time it takes to instantiate an Agent and the memory footprint of an Agent. Here are the numbers (last measured in Oct 2025, on an Apple M4 MacBook Pro):

* **Agent instantiation:** \~3μs on average
* **Memory footprint:** \~6.6Kib on average

We'll show below that Agno Agents instantiate **529× faster than Langgraph**, **57× faster than PydanticAI**, and **70× faster than CrewAI**. Agno Agents also use **24× lower memory than Langgraph**, **4× lower than PydanticAI**, and **10× lower than CrewAI**.

<Note>
  Run time performance is bottlenecked by inference and hard to benchmark accurately, so we focus on minimizing overhead, reducing memory usage, and parallelizing tool calls.
</Note>

### Instantiation Time

Let's measure instantiation time for an Agent with 1 tool. We'll run the evaluation 1000 times to get a baseline measurement. We'll compare Agno to LangGraph, CrewAI and Pydantic AI.

<Note>
  The code for this benchmark is available [here](https://github.com/agno-agi/agno/tree/main/cookbook/evals/performance). You should run the evaluation yourself on your own machine, please, do not take these results at face value.
</Note>

```shell  theme={null}

---

## Step with custom function streaming on AgentOS

**URL:** llms-txt#step-with-custom-function-streaming-on-agentos

Source: https://docs.agno.com/examples/concepts/workflows/01-basic-workflows/step_with_function_streaming_agentos

This example demonstrates how to use named steps with custom function executors and streaming on AgentOS.

This example demonstrates how to use Step objects with custom function executors, and how to stream their responses using the [AgentOS](/agent-os/introduction).

The agent and team running inside the custom function step can also stream their results directly to the AgentOS.

```python step_with_function_streaming_agentos.py theme={null}
from typing import AsyncIterator, Union

from agno.agent.agent import Agent
from agno.db.in_memory import InMemoryDb

---

## Example 1: Scrape a webpage as Markdown

**URL:** llms-txt#example-1:-scrape-a-webpage-as-markdown

**Contents:**
- Usage

agent.print_response(
    "Scrape this webpage as markdown: https://docs.agno.com/introduction",
)
bash  theme={null}
    export OPENAI_API_KEY=xxx
    export BRIGHT_DATA_API_KEY=xxx
    bash  theme={null}
    pip install -U requests openai agno
    bash Mac theme={null}
      python cookbook/tools/brightdata_tools.py
      bash Windows theme={null}
      python cookbook/tools/brightdata_tools.py
      ```
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set your API keys">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Eleven Labs

**URL:** llms-txt#eleven-labs

**Contents:**
- Prerequisites
- Example

Source: https://docs.agno.com/concepts/tools/toolkits/others/eleven_labs

**ElevenLabsTools** enable an Agent to perform audio generation tasks using [ElevenLabs](https://elevenlabs.io/docs/product/introduction)

You need to install the `elevenlabs` library and an API key which can be obtained from [Eleven Labs](https://elevenlabs.io/)

Set the `ELEVEN_LABS_API_KEY` environment variable.

The following agent will use Eleven Labs to generate audio based on a user prompt.

```python cookbook/tools/eleven_labs_tools.py theme={null}
from agno.agent import Agent
from agno.tools.eleven_labs import ElevenLabsTools

**Examples:**

Example 1 (unknown):
```unknown
Set the `ELEVEN_LABS_API_KEY` environment variable.
```

Example 2 (unknown):
```unknown
## Example

The following agent will use Eleven Labs to generate audio based on a user prompt.
```

---

## Whatsapp

**URL:** llms-txt#whatsapp

**Contents:**
- Setup
- Example Usage
- Core Components
- `Whatsapp` Interface
  - Initialization Parameters
  - Key Method
- Endpoints
  - `GET /whatsapp/status`
  - `GET /whatsapp/webhook`
  - `POST /whatsapp/webhook`

Source: https://docs.agno.com/agent-os/interfaces/whatsapp/introduction

Host agents as Whatsapp Applications.

Use the WhatsApp interface to serve Agents or Teams via WhatsApp. It mounts webhook routes on a FastAPI app and sends responses back to WhatsApp users and threads.

Follow the WhatsApp setup guide in the [Whatsapp Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/agent_os/interfaces/whatsapp/readme.md).

You will need environment variables:

* `WHATSAPP_ACCESS_TOKEN`
* `WHATSAPP_PHONE_NUMBER_ID`
* `WHATSAPP_VERIFY_TOKEN`
* Optional (production): `WHATSAPP_APP_SECRET` and `APP_ENV=production`

<Note>
  The user's phone number is automatically used as the `user_id` for runs. This ensures that sessions and memory are appropriately scoped to the user.

The phone number is also used for the `session_id` so a single Whatsapp conversation will be a single session. It is important to take this into account when considering session history.
</Note>

Create an agent, expose it with the `Whatsapp` interface, and serve via `AgentOS`:

See more in our [cookbook examples](https://github.com/agno-agi/agno/tree/main/cookbook/agent_os/interfaces/whatsapp/).

* `Whatsapp` (interface): Wraps an Agno `Agent` or `Team` for WhatsApp via FastAPI.
* `AgentOS.serve`: Serves the FastAPI app using Uvicorn.

## `Whatsapp` Interface

Main entry point for Agno WhatsApp applications.

### Initialization Parameters

| Parameter | Type              | Default | Description            |
| --------- | ----------------- | ------- | ---------------------- |
| `agent`   | `Optional[Agent]` | `None`  | Agno `Agent` instance. |
| `team`    | `Optional[Team]`  | `None`  | Agno `Team` instance.  |

Provide `agent` or `team`.

| Method       | Parameters               | Return Type | Description                                        |
| ------------ | ------------------------ | ----------- | -------------------------------------------------- |
| `get_router` | `use_async: bool = True` | `APIRouter` | Returns the FastAPI router and attaches endpoints. |

Mounted under the `/whatsapp` prefix:

### `GET /whatsapp/status`

* Health/status of the interface.

### `GET /whatsapp/webhook`

* Verifies WhatsApp webhook (`hub.challenge`).
* Returns `hub.challenge` on success; `403` on token mismatch; `500` if `WHATSAPP_VERIFY_TOKEN` missing.

### `POST /whatsapp/webhook`

* Receives WhatsApp messages and events.
* Validates signature (`X-Hub-Signature-256`); bypassed in development mode.
* Processes text, image, video, audio, and document messages via the agent/team.
* Sends replies (splits long messages; uploads and sends generated images).
* Responses: `200 {"status": "processing"}` or `{"status": "ignored"}`, `403` invalid signature, `500` errors.

---

## Agent Infra Docker

**URL:** llms-txt#agent-infra-docker

Source: https://docs.agno.com/templates/agent-infra-docker/introduction

The Agent Infra Docker template provides a simple Docker Compose file for running AgentOS. It contains:

* An AgentOS instance, serving Agents, Teams, Workflows and utilities using FastAPI.
* A PostgreSQL database for storing sessions, memories and knowledge.

<Snippet file="setup.mdx" />

<Snippet file="create-agent-infra-docker-codebase.mdx" />

<Snippet file="run-agent-infra-docker-local.mdx" />

---
