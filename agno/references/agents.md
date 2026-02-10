# Agno - Agents

**Pages:** 834

---

## Pass your app to AgentOS

**URL:** llms-txt#pass-your-app-to-agentos

agent_os = AgentOS(
    agents=[Agent(id="basic-agent", model=OpenAIChat(id="gpt-5-mini"))],
    base_app=app  # Your custom FastAPI app
)

---

## agent.print_response("Fetch the top 2 hackernews stories")

**URL:** llms-txt#agent.print_response("fetch-the-top-2-hackernews-stories")

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai httpx rich
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch confirmation_required_mixed_tools.py
    bash Mac theme={null}
      python confirmation_required_mixed_tools.py
      bash Windows   theme={null}
      python confirmation_required_mixed_tools.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Create an agent with PandasTools

**URL:** llms-txt#create-an-agent-with-pandastools

agent = Agent(tools=[PandasTools()])

---

## Create agent with HITL tools

**URL:** llms-txt#create-agent-with-hitl-tools

agent = Agent(
    name="Data Manager",
    id="data_manager",
    model=OpenAIChat(id="gpt-4o-mini"),
    tools=[delete_records, send_notification],
    instructions=["You help users manage data operations"],
    db=db,
    markdown=True,
)

---

## Debugging Agents

**URL:** llms-txt#debugging-agents

**Contents:**
- Debug Mode

Source: https://docs.agno.com/concepts/agents/debugging-agents

Learn how to debug Agno Agents.

Agno comes with a exceptionally well-built debug mode that takes your development experience to the next level. It helps you understand the flow of execution and the intermediate steps. For example:

1. Inspect the messages sent to the model and the response it generates.
2. Trace intermediate steps and monitor metrics like token usage, execution time, etc.
3. Inspect tool calls, errors, and their results.

To enable debug mode:

1. Set the `debug_mode` parameter on your agent, to enable it for all runs.
2. Set the `debug_mode` parameter on the `run` method, to enable it for the current run.
3. Set the `AGNO_DEBUG` environment variable to `True`, to enable debug mode for all agents.

```python  theme={null}
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    instructions="Write a report on the topic. Output only the report.",
    markdown=True,
    debug_mode=True,
    # debug_level=2, # Uncomment to get more detailed logs
)

---

## Agent with Structured Outputs

**URL:** llms-txt#agent-with-structured-outputs

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/vertexai/claude/structured_output

```python cookbook/models/vertexai/claude/structured_output.py theme={null}
from typing import List

from agno.agent import Agent, RunOutput  # noqa
from agno.models.vertexai.claude import Claude
from pydantic import BaseModel, Field
from rich.pretty import pprint  # noqa

class MovieScript(BaseModel):
    setting: str = Field(
        ..., description="Provide a nice setting for a blockbuster movie."
    )
    ending: str = Field(
        ...,
        description="Ending of the movie. If not available, provide a happy ending.",
    )
    genre: str = Field(
        ...,
        description="Genre of the movie. If not available, select action, thriller or romantic comedy.",
    )
    name: str = Field(..., description="Give a name to this movie")
    characters: List[str] = Field(..., description="Name of characters for this movie.")
    storyline: str = Field(
        ..., description="3 sentence storyline for the movie. Make it exciting!"
    )

movie_agent = Agent(
    model=Claude(id="claude-sonnet-4@20250514"),
    description="You help people write movie scripts.",
    output_schema=MovieScript,
)

---

## Delete a memory

**URL:** llms-txt#delete-a-memory

print("\nDeleting memory")
assert memory_id_2 is not None
memory.delete_user_memory(user_id=jane_doe_id, memory_id=memory_id_2)
print("Memory deleted\n")
memories = memory.get_user_memories(user_id=jane_doe_id)
print("Memories:")
pprint(memories)

---

## Knowledge

**URL:** llms-txt#knowledge

Source: https://docs.agno.com/reference/knowledge/knowledge

Knowledge is a class that manages knowledge bases for AI agents. It provides comprehensive knowledge management capabilities including adding new content to the knowledge base, searching the knowledge base and deleting content from the knowledge base.

<Snippet file="knowledge-reference.mdx" />

---

## run: RunOutput = agent.run("Share a 2 sentence horror story")

**URL:** llms-txt#run:-runoutput-=-agent.run("share-a-2-sentence-horror-story")

---

## Add in the query and the agent redirects it to the appropriate agent

**URL:** llms-txt#add-in-the-query-and-the-agent-redirects-it-to-the-appropriate-agent

customer_support_team.print_response(
    "Hi Team, I want to build an educational platform where the models are have access to tons of study materials, How can Agno platform help me build this?",
    stream=True,
)

---

## Video Caption Generator Agent

**URL:** llms-txt#video-caption-generator-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/video_caption_agent

This example demonstrates how to create an agent that can process videos to generate and embed captions using MoviePy and OpenAI tools.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/multimodal" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Create agent with database

**URL:** llms-txt#create-agent-with-database

---

## Continue Agent Run

**URL:** llms-txt#continue-agent-run

Source: https://docs.agno.com/reference-api/schema/agents/continue-agent-run

post /agents/{agent_id}/runs/{run_id}/continue
Continue a paused or incomplete agent run with updated tool results.

**Use Cases:**
- Resume execution after tool approval/rejection
- Provide manual tool execution results

**Tools Parameter:**
JSON string containing array of tool execution objects with results.

---

## Add from local file to the knowledge base, but don't skip if it already exists

**URL:** llms-txt#add-from-local-file-to-the-knowledge-base,-but-don't-skip-if-it-already-exists

**Contents:**
- Usage

asyncio.run(
    knowledge.add_content_async(
        name="CV",
        path="cookbook/knowledge/testing_resources/cv_1.pdf",
        metadata={"user_tag": "Engineering Candidates"},
        skip_if_exists=False,
    )
)
bash  theme={null}
    pip install -U agno sqlalchemy psycopg pgvector
    bash Mac theme={null}
      python cookbook/knowledge/basic_operations/11_skip_if_exists.py
      bash Windows theme={null}
      python cookbook/knowledge/basic_operations/11_skip_if_exists.py
      ```
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run the example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Google Cloud Storage for Agent

**URL:** llms-txt#google-cloud-storage-for-agent

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/db/gcs/gcs_for_agent

Agno supports using Google Cloud Storage (GCS) as a storage backend for Agents using the `GcsJsonDb` class. This storage backend stores session data as JSON blobs in a GCS bucket.

Configure your agent with GCS storage to enable cloud-based session persistence.

```python gcs_for_agent.py theme={null}
import uuid
import google.auth
from agno.agent import Agent
from agno.db.base import SessionType
from agno.db.gcs_json import GcsJsonDb
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Blog to Podcast Agent

**URL:** llms-txt#blog-to-podcast-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/multimodal/blog-to-podcast

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Create an agent with the PostgresTools

**URL:** llms-txt#create-an-agent-with-the-postgrestools

agent = Agent(tools=[postgres_tools])

---

## Wikipedia search agent

**URL:** llms-txt#wikipedia-search-agent

wikipedia_agent = Agent(
    name="Wikipedia Agent",
    role="Search wikipedia for information",
    model=MistralChat(id="mistral-large-latest"),
    tools=[WikipediaTools()],
    instructions=[
        "Find information about the company in the wikipedia",
    ],
)

---

## Cursor Rules for Building Agents

**URL:** llms-txt#cursor-rules-for-building-agents

**Contents:**
- What is .cursorrules?
- Why Use It?
- How to Use .cursorrules

Source: https://docs.agno.com/how-to/cursor-rules

Use .cursorrules to improve AI coding assistant suggestions when building agents with Agno

A [`.cursorrules`](https://docs.cursor.com/context/rules-for-ai) file teaches AI coding assistants (like Cursor, Windsurf) how to build better agents with Agno.

## What is .cursorrules?

`.cursorrules` is a configuration file that provides your AI coding assistant with instructions on how to generate specific code.
Agno's recommended `.cursorrules` file contains:

* Agno-specific patterns and best practices
* Correct parameter names and syntax
* Common mistakes to avoid
* When to use Agent vs Team vs Workflow

Think of it as a reference guide that helps your AI assistant build agents correctly with Agno.

Without `.cursorrules`, AI assistants might suggest:

* Wrong parameter names (like `agents=` instead of `members=` for Teams)
* Outdated patterns or incorrect syntax
* Performance anti-patterns (creating agents in loops)
* Non-existent methods or features

With `.cursorrules`, your AI will:

* Suggest correct Agno patterns automatically
* Follow performance best practices
* Use the right approach for your use case
* Catch common mistakes before you make them

## How to Use .cursorrules

Copy the Agno `.cursorrules` file to your project root:

```bash  theme={null}

---

## Meeting Summary Agent

**URL:** llms-txt#meeting-summary-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/tools/models/openai/meeting-summarizer

Multi-modal Agno agent that transcribes meeting recordings, extracts key insights, generates visual summaries, and creates audio summaries using OpenAI tools.

This example demonstrates a multi-modal meeting summarizer and visualizer agent that uses OpenAITools and ReasoningTools to transcribe a meeting recording, extract key insights, generate a visual summary, and synthesize an audio summary.

<Steps>
  <Step title="Install dependencies">
    
  </Step>

<Step title="Run the example">
    
  </Step>
</Steps>

By default, the audio summary will be saved to `tmp/meeting_summary.mp3`.

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install dependencies">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run the example">
```

---

## Agent Input as Messages List

**URL:** llms-txt#agent-input-as-messages-list

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/input_as_messages_list

This example demonstrates how to pass input to an agent as a list of Message objects, allowing for multi-turn conversations and context setup.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/input_and_output" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Thinking Agent

**URL:** llms-txt#thinking-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/dashscope/thinking_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Async Data Analyst Agent with DuckDB

**URL:** llms-txt#async-data-analyst-agent-with-duckdb

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/async/data_analyst

This example demonstrates how to create an asynchronous data analyst agent that can analyze movie data using DuckDB tools and provide insights about movie ratings.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/async" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Setup our Agent with reasoning enabled

**URL:** llms-txt#setup-our-agent-with-reasoning-enabled

reasoning_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    instructions=["Use tables to show data"],
    markdown=True,
    reasoning=True,
)

---

## Company information agent

**URL:** llms-txt#company-information-agent

company_info_agent = Agent(
    name="Company Info Searcher",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Searches the web for information on a stock.",
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
)

---

## Create a new agent and make sure it pursues the conversation

**URL:** llms-txt#create-a-new-agent-and-make-sure-it-pursues-the-conversation

**Contents:**
- Prerequisites
- Params
- Developer Resources

agent2 = Agent(
    db=db,
    session_id=agent1.session_id,
    tools=[DuckDuckGoTools()],
    add_history_to_context=True,
    debug_mode=False,
)

agent2.print_response("What's the name of the country we discussed?")
agent2.print_response("What is that country's national sport?")
```

<Snippet file="gcs-auth-storage.mdx" />

<Snippet file="db-gcs-params.mdx" />

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/db/gcs/gcs_json_for_agent.py)

---

## Test knowledge filtering

**URL:** llms-txt#test-knowledge-filtering

**Contents:**
- Usage

team_with_knowledge.print_response(
    "Tell me about Jordan Mitchell's work and experience"
)
bash  theme={null}
    pip install agno openai lancedb
    bash  theme={null}
    export OPENAI_API_KEY=****
    bash  theme={null}
    python cookbook/examples/teams/knowledge/02_team_with_knowledge_filters.py
    ```
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install required libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Create stock research agent

**URL:** llms-txt#create-stock-research-agent

stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat("gpt-5-mini"),
    role="Searches the web for information on a stock.",
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
)

---

## Memory

**URL:** llms-txt#memory

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/openai/responses/memory

```python cookbook/models/openai/responses/memory.py theme={null}
"""
This recipe shows how to use personalized memories and summaries in an agent.
Steps:
1. Run: `./cookbook/scripts/run_pgvector.sh` to start a postgres container with pgvector
2. Run: `pip install openai sqlalchemy 'psycopg[binary]' pgvector` to install the dependencies
3. Run: `python cookbook/agents/personalized_memories_and_summaries.py` to run the agent
"""

from agno.agent import Agent
from agno.db.base import SessionType
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIResponses
from rich.pretty import pprint

---

## Add Dependencies to Agent Run

**URL:** llms-txt#add-dependencies-to-agent-run

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/dependencies/add_dependencies_run

This example demonstrates how to inject dependencies into agent runs, allowing the agent to access dynamic context like user profiles and current time information for personalized responses.

```python add_dependencies_on_run.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_user_profile(user_id: str = "john_doe") -> dict:
    """Get user profile information that can be referenced in responses.

Args:
        user_id: The user ID to get profile for
    Returns:
        Dictionary containing user profile information
    """
    profiles = {
        "john_doe": {
            "name": "John Doe",
            "preferences": {
                "communication_style": "professional",
                "topics_of_interest": ["AI/ML", "Software Engineering", "Finance"],
                "experience_level": "senior",
            },
            "location": "San Francisco, CA",
            "role": "Senior Software Engineer",
        }
    }

return profiles.get(user_id, {"name": "Unknown User"})

def get_current_context() -> dict:
    """Get current contextual information like time, weather, etc."""
    from datetime import datetime

return {
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "PST",
        "day_of_week": datetime.now().strftime("%A"),
    }

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    markdown=True,
)

---

## Agent that uses structured outputs

**URL:** llms-txt#agent-that-uses-structured-outputs

**Contents:**
- Usage

structured_output_agent = Agent(
    model=Requesty(id="openai/gpt-4o"),
    description="You write movie scripts.",
    output_schema=MovieScript,
)

structured_output_agent.print_response("New York")
bash  theme={null}
    export REQUESTY_API_KEY=xxx
    bash  theme={null}
    pip install -U openai agno
    bash Mac theme={null}
      python cookbook/models/requesty/structured_output.py
      bash Windows theme={null}
      python cookbook/models/requesty/structured_output.py
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

## Agent Extra Metrics

**URL:** llms-txt#agent-extra-metrics

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/other/agent_extra_metrics

This example demonstrates how to collect special token metrics including audio, cached, and reasoning tokens. It shows different types of advanced metrics available when working with various OpenAI models.

```python agent_extra_metrics.py theme={null}
"""Show special token metrics like audio, cached and reasoning tokens"""

import requests
from agno.agent import Agent
from agno.media import Audio
from agno.models.openai import OpenAIChat
from agno.utils.pprint import pprint_run_response

---

## Agent Team

**URL:** llms-txt#agent-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/getting-started/17-agent-team

This example shows how to create a powerful team of AI agents working together to provide comprehensive financial analysis and news reporting. The team consists of:

1. Web Agent: Searches and analyzes latest news
2. Finance Agent: Analyzes financial data and market trends
3. Lead Editor: Coordinates and combines insights from both agents

Example prompts to try:

* "What's the latest news and financial performance of Apple (AAPL)?"
* "Analyze the impact of AI developments on NVIDIA's stock (NVDA)"
* "How are EV manufacturers performing? Focus on Tesla (TSLA) and Rivian (RIVN)"
* "What's the market outlook for semiconductor companies like AMD and Intel?"
* "Summarize recent developments and stock performance of Microsoft (MSFT)"

```python agent_team.py theme={null}
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools

web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    instructions=dedent("""\
        You are an experienced web researcher and news analyst! 🔍

Follow these steps when searching for information:
        1. Start with the most recent and relevant sources
        2. Cross-reference information from multiple sources
        3. Prioritize reputable news outlets and official sources
        4. Always cite your sources with links
        5. Focus on market-moving news and significant developments

Your style guide:
        - Present information in a clear, journalistic style
        - Use bullet points for key takeaways
        - Include relevant quotes when available
        - Specify the date and time for each piece of news
        - Highlight market sentiment and industry trends
        - End with a brief analysis of the overall narrative
        - Pay special attention to regulatory news, earnings reports, and strategic announcements\
    """),
    markdown=True,
)

finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[
        ExaTools(
            include_domains=["trendlyne.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
    instructions=dedent("""\
        You are a skilled financial analyst with expertise in market data! 📊

Follow these steps when analyzing financial data:
        1. Start with the latest stock price, trading volume, and daily range
        2. Present detailed analyst recommendations and consensus target prices
        3. Include key metrics: P/E ratio, market cap, 52-week range
        4. Analyze trading patterns and volume trends
        5. Compare performance against relevant sector indices

Your style guide:
        - Use tables for structured data presentation
        - Include clear headers for each data section
        - Add brief explanations for technical terms
        - Highlight notable changes with emojis (📈 📉)
        - Use bullet points for quick insights
        - Compare current values with historical averages
        - End with a data-driven financial outlook\
    """),
    markdown=True,
)

agent_team = Team(
    members=[web_agent, finance_agent],
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=dedent("""\
        You are the lead editor of a prestigious financial news desk! 📰

Your role:
        1. Coordinate between the web researcher and financial analyst
        2. Combine their findings into a compelling narrative
        3. Ensure all information is properly sourced and verified
        4. Present a balanced view of both news and data
        5. Highlight key risks and opportunities

Your style guide:
        - Start with an attention-grabbing headline
        - Begin with a powerful executive summary
        - Present financial data first, followed by news context
        - Use clear section breaks between different types of information
        - Include relevant charts or tables when available
        - Add 'Market Sentiment' section with current mood
        - Include a 'Key Takeaways' section at the end
        - End with 'Risk Factors' when appropriate
        - Sign off with 'Market Watch Team' and the current date\
    """),
    add_datetime_to_context=True,
    markdown=True,
    show_members_responses=False,
)

---

## Create team with custom tool and agent members

**URL:** llms-txt#create-team-with-custom-tool-and-agent-members

team = Team(name="Q & A team", members=[web_agent], tools=[answer_from_known_questions])

---

## Define how the agent should analyze the data

**URL:** llms-txt#define-how-the-agent-should-analyze-the-data

**Contents:**
  - 3c. Define the Intelligence Synthesis

analysis_framework = dedent("""
    ANALYSIS FRAMEWORK:
    - Classify sentiment as Positive/Negative/Neutral/Mixed with detailed reasoning
    - Weight analysis by engagement volume and author influence (verified accounts = 1.5x)
    - Identify engagement patterns: viral advocacy, controversy, influence concentration
    - Extract cross-platform themes and recurring discussion points
""")

print("Analysis framework defined")
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
### 3c. Define the Intelligence Synthesis
```

---

## Sqlite for Agent

**URL:** llms-txt#sqlite-for-agent

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/db/sqlite/sqlite_for_agent

Agno supports using Sqlite as a storage backend for Agents using the `SqliteDb` class.

You need to provide either `db_url`, `db_file` or `db_engine`. The following example uses `db_file`.

```python sqlite_for_agent.py theme={null}

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Create a fresh agent for streaming

**URL:** llms-txt#create-a-fresh-agent-for-streaming

streaming_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[
        KnowledgeTools(
            knowledge=agno_docs,
            think=True,
            search=True,
            analyze=True,
            add_instructions=True,
        )
    ],
    instructions=dedent("""\
        You are an expert problem-solving assistant with strong analytical skills! 🧠
        Use the knowledge tools to organize your thoughts, search for information,
        and analyze results step-by-step.
        \
    """),
    markdown=True,
)

---

## Create web search agent for fallback

**URL:** llms-txt#create-web-search-agent-for-fallback

web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    tools=[DuckDuckGoTools()],
    markdown=True,
)

---

## Agent with URL Context

**URL:** llms-txt#agent-with-url-context

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/gemini/url_context

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Create your AgentOS app

**URL:** llms-txt#create-your-agentos-app

agent_os = AgentOS(agents=[agent])
app = agent_os.get_app()

---

## Distributed RAG with LanceDB

**URL:** llms-txt#distributed-rag-with-lancedb

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/distributed_rag/distributed_rag_lancedb

This example demonstrates how multiple specialized agents coordinate to provide comprehensive RAG responses using distributed knowledge bases and specialized retrieval strategies with LanceDB. The team includes primary retrieval, context expansion, answer synthesis, and quality validation.

```python cookbook/examples/teams/distributed_rag/02_distributed_rag_lancedb.py theme={null}
"""
This example demonstrates how multiple specialized agents coordinate to provide
comprehensive RAG responses using distributed knowledge bases and specialized
retrieval strategies with LanceDB.

Team Composition:
- Primary Retriever: Handles primary document retrieval from main knowledge base
- Context Expander: Expands context by finding related information
- Answer Synthesizer: Synthesizes retrieved information into comprehensive answers
- Quality Validator: Validates answer quality and suggests improvements

Setup:
1. Run: `pip install openai lancedb tantivy pypdf sqlalchemy agno`
2. Run this script to see distributed RAG in action
"""

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.vectordb.lancedb import LanceDb, SearchType

---

## Image Agent with Bytes

**URL:** llms-txt#image-agent-with-bytes

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/dashscope/image_agent_bytes

```python cookbook/models/dashscope/image_agent_bytes.py theme={null}
from pathlib import Path

from agno.agent import Agent
from agno.media import Image
from agno.models.dashscope import DashScope
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.utils.media import download_image

agent = Agent(
    model=DashScope(id="qwen-vl-plus"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

image_path = Path(__file__).parent.joinpath("sample.jpg")

download_image(
    url="https://upload.wikimedia.org/wikipedia/commons/a/a7/Camponotus_flavomarginatus_ant.jpg",
    output_path=str(image_path),
)

---

## Run the agent synchronously

**URL:** llms-txt#run-the-agent-synchronously

**Contents:**
- Usage

structured_output_response: RunOutput = structured_output_agent.run(
    "Llamas ruling the world"
)
pprint(structured_output_response.content)

bash  theme={null}
    export XAI_API_KEY=xxx
    bash  theme={null}
    pip install -U xai agno
    bash Mac theme={null}
      python cookbook/models/xai/structured_output.py
      bash Windows theme={null}
      python cookbook/models/xai/structured_output.py
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

## Agent with Memory

**URL:** llms-txt#agent-with-memory

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/vllm/memory

```python cookbook/models/vllm/memory.py theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.vllm import VLLM
from agno.utils.pprint import pprint

---

## Setup our Agent with the reasoning tools

**URL:** llms-txt#setup-our-agent-with-the-reasoning-tools

reasoning_agent = Agent(
    model=Claude(id="claude-3-7-sonnet-latest"),
    tools=[
        ReasoningTools(add_instructions=True),
        DuckDuckGoTools(),
    ],
    instructions="Use tables where possible",
    markdown=True,
)

---

## Create an agent with SingleStore db

**URL:** llms-txt#create-an-agent-with-singlestore-db

**Contents:**
- Params
- Developer Resources

agent = Agent(
    db=db,
    tools=[DuckDuckGoTools()],
    add_history_to_context=True,
)
agent.print_response("How many people live in Canada?")
agent.print_response("What is their national anthem called?")

<Snippet file="db-singlestore-params.mdx" />

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/db/singlestore/singlestore_for_agent.py)

---

## Step 2: Query the knowledge base with different filter combinations

**URL:** llms-txt#step-2:-query-the-knowledge-base-with-different-filter-combinations

---

## Knowledge Content Types

**URL:** llms-txt#knowledge-content-types

**Contents:**
- Next Steps

Source: https://docs.agno.com/concepts/knowledge/content_types

Agno Knowledge uses `content` as the building block of any piece of knowledge.
Content can be added to knowledge from different sources.

| Content Origin | Description                                                           |
| -------------- | --------------------------------------------------------------------- |
| Path           | Local files or directories containing files                           |
| Url            | Direct links to files or other sites                                  |
| Text           | Raw text content                                                      |
| Topic          | Search topics from repositories like Arxiv or Wikipedia               |
| Remote Content | Content stored in remote repositories like S3 or Google Cloud Storage |

Knowledge content needs to be read and chunked before it can be passed to any VectorDB for embedding, storage and ultimately, retrieval.
When content is added to Knowledge, a default reader is selected. Readers are used to parse content from the origin and then chunk it into smaller
pieces that will then be embedded by the VectorDB.

Custom readers or an override to the default reader and/or its settings can be passed when adding the content. In the below example, an instance of the standard `PDFReader` class is created
but we update the chunk\_size. Similarly, we can update the `chunking_strategy` and other parameters that will influence how content is ingested and processed.

For more information about the different readers and their capabilities checkout the [Readers](/concepts/knowledge/readers) page.

<CardGroup cols={2}>
  <Card title="Search & Retrieval" icon="magnifying-glass" href="/concepts/knowledge/core-concepts/search-retrieval">
    Learn how agents search and find information in your knowledge base
  </Card>

<Card title="Readers" icon="book-open" href="/concepts/knowledge/readers">
    Explore content parsing and ingestion options in detail
  </Card>

<Card title="Chunking Strategies" icon="scissors" href="/concepts/knowledge/chunking/overview">
    Optimize how content is broken down for better search results
  </Card>

<Card title="Vector Databases" icon="database" href="/concepts/vectordb/overview">
    Choose the right storage solution for your knowledge base
  </Card>
</CardGroup>

---

## RAG with Sentence Transformer

**URL:** llms-txt#rag-with-sentence-transformer

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/knowledge/rag/rag_sentence_transformer

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set environment variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>
      
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set environment variables">
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

---

## 2. Set a custom MemoryManager on the agent

**URL:** llms-txt#2.-set-a-custom-memorymanager-on-the-agent

---

## -*- Print the messages in the memory

**URL:** llms-txt#-*--print-the-messages-in-the-memory

**Contents:**
- Usage

print("\n" + "=" * 50)
print("CHAT HISTORY AFTER SECOND RUN")
print("=" * 50)
try:
    chat_history = team.get_chat_history(session_id="test_session")
    pprint([m.model_dump(include={"role", "content"}) for m in chat_history])
except Exception as e:
    print(f"Error getting chat history: {e}")
    print("This indicates an issue with in-memory database session handling")
bash  theme={null}
    pip install agno rich
    bash  theme={null}
    export OPENAI_API_KEY=****
    bash  theme={null}
    python cookbook/examples/teams/session/07_in_memory_db.py
    ```
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install required libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Create agent with LangDB model (uses environment variables automatically)

**URL:** llms-txt#create-agent-with-langdb-model-(uses-environment-variables-automatically)

agent = Agent(
    name="Web Research Agent",
    model=LangDB(id="openai/gpt-4.1"),
    tools=[DuckDuckGoTools()],
    instructions="Answer questions using web search and provide comprehensive information"
)

---

## Create and run an agent

**URL:** llms-txt#create-and-run-an-agent

agent = Agent(model=OpenAIChat(id="gpt-5-mini"))
response = agent.run("Share a 2 sentence horror story")

---

## === BASIC AGENTS ===

**URL:** llms-txt#===-basic-agents-===

researcher = Agent(
    name="Researcher",
    instructions="Research the given topic and provide detailed findings.",
    tools=[DuckDuckGoTools()],
)

summarizer = Agent(
    name="Summarizer",
    instructions="Create a clear summary of the research findings.",
)

fact_checker = Agent(
    name="Fact Checker",
    instructions="Verify facts and check for accuracy in the research.",
    tools=[DuckDuckGoTools()],
)

writer = Agent(
    name="Writer",
    instructions="Write a comprehensive article based on all available research and verification.",
)

---

## run: RunOutput = agent.run("New York")

**URL:** llms-txt#run:-runoutput-=-agent.run("new-york")

---

## Web Search Reader (Async)

**URL:** llms-txt#web-search-reader-(async)

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/web-search/web-search-reader-async

The **Web Search Reader** searches and reads web search results, converting them into vector embeddings for your knowledge base.

```python examples/concepts/knowledge/readers/web_search_reader_async.py theme={null}
import asyncio

from agno.agent import Agent
from agno.db.postgres.postgres import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.web_search_reader import WebSearchReader
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

db = PostgresDb(id="web-search-db", db_url=db_url)

vector_db = PgVector(
    db_url=db_url,
    table_name="web_search_documents",
)
knowledge = Knowledge(
    name="Web Search Documents",
    contents_db=db,
    vector_db=vector_db,
)

---

## When to use a Workflow vs a Team in Agno

**URL:** llms-txt#when-to-use-a-workflow-vs-a-team-in-agno

**Contents:**
- Use a Workflow when:
- Use an Agent Team when:
- 💡 Pro Tip

Source: https://docs.agno.com/faq/When-to-use-a-Workflow-vs-a-Team-in-Agno

Agno offers two powerful ways to build multi-agent systems: **Workflows** and **Teams**. Each is suited for different kinds of use-cases.

## Use a Workflow when:

You need **orchestrated, multi-step execution** with flexible control flow and a predictable outcome.

Workflows are ideal for:

* **Sequential processes** - Step-by-step agent executions with dependencies
* **Parallel execution** - Running independent tasks simultaneously
* **Conditional logic** - Dynamic routing based on content analysis
* **Quality assurance** - Iterative loops with end conditions
* **Complex pipelines** - Mixed components (agents, teams, functions) with branching
* **Structured processes** - Data transformation with predictable patterns

[Learn more about Workflows](/concepts/workflows/overview)

## Use an Agent Team when:

Your task requires reasoning, collaboration, or multi-tool decision-making.

Agent Teams are best for:

* Research and planning
* Tasks where agents divide responsibilities

[Learn more about Agent Teams](/concepts/teams/overview)

> Think of **Workflows** as assembly lines for known tasks,
> and **Agent Teams** as collaborative task forces for solving open-ended problems.

---

## Setup an Agent with our custom tool.

**URL:** llms-txt#setup-an-agent-with-our-custom-tool.

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[get_customer_profile],
    instructions="Your task is to retrieve customer profiles for the user.",
)

async def run_agent():
    # Running the Agent: it should call our custom tool and yield the custom event
    async for event in agent.arun(
        "Hello, can you get me the customer profile for customer with ID 123?",
        stream=True,
    ):
        if isinstance(event, CustomEvent):
            print(f"✅ Custom event emitted: {event}")

asyncio.run(run_agent())
```

---

## agent.print_response("Create a simple web app that displays a random number between 1 and 100.")

**URL:** llms-txt#agent.print_response("create-a-simple-web-app-that-displays-a-random-number-between-1-and-100.")

**Contents:**
- Usage

bash  theme={null}
    export V0_API_KEY=xxx
    bash  theme={null}
    pip install -U openai agno
    bash Mac theme={null}
      python cookbook/models/vercel/basic.py
      bash Windows theme={null}
      python cookbook/models/vercel/basic.py
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

## Multimodal Agents

**URL:** llms-txt#multimodal-agents

**Contents:**
- Multimodal inputs to an agent
  - Image Agent
  - Audio Agent

Source: https://docs.agno.com/concepts/agents/multimodal

Agno agents support text, image, audio, video and files inputs and can generate text, image, audio, video and files as output.

For a complete overview of multimodal support, please checkout the [multimodal](/concepts/multimodal/overview) documentation.

<Tip>
  Not all models support multimodal inputs and outputs.
  To see which models support multimodal inputs and outputs, please checkout the [compatibility matrix](/concepts/models/compatibility).
</Tip>

## Multimodal inputs to an agent

Let's create an agent that can understand images and make tool calls as needed

See [Image as input](/concepts/multimodal/images/image_input) for more details.

```python audio_agent.py theme={null}
import base64

import requests
from agno.agent import Agent
from agno.media import Audio
from agno.models.openai import OpenAIChat

**Examples:**

Example 1 (unknown):
```unknown
Run the agent:
```

Example 2 (unknown):
```unknown
See [Image as input](/concepts/multimodal/images/image_input) for more details.

### Audio Agent
```

---

## Create an agent that manages the shopping list

**URL:** llms-txt#create-an-agent-that-manages-the-shopping-list

shopping_agent = Agent(
    name="Shopping List Agent",
    role="Manage the shopping list",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[add_item, remove_item],
)

---

## Setup your Memory Manager, to adjust how memories are created

**URL:** llms-txt#setup-your-memory-manager,-to-adjust-how-memories-are-created

memory_manager = MemoryManager(
    db=db,
    # Select the model used for memory creation and updates. If unset, the default model of the Agent is used.
    model=OpenAIChat(id="gpt-5-mini"),
    # You can also provide additional instructions
    additional_instructions="Don't store the user's real name",
)

---

## The second Agent will be able to retrieve the Memory about the user name here:

**URL:** llms-txt#the-second-agent-will-be-able-to-retrieve-the-memory-about-the-user-name-here:

agent_2.print_response("What is my name?")
```

All agents connected to the same database automatically share memories for each user. This works across agent types, teams, and workflows, as long as they use the same `user_id`.

---

## Set up knowledge base

**URL:** llms-txt#set-up-knowledge-base

knowledge = Knowledge(
    vector_db=LanceDb(
        table_name="my_documents",
        uri="tmp/lancedb"
    ),
)

---

## Image Agent With Memory

**URL:** llms-txt#image-agent-with-memory

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/openai/responses/image_agent_with_memory

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Clickhouse Agent Knowledge

**URL:** llms-txt#clickhouse-agent-knowledge

**Contents:**
- Setup
- Example

Source: https://docs.agno.com/concepts/vectordb/clickhouse

```python agent_with_knowledge.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.db.sqlite import SqliteDb
from agno.vectordb.clickhouse import Clickhouse

knowledge=Knowledge(
    vector_db=Clickhouse(
        table_name="recipe_documents",
        host="localhost",
        port=8123,
        username="ai",
        password="ai",
    ),
)

knowledge.add_content(
  url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"
)

agent = Agent(
    db=SqliteDb(db_file="agno.db"),
    knowledge=knowledge,
    # Enable the agent to search the knowledge base
    search_knowledge=True,
    # Enable the agent to read the chat history
    read_chat_history=True,
)

**Examples:**

Example 1 (unknown):
```unknown
## Example
```

---

## Agentic approach (recommended)

**URL:** llms-txt#agentic-approach-(recommended)

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True  # Agent decides when to search
)

---

## Async Agent with Reasoning Capabilities

**URL:** llms-txt#async-agent-with-reasoning-capabilities

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/async/reasoning

This example demonstrates the difference between a regular agent and a reasoning agent when solving mathematical problems, showcasing how reasoning mode provides more detailed thought processes.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/async" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Load knowledge from web search

**URL:** llms-txt#load-knowledge-from-web-search

knowledge.add_content(
    topics=["agno"],
    reader=WebSearchReader(
        max_results=3,
        search_engine="duckduckgo",
        chunk=True,
    ),
)

---

## Agent with Reasoning Effort

**URL:** llms-txt#agent-with-reasoning-effort

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/openai/chat/reasoning_effort

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Alert if memory count is unusually high

**URL:** llms-txt#alert-if-memory-count-is-unusually-high

if len(memories) > 500:
    print("⚠️ Warning: User has excessive memories. Consider pruning.")
```

---

## Agentic RAG with Hybrid Search and Reranking

**URL:** llms-txt#agentic-rag-with-hybrid-search-and-reranking

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/agentic_search/agentic_rag

This example demonstrates how to implement Agentic RAG using Hybrid Search and Reranking with LanceDB, Cohere embeddings, and Cohere reranking for enhanced document retrieval and response generation.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your ANTHROPIC API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/agentic_search" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your ANTHROPIC API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Define specialized customer service agents

**URL:** llms-txt#define-specialized-customer-service-agents

tech_support_agent = Agent(
    name="Technical Support Specialist",
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "You are a technical support specialist with deep product knowledge.",
        "You have access to the full conversation history with this customer.",
        "Reference previous interactions to provide better help.",
        "Build on any troubleshooting steps already attempted.",
        "Be patient and provide step-by-step technical guidance.",
    ],
)

billing_agent = Agent(
    name="Billing & Account Specialist",
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "You are a billing and account specialist.",
        "You have access to the full conversation history with this customer.",
        "Reference any account details or billing issues mentioned previously.",
        "Build on any payment or account information already discussed.",
        "Be helpful with billing questions, refunds, and account changes.",
    ],
)

general_support_agent = Agent(
    name="General Customer Support",
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "You are a general customer support representative.",
        "You have access to the full conversation history with this customer.",
        "Handle general inquiries, product information, and basic support.",
        "Reference the conversation context - build on what was discussed.",
        "Be friendly and acknowledge their previous interactions.",
    ],
)

---

## In-Memory Database Storage

**URL:** llms-txt#in-memory-database-storage

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/session/07_in_memory_db

This example demonstrates how to use an in-memory database for session storage, enabling conversation history and context management without requiring a persistent database setup.

```python 07_in_memory_db.py theme={null}
"""This example shows how to use an in-memory database.

With this you will be able to store sessions, user memories, etc. without setting up a database.
Keep in mind that in production setups it is recommended to use a database.
"""

from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.openai import OpenAIChat
from rich.pretty import pprint

---

## Performance on Agent Instantiation with Tool

**URL:** llms-txt#performance-on-agent-instantiation-with-tool

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/evals/performance/performance_instantiation_with_tool

Example showing how to analyze the runtime and memory usage of an Agent that is using tools.

---

## Setup an Agent focused on coding tasks, with access to the Daytona tools

**URL:** llms-txt#setup-an-agent-focused-on-coding-tasks,-with-access-to-the-daytona-tools

agent = Agent(
    name="Coding Agent with Daytona tools",
    id="coding-agent",
    model=Claude(id="claude-sonnet-4-20250514"),
    tools=[daytona_tools],
    markdown=True,
        instructions=[
        "You are an expert at writing and validating Python code. You have access to a remote, secure Daytona sandbox.",
        "Your primary purpose is to:",
        "1. Write clear, efficient Python code based on user requests",
        "2. Execute and verify the code in the Daytona sandbox",
        "3. Share the complete code with the user, as this is the main use case",
        "4. Provide thorough explanations of how the code works",
        "You can use the run_python_code tool to run Python code in the Daytona sandbox.",
        "Guidelines:",
        "- ALWAYS share the complete code with the user, properly formatted in code blocks",
        "- Verify code functionality by executing it in the sandbox before sharing",
        "- Iterate and debug code as needed to ensure it works correctly",
        "- Use pandas, matplotlib, and other Python libraries for data analysis when appropriate",
        "- Create proper visualizations when requested and add them as image artifacts to show inline",
        "- Handle file uploads and downloads properly",
        "- Explain your approach and the code's functionality in detail",
        "- Format responses with both code and explanations for maximum clarity",
        "- Handle errors gracefully and explain any issues encountered",
    ],
)

agent.print_response(
    "Write Python code to generate the first 10 Fibonacci numbers and calculate their sum and average"
)
```

---

## Research Agent

**URL:** llms-txt#research-agent

web_agent = Agent(
    name="Market Research Agent",
    model=LangDB(id="openai/gpt-4.1"),
    tools=[DuckDuckGoTools()],
    instructions="Research current market conditions and news"
)

---

## AgentOps

**URL:** llms-txt#agentops

**Contents:**
- Integrating Agno with AgentOps
- Prerequisites
- Logging Model Calls with AgentOps

Source: https://docs.agno.com/integrations/observability/agentops

Integrate Agno with AgentOps to send traces and logs to a centralized observability platform.

## Integrating Agno with AgentOps

[AgentOps](https://app.agentops.ai/) provides automatic instrumentation for your Agno agents to track all operations including agent interactions, team coordination, tool usage, and workflow execution.

1. **Install AgentOps**

Ensure you have the AgentOps package installed:

2. **Authentication**
   Go to [AgentOps](https://app.agentops.ai/) and copy your API key

## Logging Model Calls with AgentOps

This example demonstrates how to use AgentOps to log model calls.

```python  theme={null}
import agentops
from agno.agent import Agent
from agno.models.openai import OpenAIChat

**Examples:**

Example 1 (unknown):
```unknown
2. **Authentication**
   Go to [AgentOps](https://app.agentops.ai/) and copy your API key
```

Example 2 (unknown):
```unknown
## Logging Model Calls with AgentOps

This example demonstrates how to use AgentOps to log model calls.
```

---

## 2. Create knowledge base

**URL:** llms-txt#2.-create-knowledge-base

knowledge = Knowledge(
    name="Company Documentation",
    vector_db=vector_db,
    max_results=10
)

---

## Filtering on MilvusDB

**URL:** llms-txt#filtering-on-milvusdb

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/vector-dbs/filtering_milvus_db

Learn how to filter knowledge base searches using Pdf documents with user-specific metadata in MilvusDB.

```python  theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.milvus import Milvus

---

## Agent gets only hotel management tools - focused!

**URL:** llms-txt#agent-gets-only-hotel-management-tools---focused!

**Contents:**
- Advanced Usage
  - Multiple Toolsets
  - Custom Authentication and Parameters
  - Manual Connection Management
- Toolkit Params
- Toolkit Functions
- Demo Examples
- Developer Resources

tools = MCPToolbox(url="http://127.0.0.1:5001", toolsets=["hotel-management"])  # 3 tools
python cookbook/tools/mcp/mcp_toolbox_for_db.py theme={null}
import asyncio
from textwrap import dedent
from agno.agent import Agent
from agno.tools.mcp_toolbox import MCPToolbox

url = "http://127.0.0.1:5001"

async def run_agent(message: str = None) -> None:
    """Run an interactive CLI for the Hotel agent with the given message."""

async with MCPToolbox(
        url=url, toolsets=["hotel-management", "booking-system"]
    ) as db_tools:
        print(db_tools.functions)  # Print available tools for debugging
        agent = Agent(
            tools=[db_tools],
            instructions=dedent(
                """ \
                You're a helpful hotel assistant. You handle hotel searching, booking and
                cancellations. When the user searches for a hotel, mention it's name, id,
                location and price tier. Always mention hotel ids while performing any
                searches. This is very important for any operations. For any bookings or
                cancellations, please provide the appropriate confirmation. Be sure to
                update checkin or checkout dates if mentioned by the user.
                Don't ask for confirmations from the user.
            """
            ),
            markdown=True,
            show_tool_calls=True,
            add_history_to_messages=True,
            debug_mode=True,
        )

await agent.acli_app(message=message, stream=True)

if __name__ == "__main__":
    asyncio.run(run_agent(message=None))
python  theme={null}
async def production_example():
    async with MCPToolbox(url=url) as toolbox:
        # Load with authentication and bound parameters
        hotel_tools = await toolbox.load_toolset(
            "hotel-management",
            auth_token_getters={"hotel_api": lambda: "your-hotel-api-key"},
            bound_params={"region": "us-east-1"},
        )

booking_tools = await toolbox.load_toolset(
            "booking-system",
            auth_token_getters={"booking_api": lambda: "your-booking-api-key"},
            bound_params={"environment": "production"},
        )

# Use individual tools instead of the toolbox
        all_tools = hotel_tools + booking_tools[:2]  # First 2 booking tools only
        
        agent = Agent(tools=all_tools, instructions="Hotel management with auth.")
        await agent.aprint_response("Book a hotel for tonight")
python  theme={null}
async def manual_connection_example():
    # Initialize without auto-connection
    toolbox = MCPToolbox(url=url, toolsets=["hotel-management"])
    
    try:
        await toolbox.connect()
        agent = Agent(
            tools=[toolbox],
            instructions="Hotel search assistant.",
            markdown=True
        )
        await agent.aprint_response("Show me hotels in Basel")
    finally:
        await toolbox.close()  # Always clean up
```

| Parameter   | Type                       | Default             | Description                                                                |
| ----------- | -------------------------- | ------------------- | -------------------------------------------------------------------------- |
| `url`       | `str`                      | -                   | Base URL for the toolbox service (automatically appends "/mcp" if missing) |
| `toolsets`  | `Optional[List[str]]`      | `None`              | List of toolset names to filter tools by. Cannot be used with `tool_name`. |
| `tool_name` | `Optional[str]`            | `None`              | Single tool name to load. Cannot be used with `toolsets`.                  |
| `headers`   | `Optional[Dict[str, Any]]` | `None`              | HTTP headers for toolbox client requests                                   |
| `transport` | `str`                      | `"streamable-http"` | MCP transport protocol. Options: `"stdio"`, `"sse"`, `"streamable-http"`   |

<Note>
  Only one of `toolsets` or `tool_name` can be specified. The implementation validates this and raises a `ValueError` if both are provided.
</Note>

| Function                                                                                            | Description                                                    |
| --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| `async connect()`                                                                                   | Initialize and connect to both MCP server and toolbox client   |
| `async load_tool(tool_name, auth_token_getters={}, bound_params={})`                                | Load a single tool by name with optional authentication        |
| `async load_toolset(toolset_name, auth_token_getters={}, bound_params={}, strict=False)`            | Load all tools from a specific toolset                         |
| `async load_multiple_toolsets(toolset_names, auth_token_getters={}, bound_params={}, strict=False)` | Load tools from multiple toolsets                              |
| `async load_toolset_safe(toolset_name)`                                                             | Safely load a toolset and return tool names for error handling |
| `get_client()`                                                                                      | Get the underlying ToolboxClient instance                      |
| `async close()`                                                                                     | Close both toolbox client and MCP client connections           |

The complete demo includes multiple working patterns:

* **[Basic Agent](https://github.com/agno-agi/agno/blob/main/cookbook/tools/mcp/mcp_toolbox_demo/agent.py)**: Simple hotel assistant with toolset filtering
* **[AgentOS Integration](https://github.com/agno-agi/agno/blob/main/cookbook/tools/mcp/mcp_toolbox_demo/agent_os.py)**: Integration with AgentOS control plane
* **[Workflow Integration](https://github.com/agno-agi/agno/blob/main/cookbook/tools/mcp/mcp_toolbox_demo/hotel_management_workflows.py)**: Using MCPToolbox in Agno workflows
* **[Type-Safe Agent](https://github.com/agno-agi/agno/blob/main/cookbook/tools/mcp/mcp_toolbox_demo/hotel_management_typesafe.py)**: Implementation with Pydantic models

You can use `include_tools` or `exclude_tools` to modify the list of tools the agent has access to. Learn more about [selecting tools](/concepts/tools/selecting-tools).

## Developer Resources

* View [Tools](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/mcp_toolbox.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/mcp/mcp_toolbox_demo)

For more information about MCP Toolbox for Databases, visit the [official documentation](https://googleapis.github.io/genai-toolbox/getting-started/introduction/).

**Examples:**

Example 1 (unknown):
```unknown
**The flow:**

1. MCP Toolbox Server exposes 50+ database tools
2. MCPToolbox connects and loads ALL tools internally
3. Filters to only the `hotel-management` toolset (3 tools)
4. Agent sees only the 3 relevant tools and stays focused

## Advanced Usage

### Multiple Toolsets

Load tools from multiple related toolsets:
```

Example 2 (unknown):
```unknown
### Custom Authentication and Parameters

For production scenarios with authentication:
```

Example 3 (unknown):
```unknown
### Manual Connection Management

For explicit control over connections:
```

---

## Define specialized agents for different media types

**URL:** llms-txt#define-specialized-agents-for-different-media-types

image_generator = Agent(
    name="Image Generator",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[OpenAITools(image_model="gpt-image-1")],
    instructions="""You are an expert image generation specialist.
    When users request image creation, you should ACTUALLY GENERATE the image using your available image generation tools.

Always use the generate_image tool to create the requested image based on the user's specifications.
    Include detailed, creative prompts that incorporate style, composition, lighting, and mood details.

After generating the image, provide a brief description of what you created.""",
)

image_describer = Agent(
    name="Image Describer",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="""You are an expert image analyst and describer.
    When you receive an image (either as input or from a previous step), analyze and describe it in vivid detail, including:
    - Visual elements and composition
    - Colors, lighting, and mood
    - Artistic style and technique
    - Emotional impact and narrative

If no image is provided, work with the image description or prompt from the previous step.
    Provide rich, engaging descriptions that capture the essence of the visual content.""",
)

video_generator = Agent(
    name="Video Generator",
    model=OpenAIChat(id="gpt-5-mini"),
    # Video Generation only works on VertexAI mode
    tools=[GeminiTools(vertexai=True)],
    instructions="""You are an expert video production specialist.
    Create detailed video generation prompts and storyboards based on user requests.
    Include scene descriptions, camera movements, transitions, and timing.
    Consider pacing, visual storytelling, and technical aspects like resolution and duration.
    Format your response as a comprehensive video production plan.""",
)

video_describer = Agent(
    name="Video Describer",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="""You are an expert video analyst and critic.
    Analyze and describe videos comprehensively, including:
    - Scene composition and cinematography
    - Narrative flow and pacing
    - Visual effects and production quality
    - Audio-visual harmony and mood
    - Technical execution and artistic merit
    Provide detailed, professional video analysis.""",
)

---

## Create a financial advisor agent with comprehensive hooks

**URL:** llms-txt#create-a-financial-advisor-agent-with-comprehensive-hooks

**Contents:**
- Usage

agent = Agent(
    name="Financial Advisor",
    model=OpenAIChat(id="gpt-5-mini"),
    pre_hooks=[transform_input],
    description="A professional financial advisor providing investment guidance and financial planning advice.",
    instructions=[
        "You are a knowledgeable financial advisor with expertise in:",
        "• Investment strategies and portfolio management",
        "• Retirement planning and savings strategies",
        "• Risk assessment and diversification",
        "• Tax-efficient investing",
        "",
        "Provide clear, actionable advice while being mindful of individual circumstances.",
        "Always remind users to consult with a licensed financial advisor for personalized advice.",
    ],
    debug_mode=True,
)

agent.print_response(
    input="I'm 35 years old and want to start investing for retirement. moderate risk tolerance. retirement savings in IRAs/401(k)s= $100,000. total savings is $200,000. my net worth is $300,000",
    session_id="test_session",
    user_id="test_user",
    stream=True,
)
bash  theme={null}
    pip install -U agno openai
    bash Mac theme={null}
      python cookbook/agents/hooks/input_transformation_pre_hook.py
      bash Windows theme={null}
      python cookbook/agents/hooks/input_transformation_pre_hook.py
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

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Agent Session

**URL:** llms-txt#agent-session

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/getting-started/09-agent-session

This example shows how to create an agent with persistent memory stored in a SQLite database. We set the session\_id on the agent when resuming the conversation, this way the previous chat history is preserved.

* Stores conversation history in a SQLite database
* Continues conversations across multiple sessions
* References previous context in responses

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run the agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Basic Agent

**URL:** llms-txt#basic-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/vllm/basic

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Setup vLLM Server">
    Start a vLLM server locally:

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Setup vLLM Server">
    Start a vLLM server locally:
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

## In-Memory Storage

**URL:** llms-txt#in-memory-storage

**Contents:**
- Usage

Source: https://docs.agno.com/concepts/db/in_memory

Agno supports using In-Memory storage with the `InMemoryDb` class. By doing this, you will be able to use all features that depend on having a database, without having to set one up.

<Warning>
  Using the In-Memory storage is not recommended for production applications.
  Use it for demos, testing and any other use case where you don't want to setup a database.
</Warning>

```python  theme={null}
from agno.agent import Agent
from agno.db.in_memory import InMemoryDb

---

## Agentic RAG with Reasoning Tools

**URL:** llms-txt#agentic-rag-with-reasoning-tools

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/agentic_search/agentic_rag_with_reasoning

This example demonstrates how to implement Agentic RAG with Reasoning Tools, combining knowledge base search with structured reasoning capabilities for more sophisticated responses.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your ANTHROPIC API  key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/agentic_search" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your ANTHROPIC API  key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## - Real-time memory updates during conversation

**URL:** llms-txt#--real-time-memory-updates-during-conversation

---

## Research Agent using Exa

**URL:** llms-txt#research-agent-using-exa

**Contents:**
- Code

Source: https://docs.agno.com/examples/use-cases/agents/research-agent-exa

This example shows how to create a sophisticated research agent that combines
academic search capabilities with scholarly writing expertise. The agent performs
thorough research using Exa's academic search, analyzes recent publications, and delivers
well-structured, academic-style reports on any topic.

* Advanced academic literature search
* Recent publication analysis
* Cross-disciplinary synthesis
* Academic writing expertise
* Citation management

Example prompts to try:

* "Explore recent advances in quantum machine learning"
* "Analyze the current state of fusion energy research"
* "Investigate the latest developments in CRISPR gene editing"
* "Research the intersection of blockchain and sustainable energy"
* "Examine recent breakthroughs in brain-computer interfaces"

```python research_agent_exa.py theme={null}
from datetime import datetime
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools

---

## Create agent with Redis db

**URL:** llms-txt#create-agent-with-redis-db

**Contents:**
- Usage

agent = Agent(
    db=db,
    enable_user_memories=True,
)

agent.print_response("My name is John Doe and I like to play basketball on the weekends.")
agent.print_response("What's do I do in weekends?")
bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    pip install -U agno openai redis
    bash  theme={null}
    docker run --name my-redis -p 6379:6379 -d redis
    bash Mac/Linux theme={null}
      python cookbook/memory/db/mem-redis-memory.py
      bash Windows theme={null}
      python cookbook/memory/db/mem-redis-memory.py
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

  <Step title="Set environment variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Redis">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

---

## Recipe Rag Image

**URL:** llms-txt#recipe-rag-image

**Contents:**
- Code

Source: https://docs.agno.com/examples/use-cases/agents/recipe_rag_image

An agent that uses Llama 4 for multi-modal RAG and OpenAITools to create a visual, step-by-step image manual for a recipe.

```python cookbook/examples/agents/recipe_rag_image.py theme={null}
import asyncio
from pathlib import Path

from agno.agent import Agent
from agno.knowledge.embedder.cohere import CohereEmbedder
from agno.knowledge.knowledge import Knowledge

---

## Example: Ask the agent to search using Searxng

**URL:** llms-txt#example:-ask-the-agent-to-search-using-searxng

**Contents:**
- Toolkit Params
- Toolkit Functions
- Developer Resources

agent.print_response("""
Please search for information about artificial intelligence
and summarize the key points from the top results
""")
```

| Parameter           | Type        | Default | Description                                                        |
| ------------------- | ----------- | ------- | ------------------------------------------------------------------ |
| `host`              | `str`       | -       | The host for the connection.                                       |
| `engines`           | `List[str]` | `[]`    | A list of search engines to use.                                   |
| `fixed_max_results` | `int`       | `None`  | Optional parameter to specify the fixed maximum number of results. |

| Function         | Description                                                                                                                                                                                                                         |
| ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `search`         | Performs a general web search using the specified query. Parameters include `query` for the search term and `max_results` for the maximum number of results (default is 5). Returns the search results.                             |
| `image_search`   | Performs an image search using the specified query. Parameters include `query` for the search term and `max_results` for the maximum number of results (default is 5). Returns the image search results.                            |
| `it_search`      | Performs a search for IT-related information using the specified query. Parameters include `query` for the search term and `max_results` for the maximum number of results (default is 5). Returns the IT-related search results.   |
| `map_search`     | Performs a search for maps using the specified query. Parameters include `query` for the search term and `max_results` for the maximum number of results (default is 5). Returns the map search results.                            |
| `music_search`   | Performs a search for music-related information using the specified query. Parameters include `query` for the search term and `max_results` for the maximum number of results (default is 5). Returns the music search results.     |
| `news_search`    | Performs a search for news using the specified query. Parameters include `query` for the search term and `max_results` for the maximum number of results (default is 5). Returns the news search results.                           |
| `science_search` | Performs a search for science-related information using the specified query. Parameters include `query` for the search term and `max_results` for the maximum number of results (default is 5). Returns the science search results. |
| `video_search`   | Performs a search for videos using the specified query. Parameters include `query` for the search term and `max_results` for the maximum number of results (default is 5). Returns the video search results.                        |

You can use `include_tools` or `exclude_tools` to modify the list of tools the agent has access to. Learn more about [selecting tools](/concepts/tools/selecting-tools).

## Developer Resources

* View [Tools](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/searxng.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/searxng_tools.py)

---

## Agent Context

**URL:** llms-txt#agent-context

**Contents:**
- Code

Source: https://docs.agno.com/examples/getting-started/08-agent-context

This example shows how to inject external dependencies into an agent. The context is evaluated when the agent is run, acting like dependency injection for Agents.

Example prompts to try:

* "Summarize the top stories on HackerNews"
* "What are the trending tech discussions right now?"
* "Analyze the current top stories and identify trends"
* "What's the most upvoted story today?"

```python agent_context.py theme={null}
import json
from textwrap import dedent

import httpx
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_top_hackernews_stories(num_stories: int = 5) -> str:
    """Fetch and return the top stories from HackerNews.

Args:
        num_stories: Number of top stories to retrieve (default: 5)
    Returns:
        JSON string containing story details (title, url, score, etc.)
    """
    # Get top stories
    stories = [
        {
            k: v
            for k, v in httpx.get(
                f"https://hacker-news.firebaseio.com/v0/item/{id}.json"
            )
            .json()
            .items()
            if k != "kids"  # Exclude discussion threads
        }
        for id in httpx.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json"
        ).json()[:num_stories]
    ]
    return json.dumps(stories, indent=4)

---

## Enable AgentOS MCP

**URL:** llms-txt#enable-agentos-mcp

**Contents:**
- Code

Source: https://docs.agno.com/examples/agent-os/mcp/enable_mcp_example

Complete AgentOS setup with MCP support enabled

```python cookbook/agent_os/mcp/enable_mcp_example.py theme={null}

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Setup your Agent with Agentic Memory

**URL:** llms-txt#setup-your-agent-with-agentic-memory

**Contents:**
- Storage: Where Memories Live
  - Custom Table Names

agent = Agent(
    db=db,
    enable_agentic_memory=True, # This enables Agentic Memory for the Agent
)
python  theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb

**Examples:**

Example 1 (unknown):
```unknown
With agentic memory, the agent is equipped with tools to manage memories when it deems relevant. This gives more flexibility but requires the agent to make intelligent decisions about what to remember.

**Best for:** Complex workflows, multi-turn interactions where the agent needs to decide what's worth remembering based on context.

<Note>
  **Important:** Don't enable both `enable_user_memories` and `enable_agentic_memory` at the same time, as they're mutually exclusive. While nothing will break if you set both, `enable_agentic_memory` will always take precedence and `enable_user_memories` will be ignored.
</Note>

## Storage: Where Memories Live

Memories are stored in the database you connect to your agent. Agno supports all major database systems: Postgres, SQLite, MongoDB, and more. Check the [Storage documentation](/concepts/db/overview) for the full list of supported databases and setup instructions.

By default, memories are stored in the `agno_memories` table (or collection, for document databases). If this table doesn't exist when your agent first tries to store a memory, Agno creates it automatically with no manual schema setup required.

### Custom Table Names

You can specify a custom table name for storing memories:
```

---

## AgentOS Demo

**URL:** llms-txt#agentos-demo

**Contents:**
- Code

Source: https://docs.agno.com/examples/agent-os/demo

AgentOS demo with agents and teams

Here is a full example of an AgentOS with multiple agents and teams. It also shows how to instantiate agents with a database, knowledge base, and tools.

```python cookbook/agent_os/demo.py theme={null}
"""
AgentOS Demo

Prerequisites:
pip install -U fastapi uvicorn sqlalchemy pgvector psycopg openai ddgs mcp
"""

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.mcp import MCPTools
from agno.vectordb.pgvector import PgVector

---

## To equipt our Agent with our tool, we simply pass it with the tools parameter

**URL:** llms-txt#to-equipt-our-agent-with-our-tool,-we-simply-pass-it-with-the-tools-parameter

agent = Agent(
    model=OpenAIChat(id="gpt-5-nano"),
    tools=[get_weather],
    markdown=True,
)

---

## Define your agents/team

**URL:** llms-txt#define-your-agents/team

content_creation_workflow = Workflow(
    name="Content Creation Workflow",
    description="Automated content creation from blog posts to social media",
    db=SqliteDb(db_file="tmp/workflow.db"),
    steps=[research_team, content_planner],
)

---

## Agent with Knowledge

**URL:** llms-txt#agent-with-knowledge

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/vercel/knowledge

```python cookbook/models/vercel/knowledge.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.vercel import V0
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    vector_db=PgVector(table_name="recipes", db_url=db_url),
)

---

## AgentOS with MCPTools

**URL:** llms-txt#agentos-with-mcptools

**Contents:**
- Code

Source: https://docs.agno.com/examples/agent-os/mcp/mcp_tools_example

Complete AgentOS setup with MCPTools enabled on agents

```python cookbook/agent_os/mcp/mcp_tools_example.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.tools.mcp import MCPTools

---

## Load knowledge base using hybrid search

**URL:** llms-txt#load-knowledge-base-using-hybrid-search

hybrid_db = PgVector(table_name="recipes", db_url=db_url, search_type=SearchType.hybrid)
knowledge = Knowledge(
    name="Hybrid Search Knowledge Base",
    vector_db=hybrid_db,
)

knowledge.add_content(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
)

---

## Implementing a Custom Retriever

**URL:** llms-txt#implementing-a-custom-retriever

**Contents:**
- Setup
  - Example: Custom Retriever for `Knowledge`

Source: https://docs.agno.com/concepts/knowledge/advanced/custom-retriever

Learn how to implement a custom retriever for precise control over document retrieval in your knowledge base.

In some cases, you may need complete control over how your agent retrieves information from the knowledge base. This can be achieved by implementing a custom retriever function. A custom retriever allows you to define the logic for searching and retrieving documents from your vector database.

Follow the instructions in the [Qdrant Setup Guide](https://qdrant.tech/documentation/guides/installation/) to install Qdrant locally. Here is a guide to get API keys: [Qdrant API Keys](https://qdrant.tech/documentation/cloud/authentication/).

### Example: Custom Retriever for `Knowledge`

Below is a detailed example of how to implement a custom retriever function using the `agno` library. This example demonstrates how to set up a knowledge base with PDF documents, define a custom retriever, and use it with an agent.

```python  theme={null}
from typing import Optional
from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.qdrant import Qdrant
from qdrant_client import QdrantClient

---

## Run agent as an interactive CLI app

**URL:** llms-txt#run-agent-as-an-interactive-cli-app

agent.cli_app(stream=True)
```

---

## Team with Knowledge Base

**URL:** llms-txt#team-with-knowledge-base

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/knowledge/team_with_knowledge

This example demonstrates how to create a team with knowledge base integration. The team has access to a knowledge base with Agno documentation and can combine this knowledge with web search capabilities.

```python cookbook/examples/teams/knowledge/01_team_with_knowledge.py theme={null}
"""
This example demonstrates how to create a team with knowledge base integration.

The team has access to a knowledge base with Agno documentation and can combine
this knowledge with web search capabilities.
"""

from pathlib import Path

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.lancedb import LanceDb, SearchType

---

## LanceDB Agent Knowledge

**URL:** llms-txt#lancedb-agent-knowledge

**Contents:**
- Setup
- Example

Source: https://docs.agno.com/concepts/vectordb/lancedb

```python agent_with_knowledge.py theme={null}
import typer
from typing import Optional
from rich.prompt import Prompt

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType

**Examples:**

Example 1 (unknown):
```unknown
## Example
```

---

## We have to create a tool with the correct name, arguments and docstring for the agent to know what to call.

**URL:** llms-txt#we-have-to-create-a-tool-with-the-correct-name,-arguments-and-docstring-for-the-agent-to-know-what-to-call.

**Contents:**
- Usage

@tool(external_execution=True)
def execute_shell_command(command: str) -> str:
    """Execute a shell command.

Args:
        command (str): The shell command to execute

Returns:
        str: The output of the shell command
    """
    if command.startswith("ls"):
        return subprocess.check_output(command, shell=True).decode("utf-8")
    else:
        raise Exception(f"Unsupported command: {command}")

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[execute_shell_command],
    markdown=True,
    db=SqliteDb(session_table="test_session", db_file="tmp/example.db"),
)

async def main():
    async for run_event in agent.arun(
        "What files do I have in my current directory?", stream=True
    ):
        if run_event.is_paused:
            for tool in run_event.tools_awaiting_external_execution:  # type: ignore
                if tool.tool_name == execute_shell_command.name:
                    print(
                        f"Executing {tool.tool_name} with args {tool.tool_args} externally"
                    )
                    # We execute the tool ourselves. You can also execute something completely external here.
                    result = execute_shell_command.entrypoint(**tool.tool_args)  # type: ignore
                    # We have to set the result on the tool execution object so that the agent can continue
                    tool.result = result

async for resp in agent.acontinue_run(  # type: ignore
                run_id=run_event.run_id,
                updated_tools=run_event.tools,
                stream=True,
            ):
                print(resp.content, end="")
        else:
            print(run_event.content, end="")

# Or for simple debug flow
    # agent.print_response("What files do I have in my current directory?", stream=True)

if __name__ == "__main__":
    asyncio.run(main())
bash  theme={null}
    pip install -U agno openai
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch external_tool_execution_stream_async.py
    bash Mac theme={null}
      python external_tool_execution_stream_async.py
      bash Windows   theme={null}
      python external_tool_execution_stream_async.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## JSON Reader (Async)

**URL:** llms-txt#json-reader-(async)

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/json/json-reader-async

The **JSON Reader** with asynchronous processing allows you to handle JSON files efficiently and integrate them with knowledge bases.

```python examples/concepts/knowledge/readers/json_reader_async.py theme={null}
import json
import asyncio
from pathlib import Path

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.json_reader import JSONReader
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

---

## Recommended: Single memory processing after conversation

**URL:** llms-txt#recommended:-single-memory-processing-after-conversation

agent = Agent(
    db=db,
    enable_user_memories=True  # Processes memories once at end
)

---

## Create agents for research

**URL:** llms-txt#create-agents-for-research

research_agent = Agent(
    name="Research Agent",
    role="Research specialist",
    tools=[HackerNewsTools(), DuckDuckGoTools()],
    instructions="You are a research specialist. Research the given topic thoroughly.",
    markdown=True,
)

analysis_agent = Agent(
    name="Analysis Agent",
    role="Data analyst",
    instructions="You are a data analyst. Analyze and summarize research findings.",
    markdown=True,
)

content_agent = Agent(
    name="Content Agent",
    role="Content creator",
    instructions="You are a content creator. Create engaging content based on research.",
    markdown=True,
)

---

## Setup your Workflow

**URL:** llms-txt#setup-your-workflow

**Contents:**
- Supported databases

workflow = Workflow(db=db, ...)
```

<Note>
  Learn more about [Teams](/concepts/teams/overview) and
  [Workflows](/concepts/workflows/overview), Agno abstractions to build
  multi-agent systems.
</Note>

## Supported databases

This is the list of the databases we currently support:

<CardGroup cols={3}>
  <Card title="DynamoDB" icon="database" iconType="duotone" href="/concepts/db/dynamodb">
    Amazon's NoSQL database service
  </Card>

<Card title="FireStore" icon="database" iconType="duotone" href="/concepts/db/firestore">
    Google's NoSQL document database
  </Card>

<Card title="JSON" icon="file-code" iconType="duotone" href="/concepts/db/json">
    Simple file-based JSON storage
  </Card>

<Card title="JSON on GCS" icon="cloud" iconType="duotone" href="/concepts/db/gcs">
    JSON storage on Google Cloud Storage
  </Card>

<Card title="MongoDB" icon="database" iconType="duotone" href="/concepts/db/mongodb">
    Popular NoSQL document database
  </Card>

<Card title="MySQL" icon="database" iconType="duotone" href="/concepts/db/mysql">
    Widely-used relational database
  </Card>

<Card title="Neon" icon="database" iconType="duotone" href="/concepts/db/neon">
    Serverless PostgreSQL platform
  </Card>

<Card title="PostgreSQL" icon="database" iconType="duotone" href="/concepts/db/postgres">
    Advanced open-source relational database
  </Card>

<Card title="Redis" icon="database" iconType="duotone" href="/concepts/db/redis">
    In-memory data structure store
  </Card>

<Card title="SingleStore" icon="database" iconType="duotone" href="/concepts/db/singlestore">
    Real-time analytics database
  </Card>

<Card title="SQLite" icon="database" iconType="duotone" href="/concepts/db/sqlite">
    Lightweight embedded database
  </Card>

<Card title="Supabase" icon="database" iconType="duotone" href="/concepts/db/supabase">
    Open source Firebase alternative
  </Card>
</CardGroup>

<Note>
  We also support using an [In-Memory](/concepts/db/in_memory) database. This is not recommended for production, but perfect for demos and testing.
</Note>

You can see a detailed list of [examples](/examples/concepts/db) for all supported databases.

---

## Async Agent with Tools

**URL:** llms-txt#async-agent-with-tools

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/vllm/async_tool_use

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install Libraries">
    
  </Step>

<Step title="Start vLLM server">
    
  </Step>

<Step title="Run Agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install Libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Start vLLM server">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
```

---

## Async agent responses

**URL:** llms-txt#async-agent-responses

**Contents:**
  - Knowledge Filtering

response = await agent.arun("What's in the dataset?")
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
### Knowledge Filtering

Control what information agents can access:
```

---

## You can also get the user memories from the agent

**URL:** llms-txt#you-can-also-get-the-user-memories-from-the-agent

---

## Reasoning Agents

**URL:** llms-txt#reasoning-agents

**Contents:**
  - Example

Source: https://docs.agno.com/concepts/reasoning/reasoning-agents

Reasoning Agents are a new type of multi-agent system developed by Agno that combines chain of thought reasoning with tool use.

You can enable reasoning on any Agent by setting `reasoning=True`.

When an Agent with `reasoning=True` is given a task, a separate "Reasoning Agent" first solves the problem using chain-of-thought. At each step, it calls tools to gather information, validate results, and iterate until it reaches a final answer. Once the Reasoning Agent has a final answer, it hands the results back to the original Agent to validate and provide a response.

```python reasoning_agent.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat

---

## Add content to the knowledge

**URL:** llms-txt#add-content-to-the-knowledge

**Contents:**
- Usage

knowledge.add_content(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"
)

agent = Agent(model=V0(id="v0-1.0-md"), knowledge=knowledge)
agent.print_response("How to make Thai curry?", markdown=True)
bash  theme={null}
    export V0_API_KEY=xxx
    bash  theme={null}
    pip install -U ddgs sqlalchemy pgvector pypdf openai agno
    bash  theme={null}
    docker run -d \
      -e POSTGRES_DB=ai \
      -e POSTGRES_USER=ai \
      -e POSTGRES_PASSWORD=ai \
      -e PGDATA=/var/lib/postgresql/data/pgdata \
      -v pgvolume:/var/lib/postgresql/data \
      -p 5532:5432 \
      --name pgvector \
      agnohq/pgvector:16
    bash Mac theme={null}
      python cookbook/models/vercel/knowledge.py
      bash Windows theme={null}
      python cookbook/models/vercel/knowledge.py
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

  <Step title="Run PgVector">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

---

## Memory with MongoDB

**URL:** llms-txt#memory-with-mongodb

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/memory/db/mem-mongodb-memory

```python cookbook/memory/db/mem-mongodb-memory.py theme={null}
from agno.agent import Agent
from agno.db.mongo import MongoDb

---

## Youtube Agent

**URL:** llms-txt#youtube-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/use-cases/agents/youtube-agent

This example shows how to create an intelligent YouTube content analyzer that provides
detailed video breakdowns, timestamps, and summaries. Perfect for content creators,
researchers, and viewers who want to efficiently navigate video content.

Example prompts to try:

* "Analyze this tech review: \[video\_url]"
* "Get timestamps for this coding tutorial: \[video\_url]"
* "Break down the key points of this lecture: \[video\_url]"
* "Summarize the main topics in this documentary: \[video\_url]"
* "Create a study guide from this educational video: \[video\_url]"

```python youtube_agent.py theme={null}
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.youtube import YouTubeTools

youtube_agent = Agent(
    name="YouTube Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[YouTubeTools()],
        instructions=dedent("""\
        You are an expert YouTube content analyst with a keen eye for detail! 🎓
        Follow these steps for comprehensive video analysis:
        1. Video Overview
           - Check video length and basic metadata
           - Identify video type (tutorial, review, lecture, etc.)
           - Note the content structure
        2. Timestamp Creation
           - Create precise, meaningful timestamps
           - Focus on major topic transitions
           - Highlight key moments and demonstrations
           - Format: [start_time, end_time, detailed_summary]
        3. Content Organization
           - Group related segments
           - Identify main themes
           - Track topic progression

Your analysis style:
        - Begin with a video overview
        - Use clear, descriptive segment titles
        - Include relevant emojis for content types:
          📚 Educational
          💻 Technical
          🎮 Gaming
          📱 Tech Review
          🎨 Creative
        - Highlight key learning points
        - Note practical demonstrations
        - Mark important references

Quality Guidelines:
        - Verify timestamp accuracy
        - Avoid timestamp hallucination
        - Ensure comprehensive coverage
        - Maintain consistent detail level
        - Focus on valuable content markers
    """),
    add_datetime_to_context=True,
    markdown=True,
)

---

## AgentOS Parameters

**URL:** llms-txt#agentos-parameters

Source: https://docs.agno.com/agent-os/customize/os/attributes

Learn about the attributes of the AgentOS class

You can configure the behaviour of your AgentOS by passing the following parameters to the `AgentOS` class:

* `agents`: List of agents to include in the AgentOS
* `teams`: List of teams to include in the AgentOS
* `workflows`: List of workflows to include in the AgentOS
* `knowledge`: List of knowledge instances to include in the AgentOS
* `interfaces`: List of interfaces to include in the AgentOS
  * See the [Interfaces](/agent-os/interfaces) section for more details.
* `config`: Configuration file path or `AgentOSConfig` instance
  * See the [Configuration](/agent-os/customize/config) page for more details.
* `base_app`: Optional custom FastAPI app to use instead of creating a new one
  * See the [Custom FastAPI App](/agent-os/customize/custom-fastapi) page for more details.
* `lifespan`: Optional lifespan context manager for the FastAPI app
  * See the [Lifespan](/agent-os/customize/os/lifespan) page for more details.
* `enable_mcp_server`: Turn your AgentOS into an MCP server
  * See the [MCP enabled AgentOS](/agent-os/mcp/mcp) page for more details.
* `on_route_conflict`: Optionally preserve your custom routes over AgentOS routes (set to `"preserve_base_app"`). Defaults to `"preserve_agentos"`, preserving the AgentOS routes
  * See the [Overriding Routes](/agent-os/customize/os/override_routes) page for more details.

See the [AgentOS class reference](/reference/agent-os/agent-os) for more details.

---

## Reddit search agent with tool hooks

**URL:** llms-txt#reddit-search-agent-with-tool-hooks

reddit_agent = Agent(
    name="Reddit Agent",
    id="reddit-agent",
    role="Search reddit for information",
    tools=[RedditTools(cache_results=True)],
    instructions=[
        "Find information about the company on Reddit",
    ],
    tool_hooks=[logger_hook],
)

---

## Agent searches knowledge base for return policy information

**URL:** llms-txt#agent-searches-knowledge-base-for-return-policy-information

---

## Cross-Reference Validator Agent - Validates across sources

**URL:** llms-txt#cross-reference-validator-agent---validates-across-sources

cross_reference_validator = Agent(
    name="Cross-Reference Validator",
    model=Claude(id="claude-3-7-sonnet-latest"),
    role="Validate information consistency across different search results",
    instructions=[
        "Compare and validate information from both searchers.",
        "Identify consistencies and discrepancies in the results.",
        "Highlight areas where information aligns or conflicts.",
        "Assess the reliability of different information sources.",
    ],
    markdown=True,
)

---

## Create another fresh agent

**URL:** llms-txt#create-another-fresh-agent

streaming_agent_alt = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[ReasoningTools(add_instructions=True)],
    instructions=dedent("""\
        You are an expert problem-solving assistant with strong analytical skills! 🧠
        Use step-by-step reasoning to solve the problem.
        \
    """),
)

---

## PDF URL Password Reader

**URL:** llms-txt#pdf-url-password-reader

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/pdf/pdf-url-password-reader

The **PDF URL Password Reader** processes password-protected PDF files directly from URLs, allowing you to handle secure remote documents.

```python examples/concepts/knowledge/readers/pdf_reader_url_password.py theme={null}
from agno.agent import Agent
from agno.knowledge.content import ContentAuth
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

---

## Create the social media analysis agent

**URL:** llms-txt#create-the-social-media-analysis-agent

**Contents:**
- Usage

social_media_agent = Agent(
    name="Social Media Analyst",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[
        XTools(
            include_post_metrics=True,
            wait_on_rate_limit=True,
        )
    ],
    instructions="""
    You are a senior Brand Intelligence Analyst with a specialty in social-media listening  on the X (Twitter) platform.  
    Your job is to transform raw tweet content and engagement metrics into an executive-ready intelligence report that helps product, marketing, and support teams  make data-driven decisions.

────────────────────────────────────────────────────────────
    CORE RESPONSIBILITIES
    ────────────────────────────────────────────────────────────
    1. Retrieve tweets with X tools that you have access to and analyze both the text and metrics such as likes, retweets, replies.
    2. Classify every tweet as Positive / Negative / Neutral / Mixed, capturing the reasoning (e.g., praise for feature X, complaint about bugs, etc.).
    3. Detect patterns in engagement metrics to surface:
       • Viral advocacy (high likes & retweets, low replies)
       • Controversy (low likes, high replies)
       • Influence concentration (verified or high-reach accounts driving sentiment)
    4. Extract thematic clusters and recurring keywords covering:
       • Feature praise / pain points  
       • UX / performance issues  
       • Customer-service interactions  
       • Pricing & ROI perceptions  
       • Competitor mentions & comparisons  
       • Emerging use-cases & adoption barriers
    5. Produce actionable, prioritized recommendations (Immediate, Short-term, Long-term) that address the issues and pain points.
    6. Supply a response strategy: which posts to engage, suggested tone & template,    influencer outreach, and community-building ideas.

────────────────────────────────────────────────────────────
    DELIVERABLE FORMAT (markdown)
    ────────────────────────────────────────────────────────────
    ### 1 · Executive Snapshot
    • Brand-health score (1-10)  
    • Net sentiment ( % positive – % negative )  
    • Top 3 positive & negative drivers  
    • Red-flag issues that need urgent attention

### 2 · Quantitative Dashboard
    | Sentiment | #Posts | % | Avg Likes | Avg Retweets | Avg Replies | Notes |
    |-----------|-------:|---:|----------:|-------------:|------------:|------|
    ( fill table )

### 3 · Key Themes & Representative Quotes
    For each major theme list: description, sentiment trend, excerpted tweets (truncated),  and key metrics.

### 4 · Competitive & Market Signals
    • Competitors referenced, sentiment vs. Agno  
    • Feature gaps users mention  
    • Market positioning insights

### 5 · Risk Analysis
    • Potential crises / viral negativity  
    • Churn indicators  
    • Trust & security concerns

### 6 · Opportunity Landscape
    • Features or updates that delight users  
    • Advocacy moments & influencer opportunities  
    • Untapped use-cases highlighted by the community

### 7 · Strategic Recommendations
    **Immediate (≤48 h)** – urgent fixes or comms  
    **Short-term (1-2 wks)** – quick wins & tests  
    **Long-term (1-3 mo)** – roadmap & positioning

### 8 · Response Playbook
    For high-impact posts list: tweet-id/url, suggested response, recommended responder (e. g., support, PM, exec), and goal (defuse, amplify, learn).

────────────────────────────────────────────────────────────
    ASSESSMENT & REASONING GUIDELINES
    ────────────────────────────────────────────────────────────
    • Weigh sentiment by engagement volume & author influence (verified == ×1.5 weight).  
    • Use reply-to-like ratio > 0.5 as controversy flag.  
    • Highlight any coordinated or bot-like behaviour.  
    • Use the tools provided to you to get the data you need.

Remember: your insights will directly inform the product strategy, customer-experience efforts, and brand reputation.  Be objective, evidence-backed, and solution-oriented.
""",
    markdown=True,
)

social_media_agent.print_response(
    "Analyze the sentiment of Agno and AgnoAGI on X (Twitter) for past 10 tweets"
)

bash  theme={null}
    export OPENAI_API_KEY=xxx
    export X_BEARER_TOKEN=xxx
    export X_CONSUMER_KEY=xxx
    export X_CONSUMER_SECRET=xxx
    export X_ACCESS_TOKEN=xxx
    export X_ACCESS_TOKEN_SECRET=xxx
    bash  theme={null}
    pip install -U agno openai tweepy
    bash Mac theme={null}
      python cookbook/examples/agents/social_media_agent.py
      bash Windows theme={null}
      python cookbook/examples/agents/social_media_agent.py
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

## Agent with Media

**URL:** llms-txt#agent-with-media

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/integrations/discord/agent_with_media

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API keys">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Custom Memory Manager

**URL:** llms-txt#custom-memory-manager

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/memory/04-custom-memory-manager

This example shows how you can configure the Memory Manager.

We also set custom system prompts for the memory manager. You can either override the entire system prompt or add additional instructions which is added to the end of the system prompt.

```python custom_memory_manager.py theme={null}
from agno.agent.agent import Agent
from agno.db.postgres import PostgresDb
from agno.memory import MemoryManager
from agno.models.openai import OpenAIChat
from rich.pretty import pprint

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

db = PostgresDb(db_url=db_url)

---

## Create web search agent for supplementary information

**URL:** llms-txt#create-web-search-agent-for-supplementary-information

web_agent = Agent(
    name="Web Search Agent",
    role="Handle web search requests",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    instructions=["Always include sources"],
)

---

## AgentOS + MCPTools

**URL:** llms-txt#agentos-+-mcptools

Source: https://docs.agno.com/agent-os/mcp/tools

Learn how to use MCPTools in your AgentOS

Model Context Protocol (MCP) gives Agents the ability to interact with external systems through a standardized interface.

You can give your agents access to tools from MCP servers using [`MCPTools`](/concepts/tools/mcp).

When using MCPTools within AgentOS, the lifecycle is automatically managed. No need to manually connect or disconnect the `MCPTools` instance.

```python mcp_tools_example.py theme={null}
from agno.agent import Agent
from agno.os import AgentOS
from agno.tools.mcp import MCPTools

---

## What are Workflows?

**URL:** llms-txt#what-are-workflows?

**Contents:**
- Why should you use Workflows?
- Deterministic Step Execution
- Guides

Source: https://docs.agno.com/concepts/workflows/overview

Learn how Agno Workflows enable deterministic, controlled automation of multi-agent systems

Agno Workflows enable you to build deterministic, controlled agentic flows by orchestrating agents, teams, and functions through a series of defined steps. Unlike free-form agent interactions, workflows provide structured automation with predictable execution patterns, making them ideal for production systems that require reliable, repeatable processes.

<img className="block dark:hidden" src="https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow-light.png?fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=a308215dbae7c8e9050d03af47cfcf1b" alt="Workflows flow diagram" data-og-width="2994" width="2994" data-og-height="756" height="756" data-path="images/workflows-flow-light.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow-light.png?w=280&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=36da448838231c986ea6fbee6cd20adf 280w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow-light.png?w=560&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=2f79f8986f962ceed254128c04e2fff0 560w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow-light.png?w=840&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=602db868a58a7ebadfb6849d783dacdf 840w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow-light.png?w=1100&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=79ab80554e556943fad1bb1c54c23c1b 1100w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow-light.png?w=1650&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=0c06010680d6e281b4ca6f90f8febc23 1650w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow-light.png?w=2500&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=6195335508ec97552803e2920695044d 2500w" />

<img className="hidden dark:block" src="https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow.png?fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=e9ef16c48420b7eee9312561ab56098e" alt="Workflows flow diagram" data-og-width="2994" width="2994" data-og-height="756" height="756" data-path="images/workflows-flow.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow.png?w=280&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=cb8faae1ea504803ff761ae3b89c51fb 280w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow.png?w=560&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=498fe144844ce93806c7f590823ae666 560w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow.png?w=840&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=e8bd51333fbf023524a636d579f489f2 840w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow.png?w=1100&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=f4447ccd6c0c84f2ca104eb2ce7b560b 1100w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow.png?w=1650&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=5a6c0f92fc29f107e4249432216a6b0f 1650w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-flow.png?w=2500&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=0192f698b51c565c3efd9259472c8750 2500w" />

## Why should you use Workflows?

Workflows provide deterministic control over your agentic systems, enabling you to build reliable automation that executes consistently every time. They're essential when you need:

**Deterministic Execution**

* Predictable step-by-step processing with defined inputs and outputs
* Consistent results across multiple runs
* Clear audit trails for production systems

**Complex Orchestration**

* Multi-agent coordination with controlled handoffs
* Parallel processing and conditional branching
* Loop structures for iterative tasks

Workflows excel at **deterministic agent automation**, while [Teams](/concepts/teams/overview) are designed for **dynamic agentic coordination**. Use workflows when you need predictable, repeatable processes; use teams when you need flexible, collaborative problem-solving.

## Deterministic Step Execution

Workflows execute as a controlled sequence of steps, where each step produces deterministic outputs that feed into the next step. This creates predictable data flows and consistent results, unlike free-form agent conversations.

* **Agents**: Individual AI executors with specific capabilities and instructions
* **Teams**: Coordinated groups of agents working together on complex problems
* **Functions**: Custom Python functions for specialized processing logic

**Deterministic Benefits**
Your agents and teams retain their individual characteristics and capabilities, but now operate within a structured framework that ensures:

* **Predictable execution**: Steps run in defined order with controlled inputs/outputs
* **Repeatable results**: Same inputs produce consistent outputs across runs
* **Clear data flow**: Output from each step explicitly becomes input for the next
* **Controlled state**: Session management and state persistence between steps
* **Reliable error handling**: Built-in retry mechanisms and error recovery

<CardGroup cols={2}>
  <Card title="View Complete Example" icon="code" href="/examples/concepts/workflows/01-basic-workflows/sequence_of_functions_and_agents">
    See the full example with agents, teams, and functions working together
  </Card>

<Card title="Use in AgentOS" icon="play" href="/agent-os/features/chat-interface#run-a-workflow">
    Run your workflows through the AgentOS chat interface
  </Card>
</CardGroup>

---

## Supabase MCP agent

**URL:** llms-txt#supabase-mcp-agent

Source: https://docs.agno.com/examples/concepts/tools/mcp/supabase

Using the [Supabase MCP server](https://github.com/supabase-community/supabase-mcp) to create an Agent that can create projects, database schemas, edge functions, and more:

```python  theme={null}
"""🔑 Supabase MCP Agent - Showcase Supabase MCP Capabilities

This example demonstrates how to use the Supabase MCP server to create projects, database schemas, edge functions, and more.

Setup:
1. Install Python dependencies: `pip install agno mcp-sdk`
2. Create a Supabase Access Token: https://supabase.com/dashboard/account/tokens and set it as the SUPABASE_ACCESS_TOKEN environment variable.
"""

import asyncio
import os
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools
from agno.tools.reasoning import ReasoningTools
from agno.utils.log import log_error, log_exception, log_info

async def run_agent(task: str) -> None:
    token = os.getenv("SUPABASE_ACCESS_TOKEN")
    if not token:
        log_error("SUPABASE_ACCESS_TOKEN environment variable not set.")
        return

npx_cmd = "npx.cmd" if os.name == "nt" else "npx"

try:
        async with MCPTools(
            f"{npx_cmd} -y @supabase/mcp-server-supabase@latest --access-token={token}"
        ) as mcp:
            instructions = dedent(f"""
                You are an expert Supabase MCP architect. Given the project description:
                {task}

Automatically perform the following steps :
                1. Plan the entire database schema based on the project description.
                2. Call `list_organizations` and select the first organization in the response.
                3. Use `get_cost(type='project')` to estimate project creation cost and mention the cost in your response.
                4. Create a new Supabase project with `create_project`, passing the confirmed cost ID.
                5. Poll project status with `get_project` until the status is `ACTIVE_HEALTHY`.
                6. Analyze the project requirements and propose a complete, normalized SQL schema (tables,  columns, data types, indexes, constraints, triggers, and functions) as DDL statements.
                7. Apply the schema using `apply_migration`, naming the migration `initial_schema`.
                8. Validate the deployed schema via `list_tables` and `list_extensions`.
                8. Deploy a simple health-check edge function with `deploy_edge_function`.
                9. Retrieve and print the project URL (`get_project_url`) and anon key (`get_anon_key`).
            """)
            agent = Agent(
                model=OpenAIChat(id="o4-mini"),
                instructions=instructions,
                tools=[mcp, ReasoningTools(add_instructions=True)],
                markdown=True,
            )

log_info(f"Running Supabase project agent for: {task}")
            await agent.aprint_response(
                message=task,
                stream=True,
                stream_events=True,
                show_full_reasoning=True,
            )
    except Exception as e:
        log_exception(f"Unexpected error: {e}")

if __name__ == "__main__":
    demo_description = (
        "Develop a cloud-based SaaS platform with AI-powered task suggestions, calendar syncing, predictive prioritization, "
        "team collaboration, and project analytics."
    )
    asyncio.run(run_agent(demo_description))

---

## Get the combined app with both AgentOS and your routes

**URL:** llms-txt#get-the-combined-app-with-both-agentos-and-your-routes

**Contents:**
  - Adding Middleware
  - Running with FastAPI CLI
  - Running in Production
- Adding Custom Routers

app = agent_os.get_app()
bash Install FastAPI CLI theme={null}
pip install "fastapi[standard]"
bash Run with FastAPI CLI theme={null}
  fastapi run your_app.py
  bash Run with auto-reload theme={null}
  fastapi run your_app.py --reload
  bash Custom host and port theme={null}
  fastapi run your_app.py --host 0.0.0.0 --port 8000
  bash Uvicorn theme={null}
  uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
  bash Gunicorn with Uvicorn workers theme={null}
  gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
  bash FastAPI CLI (Production) theme={null}
  fastapi run main.py --host 0.0.0.0 --port 8000
  python custom_fastapi_app.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.tools.duckduckgo import DuckDuckGoTools
from fastapi import FastAPI

**Examples:**

Example 1 (unknown):
```unknown
<Tip>
  Your custom FastAPI app can have its own middleware and dependencies.

  If you have your own CORS middleware, it will be updated to include the AgentOS allowed origins, to make the AgentOS instance compatible with the Control Plane.
  If not then the appropriate CORS middleware will be added to the app.
</Tip>

### Adding Middleware

You can add any FastAPI middleware to your custom FastAPI app and it would be respected by AgentOS.

Agno also provides some built-in middleware for common use cases, including authentication.

See the [Middleware](/agent-os/customize/middleware/overview) page for more details.

### Running with FastAPI CLI

AgentOS applications are compatible with the [FastAPI CLI](https://fastapi.tiangolo.com/deployment/manually/) for development.

First, install the FastAPI CLI:
```

Example 2 (unknown):
```unknown
Then run the app:

<CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown

```

---

## Let's run the agent providing a session_state. This session_state will be stored in the database.

**URL:** llms-txt#let's-run-the-agent-providing-a-session_state.-this-session_state-will-be-stored-in-the-database.

agent.print_response(
    "Can you tell me what's in your session_state?",
    session_state={"shopping_list": ["Potatoes"]},
    stream=True,
)
print(f"Stored session state: {agent.get_session_state()}")

---

## Performance on Agent Response

**URL:** llms-txt#performance-on-agent-response

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/evals/performance/performance_simple_response

Example showing how to analyze the runtime and memory usage of an Agent's run, given its response.

---

## Setup our AgentOS app by passing your FastAPI app

**URL:** llms-txt#setup-our-agentos-app-by-passing-your-fastapi-app

agent_os = AgentOS(
    description="Example app with custom routers",
    agents=[web_research_agent],
    base_app=app,
)

---

## Agent Input as List

**URL:** llms-txt#agent-input-as-list

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/input_as_list

This example demonstrates how to provide input to an agent as a list format for multimodal content combining text and images.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/input_and_output" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## CSV Reader Async

**URL:** llms-txt#csv-reader-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/csv/csv-reader-async

The **CSV Reader** with asynchronous processing allows you to handle CSV files and integrate them with knowledge bases efficiently.

```python examples/concepts/knowledge/readers/csv_reader_async.py theme={null}
import asyncio
from pathlib import Path

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="csv_documents",
        db_url=db_url,
    ),
    max_results=5,  # Number of results to return on search
)

---

## What is Storage?

**URL:** llms-txt#what-is-storage?

**Contents:**
- Adding storage to your Agent

Source: https://docs.agno.com/concepts/db/overview

Enable your Agents to store session history, memories, and more.

**Storage** adds persistence to your Agents, allowing them to remember previous messages, user memories, and more.

It works by equipping your Agents with a database that they will use to store and retrieve:

* [Sessions](/concepts/agents/sessions)
* [User Memories](/concepts/agents/memory)

In addition this DB is used to store [knowledge](/concepts/knowledge/content_db) and [evals](/concepts/evals/overview).

<Tip>
  **When should I use Storage on my Agents?**

Agents are ephemeral by default. They won't remember previous conversations.

But in production environments, you will often need to continue the same session across multiple requests. Storage is the way to persist the session history and state in a database, enabling us to pick up where we left off.

Storage also lets us inspect and evaluate Agent sessions, extract few-shot examples and build internal monitoring tools. In general, it lets you **keep track of the data**, to build better Agents.
</Tip>

## Adding storage to your Agent

To enable session persistence on your Agent, just setup a database and provide it to the Agent:

```python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SQLiteDb

---

## Firecrawl Reader

**URL:** llms-txt#firecrawl-reader

**Contents:**
- Code
- Usage
- Params

Source: https://docs.agno.com/examples/concepts/knowledge/readers/firecrawl/firecrawl-reader

The **Firecrawl Reader** uses the Firecrawl API to scrape and crawl web content, converting it into documents for your knowledge base.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Set API Key">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

<Snippet file="firecrawl-reader-reference.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set API Key">
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

## PPTX Reader Async

**URL:** llms-txt#pptx-reader-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/pptx/pptx-reader-async

The **PPTX Reader** with asynchronous processing allows you to read and extract text content from PowerPoint (.pptx) files with better performance for concurrent operations.

```python pptx_reader_async.py theme={null}
import asyncio

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pptx_reader import PPTXReader
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    # Table name: ai.pptx_documents
    vector_db=PgVector(
        table_name="pptx_documents",
        db_url=db_url,
    ),
)

---

## What are Knowledge Filters?

**URL:** llms-txt#what-are-knowledge-filters?

**Contents:**
- Why Use Knowledge Filters?
- How Do Knowledge Filters Work?
- Ways to Apply Filters
- Filters in Traditional RAG vs. Agentic RAG
- Best Practices
- Manual vs. Agentic Filtering
- Developer Resources

Source: https://docs.agno.com/concepts/knowledge/filters/overview

Use knowledge filters to restrict and refine searches

Knowledge filters allow you to restrict and refine searches within your knowledge base using metadata such as user IDs, document types, years, and more. This feature is especially useful when you have a large collection of documents and want to retrieve information relevant to specific users or contexts.

## Why Use Knowledge Filters?

* **Personalization:** Retrieve information for a specific user or group.
* **Security:** Restrict access to sensitive documents.
* **Efficiency:** Reduce noise by narrowing down search results.

## How Do Knowledge Filters Work?

When you load documents into your knowledge base, you can attach metadata (like user ID, document type, year, etc.). Later, when querying, you can specify filters to only search documents matching certain criteria.

**Example Metadata:**

## Ways to Apply Filters

You can apply knowledge filters in two main ways:

1. **Manual Filters:** Explicitly pass filters when querying.
2. **Agentic Filters:** Let the Agent automatically extract filters from your query.

> **Tip:** You can combine multiple filters for more precise results!

## Filters in Traditional RAG vs. Agentic RAG

When configuring your Agent it is important to choose the right approach for your use case. There are two broad approaches to RAG with Agno agents: traditional RAG and agentic RAG. With a traditional RAG approach you set `add_knowledge_to_context=True` to ensure that references are included in the system message sent to the LLM. For Agentic RAG, you set `search_knowledge=True` to leverage the agent's ability search the knowledge base directly.

<Check>
  Remember to use only one of these configurations at a time, setting the other to false. By default, `search_knowledge=True` is preferred as it offers a more dynamic and interactive experience.
  Checkout an example [here](/examples/concepts/knowledge/filters/filtering) of how to set up knowledge filters in a Traditional RAG system
</Check>

* Make your prompts descriptive (e.g., include user names, document types, years).
* Use agentic filtering for interactive applications or chatbots.

## Manual vs. Agentic Filtering

| Manual Filtering         | Agentic Filtering                |
| ------------------------ | -------------------------------- |
| Explicit filters in code | Filters inferred from query text |
| Full control             | More natural, less code          |
| Good for automation      | Good for user-facing apps        |

<Note>
  🚦 **Currently, knowledge filtering is supported on the following vector databases:**

* **Qdrant**
  * **LanceDB**
  * **PgVector**
  * **MongoDB**
  * **Pinecone**
  * **Weaviate**
  * **ChromaDB**
  * **Milvus**
</Note>

## Developer Resources

See the detailed cookbooks [here](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/filters/README.md)

**Examples:**

Example 1 (unknown):
```unknown
## Ways to Apply Filters

You can apply knowledge filters in two main ways:

1. **Manual Filters:** Explicitly pass filters when querying.
2. **Agentic Filters:** Let the Agent automatically extract filters from your query.

> **Tip:** You can combine multiple filters for more precise results!

## Filters in Traditional RAG vs. Agentic RAG

When configuring your Agent it is important to choose the right approach for your use case. There are two broad approaches to RAG with Agno agents: traditional RAG and agentic RAG. With a traditional RAG approach you set `add_knowledge_to_context=True` to ensure that references are included in the system message sent to the LLM. For Agentic RAG, you set `search_knowledge=True` to leverage the agent's ability search the knowledge base directly.

Example:
```

---

## Performance Evals

**URL:** llms-txt#performance-evals

**Contents:**
- Basic Example
- Tool Usage Performance
- Performance with asyncronous functions

Source: https://docs.agno.com/concepts/evals/performance

Learn how to measure the latency and memory footprint of your Agno Agents and Teams.

Performance evals measure the latency and memory footprint of an Agent or Team.

<Frame>
  <img height="200" src="https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=ed1f5ecf303b83d454af05ae6e3a14d7" data-og-width="1528" data-og-height="748" data-path="images/evals/performance_basic.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=280&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=037bf59b601e8c9b8cf5779ca66cd302 280w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=560&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=3c79dff6bf7eca3de5abad855b0598a0 560w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=840&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=d4fd86aa92eecfba7a32c9608a23abb3 840w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=1100&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=59b2683492b2a8473b66800c0bb13129 1100w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=1650&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=a1ee1c1d8b8e01abdbabbe6e49fbac60 1650w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=2500&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=2efdebf30a5a05f1303f4baaa840db11 2500w" />
</Frame>

## Tool Usage Performance

Compare how tools affects your agent's performance:

## Performance with asyncronous functions

Evaluate agent performance with asyncronous functions:

```python async_performance.py theme={null}

"""This example shows how to run a Performance evaluation on an async function."""

from agno.agent import Agent
from agno.eval.performance import PerformanceEval
from agno.models.openai import OpenAIChat

**Examples:**

Example 1 (unknown):
```unknown
<Frame>
  <img height="200" src="https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=ed1f5ecf303b83d454af05ae6e3a14d7" data-og-width="1528" data-og-height="748" data-path="images/evals/performance_basic.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=280&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=037bf59b601e8c9b8cf5779ca66cd302 280w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=560&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=3c79dff6bf7eca3de5abad855b0598a0 560w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=840&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=d4fd86aa92eecfba7a32c9608a23abb3 840w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=1100&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=59b2683492b2a8473b66800c0bb13129 1100w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=1650&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=a1ee1c1d8b8e01abdbabbe6e49fbac60 1650w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/performance_basic.png?w=2500&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=2efdebf30a5a05f1303f4baaa840db11 2500w" />
</Frame>

## Tool Usage Performance

Compare how tools affects your agent's performance:
```

Example 2 (unknown):
```unknown
## Performance with asyncronous functions

Evaluate agent performance with asyncronous functions:
```

---

## RAG with LanceDB and SQLite

**URL:** llms-txt#rag-with-lancedb-and-sqlite

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/rag/rag-with-lance-db-and-sqlite

```python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.ollama import Ollama
from agno.vectordb.lancedb import LanceDb

---

## Knowledge base with advanced reranking

**URL:** llms-txt#knowledge-base-with-advanced-reranking

reranked_knowledge = Knowledge(
    vector_db=LanceDb(
        table_name="recipes_reranked",
        uri="tmp/lancedb",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        reranker=CohereReranker(model="rerank-v3.5"),
    ),
)

---

## How Knowledge Works

**URL:** llms-txt#how-knowledge-works

**Contents:**
- The Knowledge Pipeline: Three Simple Steps
- Vector Embeddings and Search
- Setting Up Knowledge in Code

Source: https://docs.agno.com/concepts/knowledge/how-it-works

Learn the Knowledge pipeline and technical architecture that powers intelligent knowledge retrieval in Agno agents.

At its core, Agno's Knowledge system is **Retrieval Augmented Generation (RAG)** made simple. Instead of cramming everything into a prompt, you store information in a searchable knowledge base and let agents pull exactly what they need, when they need it.

## The Knowledge Pipeline: Three Simple Steps

<Steps>
  <Step title="Store: Break Down and Index Information">
    Your documents, files, and data are processed by specialized readers, broken into chunks using configurable strategies, and stored in a vector database with their meanings captured as embeddings.

**Example:** A 50-page employee handbook is processed by Agno's PDFReader, chunked using SemanticChunking strategy, and becomes 200 searchable chunks with topics like "vacation policy," "remote work guidelines," or "expense procedures."
  </Step>

<Step title="Search: Find Relevant Information">
    When a user asks a question, the agent automatically searches the knowledge base using Agno's search methods to find the most relevant information chunks.

**Example:** User asks "How many vacation days do I get?" → Agent calls `knowledge.search()` and finds chunks about vacation policies, PTO accrual, and holiday schedules.
  </Step>

<Step title="Generate: Create Contextual Responses">
    The agent combines the retrieved information with the user's question to generate an accurate, contextual response, with sources tracked through Agno's content management system.

**Example:** "Based on your employee handbook, full-time employees receive 15 vacation days per year, accrued monthly at 1.25 days per month..."
  </Step>
</Steps>

## Vector Embeddings and Search

Think of embeddings as a way to capture meaning in numbers. When you ask "What's our refund policy?", the system doesn't just match the word "refund"—it understands you're asking about returns, money back, and customer satisfaction.

That's because text gets converted into **vectors** (lists of numbers) where similar meanings cluster together. "Refund policy" and "return procedures" end up close in vector space, even though they don't share exact words. This is what enables semantic search beyond simple keyword matching.

## Setting Up Knowledge in Code

Here's how you connect the pieces to build a knowledge-powered agent:

```python  theme={null}
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.chunking.semantic import SemanticChunking
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.agent import Agent

---

## Now let's setup an Agent and run it.

**URL:** llms-txt#now-let's-setup-an-agent-and-run-it.

---

## Team with Agentic Knowledge Filters

**URL:** llms-txt#team-with-agentic-knowledge-filters

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/knowledge/team_with_agentic_knowledge_filters

This example demonstrates how to use agentic knowledge filters with teams. Unlike predefined filters, agentic knowledge filters allow the AI to dynamically determine which documents to search based on the query context, providing more intelligent and context-aware document retrieval.

```python cookbook/examples/teams/knowledge/03_team_with_agentic_knowledge_filters.py theme={null}
"""
This example demonstrates how to use agentic knowledge filters with teams.

Agentic knowledge filters allow the AI to dynamically determine which documents
to search based on the query context, rather than using predefined filters.
"""

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.lancedb import LanceDb

---

## Agentic RAG with PgVector

**URL:** llms-txt#agentic-rag-with-pgvector

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/knowledge/rag/agentic-rag-pgvector

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run PgVector">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

  <Step title="Run PgVector">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

---

## Hybrid knowledge base for comprehensive search

**URL:** llms-txt#hybrid-knowledge-base-for-comprehensive-search

hybrid_knowledge = Knowledge(
    vector_db=PgVector(
        table_name="recipes_hybrid",
        db_url=db_url,
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

---

## Image to Image Generation Agent

**URL:** llms-txt#image-to-image-generation-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/image_to_image_agent

This example demonstrates how to create an AI agent that generates images from existing images using the Fal AI API.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/multimodal" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Evidence Evaluator Agent - Specialized in evidence assessment

**URL:** llms-txt#evidence-evaluator-agent---specialized-in-evidence-assessment

evidence_evaluator = Agent(
    name="Evidence Evaluator",
    model=Claude(id="claude-sonnet-4-20250514"),
    role="Evaluate evidence quality and identify information gaps",
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "Evaluate the quality and reliability of gathered evidence.",
        "Identify gaps in information or reasoning.",
        "Assess the strength of logical connections.",
        "Highlight areas needing additional clarification.",
        "Use reasoning tools to structure your evaluation.",
    ],
    markdown=True,
)

---

## Add Markdown content to knowledge base

**URL:** llms-txt#add-markdown-content-to-knowledge-base

knowledge.add_content(
    path=Path("README.md"),
    reader=MarkdownReader(),
)

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
)

---

## Sync Operations

**URL:** llms-txt#sync-operations

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/basic-operations/sync-operations

This example shows how to add content to your knowledge base synchronously. While async operations are recommended for better performance, sync operations can be useful in certain scenarios.

```python 13_sync.py theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector

contents_db = PostgresDb(
    db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    knowledge_table="knowledge_contents",
)

---

## Agent with Grounding

**URL:** llms-txt#agent-with-grounding

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/gemini/grounding

```python cookbook/models/google/gemini/grounding.py theme={null}
"""Grounding with Gemini.

Grounding enables Gemini to search the web and provide responses backed by
real-time information with citations. This is a legacy tool - for Gemini 2.0+
models, consider using the 'search' parameter instead.

from agno.agent import Agent
from agno.models.google import Gemini

agent = Agent(
    model=Gemini(
        id="gemini-2.0-flash",
        grounding=True,
        grounding_dynamic_threshold=0.7,  # Optional: set threshold for grounding
    ),
    add_datetime_to_context=True,
)

---

## Create an agent equipped with X toolkit

**URL:** llms-txt#create-an-agent-equipped-with-x-toolkit

agent = Agent(
    instructions=[
        "Use X tools to interact as the authorized user",
        "Generate appropriate content when asked to create posts",
        "Only post content when explicitly instructed",
        "Respect X's usage policies and rate limits",
    ],
    tools=[x_tools],
    )

---

## Filtering on Load

**URL:** llms-txt#filtering-on-load

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/filtering_on_load

```python  theme={null}
from agno.agent import Agent
from agno.db.postgres.postgres import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.lancedb import LanceDb

---

## Step 2: Query the knowledge base with Agent using filters from query automatically

**URL:** llms-txt#step-2:-query-the-knowledge-base-with-agent-using-filters-from-query-automatically

---

## Initialize Knowledge

**URL:** llms-txt#initialize-knowledge

knowledge = Knowledge(
    vector_db=vector_db,
    max_results=5,
    contents_db=PostgresDb(
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        knowledge_table="knowledge_contents",
    ),
)

knowledge.add_content(
    path=downloaded_csv_paths[0],
    metadata={
        "data_type": "sales",
        "quarter": "Q1",
        "year": 2024,
        "region": "north_america",
        "currency": "USD",
    },
)

knowledge.add_content(
    path=downloaded_csv_paths[1],
    metadata={
        "data_type": "sales",
        "year": 2024,
        "region": "europe",
        "currency": "EUR",
    },
)

knowledge.add_content(
    path=downloaded_csv_paths[2],
    metadata={
        "data_type": "survey",
        "survey_type": "customer_satisfaction",
        "year": 2024,
        "target_demographic": "mixed",
    },
)

knowledge.add_content(
    path=downloaded_csv_paths[3],
    metadata={
        "data_type": "financial",
        "sector": "technology",
        "year": 2024,
        "report_type": "quarterly_earnings",
    },
)

---

## Financial data agent

**URL:** llms-txt#financial-data-agent

finance_agent = Agent(
    name="Finance Agent",
    model=Claude(id="claude-3-5-sonnet-latest"),
    role="Get financial data",
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
    instructions=[
        "You are a finance agent that can get financial data about stocks, companies, and the economy.",
        "Always use real-time data when possible.",
    ],
)

---

## Web Search Agent

**URL:** llms-txt#web-search-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/langdb/tool_use

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Async Agent with Tool Usage

**URL:** llms-txt#async-agent-with-tool-usage

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/async/tool_use

This example demonstrates how to use an async agent with DuckDuckGo search tools to gather current information about events happening in different countries.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/async" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## With agentic memory: (10 × 500) + (7 × 5,000) = 40,000 tokens

**URL:** llms-txt#with-agentic-memory:-(10-×-500)-+-(7-×-5,000)-=-40,000-tokens

---

## Final Synthesizer Agent - Specialized in optimal synthesis

**URL:** llms-txt#final-synthesizer-agent---specialized-in-optimal-synthesis

final_synthesizer = Agent(
    name="Final Synthesizer",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Synthesize reranked results into optimal comprehensive responses",
    instructions=[
        "Synthesize information from all team members into optimal responses.",
        "Leverage the reranked and analyzed results for maximum quality.",
        "Create responses that demonstrate the benefits of advanced reranking.",
        "Ensure optimal information organization and presentation.",
        "Include confidence levels and source quality indicators.",
    ],
    markdown=True,
)

---

## Create a team for collaborative audio sentiment analysis

**URL:** llms-txt#create-a-team-for-collaborative-audio-sentiment-analysis

**Contents:**
- Usage

sentiment_team = Team(
    name="Audio Sentiment Team",
    members=[transcription_agent, sentiment_analyst],
    model=Gemini(id="gemini-2.0-flash-exp"),
    instructions=[
        "Analyze audio sentiment with conversation memory.",
        "Audio Transcriber: First transcribe audio with speaker identification.",
        "Sentiment Analyst: Analyze emotional tone and conversation dynamics.",
    ],
    add_history_to_context=True,
    markdown=True,
    db=SqliteDb(
        session_table="audio_sentiment_team_sessions",
        db_file="tmp/audio_sentiment_team.db",
    ),
)

url = "https://agno-public.s3.amazonaws.com/demo_data/sample_conversation.wav"

response = requests.get(url)
audio_content = response.content

sentiment_team.print_response(
    "Give a sentiment analysis of this audio conversation. Use speaker A, speaker B to identify speakers.",
    audio=[Audio(content=audio_content)],
    stream=True,
)

sentiment_team.print_response(
    "What else can you tell me about this audio conversation?",
    stream=True,
)
bash  theme={null}
    pip install agno requests google-generativeai
    bash  theme={null}
    export GOOGLE_API_KEY=****
    bash  theme={null}
    python cookbook/examples/teams/multimodal/audio_sentiment_analysis.py
    ```
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install required libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## LangChain Async

**URL:** llms-txt#langchain-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/langchain/async-langchain-db

```python cookbook/knowledge/vector_db/langchain/langchain_db.py theme={null}
import asyncio
import pathlib

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.langchaindb import LangChainVectorDb
from langchain.text_splitter import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings

---

## run_response_strem: Iterator[RunOutputEvent] = agent.run("What is the stock price of NVDA", stream=True)

**URL:** llms-txt#run_response_strem:-iterator[runoutputevent]-=-agent.run("what-is-the-stock-price-of-nvda",-stream=true)

---

## Load knowledge base using vector search

**URL:** llms-txt#load-knowledge-base-using-vector-search

vector_db = PgVector(table_name="recipes", db_url=db_url, search_type=SearchType.vector)
knowledge = Knowledge(
    name="Vector Search Knowledge Base",
    vector_db=vector_db,
)

knowledge.add_content(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
)

---

## Deep Knowledge

**URL:** llms-txt#deep-knowledge

**Contents:**
- Code

Source: https://docs.agno.com/examples/use-cases/agents/deep_knowledge

This agent performs iterative searches through its knowledge base, breaking down complex
queries into sub-questions, and synthesizing comprehensive answers. It's designed to explore
topics deeply and thoroughly by following chains of reasoning.

In this example, the agent uses the Agno documentation as a knowledge base

* Iteratively searches a knowledge base
* Source attribution and citations

```python cookbook/examples/agents/deep_knowledge.py theme={null}
from textwrap import dedent
from typing import List, Optional

import inquirer
import typer
from agno.agent import Agent
from agno.db.base import SessionType
from agno.db.sqlite import SqliteDb
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.vectordb.lancedb import LanceDb, SearchType
from rich import print

def initialize_knowledge_base():
    """Initialize the knowledge base with your preferred documentation or knowledge source
    Here we use Agno docs as an example, but you can replace with any relevant URLs
    """
    agent_knowledge = Knowledge(
        vector_db=LanceDb(
            uri="tmp/lancedb",
            table_name="deep_knowledge_knowledge",
            search_type=SearchType.hybrid,
            embedder=OpenAIEmbedder(id="text-embedding-3-small"),
        ),
    )
    agent_knowledge.add_content(
        url="https://docs.agno.com/llms-full.txt",
    )
    return agent_knowledge

def get_agent_db():
    """Return agent storage"""
    return SqliteDb(session_table="deep_knowledge_sessions", db_file="tmp/agents.db")

def create_agent(session_id: Optional[str] = None) -> Agent:
    """Create and return a configured DeepKnowledge agent."""
    agent_knowledge = initialize_knowledge_base()
    agent_db = get_agent_db()
    return Agent(
        name="DeepKnowledge",
        session_id=session_id,
        model=OpenAIChat(id="gpt-5-mini"),
        description=dedent("""\
        You are DeepKnowledge, an advanced reasoning agent designed to provide thorough,
        well-researched answers to any query by searching your knowledge base.

Your strengths include:
        - Breaking down complex topics into manageable components
        - Connecting information across multiple domains
        - Providing nuanced, well-researched answers
        - Maintaining intellectual honesty and citing sources
        - Explaining complex concepts in clear, accessible terms"""),
        instructions=dedent("""\
        Your mission is to leave no stone unturned in your pursuit of the correct answer.

To achieve this, follow these steps:
        1. **Analyze the input and break it down into key components**.
        2. **Search terms**: You must identify at least 3-5 key search terms to search for.
        3. **Initial Search:** Searching your knowledge base for relevant information. You must make atleast 3 searches to get all relevant information.
        4. **Evaluation:** If the answer from the knowledge base is incomplete, ambiguous, or insufficient - Ask the user for clarification. Do not make informed guesses.
        5. **Iterative Process:**
            - Continue searching your knowledge base till you have a comprehensive answer.
            - Reevaluate the completeness of your answer after each search iteration.
            - Repeat the search process until you are confident that every aspect of the question is addressed.
        4. **Reasoning Documentation:** Clearly document your reasoning process:
            - Note when additional searches were triggered.
            - Indicate which pieces of information came from the knowledge base and where it was sourced from.
            - Explain how you reconciled any conflicting or ambiguous information.
        5. **Final Synthesis:** Only finalize and present your answer once you have verified it through multiple search passes.
            Include all pertinent details and provide proper references.
        6. **Continuous Improvement:** If new, relevant information emerges even after presenting your answer,
            be prepared to update or expand upon your response.

**Communication Style:**
        - Use clear and concise language.
        - Organize your response with numbered steps, bullet points, or short paragraphs as needed.
        - Be transparent about your search process and cite your sources.
        - Ensure that your final answer is comprehensive and leaves no part of the query unaddressed.

Remember: **Do not finalize your answer until every angle of the question has been explored.**"""),
        additional_context=dedent("""\
        You should only respond with the final answer and the reasoning process.
        No need to include irrelevant information.

- User ID: {user_id}
        - Memory: You have access to your previous search results and reasoning process.
        """),
        knowledge=agent_knowledge,
        db=agent_db,
        add_history_to_context=True,
        num_history_runs=3,
        read_chat_history=True,
        markdown=True,
    )

def get_example_topics() -> List[str]:
    """Return a list of example topics for the agent."""
    return [
        "What are AI agents and how do they work in Agno?",
        "What chunking strategies does Agno support for text processing?",
        "How can I implement custom tools in Agno?",
        "How does knowledge retrieval work in Agno?",
        "What types of embeddings does Agno support?",
    ]

def handle_session_selection() -> Optional[str]:
    """Handle session selection and return the selected session ID."""
    agent_db = get_agent_db()

new = typer.confirm("Do you want to start a new session?", default=True)
    if new:
        return None

existing_sessions: List[str] = agent_db.get_sessions(session_type=SessionType.AGENT)
    if not existing_sessions:
        print("No existing sessions found. Starting a new session.")
        return None

print("\nExisting sessions:")
    for i, session in enumerate(existing_sessions, 1):
        print(f"{i}. {session}")

session_idx = typer.prompt(
        "Choose a session number to continue (or press Enter for most recent)",
        default=1,
    )

try:
        return existing_sessions[int(session_idx) - 1]
    except (ValueError, IndexError):
        return existing_sessions[0]

def run_interactive_loop(agent: Agent):
    """Run the interactive question-answering loop."""
    example_topics = get_example_topics()

while True:
        choices = [f"{i + 1}. {topic}" for i, topic in enumerate(example_topics)]
        choices.extend(["Enter custom question...", "Exit"])

questions = [
            inquirer.List(
                "topic",
                message="Select a topic or ask a different question:",
                choices=choices,
            )
        ]
        answer = inquirer.prompt(questions)

if answer["topic"] == "Exit":
            break

if answer["topic"] == "Enter custom question...":
            questions = [inquirer.Text("custom", message="Enter your question:")]
            custom_answer = inquirer.prompt(questions)
            topic = custom_answer["custom"]
        else:
            topic = example_topics[int(answer["topic"].split(".")[0]) - 1]

agent.print_response(topic, stream=True)

def deep_knowledge_agent():
    """Main function to run the DeepKnowledge agent."""

session_id = handle_session_selection()
    agent = create_agent(session_id)

print("\n🤔 Welcome to DeepKnowledge - Your Advanced Research Assistant! 📚")
    if session_id is None:
        session_id = agent.session_id
        if session_id is not None:
            print(f"[bold green]Started New Session: {session_id}[/bold green]\n")
        else:
            print("[bold green]Started New Session[/bold green]\n")
    else:
        print(f"[bold blue]Continuing Previous Session: {session_id}[/bold blue]\n")

run_interactive_loop(agent)

if __name__ == "__main__":
    typer.run(deep_knowledge_agent)

---

## Create Knowledge with both databases

**URL:** llms-txt#create-knowledge-with-both-databases

**Contents:**
  - Alternative Database Examples

knowledge = Knowledge(
    name="My Knowledge Base",
    vector_db=vector_db,
    contents_db=contents_db  # This enables content tracking!
)
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
### Alternative Database Examples
```

---

## Agent with User Memory

**URL:** llms-txt#agent-with-user-memory

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/integrations/discord/agent_with_user_memory

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API keys">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Memory Manager

**URL:** llms-txt#memory-manager

Source: https://docs.agno.com/reference/memory/memory

Memory is a class that manages conversation history, session summaries, and long-term user memories for AI agents. It provides comprehensive memory management capabilities including adding new memories, searching memories, and deleting memories.

<Snippet file="memory-manager-reference.mdx" />

---

## Retrieve the memories about the user

**URL:** llms-txt#retrieve-the-memories-about-the-user

**Contents:**
- Memory Data Model
- Developer Resources

memories = agent.get_user_memories(user_id="123")
print(memories)
```

Each memory stored in your database contains the following fields:

| Field        | Type   | Description                                     |
| ------------ | ------ | ----------------------------------------------- |
| `memory_id`  | `str`  | The unique identifier for the memory.           |
| `memory`     | `str`  | The memory content, stored as a string.         |
| `topics`     | `list` | The topics of the memory.                       |
| `input`      | `str`  | The input that generated the memory.            |
| `user_id`    | `str`  | The user ID of the memory.                      |
| `agent_id`   | `str`  | The agent ID of the memory.                     |
| `team_id`    | `str`  | The team ID of the memory.                      |
| `updated_at` | `int`  | The timestamp when the memory was last updated. |

<Tip>
  View and manage all your memories visually through the [Memories page in AgentOS](https://os.agno.com/memory)/
</Tip>

## Developer Resources

* View [Examples](/examples/concepts/memory)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/memory/)

---

## Image to Text Agent

**URL:** llms-txt#image-to-text-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/multimodal/image-to-text

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Create an agent that can research and send personalized email updates

**URL:** llms-txt#create-an-agent-that-can-research-and-send-personalized-email-updates

**Contents:**
- Usage

agent = Agent(
    name="Research Newsletter Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    description="""You are an AI research specialist who creates and sends
    personalized email newsletters about the latest developments in artificial
    intelligence and technology.""",
    instructions=[
        """When given a prompt:,
        1. Extract the recipient's email address carefully. Look for the
        complete email in format 'user@domain.com'.,
        2. Research the latest AI developments using DuckDuckGo,
        3. Compose a concise, engaging email with:
           - A compelling subject line,
           - 3-4 key developments or news items,
           - Brief explanations of why they matter,
           - Links to sources,
        4. Format the content in a clean, readable way,
        5. Send the email using AWS SES. IMPORTANT: The receiver_email parameter
        must be the COMPLETE email address including the @ symbol and domain.""",
    ],
    tools=[
        AWSSESTool(
            sender_email=sender_email,
            sender_name=sender_name,
            region_name=region_name
        ),
        DuckDuckGoTools(),
    ],
    markdown=True,
    )

agent.print_response(
    "Research AI developments in healthcare from the past week with a focus on practical applications in clinical settings. Send the summary via email to johndoe@example.com"
)
```

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set up AWS SES">
    ### Verify your email/domain: **For testing:** 1. Go to \[AWS SES

Console]\([https://console.aws.amazon.com/ses/home](https://console.aws.amazon.com/ses/home)) > Verified Identities >
    Create Identity 2. Choose "Email Address" verification 3. Click verification
    link sent to your email **For production:** 1. Choose "Domain" and follow DNS
    verification steps 2. Add DKIM and SPF records to your domain's DNS **Note:**
    In sandbox mode, both sender and recipient emails must be verified.
  </Step>

<Step title="Configure AWS credentials">
    ### Create IAM user: 1. Go to IAM Console > Users > Add User 2. Enable

"Programmatic access" 3. Attach 'AmazonSESFullAccess' policy ### Set
    credentials (choose one method): **Method 1 - Using AWS CLI:** `bash aws
      configure ` **Method 2 - Environment variables:** `bash export
      AWS_ACCESS_KEY_ID=xxx export AWS_SECRET_ACCESS_KEY=xxx export
      AWS_DEFAULT_REGION=us-east-1 export OPENAI_API_KEY=xxx `
  </Step>

<Step title="Install libraries">
    `bash pip install -U boto3 openai ddgs agno `
  </Step>

<Step title="Run Agent">
    `bash python cookbook/tools/aws_ses_tools.py `
  </Step>

<Step title="Troubleshooting">
    If emails aren't sending, check:

* Both sender and recipient are verified (in sandbox mode)
    * AWS credentials are correctly configured
    * You're within sending limits
    * Your IAM user has correct SES permissions
    * Use SES Console's 'Send Test Email' feature to verify setup
  </Step>
</Steps>

---

## Custom Retriever

**URL:** llms-txt#custom-retriever

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/custom_retriever/custom-retriever

```python retriever.py theme={null}
from typing import Optional

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.qdrant import Qdrant
from qdrant_client import QdrantClient

---

## OR

**URL:** llms-txt#or

**Contents:**
  - Memory Growth Monitoring

agent = Agent(db=db, enable_agentic_memory=True)  # Agentic
python  theme={null}
from agno.agent import Agent

agent = Agent(db=db, enable_user_memories=True)

**Examples:**

Example 1 (unknown):
```unknown
### Memory Growth Monitoring

Track memory counts to catch issues early:
```

---

## Option 1: Filters on the Agent

**URL:** llms-txt#option-1:-filters-on-the-agent

---

## Async Agent with Structured Output

**URL:** llms-txt#async-agent-with-structured-output

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/async/structured_output

This example demonstrates how to use async agents with structured output schemas, comparing structured output mode versus JSON mode for generating movie scripts with defined data models.

```python structured_output.py theme={null}
import asyncio
from typing import List

from agno.agent import Agent, RunOutput  # noqa
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from rich.pretty import pprint  # noqa

class MovieScript(BaseModel):
    setting: str = Field(
        ..., description="Provide a nice setting for a blockbuster movie."
    )
    ending: str = Field(
        ...,
        description="Ending of the movie. If not available, provide a happy ending.",
    )
    genre: str = Field(
        ...,
        description="Genre of the movie. If not available, select action, thriller or romantic comedy.",
    )
    name: str = Field(..., description="Give a name to this movie")
    characters: List[str] = Field(..., description="Name of characters for this movie.")
    storyline: str = Field(
        ..., description="3 sentence storyline for the movie. Make it exciting!"
    )

---

## Traditional RAG approach

**URL:** llms-txt#traditional-rag-approach

**Contents:**
- Ready to Build?

agent = Agent(
    knowledge=knowledge,
    add_knowledge_to_context=True  # Always includes knowledge
)
```

Now that you understand how Knowledge works in Agno, here's where to go next:

<CardGroup cols={2}>
  <Card title="Getting Started Guide" icon="rocket" href="/concepts/knowledge/getting-started">
    Follow our step-by-step tutorial to create your first knowledge base in minutes
  </Card>

<Card title="Performance Quick Wins" icon="gauge" href="/concepts/knowledge/advanced/performance-tips">
    Optimize search quality, speed, and resource usage for production
  </Card>
</CardGroup>

---

## Slack Reasoning Finance Agent

**URL:** llms-txt#slack-reasoning-finance-agent

**Contents:**
- Code
- Usage
- Key Features

Source: https://docs.agno.com/examples/agent-os/interfaces/slack/reasoning_agent

Slack agent with advanced reasoning and financial analysis capabilities

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set Environment Variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

* **Advanced Reasoning**: ThinkingTools for step-by-step financial analysis
* **Real-time Data**: Stock prices, analyst recommendations, company news
* **Claude Powered**: Superior analytical and reasoning capabilities
* **Slack Integration**: Works in channels and direct messages
* **Structured Output**: Well-formatted tables and financial insights

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Simple function to run an agent which performance we will evaluate

**URL:** llms-txt#simple-function-to-run-an-agent-which-performance-we-will-evaluate

def run_agent():
    agent = Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        system_message="Be concise, reply with one sentence.",
    )
    response = agent.run("What is the capital of France?")
    print(response.content)
    return response

---

## Create your agent

**URL:** llms-txt#create-your-agent

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    knowledge=knowledge,
    search_knowledge=True,
    instructions=["Always search knowledge before answering"]
)

---

## Agents

**URL:** llms-txt#agents

**Contents:**
- Guides
- Developer Resources

Source: https://docs.agno.com/concepts/agents/overview

Learn about Agno Agents and how they work.

**Agents are AI programs where a language model controls the flow of execution.**

The core of an Agent is a model using tools in a loop, guided by instructions:

* **Model:** controls the flow of execution. It decides whether to reason, act or respond.
* **Instructions:** program the Agent, teaching it how to use tools and respond.
* **Tools:** enable an Agent to take actions and interact with external systems.

Agents also have memory, knowledge, storage and the ability to reason:

* **Memory:** gives Agents the ability to store and recall information from previous interactions, allowing them to learn and improve their responses.
* **Storage:** is used by Agents to save session history and state in a database. Model APIs are stateless and storage makes Agents stateful, enabling multi-turn conversations.
* **Knowledge:** is domain-specific information the Agent can **search at runtime** to provide better responses (RAG). Knowledge is stored in a vector database and this search at runtime pattern is known as **Agentic RAG** or **Agentic Search**.
* **Reasoning:** enables Agents to "think" before responding and "analyze" the results of their actions before responding, this improves reliability and quality of responses.

<Tip>
  If this is your first time using Agno, [start here](/introduction/quickstart) before diving into advanced concepts.
</Tip>

Learn how to build, run and manage your Agents using the following guides.

<CardGroup cols={3}>
  <Card title="Building Agents" icon="wrench" iconType="duotone" href="/concepts/agents/building-agents">
    Learn how to run your agents.
  </Card>

<Card title="Running Agents" icon="user-robot" iconType="duotone" href="/concepts/agents/running-agents">
    Learn how to run your agents.
  </Card>

<Card title="Debugging Agents" icon="bug" iconType="duotone" href="/concepts/agents/debugging-agents">
    Learn how to debug and troubleshoot your agents.
  </Card>

<Card title="Agent Sessions" icon="comments" iconType="duotone" href="/concepts/agents/sessions">
    Learn about agent sessions.
  </Card>

<Card title="Input & Output" icon="fire" iconType="duotone" href="/concepts/agents/input-output">
    Learn about input and output for agents.
  </Card>

<Card title="Context Engineering" icon="file-lines" iconType="duotone" href="/concepts/agents/context">
    Learn about context engineering.
  </Card>

<Card title="Dependencies" icon="brackets-curly" iconType="duotone" href="/concepts/agents/dependencies">
    Learn about dependency injection in your agent's context.
  </Card>

<Card title="Agent State" icon="crystal-ball" iconType="duotone" href="/concepts/agents/state">
    Learn about managing agent state.
  </Card>

<Card title="Agent Storage" icon="database" iconType="duotone" href="/concepts/agents/storage">
    Learn about session storage.
  </Card>

<Card title="Memory" icon="head-side-brain" iconType="duotone" href="/concepts/agents/memory">
    Learn about adding memory to your agents.
  </Card>

<Card title="Knowledge" icon="books" iconType="duotone" href="/concepts/agents/knowledge">
    Learn about knowledge in agents.
  </Card>

<Card title="Tools" icon="wrench" iconType="duotone" href="/concepts/agents/tools">
    Learn about adding tools to your agents.
  </Card>

<Card title="Agent Metrics" icon="chart-line" iconType="duotone" href="/concepts/agents/metrics">
    Learn how to track agent metrics.
  </Card>

<Card title="Pre-hooks & Post-hooks" icon="link" iconType="duotone" href="/concepts/agents/pre-hooks-and-post-hooks">
    Learn about pre-hooks and post-hooks for agents.
  </Card>

<Card title="Guardrails" icon="shield-check" iconType="duotone" href="/concepts/agents/guardrails/overview">
    Learn about implementing guardrails for your agents.
  </Card>
</CardGroup>

## Developer Resources

* View the [Agent schema](/reference/agents/agent)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/agents/README.md)

---

## Meeting Summarizer Agent

**URL:** llms-txt#meeting-summarizer-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/use-cases/agents/meeting_summarizer_agent

This agent uses OpenAITools (transcribe\_audio, generate\_image, generate\_speech)
to process a meeting recording, summarize it, visualize it, and create an audio summary.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Zep Memory Tools

**URL:** llms-txt#zep-memory-tools

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/tools/database/zep

```python cookbook/tools/zep_tools.py theme={null}
import time
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.zep import ZepTools

---

## Create an agent with the knowledge instance

**URL:** llms-txt#create-an-agent-with-the-knowledge-instance

**Contents:**
- Usage

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    debug_mode=True,
)

if __name__ == "__main__":
    asyncio.run(
        agent.aprint_response(
            "Explain what this text means: low end eats the high end", markdown=True
        )
    )
bash  theme={null}
    pip install -U llama-index-core llama-index-readers-file llama-index-embeddings-openai pypdf openai agno
    bash Mac theme={null}
      python cookbook/knowledge/vector_db/llamaindex_db/llamaindex_db.py
      bash Windows theme={null}
      python cookbook/knowledge/vector_db/llamaindex_db/llamaindex_db.py
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

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## When initializing the knowledge base, we can attach metadata that will be used for filtering

**URL:** llms-txt#when-initializing-the-knowledge-base,-we-can-attach-metadata-that-will-be-used-for-filtering

---

## Agent with Knowledge Base

**URL:** llms-txt#agent-with-knowledge-base

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/cerebras/knowledge

```python cookbook/models/cerebras/basic_knowledge.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.cerebras import Cerebras
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    vector_db=PgVector(table_name="recipes", db_url=db_url),
)

---

## PDF Input Bytes Agent

**URL:** llms-txt#pdf-input-bytes-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/vertexai/claude/pdf_input_bytes

```python cookbook/models/vertexai/claude/pdf_input_bytes.py theme={null}
from pathlib import Path

from agno.agent import Agent
from agno.media import File
from agno.models.vertexai.claude import Claude
from agno.utils.media import download_file

pdf_path = Path(__file__).parent.joinpath("ThaiRecipes.pdf")

---

## Initialize knowledge base with vector database

**URL:** llms-txt#initialize-knowledge-base-with-vector-database

agno_docs_knowledge = Knowledge(
    vector_db=LanceDb(
        uri=str(tmp_dir.joinpath("lancedb")),
        table_name="agno_docs",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

---

## ChromaDB

**URL:** llms-txt#chromadb

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/chroma-db/chroma-db

```python cookbook/knowledge/vector_db/chroma_db/chroma_db.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb

---

## Agent Run Metadata

**URL:** llms-txt#agent-run-metadata

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/other/agent_run_metadata

This example demonstrates how to attach custom metadata to agent runs. This is useful for tracking business context, request types, and operational information for monitoring and analytics.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/other" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Print the response in the terminal

**URL:** llms-txt#print-the-response-in-the-terminal

**Contents:**
- Quick fix: Configure a Different Embedder

agent.print_response("Share a 2 sentence horror story.")
python  theme={null}
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
from agno.knowledge.embedder.google import GeminiEmbedder

**Examples:**

Example 1 (unknown):
```unknown
For more details on configuring different model providers, check our [models documentation](/concepts/models)

## Quick fix: Configure a Different Embedder

The same applies to embeddings. If you want to use a different embedder instead of `OpenAIEmbedder`, configure it explicitly.

For example, to use Google's Gemini as an embedder, use `GeminiEmbedder`:
```

---

## Agent with Output Model

**URL:** llms-txt#agent-with-output-model

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/output_model

This example demonstrates how to use the output\_model parameter to specify a different model for generating the final response, enabling model switching during agent execution.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/input_and_output" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## json_mode_response: RunOutput = json_mode_agent.arun("New York")

**URL:** llms-txt#json_mode_response:-runoutput-=-json_mode_agent.arun("new-york")

---

## movie_agent: RunOutput = movie_agent.run("New York")

**URL:** llms-txt#movie_agent:-runoutput-=-movie_agent.run("new-york")

---

## Traditional RAG with PgVector

**URL:** llms-txt#traditional-rag-with-pgvector

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/knowledge/rag/traditional-rag-pgvector

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Snippet file="run-pgvector-step.mdx" />

<Step title="Run Agent">
    <CodeGroup>

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

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Filtering on SurrealDB

**URL:** llms-txt#filtering-on-surrealdb

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/vector-dbs/filtering_surreal_db

Learn how to filter knowledge base searches using Pdf documents with user-specific metadata in SurrealDB.

```python  theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.surrealdb import SurrealDb
from surrealdb import Surreal

---

## Setting up an example Agent

**URL:** llms-txt#setting-up-an-example-agent

---

## response: RunOutput = agent.run("New York")

**URL:** llms-txt#response:-runoutput-=-agent.run("new-york")

---

## Example agent implementation

**URL:** llms-txt#example-agent-implementation

**Contents:**
- Usage

from agno.agent import Agent  # noqa: E402
from agno.models.openai import OpenAIChat  # noqa: E402

class VegetarianRecipeAgent:
    def __init__(self):
        self.history = []

@scenario_cache()
    def run(self, message: str):
        self.history.append({"role": "user", "content": message})

agent = Agent(
            model=OpenAIChat(id="gpt-5-mini"),
            markdown=True,
            instructions="You are a vegetarian recipe agent",
        )

response = agent.run(message)
        result = response.content
        print(result)
        self.history.append(result)

return {"message": result}
bash  theme={null}
    pip install -U agno openai scenario pytest
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch scenario_testing.py
    bash Mac theme={null}
      pytest scenario_testing.py -v
      bash Windows   theme={null}
      pytest scenario_testing.py -v
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/other" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## memory_manager=memory_manager,

**URL:** llms-txt#memory_manager=memory_manager,

---

## Load knowledge base using keyword search

**URL:** llms-txt#load-knowledge-base-using-keyword-search

keyword_db = PgVector(
    table_name="recipes", db_url=db_url, search_type=SearchType.keyword
)
knowledge = Knowledge(
    name="Keyword Search Knowledge Base",
    vector_db=keyword_db,
)

knowledge.add_content(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
)

---

## WhatsApp Image Generation Agent (Tool-based)

**URL:** llms-txt#whatsapp-image-generation-agent-(tool-based)

**Contents:**
- Code
- Usage
- Key Features

Source: https://docs.agno.com/examples/agent-os/interfaces/whatsapp/image_generation_tools

WhatsApp agent that generates images using OpenAI's image generation tools

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set Environment Variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

* **Tool-based Generation**: OpenAI's GPT Image-1 model via external tools
* **High-Quality Images**: Professional-grade image generation
* **Conversational Interface**: Natural language interaction for image requests
* **History Context**: Remembers previous images and conversations
* **GPT-4o Orchestration**: Intelligent conversation and tool management

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Agentic Filtering

**URL:** llms-txt#agentic-filtering

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/agentic-filtering

```python cookbook/knowledge/filters/agentic_filtering.py theme={null}
import asyncio
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.lancedb import LanceDb

---

## Create team with agentic knowledge filters enabled

**URL:** llms-txt#create-team-with-agentic-knowledge-filters-enabled

team_with_knowledge = Team(
    name="Team with Knowledge",
    members=[
        web_agent
    ],  # If you omit the member, the leader will search the knowledge base itself.
    model=OpenAIChat(id="gpt-5-mini"),
    knowledge=knowledge,
    show_members_responses=True,
    markdown=True,
    enable_agentic_knowledge_filters=True,  # Allow AI to determine filters
)

---

## Create an Agent with the ElevenLabs tool

**URL:** llms-txt#create-an-agent-with-the-elevenlabs-tool

**Contents:**
- Toolkit Params
- Toolkit Functions
- Developer Resources

agent = Agent(tools=[
    ElevenLabsTools(
        voice_id="JBFqnCBsd6RMkjVDRZzb", model_id="eleven_multilingual_v2", target_directory="audio_generations"
    )
], name="ElevenLabs Agent")

agent.print_response("Generate a audio summary of the big bang theory", markdown=True)
```

| Parameter                      | Type            | Default                  | Description                                                                                                                                                                    |
| ------------------------------ | --------------- | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `api_key`                      | `str`           | `None`                   | The Eleven Labs API key for authentication                                                                                                                                     |
| `voice_id`                     | `str`           | `JBFqnCBsd6RMkjVDRZzb`   | The voice ID to use for the audio generation                                                                                                                                   |
| `target_directory`             | `Optional[str]` | `None`                   | The directory to save the audio file                                                                                                                                           |
| `model_id`                     | `str`           | `eleven_multilingual_v2` | The model's id to use for the audio generation                                                                                                                                 |
| `output_format`                | `str`           | `mp3_44100_64`           | The output format to use for the audio generation (check out [the docs](https://elevenlabs.io/docs/api-reference/text-to-speech#parameter-output-format) for more information) |
| `enable_text_to_speech`        | `bool`          | `True`                   | Enable the text\_to\_speech functionality.                                                                                                                                     |
| `enable_generate_sound_effect` | `bool`          | `True`                   | Enable the generate\_sound\_effect functionality.                                                                                                                              |
| `enable_get_voices`            | `bool`          | `True`                   | Enable the get\_voices functionality.                                                                                                                                          |
| `all`                          | `bool`          | `False`                  | Enable all functionality.                                                                                                                                                      |

| Function                | Description                                     |
| ----------------------- | ----------------------------------------------- |
| `text_to_speech`        | Convert text to speech                          |
| `generate_sound_effect` | Generate sound effect audio from a text prompt. |
| `get_voices`            | Get the list of voices available                |

## Developer Resources

* View [Tools](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/eleven_labs.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/elevenlabs_tools.py)

---

## Audio Streaming Agent

**URL:** llms-txt#audio-streaming-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/multimodal/audio-streaming

```python  theme={null}
import base64
import wave
from typing import Iterator

from agno.agent import Agent, RunOutputEvent
from agno.models.openai import OpenAIChat

---

## Agent with Tools and Streaming

**URL:** llms-txt#agent-with-tools-and-streaming

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/portkey/tool_use_stream

```python cookbook/models/portkey/tool_use_stream.py theme={null}
from agno.agent import Agent
from agno.models.portkey import Portkey
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=Portkey(id="@first-integrati-707071/gpt-5-nano"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

---

## Writer agent that can write content

**URL:** llms-txt#writer-agent-that-can-write-content

medical_agent = Agent(
    name="Medical Agent",
    role="Write content",
    model=Claude(id="claude-3-5-sonnet-latest"),
    description="You are an AI agent that can write content.",
    tools=[PubmedTools()],
    instructions=[
        "You are a medical agent that can answer questions about medical topics.",
    ],
)

---

## Agent Input as Dictionary

**URL:** llms-txt#agent-input-as-dictionary

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/input_as_dict

This example demonstrates how to provide input to an agent as a dictionary format, specifically for multimodal inputs like text and images.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/input_and_output" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Firecrawl Reader (Async)

**URL:** llms-txt#firecrawl-reader-(async)

**Contents:**
- Code
- Usage
- Params

Source: https://docs.agno.com/examples/concepts/knowledge/readers/firecrawl/firecrawl-reader-async

The **Firecrawl Reader** with asynchronous processing uses the Firecrawl API to scrape and crawl web content efficiently, converting it into documents for your knowledge base.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Set API Key">
    
  </Step>

<Snippet file="run-pgvector-step.mdx" />

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

<Snippet file="firecrawl-reader-reference.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set API Key">
```

Example 3 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Enable agentic filtering

**URL:** llms-txt#enable-agentic-filtering

**Contents:**
- Usage

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    enable_agentic_knowledge_filters=True,
)

agent.print_response(
    "Tell me about revenue performance and top selling products in the region north_america and data_type sales",
    markdown=True,
)

bash  theme={null}
    pip install -U agno lancedb openai
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Mac theme={null}
      python cookbook/knowledge/filters/agentic_filtering.py
      bash Windows theme={null}
      python cookbook/knowledge/filters/agentic_filtering.py
      ```
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run the example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Initialize knowledge base

**URL:** llms-txt#initialize-knowledge-base

**Contents:**
- Usage

knowledge = Knowledge()
knowledge.load_documents("./docs/")

agent = Agent(
    instructions=[
        "You are a knowledge assistant that helps find and analyze information",
        "Search through the knowledge base to answer questions",
        "Provide detailed analysis and reasoning about the information found",
    ],
    tools=[KnowledgeTools(knowledge=knowledge)],
    markdown=True,
)

agent.print_response("What are the best practices for API design?")
bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    pip install -U openai agno
    bash Mac theme={null}
      python cookbook/tools/knowledge_tools.py
      bash Windows theme={null}
      python cookbook/tools/knowledge_tools.py
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

## Create a Tech News Reporter Agent with a Silicon Valley personality

**URL:** llms-txt#create-a-tech-news-reporter-agent-with-a-silicon-valley-personality

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=dedent("""\
        You are a tech-savvy Hacker News reporter with a passion for all things technology! 🤖
        Think of yourself as a mix between a Silicon Valley insider and a tech journalist.

Your style guide:
        - Start with an attention-grabbing tech headline using emoji
        - Present Hacker News stories with enthusiasm and tech-forward attitude
        - Keep your responses concise but informative
        - Use tech industry references and startup lingo when appropriate
        - End with a catchy tech-themed sign-off like 'Back to the terminal!' or 'Pushing to production!'

Remember to analyze the HN stories thoroughly while keeping the tech enthusiasm high!\
    """),
    tools=[get_top_hackernews_stories],
    markdown=True,
)

---

## Create test JSON data

**URL:** llms-txt#create-test-json-data

**Contents:**
- Usage
- Params

json_path = Path("tmp/test.json")
json_path.parent.mkdir(exist_ok=True)
test_data = {
    "users": [
        {"id": 1, "name": "John Doe", "role": "Developer"},
        {"id": 2, "name": "Jane Smith", "role": "Designer"}
    ],
    "project": "Knowledge Base System"
}
json_path.write_text(json.dumps(test_data, indent=2))

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="json_documents",
        db_url=db_url,
    ),
)

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
)

async def main():
    # Add JSON content to knowledge base
    await knowledge.add_content_async(
        path=json_path,
        reader=JSONReader(),
    )

# Query the knowledge base
    await agent.aprint_response(
        "What information is available about the users?",
        markdown=True
    )

if __name__ == "__main__":
    asyncio.run(main())
bash  theme={null}
    pip install -U sqlalchemy psycopg pgvector agno openai
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Mac theme={null}
      python examples/concepts/knowledge/readers/json_reader_async.py
      bash Windows theme={null}
      python examples/concepts/knowledge/readers/json_reader_async.py
      ```
    </CodeGroup>
  </Step>
</Steps>

<Snippet file="json-reader-reference.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Flash Thinking Agent

**URL:** llms-txt#flash-thinking-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/gemini/flash_thinking

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## WhatsApp Reasoning Finance Agent

**URL:** llms-txt#whatsapp-reasoning-finance-agent

**Contents:**
- Code
- Usage
- Key Features

Source: https://docs.agno.com/examples/agent-os/interfaces/whatsapp/reasoning_agent

WhatsApp agent with advanced reasoning and financial analysis capabilities

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set Environment Variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

* **Advanced Reasoning**: ThinkingTools for step-by-step financial analysis
* **Real-time Data**: Stock prices, analyst recommendations, company news
* **Claude Powered**: Superior analytical and reasoning capabilities
* **Structured Output**: Well-formatted tables and financial insights
* **Market Intelligence**: Comprehensive company analysis and recommendations

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Upstash

**URL:** llms-txt#upstash

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/upstash-db/upstash-db

```python cookbook/knowledge/vector_db/upstash_db/upstash_db.py theme={null}
import os

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.upstashdb import UpstashVectorDb

---

## Interact with the Agent so that it can learn about the user

**URL:** llms-txt#interact-with-the-agent-so-that-it-can-learn-about-the-user

agent.print_response("My name is John Billings")
agent.print_response("I live in NYC")
agent.print_response("I'm going to a concert tomorrow")

---

## AgentOS manages MCP lifespan

**URL:** llms-txt#agentos-manages-mcp-lifespan

agent_os = AgentOS(
    description="AgentOS with MCP Tools",
    agents=[agent],
)

app = agent_os.get_app()

if __name__ == "__main__":
    # Don't use reload=True with MCP tools to avoid lifespan issues
    agent_os.serve(app="mcp_tools_example:app")
```

<Note>
  If you are using `MCPTools` within AgentOS, you should not use `reload=True` when serving your AgentOS.
  This can break the MCP connection during the FastAPI lifecycle.
</Note>

See here for a [full example](/examples/agent-os/mcp/mcp_tools_example).

---

## asyncio.run(agent.aprint_response("Fetch the top 2 hackernews stories"))

**URL:** llms-txt#asyncio.run(agent.aprint_response("fetch-the-top-2-hackernews-stories"))

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai httpx rich
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch confirmation_required_async.py
    bash Mac theme={null}
      python confirmation_required_async.py
      bash Windows theme={null}
      python confirmation_required_async.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Vector-focused knowledge base for similarity search

**URL:** llms-txt#vector-focused-knowledge-base-for-similarity-search

vector_knowledge = Knowledge(
    vector_db=PgVector(
        table_name="recipes_vector",
        db_url=db_url,
        search_type=SearchType.vector,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

---

## Context Expander Agent - Specialized in expanding context

**URL:** llms-txt#context-expander-agent---specialized-in-expanding-context

context_expander = Agent(
    name="Context Expander",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Expand context by finding related and supplementary information",
    knowledge=context_knowledge,
    search_knowledge=True,
    instructions=[
        "Find related information that complements the primary retrieval.",
        "Look for background context, related topics, and supplementary details.",
        "Search for information that helps understand the broader context.",
        "Identify connections between different pieces of information.",
    ],
    markdown=True,
)

---

## Audio Output Agent

**URL:** llms-txt#audio-output-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/openai/chat/audio_output_agent

```python cookbook/models/openai/chat/audio_output_agent.py theme={null}
from agno.agent import Agent, RunOutput  # noqa
from agno.models.openai import OpenAIChat
from agno.utils.audio import write_audio_to_file
from agno.db.in_memory import InMemoryDb

---

## Define the path to the document to be loaded into the knowledge base

**URL:** llms-txt#define-the-path-to-the-document-to-be-loaded-into-the-knowledge-base

state_of_the_union = pathlib.Path(
    "cookbook/knowledge/testing_resources/state_of_the_union.txt"
)

---

## Create a knowledge base with the ArXiv documents

**URL:** llms-txt#create-a-knowledge-base-with-the-arxiv-documents

knowledge = Knowledge(
    # Table name: ai.arxiv_documents
    vector_db=PgVector(
        table_name="arxiv_documents",
        db_url=db_url,
    ),
)

---

## Get Agent Details

**URL:** llms-txt#get-agent-details

Source: https://docs.agno.com/reference-api/schema/agents/get-agent-details

get /agents/{agent_id}
Retrieve detailed configuration and capabilities of a specific agent.

**Returns comprehensive agent information including:**
- Model configuration and provider details
- Complete tool inventory and configurations
- Session management settings
- Knowledge base and memory configurations
- Reasoning capabilities and settings
- System prompts and response formatting options

---

## Create team with both agents

**URL:** llms-txt#create-team-with-both-agents

**Contents:**
- Usage

news_analysis_team = Team(
    name="News Analysis Team",
    id=str(uuid4()),
    user_id=str(uuid4()),
    model=OpenAIChat(id="gpt-5-mini"),
    members=[
        article_agent,
        news_research_agent,
    ],
    instructions=[
        "Coordinate between article summarization and news research.",
        "First summarize any provided articles, then find related news.",
        "Combine information to provide comprehensive analysis.",
    ],
    show_members_responses=True,
    markdown=True,
)

if __name__ == "__main__":
    news_analysis_team.print_response(
        "Please summarize https://www.rockymountaineer.com/blog/experience-icefields-parkway-scenic-drive-lifetime and find related news about scenic train routes in Canada.",
        stream=True,
    )
bash  theme={null}
    export LANGFUSE_PUBLIC_KEY=<your-key>
    export LANGFUSE_SECRET_KEY=<your-key>
    bash  theme={null}
    pip install -U agno openai ddgs newspaper4k langfuse opentelemetry-sdk opentelemetry-exporter-otlp openinference-instrumentation-agno
    bash Mac theme={null}
      python cookbook/integrations/observability/langfuse_via_openinference_team.py
      bash Windows theme={null}
      python cookbook/integrations/observability/langfuse_via_openinference_team.py
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
    Either self-host or sign up for an account at [https://us.cloud.langfuse.com](https://us.cloud.langfuse.com)
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

## Wikipedia Reader (Async)

**URL:** llms-txt#wikipedia-reader-(async)

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/wikipedia/wikipedia-reader-async

The **Wikipedia Reader** with asynchronous processing allows you to search and read Wikipedia articles efficiently, converting them into vector embeddings for your knowledge base.

```python examples/concepts/knowledge/readers/wikipedia_reader_async.py theme={null}
import asyncio

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.arxiv_reader import ArxivReader
from agno.knowledge.reader.wikipedia_reader import WikipediaReader
from agno.vectordb.pgvector import PgVector

---

## Asynchronous Streaming Agent

**URL:** llms-txt#asynchronous-streaming-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/meta/async_stream

```python cookbook/models/meta/llama/async_basic_stream.py theme={null}
import asyncio
from typing import Iterator  # noqa

from agno.agent import Agent, RunOutput  # noqa
from agno.models.meta import Llama

agent = Agent(model=Llama(id="Llama-4-Maverick-17B-128E-Instruct-FP8"), markdown=True)

---

## Create OpenAI agent

**URL:** llms-txt#create-openai-agent

openai_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant.",
    db=db,
    add_history_to_context=True,
)

---

## LlamaIndex Async

**URL:** llms-txt#llamaindex-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/llamaindex-db/async-llamaindex-db

```python cookbook/knowledge/vector_db/llamaindex_db/llamaindex_db.py theme={null}
import asyncio
from pathlib import Path
from shutil import rmtree

import httpx
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.llamaindex import LlamaIndexVectorDb
from llama_index.core import (
    SimpleDirectoryReader,
    StorageContext,
    VectorStoreIndex,
)
from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.retrievers import VectorIndexRetriever

data_dir = Path(__file__).parent.parent.parent.joinpath("wip", "data", "paul_graham")
if data_dir.is_dir():
    rmtree(path=data_dir, ignore_errors=True)
data_dir.mkdir(parents=True, exist_ok=True)

url = "https://raw.githubusercontent.com/run-llama/llama_index/main/docs/docs/examples/data/paul_graham/paul_graham_essay.txt"
file_path = data_dir.joinpath("paul_graham_essay.txt")
response = httpx.get(url)
if response.status_code == 200:
    with open(file_path, "wb") as file:
        file.write(response.content)
    print(f"File downloaded and saved as {file_path}")
else:
    print("Failed to download the file")

documents = SimpleDirectoryReader(str(data_dir)).load_data()

splitter = SentenceSplitter(chunk_size=1024)

nodes = splitter.get_nodes_from_documents(documents)

storage_context = StorageContext.from_defaults()

index = VectorStoreIndex(nodes=nodes, storage_context=storage_context)

knowledge_retriever = VectorIndexRetriever(index)

knowledge = Knowledge(
    vector_db=LlamaIndexVectorDb(knowledge_retriever=knowledge_retriever)
)

---

## Setup AgentOS with MCP enabled

**URL:** llms-txt#setup-agentos-with-mcp-enabled

agent_os = AgentOS(
    description="Example app with MCP enabled",
    agents=[web_research_agent],
    enable_mcp_server=True,  # This enables a LLM-friendly MCP server at /mcp
)

app = agent_os.get_app()

if __name__ == "__main__":
    # Your MCP server will be available at http://localhost:7777/mcp
    agent_os.serve(app="enable_mcp_example:app", reload=True)
```

Once enabled, your AgentOS will expose an MCP server at the `/mcp` endpoint that provides:

* Access to your AgentOS configuration
* Information about available agents, teams, and workflows
* The ability to run agents, teams, and workflows
* The ability to create and delete sessions
* The ability to create, update, and delete memories

See here for a [full example](/examples/agent-os/mcp/enable_mcp_example).

---

## How does shared state work between workflows, teams and agents?

**URL:** llms-txt#how-does-shared-state-work-between-workflows,-teams-and-agents?

**Contents:**
- How Workflow Session State Works
  - 1. State Initialization
  - 2. State Access and Modification

Source: https://docs.agno.com/concepts/workflows/workflow_session_state

Learn to handle shared state between the different components of a Workflow

Workflow session state enables persistent data sharing across all components within a workflow - agents, teams, and custom functions. This shared state maintains continuity and enables sophisticated coordination between different workflow components, making it essential for building stateful, deterministic automation systems.

<img className="block dark:hidden" src="https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state-light.png?fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=eb9f2f37de2699763ae1cab8b26e5792" alt="Workflows session state diagram" data-og-width="2199" width="2199" data-og-height="1203" height="1203" data-path="images/workflows-session-state-light.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state-light.png?w=280&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=be8235601f44c3d5c899e769bd7e10a7 280w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state-light.png?w=560&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=c54d2a340511cf08b6f62ee2dc725ab6 560w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state-light.png?w=840&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=a8704d97da7f5fd6490acd6e9e847f21 840w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state-light.png?w=1100&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=88b25555c12572fbb92d1b7724e77cc6 1100w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state-light.png?w=1650&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=e0c24367b61326e2115cfa74059d1316 1650w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state-light.png?w=2500&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=c5d4f68f953670a714b4a5d334f9b5fb 2500w" />

<img className="hidden dark:block" src="https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state.png?fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=5e56bc8354bbb79f31d6c4140e5dea2e" alt="Workflows session state diagram" data-og-width="2199" width="2199" data-og-height="1203" height="1203" data-path="images/workflows-session-state.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state.png?w=280&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=494e73f94a71a1611b068a2561ed6c7a 280w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state.png?w=560&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=3c754db0830ab28e7640f553c9dd93a9 560w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state.png?w=840&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=fa17e5cf5ebf2d45a85a328abbd52bf7 840w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state.png?w=1100&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=e82eae67add368163f04fcb09dab4271 1100w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state.png?w=1650&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=d66bd915da648ef787dd86aa2a5eede6 1650w, https://mintcdn.com/agno-v2/JYIBgMrzFEujZh3_/images/workflows-session-state.png?w=2500&fit=max&auto=format&n=JYIBgMrzFEujZh3_&q=85&s=5bf1239ad621457d50d67b28153b9a1b 2500w" />

## How Workflow Session State Works

### 1. State Initialization

Initialize session state when creating a workflow. The state can start empty or with predefined data that all workflow components can access and modify.

### 2. State Access and Modification

All workflow components - agents, teams, and functions - can read from and write to the shared session state. This enables persistent data flow and coordination across the entire workflow execution.

**Example: Shopping List Management**

```python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai.chat import OpenAIChat
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow

db = SqliteDb(db_file="tmp/workflow.db")

**Examples:**

Example 1 (unknown):
```unknown
### 2. State Access and Modification

All workflow components - agents, teams, and functions - can read from and write to the shared session state. This enables persistent data flow and coordination across the entire workflow execution.

**Example: Shopping List Management**
```

---

## Building Agents

**URL:** llms-txt#building-agents

**Contents:**
- Run your Agent

Source: https://docs.agno.com/concepts/agents/building-agents

Learn how to build Agents with Agno.

To build effective agents, start simple -- just a model, tools, and instructions. Once that works, layer in more functionality as needed.

It's also best to begin with well-defined tasks like report generation, data extraction, classification, summarization, knowledge search, and document processing. These early wins help you identify what works, validate user needs, and set the stage for advanced systems.

Here's the simplest possible report generation agent:

When running your agent, use the `Agent.print_response()` method to print the response in the terminal. This is only for development purposes and not recommended for production use. In production, use the `Agent.run()` or `Agent.arun()` methods. For example:

```python  theme={null}
from typing import Iterator
from agno.agent import Agent, RunOutput, RunOutputEvent, RunEvent
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools
from agno.utils.pprint import pprint_run_response

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    instructions="Write a report on the topic. Output only the report.",
    markdown=True,
)

**Examples:**

Example 1 (unknown):
```unknown
## Run your Agent

When running your agent, use the `Agent.print_response()` method to print the response in the terminal. This is only for development purposes and not recommended for production use. In production, use the `Agent.run()` or `Agent.arun()` methods. For example:
```

---

## Now provide the adjusted Memory Manager to your Agent

**URL:** llms-txt#now-provide-the-adjusted-memory-manager-to-your-agent

**Contents:**
- Control what gets stored in the session
- Developer Resources

team = Team(
  members=[],
  db=db,
  session_summary_manager=session_summary_manager,
  enable_session_summaries=True,
)

team.print_response("What is the speed of light?", stream=True)

session_summary = team.get_session_summary()
print(f"Session summary: {session_summary.summary}")
```

See the [Session Summary Manager](/reference/session/summary_manager) reference for more details.

## Control what gets stored in the session

As your sessions grow, you may want to decide what data exactly is persisted. Agno provides three flags to optimize storage while maintaining full functionality during execution:

* **`store_media`** - Controls storage of images, videos, audio, and files
* **`store_tool_messages`** - Controls storage of tool calls and their results
* **`store_history_messages`** - Controls storage of history messages

<Tip>
  ### How it works

These flags only affect what gets **persisted to the database**. During execution, all data remains available to your team - media, tool results, and history are still accessible in the `RunOutput` object. The data is scrubbed right before saving to the database.

* Your team functionality remains unchanged
  * Tools can access all data they need during execution
  * Only the database storage is optimized
</Tip>

## Developer Resources

* View the [Team schema](/reference/teams/team)
* View the [Session schema](/reference/teams/session)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/teams/session/)

---

## Our Agent will now be able to use our tool, when it deems it relevant

**URL:** llms-txt#our-agent-will-now-be-able-to-use-our-tool,-when-it-deems-it-relevant

**Contents:**
  - Using the Toolkit Class

agent.print_response("What is the weather in San Francisco?", stream=True)
python  theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat

**Examples:**

Example 1 (unknown):
```unknown
<Tip>
  In the example above, the `get_weather` function is a tool. When called, the tool result is shown in the output.

  Then, the Agent will stop after the tool call (without waiting for the model to respond) because we set `stop_after_tool_call=True`.
</Tip>

### Using the Toolkit Class

The `Toolkit` class provides a way to manage multiple tools with additional control over their execution.

You can specify which tools should stop the agent after execution and which should have their results shown.
```

---

## Traditional RAG with LanceDB

**URL:** llms-txt#traditional-rag-with-lancedb

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/knowledge/rag/traditional-rag-lancedb

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Performance on Agent Instantiation

**URL:** llms-txt#performance-on-agent-instantiation

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/evals/performance/performance_agent_instantiation

Evaluation to analyze the runtime and memory usage of an Agent.

---

## Setup the database for the Agent Session to be stored

**URL:** llms-txt#setup-the-database-for-the-agent-session-to-be-stored

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
db = PostgresDb(db_url=db_url)

agent = Agent(
    model=OpenAIResponses(id="gpt-5-mini"),
    db=db,
    tools=[{"type": "file_search"}, {"type": "web_search_preview"}],
    markdown=True,
)

agent.print_response(
    "Summarize the contents of the attached file and search the web for more information.",
    files=[File(url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf")],
)

---

## Define agents with response models

**URL:** llms-txt#define-agents-with-response-models

research_agent = Agent(
    name="AI Research Specialist",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[HackerNewsTools(), DuckDuckGoTools()],
    role="Research AI trends and extract structured insights",
    output_schema=ResearchFindings,
    instructions=[
        "Research the given topic thoroughly using available tools",
        "Provide structured findings with confidence scores",
        "Focus on recent developments and market trends",
        "Make sure to structure your response according to the ResearchFindings model",
    ],
)

strategy_agent = Agent(
    name="Content Strategy Expert",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Create content strategies based on research findings",
    output_schema=ContentStrategy,
    instructions=[
        "Analyze the research findings provided from the previous step",
        "Create a comprehensive content strategy based on the structured research data",
        "Focus on audience engagement and brand building",
        "Structure your response according to the ContentStrategy model",
    ],
)

planning_agent = Agent(
    name="Content Planning Specialist",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Create detailed content plans and calendars",
    output_schema=FinalContentPlan,
    instructions=[
        "Use the content strategy from the previous step to create a detailed implementation plan",
        "Include specific timelines and success metrics",
        "Consider budget and resource constraints",
        "Structure your response according to the FinalContentPlan model",
    ],
)

---

## Create agent

**URL:** llms-txt#create-agent

research_agent = Agent(
    id="user-agent",
    model=OpenAIChat(id="gpt-5-mini"),
    db=db,
    tools=[get_user_details],
    instructions="You are a user agent that can get user details if the user asks for them.",
)

agent_os = AgentOS(
    description="JWT Protected AgentOS",
    agents=[research_agent],
)

---

## Teams

**URL:** llms-txt#teams

**Contents:**
- Guides
- Developer Resources

Source: https://docs.agno.com/concepts/teams/overview

Build autonomous multi-agent systems with Agno Teams.

A Team is a collection of Agents (or other sub-teams) that work together to accomplish tasks.

A `Team` has a list of `members` that can be instances of either `Agent` or `Team`.

<Note>
  It is highly recommended to first learn more about [Agents](/concepts/agents/overview) before diving into Teams.
</Note>

The team leader delegates tasks to members depending on the role of the members and the nature of the tasks.  See the [Delegation](/concepts/teams/delegation) guide for more details.

As with agents, teams support the following features:

* **Model:** Set the model that is used by the "team leader" to delegate tasks to the team members.
* **Instructions:** Instruct the team leader on how to solve problems. The names, descriptions and roles of team members are automatically provided to the team leader.
* **Tools:** If the team leader needs to be able to use tools directly, you can add tools to the team.
* **Reasoning:** Enables the team leader to "think" before responding or delegating tasks to team members, and "analyze" the results of team members' responses.
* **Knowledge:** If the team needs to search for information, you can add a knowledge base to the team. This is accessible to the team leader.
* **Storage:** The Team's session history and state is stored in a database. This enables your team to continue conversations from where they left off, enabling multi-turn, long-term conversations.
* **Memory:** Gives Teams the ability to store and recall information from previous interactions, allowing them to learn user preferences and personalize their responses.

<Note>
  If you are migrating from Agno v1.x.x, the `mode` parameter has been deprecated. Please see the [Migration Guide](/how-to/v2-migration#teams) for more details on how to migrate your teams.
</Note>

<CardGroup cols={3}>
  <Card title="Building Teams" icon="wrench" iconType="duotone" href="/concepts/teams/building-teams">
    Learn how to build your teams.
  </Card>

<Card title="Running your Team" icon="user-robot" iconType="duotone" href="/concepts/teams/running-teams">
    Learn how to run your teams.
  </Card>

<Card title="Debugging Teams" icon="bug" iconType="duotone" href="/concepts/teams/debugging-teams">
    Learn how to debug and troubleshoot your teams.
  </Card>

<Card title="Team Sessions" icon="comments" iconType="duotone" href="/concepts/teams/sessions">
    Learn about team sessions.
  </Card>

<Card title="Input & Output" icon="fire" iconType="duotone" href="/concepts/teams/input-output">
    Learn about input and output for teams.
  </Card>

<Card title="Context Engineering" icon="file-lines" iconType="duotone" href="/concepts/teams/context">
    Learn about context engineering.
  </Card>

<Card title="Dependencies" icon="brackets-curly" iconType="duotone" href="/concepts/teams/dependencies">
    Learn about dependency injection in your team's context.
  </Card>

<Card title="Team State" icon="crystal-ball" iconType="duotone" href="/concepts/teams/state">
    Learn about managing team state.
  </Card>

<Card title="Team Storage" icon="database" iconType="duotone" href="/concepts/teams/storage">
    Learn about session storage.
  </Card>

<Card title="Memory" icon="head-side-brain" iconType="duotone" href="/concepts/teams/memory">
    Learn about adding memory to your teams.
  </Card>

<Card title="Knowledge" icon="books" iconType="duotone" href="/concepts/teams/knowledge">
    Learn about knowledge in teams.
  </Card>

<Card title="Team Metrics" icon="chart-line" iconType="duotone" href="/concepts/teams/metrics">
    Learn how to track team metrics.
  </Card>

<Card title="Pre-hooks & Post-hooks" icon="link" iconType="duotone" href="/concepts/teams/pre-hooks-and-post-hooks">
    Learn about pre-hooks and post-hooks for teams.
  </Card>

<Card title="Guardrails" icon="shield-check" iconType="duotone" href="/concepts/teams/guardrails">
    Learn about implementing guardrails for your teams.
  </Card>
</CardGroup>

## Developer Resources

* View the [Team reference](/reference/teams/team)
* View [Usecases](/examples/use-cases/teams/)
* View [Examples](/examples/concepts/teams/)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/teams/README.md)

---

## Create an Agent with the ModelsLabs tool

**URL:** llms-txt#create-an-agent-with-the-modelslabs-tool

**Contents:**
- Toolkit Params
- Toolkit Functions
- Developer Resources

agent = Agent(tools=[ModelsLabsTools()], name="ModelsLabs Agent")

agent.print_response("Generate a video of a beautiful sunset over the ocean", markdown=True)
```

| Parameter             | Type   | Default | Description                                                                |
| --------------------- | ------ | ------- | -------------------------------------------------------------------------- |
| `api_key`             | `str`  | `None`  | The ModelsLab API key for authentication                                   |
| `wait_for_completion` | `bool` | `False` | Whether to wait for the video to be ready                                  |
| `add_to_eta`          | `int`  | `15`    | Time to add to the ETA to account for the time it takes to fetch the video |
| `max_wait_time`       | `int`  | `60`    | Maximum time to wait for the video to be ready                             |
| `file_type`           | `str`  | `"mp4"` | The type of file to generate                                               |

| Function         | Description                                     |
| ---------------- | ----------------------------------------------- |
| `generate_media` | Generates a video or gif based on a text prompt |

## Developer Resources

* View [Tools](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/models_labs.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/models_labs_tools.py)

---

## Agent that uses a structured output

**URL:** llms-txt#agent-that-uses-a-structured-output

**Contents:**
- Usage

structured_output_agent = Agent(
    model=Nebius(id="Qwen/Qwen3-30B-A3B"),
    description="You are a helpful assistant. Summarize the movie script based on the location in a JSON object.",
    output_schema=MovieScript,
)

structured_output_agent.print_response("New York")
bash  theme={null}
    export NEBIUS_API_KEY=xxx
    bash  theme={null}
    pip install -U openai agno
    bash Mac theme={null}
      python cookbook/models/nebius/structured_output.py
      bash Windows theme={null}
      python cookbook/models/nebius/structured_output.py
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

## In-Memory Database Session

**URL:** llms-txt#in-memory-database-session

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/session/in_memory_db

This example shows how to use an in-memory database with teams for storing sessions, user memories, etc. without setting up a persistent database - useful for development and testing.

```python cookbook/examples/teams/session/07_in_memory_db.py theme={null}
"""This example shows how to use an in-memory database with teams.

With this you will be able to store team sessions, user memories, etc. without setting up a database.
Keep in mind that in production setups it is recommended to use a database.
"""

from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from rich.pretty import pprint

---

## Agentic RAG with Reranking

**URL:** llms-txt#agentic-rag-with-reranking

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/knowledge/rag/agentic-rag-with-reranking

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API keys">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## DynamoDB for Agent

**URL:** llms-txt#dynamodb-for-agent

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/db/dynamodb/dynamodb_for_agent

Agno supports using DynamoDB as a storage backend for Agents using the `DynamoDb` class.

You need to provide `aws_access_key_id` and `aws_secret_access_key` parameters to the `DynamoDb` class.

```python dynamo_for_agent.py theme={null}
from agno.db.dynamo import DynamoDb

---

## Create a knowledge retriever from the vector store

**URL:** llms-txt#create-a-knowledge-retriever-from-the-vector-store

**Contents:**
- Usage

knowledge_retriever = db.as_retriever()

knowledge = Knowledge(
    vector_db=LangChainVectorDb(knowledge_retriever=knowledge_retriever)
)

agent = Agent(knowledge=knowledge)

agent.print_response("What did the president say?", markdown=True)
bash  theme={null}
    pip install -U langchain langchain-community langchain-openai langchain-chroma pypdf openai agno
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Mac theme={null}
      python cookbook/knowledge/vector_db/langchain/langchain_db.py
      bash Windows theme={null}
      python cookbook/knowledge/vector_db/langchain/langchain_db.py
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

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
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

## Agent responds with current, accurate policy details

**URL:** llms-txt#agent-responds-with-current,-accurate-policy-details

**Contents:**
  - Contextual Understanding

**Examples:**

Example 1 (unknown):
```unknown
### Contextual Understanding

The agent understands the context of questions and searches for the most relevant information, not just keyword matches.
```

---

## PgVector Agent Knowledge

**URL:** llms-txt#pgvector-agent-knowledge

**Contents:**
- Setup
- Example
- PgVector Params
- Developer Resources

Source: https://docs.agno.com/concepts/vectordb/pgvector

<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      PgVector also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>

<Tip className="mt-4">
      Use <code>aload()</code> and <code>aprint\_response()</code> methods with <code>asyncio.run()</code> for non-blocking operations in high-throughput applications.
    </Tip>
  </div>
</Card>

<Snippet file="vectordb_pgvector_params.mdx" />

## Developer Resources

* View [Cookbook (Sync)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/pgvector/pgvector_db.py)
* View [Cookbook (Async)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/pgvector/async_pg_vector.py)

**Examples:**

Example 1 (unknown):
```unknown
## Example
```

Example 2 (unknown):
```unknown
<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      PgVector also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>
```

---

## InMemoryDb

**URL:** llms-txt#inmemorydb

Source: https://docs.agno.com/reference/storage/in_memory

`InMemoryDb` is a class that implements the Db interface using an in-memory database. It provides lightweight, in-memory storage for agent/team sessions.

<Snippet file="db-in-memory-params.mdx" />

<Snippet file="db-new-bulk-methods.mdx" />

---

## Async Agent

**URL:** llms-txt#async-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/vllm/async_basic

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Start vLLM server">
    
  </Step>

<Step title="Run Agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Start vLLM server">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
```

---

## Core Concepts & Terminology

**URL:** llms-txt#core-concepts-&-terminology

**Contents:**
- Key Terminology
  - Knowledge Base
  - Agentic RAG
  - Vector Embeddings
  - Chunking
  - Dynamic Few-Shot Learning
- Core Knowledge Components
  - Content Sources
  - Readers
  - Chunking Strategies

Source: https://docs.agno.com/concepts/knowledge/core-concepts/terminology

Essential concepts and terminology for understanding how Knowledge works in Agno agents.

This reference guide defines the key concepts and terminology you'll encounter when working with Knowledge in Agno.

A structured repository of information that agents can search and retrieve from at runtime. Contains processed content optimized for AI understanding and retrieval.

**Retrieval Augmented Generation** where the agent actively decides when to search, what to search for, and how to use the retrieved information. Unlike traditional RAG systems, the agent has full control over the search process.

### Vector Embeddings

Mathematical representations of text that capture semantic meaning. Words and phrases with similar meanings have similar embeddings, enabling intelligent search beyond keyword matching.

The process of breaking large documents into smaller, manageable pieces that are optimal for search and retrieval while preserving context.

### Dynamic Few-Shot Learning

The pattern where agents retrieve specific examples or context at runtime to improve their performance on tasks, rather than having all information provided upfront.

<Accordion title="Example: Dynamic Few-Shot Learning in Action" icon="database">
  **Scenario:** Building a Text-to-SQL Agent

Instead of cramming all table schemas, column names, and example queries into the system prompt, you store this information in a knowledge base.

When a user asks for data, the agent:

1. Analyzes the request
  2. Searches for relevant schema information and example queries
  3. Uses the retrieved context to generate the best possible SQL query

This is "dynamic" because the agent gets exactly the information it needs for each specific query, and "few-shot" because it learns from examples retrieved at runtime.
</Accordion>

## Core Knowledge Components

The raw information you want your agents to access:

* **Documents**: PDFs, Word files, text files
* **Websites**: URLs, web pages, documentation sites
* **Databases**: SQL databases, APIs, structured data
* **Text**: Direct text content, notes, policies

Specialized components that parse different content types and extract meaningful text:

* **PDFReader**: Extracts text from PDF files, handles encryption
* **WebsiteReader**: Crawls web pages and extracts content
* **CSVReader**: Processes tabular data from CSV files
* **Custom Readers**: Build your own for specialized data sources

### Chunking Strategies

Methods for breaking content into optimal pieces:

* **Semantic Chunking**: Respects natural content boundaries
* **Fixed Size**: Uniform chunk sizes with overlap
* **Document Chunking**: Preserves document structure
* **Recursive Chunking**: Hierarchical splitting with multiple separators

Storage systems optimized for similarity search:

* **PgVector**: PostgreSQL extension for vector storage
* **LanceDB**: Fast, embedded vector database
* **Pinecone**: Managed vector database service
* **Qdrant**: High-performance vector search engine

## Component Relationships

The Knowledge system combines these components in a coordinated pipeline: **Readers** → **Chunking** → **Embedders** → **Vector Databases** → **Agent Retrieval**.

## Advanced Knowledge Features

### Custom Knowledge Retrievers

For complete control over how agents search your knowledge:

### Asynchronous Operations

Optimize performance with async knowledge operations:

```python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
### Asynchronous Operations

Optimize performance with async knowledge operations:
```

---

## Image Agent Bytes

**URL:** llms-txt#image-agent-bytes

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/xai/image_agent_bytes

```python cookbook/models/xai/image_agent_bytes.py theme={null}
from pathlib import Path

from agno.agent import Agent
from agno.media import Image
from agno.models.xai import xAI
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.utils.media import download_image

agent = Agent(
    model=xAI(id="grok-2-vision-latest"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

image_path = Path(__file__).parent.joinpath("sample.jpg")

download_image(
    url="https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg",
    output_path=str(image_path),
)

---

## Result Synthesizer Agent - Combines and ranks all findings

**URL:** llms-txt#result-synthesizer-agent---combines-and-ranks-all-findings

result_synthesizer = Agent(
    name="Result Synthesizer",
    model=Claude(id="claude-3-7-sonnet-latest"),
    role="Synthesize and rank all search results into comprehensive response",
    instructions=[
        "Combine results from all team members into a unified response.",
        "Rank information based on relevance and reliability.",
        "Ensure comprehensive coverage of the query topic.",
        "Present results with clear source attribution and confidence levels.",
    ],
    markdown=True,
)

---

## run_response: Iterator[RunOutputEvent] = asyncio.run(agent.arun("Share a 2 sentence horror story", stream=True))

**URL:** llms-txt#run_response:-iterator[runoutputevent]-=-asyncio.run(agent.arun("share-a-2-sentence-horror-story",-stream=true))

---

## Create the Agent

**URL:** llms-txt#create-the-agent

agno_agent = Agent(
    name="Agno Agent",
    model=Claude(id="claude-sonnet-4-5"),
    # Add a database to the Agent
    db=SqliteDb(db_file="agno.db"),
    # Add the Agno MCP server to the Agent
    tools=[MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp")],
    # Add the previous session history to the context
    add_history_to_context=True,
    markdown=True,
)

---

## In-memory database to store user shopping lists

**URL:** llms-txt#in-memory-database-to-store-user-shopping-lists

---

## Agent Debug Mode

**URL:** llms-txt#agent-debug-mode

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/other/debug

This example demonstrates how to enable debug mode for agents to get more verbose output and detailed information about agent execution.

```python debug.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat

---

## Location-Aware Agent Instructions

**URL:** llms-txt#location-aware-agent-instructions

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/context_management/location_instructions

This example demonstrates how to add location context to agent instructions, enabling the agent to provide location-specific responses and search for local news.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/context_management" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Image Agent

**URL:** llms-txt#image-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/xai/image_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Knowledge base setup (same as synchronous example)

**URL:** llms-txt#knowledge-base-setup-(same-as-synchronous-example)

embedder = OpenAIEmbedder(id="text-embedding-3-small")
vector_db = Qdrant(collection="thai-recipes", url="http://localhost:6333", embedder=embedder)
knowledge_base = Knowledge(
    vector_db=vector_db,
)

knowledge_base.add_content(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"
)

---

## Aggregate both agents into a multi-agent system

**URL:** llms-txt#aggregate-both-agents-into-a-multi-agent-system

**Contents:**
- Features
  - Observability & Tracing
  - Evaluation & Analytics
  - Alerting
- Notes

multi_ai_team = Team(
    members=[web_search_agent, finance_agent],
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful financial assistant. Answer user questions about stocks, companies, and financial data.",
    markdown=True,
)

if __name__ == "__main__":
    print("Welcome to the Financial Conversational Agent! Type 'exit' to quit.")
    messages = []
    while True:
        print("********************************")
        user_input = input("You: ")
        if user_input.strip().lower() in ["exit", "quit"]:
            print("Goodbye!")
            break
        messages.append({"role": "user", "content": user_input})
        conversation = "\n".join(
            [
                ("User: " + m["content"])
                if m["role"] == "user"
                else ("Agent: " + m["content"])
                for m in messages
            ]
        )
        response = multi_ai_team.run(
            f"Conversation so far:\n{conversation}\n\nRespond to the latest user message."
        )
        agent_reply = getattr(response, "content", response)
        print("---------------------------------")
        print("Agent:", agent_reply)
        messages.append({"role": "agent", "content": str(agent_reply)})
python  theme={null}
  instrument_agno(Maxim().logger(), {"debug" : True})
  ```
* **Maxim Docs**: For more information on Maxim's features and capabilities, refer to the [Maxim documentation](https://getmaxim.ai/docs).

By following these steps, you can effectively integrate Agno with Maxim, enabling comprehensive observability, evaluation, and monitoring of your AI agents.

**Examples:**

Example 1 (unknown):
```unknown
<img src="https://mintcdn.com/agno-v2/7E-fsqZkCqV5M6b3/images/maxim.gif?s=2269ee92857eb7024d3a8fe6f836fa54" alt="agno.gif" data-og-width="1280" width="1280" data-og-height="720" height="720" data-path="images/maxim.gif" data-optimize="true" data-opv="3" />

## Features

### Observability & Tracing

Maxim provides comprehensive observability for your Agno agents:

* **Agent Tracing**: Track your agent's complete lifecycle, including tool calls, agent trajectories, and decision flows
* **Token Usage**: Monitor prompt and completion token consumption
* **Model Information**: Track which models are being used and their performance
* **Tool Calls**: Detailed logging of all tool executions and their results
* **Performance Metrics**: Latency, cost, and error rate tracking

### Evaluation & Analytics

* **Auto Evaluations**: Automatically evaluate captured logs based on filters and sampling
* **Human Evaluations**: Use human evaluation or rating to assess log quality
* **Node Level Evaluations**: Evaluate any component of your trace for detailed insights
* **Dashboards**: Visualize traces over time, usage metrics, latency & error rates

### Alerting

Set thresholds on error rates, cost, token usage, user feedback, and latency to get real-time alerts via Slack or PagerDuty.

## Notes

* **Environment Variables**: Ensure your environment variables are correctly set for the API key and repository ID.
* **Instrumentation Order**: Call `instrument_agno()` **before** creating or executing any agents to ensure proper tracing.
* **Debug Mode**: Enable debug mode to see detailed logging information:
```

---

## Hacker News search agent

**URL:** llms-txt#hacker-news-search-agent

hacker_news_agent = Agent(
    id="hacker-news-agent",
    name="Hacker News Agent",
    role="Search Hacker News for information",
    tools=[HackerNewsTools()],
    instructions=[
        "Find articles about the company in the Hacker News",
    ],
)

---

## Use the agent to generate and print a response to a query, formatted in Markdown

**URL:** llms-txt#use-the-agent-to-generate-and-print-a-response-to-a-query,-formatted-in-markdown

**Contents:**
- Usage

agent.print_response(
    "What is the first step of making Gluai Buat Chi from the knowledge base?",
    markdown=True,
)
bash  theme={null}
    pip install -U agno lancedb ollama
    bash  theme={null}
    # Install and start Ollama
    # Pull required models
    ollama pull llama3.1:8b
    ollama pull nomic-embed-text
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch rag_with_lance_db_and_sqlite.py
    bash Mac theme={null}
      python rag_with_lance_db_and_sqlite.py
      bash Windows theme={null}
      python rag_with_lance_db_and_sqlite.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/rag" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Setup Ollama">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Performance on Agent with Storage

**URL:** llms-txt#performance-on-agent-with-storage

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/evals/performance/performance_with_storage

Example showing how to analyze the runtime and memory usage of an Agent that is using storage.

---

## Search Knowledge

**URL:** llms-txt#search-knowledge

Source: https://docs.agno.com/reference-api/schema/knowledge/search-knowledge

post /knowledge/search
Search the knowledge base for relevant documents using query, filters and search type.

---

## Memory with PostgreSQL

**URL:** llms-txt#memory-with-postgresql

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/memory/db/mem-postgres-memory

```python cookbook/memory/db/mem-postgres-memory.py theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb

---

## Team with Agentic Memory

**URL:** llms-txt#team-with-agentic-memory

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/memory/team_with_agentic_memory

This example demonstrates how to use agentic memory with a team. Unlike simple memory storage, agentic memory allows the AI to actively create, update, and delete user memories during each run based on the conversation context, providing intelligent memory management.

```python cookbook/examples/teams/memory/02_team_with_agentic_memory.py theme={null}
"""
This example shows you how to use persistent memory with an Agent.

During each run the Agent can create/update/delete user memories.

To enable this, set `enable_agentic_memory=True` in the Agent config.
"""

from agno.agent.agent import Agent
from agno.db.postgres import PostgresDb
from agno.memory import MemoryManager  # noqa: F401
from agno.models.openai import OpenAIChat
from agno.team import Team

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
db = PostgresDb(db_url=db_url)

john_doe_id = "john_doe@example.com"

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
)

team = Team(
    model=OpenAIChat(id="gpt-5-mini"),
    members=[agent],
    db=db,
    enable_agentic_memory=True,
)

team.print_response(
    "My name is John Doe and I like to hike in the mountains on weekends.",
    stream=True,
    user_id=john_doe_id,
)

team.print_response("What are my hobbies?", stream=True, user_id=john_doe_id)

---

## AgentUI

**URL:** llms-txt#agentui

**Contents:**
- Get Started with Agent UI
- Connect your AgentOS
- View the AgentUI

Source: https://docs.agno.com/agent-os/agent-ui

An Open Source AgentUI for your AgentOS

<Frame>
  <img height="200" src="https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui.png?fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=72cd1f0888dea4f1ec60a67bff5664c4" style={{ borderRadius: '8px' }} data-og-width="5364" data-og-height="2808" data-path="images/agent-ui.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui.png?w=280&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=8a962c7d75c6fd40d37b696f258b69fc 280w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui.png?w=560&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=729e6c42c46d47f9c56c66451576c53a 560w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui.png?w=840&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=cabb3ed5cb4c1934bd3a5a1cba70a2d1 840w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui.png?w=1100&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=d880656a6c120ed2ef06879bb522b840 1100w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui.png?w=1650&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=55b22efc72db2bbb9e26079d46aea5b5 1650w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui.png?w=2500&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=5331541ccf7abdb289f0e213f65c9649 2500w" />
</Frame>

Agno provides a beautiful UI for interacting with your agents, completely open source, free to use and build on top of. It's a simple interface that allows you to chat with your agents, view their memory, knowledge, and more.

<Note>
  The AgentOS only uses data in your database. No data is sent to Agno.
</Note>

The Open Source Agent UI is built with Next.js and TypeScript. After the success of the [Agent AgentOS](/agent-os/introduction), the community asked for a self-hosted alternative and we delivered!

## Get Started with Agent UI

To clone the Agent UI, run the following command in your terminal:

Enter `y` to create a new project, install dependencies, then run the agent-ui using:

Open [http://localhost:3000](http://localhost:3000) to view the Agent UI, but remember to connect to your local agents.

<Frame>
  <img height="200" src="https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=8f6e365622aefac39432083f2ec587df" style={{ borderRadius: '8px' }} data-og-width="3096" data-og-height="1832" data-path="images/agent-ui-homepage.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=280&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=f1d2aa67b73246a4d71f84fc9b581cd0 280w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=560&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=969732c206fb7c33e7f575aae105294a 560w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=840&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=f1cf21fec03209156f4d1eeec6a12163 840w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=1100&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=adf49bc5198a1c4283d0bdb9ffcf91f7 1100w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=1650&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=438d2965108fb49d808e89f9928613a3 1650w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=2500&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=b02e0c727983bc3329b8046dfa18d3a5 2500w" />
</Frame>

<Accordion title="Clone the repository manually" icon="github">
  You can also clone the repository manually

And run the agent-ui using

## Connect your AgentOS

The Agent UI needs to connect to a AgentOS server, which you can run locally or on any cloud provider.

Let's start with a local AgentOS server. Create a file `agentos.py`

In another terminal, run the AgentOS server:

<Steps>
  <Step title="Setup your virtual environment">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Install dependencies">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Export your OpenAI key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Run the AgentOS">
    
  </Step>
</Steps>

<Tip>Make sure the `serve_agentos_app()` points to the file containing your `AgentOS` app.</Tip>

* Open [http://localhost:3000](http://localhost:3000) to view the Agent UI
* Enter the `localhost:7777` endpoint on the left sidebar and start chatting with your agents and teams!

<video autoPlay muted controls className="w-full aspect-video" src="https://mintcdn.com/agno-v2/APlycdxch1exeM4A/videos/agent-ui-demo.mp4?fit=max&auto=format&n=APlycdxch1exeM4A&q=85&s=646f460d718e8c3d09b479277088fa19" data-path="videos/agent-ui-demo.mp4" />

**Examples:**

Example 1 (unknown):
```unknown
Enter `y` to create a new project, install dependencies, then run the agent-ui using:
```

Example 2 (unknown):
```unknown
Open [http://localhost:3000](http://localhost:3000) to view the Agent UI, but remember to connect to your local agents.

<Frame>
  <img height="200" src="https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=8f6e365622aefac39432083f2ec587df" style={{ borderRadius: '8px' }} data-og-width="3096" data-og-height="1832" data-path="images/agent-ui-homepage.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=280&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=f1d2aa67b73246a4d71f84fc9b581cd0 280w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=560&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=969732c206fb7c33e7f575aae105294a 560w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=840&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=f1cf21fec03209156f4d1eeec6a12163 840w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=1100&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=adf49bc5198a1c4283d0bdb9ffcf91f7 1100w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=1650&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=438d2965108fb49d808e89f9928613a3 1650w, https://mintcdn.com/agno-v2/QfHdyhk-tu-JEw8s/images/agent-ui-homepage.png?w=2500&fit=max&auto=format&n=QfHdyhk-tu-JEw8s&q=85&s=b02e0c727983bc3329b8046dfa18d3a5 2500w" />
</Frame>

<br />

<Accordion title="Clone the repository manually" icon="github">
  You can also clone the repository manually
```

Example 3 (unknown):
```unknown
And run the agent-ui using
```

Example 4 (unknown):
```unknown
</Accordion>

## Connect your AgentOS

The Agent UI needs to connect to a AgentOS server, which you can run locally or on any cloud provider.

Let's start with a local AgentOS server. Create a file `agentos.py`
```

---

## Memory creation requires a db to be provided

**URL:** llms-txt#memory-creation-requires-a-db-to-be-provided

db = SqliteDb(db_file="tmp/memory.db")

def run_agent():
    agent = Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        system_message="Be concise, reply with one sentence.",
        db=db,
        enable_user_memories=True,
    )

response = agent.run("My name is Tom! I'm 25 years old and I live in New York.")
    print(f"Agent response: {response.content}")

response_with_memory_updates_perf = PerformanceEval(
    name="Memory Updates Performance",
    func=run_agent,
    num_iterations=5,
    warmup_runs=0,
)

if __name__ == "__main__":
    response_with_memory_updates_perf.run(print_results=True, print_summary=True)
```

---

## MySQL for Agent

**URL:** llms-txt#mysql-for-agent

**Contents:**
- Usage
  - Run MySQL
- Params
- Developer Resources

Source: https://docs.agno.com/examples/concepts/db/mysql/mysql_for_agent

Agno supports using MySQL as a storage backend for Agents using the `MySQLDb` class.

Install [docker desktop](https://docs.docker.com/desktop/install/mac-install/) and run **MySQL** on port **3306** using:

<Snippet file="db-mysql-params.mdx" />

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/db/mysql/mysql_storage_for_agent.py)

**Examples:**

Example 1 (unknown):
```unknown

```

---

## Ask the Agent about the user

**URL:** llms-txt#ask-the-agent-about-the-user

**Contents:**
- Usage

agent.print_response("What do you know about me?")
bash  theme={null}
    export OPENAI_API_KEY=xxx
    export ZEP_API_KEY=xxx
    bash  theme={null}
    pip install -U zep-cloud openai agno
    bash Mac theme={null}
      python cookbook/tools/zep_tools.py
      bash Windows theme={null}
      python cookbook/tools/zep_tools.py
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

## Reasoning Agent

**URL:** llms-txt#reasoning-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/xai/reasoning_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Setup your Agent with Automatic User Memory

**URL:** llms-txt#setup-your-agent-with-automatic-user-memory

agent = Agent(
    db=db,
    enable_user_memories=True, # Automatic memory management
)

---

## Create Postgres-backed memory store

**URL:** llms-txt#create-postgres-backed-memory-store

db = PostgresDb(db_url=db_url)

---

## Performance with Memory Updates

**URL:** llms-txt#performance-with-memory-updates

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/evals/performance/performance_with_memory

Learn how to evaluate performance when memory updates are involved.

This example shows how to evaluate performance when memory updates are involved.

```python  theme={null}
"""Run `pip install openai agno memory_profiler` to install dependencies."""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.eval.performance import PerformanceEval
from agno.models.openai import OpenAIChat

---

## In-Memory Storage for Workflows

**URL:** llms-txt#in-memory-storage-for-workflows

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/db/in_memory/in_memory_for_workflow

Example using `InMemoryDb` with workflows for multi-step processes.

```python  theme={null}
from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow

---

## Standalone Memory

**URL:** llms-txt#standalone-memory

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/memory/memory_manager/01-standalone-memory

```python memory_manager/standalone_memory.py theme={null}
from agno.db.postgres import PostgresDb
from agno.memory import MemoryManager, UserMemory
from rich.pretty import pprint

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

memory = MemoryManager(db=PostgresDb(db_url=db_url))

---

## Agent Input as Message Object

**URL:** llms-txt#agent-input-as-message-object

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/input_as_message

This example demonstrates how to provide input to an agent using the Message object format for structured multimodal content.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/input_and_output" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Query the knowledge base

**URL:** llms-txt#query-the-knowledge-base

**Contents:**
- Usage
- Params

agent.print_response(
    "What are the main topics discussed in the videos?",
    markdown=True
)
bash  theme={null}
    pip install -U youtube-transcript-api pytube sqlalchemy psycopg pgvector agno openai
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Mac theme={null}
      python examples/concepts/knowledge/readers/youtube_reader_sync.py
      bash Windows theme={null}
      python examples/concepts/knowledge/readers/youtube_reader_sync.py
      ```
    </CodeGroup>
  </Step>
</Steps>

<Snippet file="youtube-reader-reference.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## User Memories and Session Summaries

**URL:** llms-txt#user-memories-and-session-summaries

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/getting-started/10-user-memories-and-summaries

This example shows how to create an agent with persistent memory that stores:

1. Personalized user memories - facts and preferences learned about specific users
2. Session summaries - key points and context from conversations
3. Chat history - stored in SQLite for persistence

* Stores user-specific memories in SQLite database
* Maintains session summaries for context
* Continues conversations across sessions with memory
* References previous context and user information in responses

Examples:
User: "My name is John and I live in NYC"
Agent: *Creates memory about John's location*

User: "What do you remember about me?"
Agent: *Recalls previous memories about John*

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run the agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Create knowledge base with embedder

**URL:** llms-txt#create-knowledge-base-with-embedder

knowledge = Knowledge(
    vector_db=PgVector(
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        table_name="my_embeddings",
        embedder=OpenAIEmbedder(),  # Default embedder
    ),
    max_results=2,  # Return top 2 most relevant chunks
)

---

## Knowledge Tools

**URL:** llms-txt#knowledge-tools

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/tools/others/knowledge

```python cookbook/tools/knowledge_tools.py theme={null}
from agno.agent import Agent
from agno.tools.knowledge import KnowledgeTools
from agno.knowledge import Knowledge

---

## Check memory count for a user

**URL:** llms-txt#check-memory-count-for-a-user

memories = agent.get_user_memories(user_id="user_123")
print(f"User has {len(memories)} memories")

---

## Agent using our URLGuardrail

**URL:** llms-txt#agent-using-our-urlguardrail

agent = Agent(
    name="URL-Protected Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    # Provide the Guardrails to be used with the pre_hooks parameter
    pre_hooks=[URLGuardrail()],
)

---

## Agent with Streaming

**URL:** llms-txt#agent-with-streaming

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/vllm/basic_stream

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install Libraries">
    
  </Step>

<Step title="Start vLLM server">
    
  </Step>

<Step title="Run Agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install Libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Start vLLM server">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
```

---

## Agent automatically searches when needed

**URL:** llms-txt#agent-automatically-searches-when-needed

user: "What's our current return policy?"

---

## Expensive model for main conversations

**URL:** llms-txt#expensive-model-for-main-conversations

**Contents:**
- Mitigation Strategy #3: Guide Memory Behavior with Instructions
- Mitigation Strategy #4: Implement Memory Pruning

agent = Agent(
    db=db,
    model=OpenAIChat(id="gpt-4o"),
    memory_manager=memory_manager,
    enable_agentic_memory=True
)
python  theme={null}
agent = Agent(
    db=db,
    enable_agentic_memory=True,
    instructions=[
        "Only update memories when users share significant new information.",
        "Don't create memories for casual conversation or temporary states.",
        "Batch multiple memory updates together when possible."
    ]
)
python  theme={null}
from datetime import datetime, timedelta

def prune_old_memories(db, user_id, days=90):
    """Remove memories older than 90 days"""
    cutoff_timestamp = int((datetime.now() - timedelta(days=days)).timestamp())
    
    memories = db.get_user_memories(user_id=user_id)
    for memory in memories:
        if memory.updated_at and memory.updated_at < cutoff_timestamp:
            db.delete_user_memory(memory_id=memory.memory_id)

**Examples:**

Example 1 (unknown):
```unknown
This approach can reduce memory-related costs by 98% while maintaining conversation quality.

## Mitigation Strategy #3: Guide Memory Behavior with Instructions

Add explicit instructions to prevent frivolous memory updates:
```

Example 2 (unknown):
```unknown
## Mitigation Strategy #4: Implement Memory Pruning

Prevent memory bloat by periodically cleaning up old or irrelevant memories:
```

---

## === AGENTS ===

**URL:** llms-txt#===-agents-===

hackernews_agent = Agent(
    name="HackerNews Researcher",
    instructions="Research tech news and trends from Hacker News",
    tools=[HackerNewsTools()],
)

exa_agent = Agent(
    name="Exa Search Researcher",
    instructions="Research using Exa advanced search capabilities",
    tools=[ExaTools()],
)

content_agent = Agent(
    name="Content Creator",
    instructions="Create well-structured content from research data",
)

---

## Agent With Knowledge

**URL:** llms-txt#agent-with-knowledge

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/meta/knowledge

```python cookbook/models/meta/llama/knowledge.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.meta import Llama
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    vector_db=PgVector(table_name="recipes", db_url=db_url),
)

---

## Team with Knowledge Tools

**URL:** llms-txt#team-with-knowledge-tools

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/reasoning/teams/knowledge-tool-team

This is a team reasoning example with knowledge tools.

<Tip>
  Enabling the reasoning option on the team leader helps optimize delegation and enhances multi-agent collaboration by selectively invoking deeper reasoning when required.
</Tip>

```python cookbook/reasoning/teams/knowledge_tool_team.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.knowledge import KnowledgeTools
from agno.vectordb.lancedb import LanceDb, SearchType

agno_docs = Knowledge(
    # Use LanceDB as the vector database and store embeddings in the `agno_docs` table
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs",
        search_type=SearchType.hybrid,
    ),
)

---

## AgentOS API Overview

**URL:** llms-txt#agentos-api-overview

**Contents:**
- Authentication
- Core Resources

Source: https://docs.agno.com/reference-api/overview

Complete API reference for interacting with AgentOS programmatically

Welcome to the comprehensive API reference for the Agno AgentOS API. This RESTful API enables you to programmatically interact with your AgentOS instance, manage agents, teams, and workflows, and integrate AgentOS capabilities into your applications.

AgentOS supports bearer-token authentication via a single Security Key.

* When `OS_SECURITY_KEY` environment variable is set on the server, all routes require:

* When `OS_SECURITY_KEY` is not set, authentication is disabled for that instance.

See the dedicated guide: [Secure your AgentOS with a Security Key](/agent-os/security).

The AgentOS API is organized around several key resources:

<CardGroup cols={2}>
  <Card title="Agents" icon="robot" href="/reference-api/schema/agents/list-all-agents">
    Create, manage, and execute individual agent runs with tools and knowledge
  </Card>

<Card title="Teams" icon="users" href="/reference-api/schema/teams/list-all-teams">
    Orchestrate multiple agents working together on complex tasks
  </Card>

<Card title="Workflows" icon="diagram-project" href="/reference-api/schema/workflows/list-all-workflows">
    Define and execute multi-step automated processes
  </Card>

<Card title="Sessions" icon="clock" href="/reference-api/schema/sessions/list-sessions">
    Track conversation history and maintain context across interactions
  </Card>

<Card title="Memory" icon="brain" href="/reference-api/schema/memory/list-memories">
    Store and retrieve persistent memories for personalized interactions
  </Card>

<Card title="Knowledge" icon="book" href="/reference-api/schema/knowledge/list-content">
    Upload, manage, and query knowledge bases for your agents
  </Card>

<Card title="Evals" icon="chart-bar" href="/reference-api/schema/evals/list-evaluation-runs">
    Run evaluations and track performance metrics for your agents
  </Card>
</CardGroup>

---

## Define custom AgentQL query for specific data extraction (see https://docs.agentql.com/concepts/query-language)

**URL:** llms-txt#define-custom-agentql-query-for-specific-data-extraction-(see-https://docs.agentql.com/concepts/query-language)

custom_query = """
{
    title
    text_content[]
}
"""

---

## Async Agent Streaming Responses

**URL:** llms-txt#async-agent-streaming-responses

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/async/streaming

This example demonstrates different methods of handling streaming responses from async agents, including manual iteration, print response, and pretty print response.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/async" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Provide the agent with the audio file and get result as text

**URL:** llms-txt#provide-the-agent-with-the-audio-file-and-get-result-as-text

**Contents:**
- Usage

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini-audio-preview", modalities=["text"]),
    markdown=True,
)
agent.print_response(
    "What is in this audio?", audio=[Audio(content=wav_data, format="wav")]
)
bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    pip install -U openai requests agno
    bash Mac theme={null}
      python cookbook/models/openai/chat/audio_input_agent.py
      bash Windows theme={null}
      python cookbook/models/openai/chat/audio_input_agent.py
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

## Create a Shopping List Manager Agent that maintains state

**URL:** llms-txt#create-a-shopping-list-manager-agent-that-maintains-state

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    # Initialize the session state with an empty shopping list (default session state for all sessions)
    session_state={"shopping_list": []},
    db=SqliteDb(db_file="tmp/example.db"),
    tools=[add_item, remove_item, list_items],
    # You can use variables from the session state in the instructions
    instructions=dedent("""\
        Your job is to manage a shopping list.

The shopping list starts empty. You can add items, remove items by name, and list all items.

Current shopping list: {shopping_list}
    """),
    markdown=True,
)

---

## Run Agent

**URL:** llms-txt#run-agent

Source: https://docs.agno.com/reference-api/schema/agui/run-agent

---

## Agent that can get financial data

**URL:** llms-txt#agent-that-can-get-financial-data

finance_agent = Agent(
    name="Finance Agent",
    role="Get financial data",
    model=Claude(id="claude-3-5-sonnet-latest"),
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
    instructions=["Use tables to display data"],
)

---

## Initialize the Agent with the knowledge_base

**URL:** llms-txt#initialize-the-agent-with-the-knowledge_base

agent = Agent(
    knowledge=knowledge_base,
    search_knowledge=True,
)

---

## Filtering on MongoDB

**URL:** llms-txt#filtering-on-mongodb

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/vector-dbs/filtering_mongo_db

Learn how to filter knowledge base searches using Pdf documents with user-specific metadata in MongoDB.

```python  theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.mongodb import MongoDb

---

## Recipe Creator

**URL:** llms-txt#recipe-creator

**Contents:**
- Code

Source: https://docs.agno.com/examples/use-cases/agents/recipe-creator

This example shows how to create an intelligent recipe recommendation system that provides
detailed, personalized recipes based on your ingredients, dietary preferences, and time constraints.
The agent combines culinary knowledge, nutritional data, and cooking techniques to deliver
comprehensive cooking instructions.

Example prompts to try:

* "I have chicken, rice, and vegetables. What can I make in 30 minutes?"
* "Create a vegetarian pasta recipe with mushrooms and spinach"
* "Suggest healthy breakfast options with oats and fruits"
* "What can I make with leftover turkey and potatoes?"
* "Need a quick dessert recipe using chocolate and bananas"

```python recipe_creator.py theme={null}
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools

recipe_agent = Agent(
    name="ChefGenius",
    tools=[ExaTools()],
    model=OpenAIChat(id="gpt-5-mini"),
    description=dedent("""\
        You are ChefGenius, a passionate and knowledgeable culinary expert with expertise in global cuisine! 🍳

Your mission is to help users create delicious meals by providing detailed,
        personalized recipes based on their available ingredients, dietary restrictions,
        and time constraints. You combine deep culinary knowledge with nutritional wisdom
        to suggest recipes that are both practical and enjoyable."""),
    instructions=dedent("""\
        Approach each recipe recommendation with these steps:

1. Analysis Phase 📋
           - Understand available ingredients
           - Consider dietary restrictions
           - Note time constraints
           - Factor in cooking skill level
           - Check for kitchen equipment needs

2. Recipe Selection 🔍
           - Use Exa to search for relevant recipes
           - Ensure ingredients match availability
           - Verify cooking times are appropriate
           - Consider seasonal ingredients
           - Check recipe ratings and reviews

3. Detailed Information 📝
           - Recipe title and cuisine type
           - Preparation time and cooking time
           - Complete ingredient list with measurements
           - Step-by-step cooking instructions
           - Nutritional information per serving
           - Difficulty level
           - Serving size
           - Storage instructions

4. Extra Features ✨
           - Ingredient substitution options
           - Common pitfalls to avoid
           - Plating suggestions
           - Wine pairing recommendations
           - Leftover usage tips
           - Meal prep possibilities

Presentation Style:
        - Use clear markdown formatting
        - Present ingredients in a structured list
        - Number cooking steps clearly
        - Add emoji indicators for:
          🌱 Vegetarian
          🌿 Vegan
          🌾 Gluten-free
          🥜 Contains nuts
          ⏱️ Quick recipes
        - Include tips for scaling portions
        - Note allergen warnings
        - Highlight make-ahead steps
        - Suggest side dish pairings"""),
    markdown=True,
    add_datetime_to_context=True,
    )

---

## Agno framework assistant

**URL:** llms-txt#agno-framework-assistant

agno_assist = Agent(
    name="Agno Assist",
    role="Help with Agno framework questions and code",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="Search your knowledge before answering. Help write working Agno code.",
    tools=[
        KnowledgeTools(
            knowledge=agno_assist_knowledge, add_instructions=True, add_few_shot=True
        ),
    ],
    add_history_to_context=True,
    add_datetime_to_context=True,
)

---

## Agentic User Input with Control Flow

**URL:** llms-txt#agentic-user-input-with-control-flow

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/agentic_user_input

This example demonstrates how to use UserControlFlowTools to allow agents to dynamically request user input when they need additional information to complete tasks.

```python agentic_user_input.py theme={null}
"""🤝 Human-in-the-Loop: Allowing users to provide input externally

This example shows how to use the UserControlFlowTools to allow the agent to get user input dynamically.
If the agent doesn't have enough information to complete a task, it will use the toolkit to get the information it needs from the user.
"""

from typing import Any, Dict, List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import Toolkit
from agno.tools.function import UserInputField
from agno.tools.user_control_flow import UserControlFlowTools
from agno.utils import pprint

class EmailTools(Toolkit):
    def __init__(self, *args, **kwargs):
        super().__init__(
            name="EmailTools", tools=[self.send_email, self.get_emails], *args, **kwargs
        )

def send_email(self, subject: str, body: str, to_address: str) -> str:
        """Send an email to the given address with the given subject and body.

Args:
            subject (str): The subject of the email.
            body (str): The body of the email.
            to_address (str): The address to send the email to.
        """
        return f"Sent email to {to_address} with subject {subject} and body {body}"

def get_emails(self, date_from: str, date_to: str) -> list[dict[str, str]]:
        """Get all emails between the given dates.

Args:
            date_from (str): The start date (in YYYY-MM-DD format).
            date_to (str): The end date (in YYYY-MM-DD format).
        """
        return [
            {
                "subject": "Hello",
                "body": "Hello, world!",
                "to_address": "test@test.com",
                "date": date_from,
            },
            {
                "subject": "Random other email",
                "body": "This is a random other email",
                "to_address": "john@doe.com",
                "date": date_to,
            },
        ]

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[EmailTools(), UserControlFlowTools()],
    markdown=True,
)

run_response = agent.run("Send an email with the body 'What is the weather in Tokyo?'")

---

## Streaming Basic Agent

**URL:** llms-txt#streaming-basic-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/ibm/basic_stream

```python cookbook/models/ibm/watsonx/basic_stream.py theme={null}
from typing import Iterator
from agno.agent import Agent, RunOutput
from agno.models.ibm import WatsonX

agent = Agent(model=WatsonX(id="ibm/granite-20b-code-instruct"), markdown=True)

---

## Define the custom knowledge retriever

**URL:** llms-txt#define-the-custom-knowledge-retriever

---

## json_mode_response: RunOutput = json_mode_agent.run("New York")

**URL:** llms-txt#json_mode_response:-runoutput-=-json_mode_agent.run("new-york")

---

## Create an Agent with the Sleep tool

**URL:** llms-txt#create-an-agent-with-the-sleep-tool

agent = Agent(tools=[SleepTools()], name="Sleep Agent")

---

## Provide the agent with the audio file and audio configuration and get result as text + audio

**URL:** llms-txt#provide-the-agent-with-the-audio-file-and-audio-configuration-and-get-result-as-text-+-audio

agent = Agent(
    model=OpenAIChat(
        id="gpt-4o-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "sage", "format": "wav"},
    ),
    db=InMemoryDb(),
    add_history_to_context=True,
    markdown=True,
)
run_output: RunOutput = agent.run("Tell me a 5 second scary story")

---

## Create an Agent that maintains state

**URL:** llms-txt#create-an-agent-that-maintains-state

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    # Initialize the session state with a counter starting at 0
    session_state={"count": 0},
    tools=[increment_counter, get_counter],
    # Use variables from the session state in the instructions
    instructions="You can increment and check a counter. Current count is: {count}",
    # Important: Resolve the state in the messages so the agent can see state changes
    resolve_in_context=True,
    markdown=True,
)

---

## Quality Validator Agent - Specialized in validation

**URL:** llms-txt#quality-validator-agent---specialized-in-validation

quality_validator = Agent(
    name="Quality Validator",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Validate answer quality and suggest improvements",
    instructions=[
        "Review the synthesized answer for accuracy and completeness.",
        "Check if the answer fully addresses the user's query.",
        "Identify any gaps or areas that need clarification.",
        "Suggest improvements or additional information if needed.",
        "Ensure the response meets high quality standards.",
    ],
    markdown=True,
)

---

## Agent Intermediate Steps Streaming

**URL:** llms-txt#agent-intermediate-steps-streaming

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/other/intermediate_steps

This example demonstrates how to stream intermediate steps during agent execution, providing visibility into tool calls and execution events.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/other" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Share Memory and History between Agents

**URL:** llms-txt#share-memory-and-history-between-agents

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/memory/07-share-memory-and-history-between-agents

This example shows how to share memory and history between agents.

You can set `add_history_to_context=True` to add the history to the context of the agent.

You can set `enable_user_memories=True` to enable user memory generation at the end of each run.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

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

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## List of models available in the AgentOS

**URL:** llms-txt#list-of-models-available-in-the-agentos

available_models:
  - <MODEL_STRING>
  ...

---

## agent.print_response("I also like to play basketball.")

**URL:** llms-txt#agent.print_response("i-also-like-to-play-basketball.")

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai psycopg
    bash  theme={null}
    # Start PostgreSQL container with pgvector
    cookbook/scripts/run_pgvector.sh
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch 04_session_summary_references.py
    bash Mac theme={null}
      python 04_session_summary_references.py
      bash Windows theme={null}
      python 04_session_summary_references.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/session" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Setup PostgreSQL">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Setup basic agents, teams and workflows

**URL:** llms-txt#setup-basic-agents,-teams-and-workflows

basic_agent = Agent(
    name="Basic Agent",
    db=db,
    enable_session_summaries=True,
    enable_user_memories=True,
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    markdown=True,
)
basic_team = Team(
    id="basic-team",
    name="Basic Team",
    model=OpenAIChat(id="gpt-5-mini"),
    db=db,
    members=[basic_agent],
    enable_user_memories=True,
)
basic_workflow = Workflow(
    id="basic-workflow",
    name="Basic Workflow",
    description="Just a simple workflow",
    db=db,
    steps=[
        Step(
            name="step1",
            description="Just a simple step",
            agent=basic_agent,
        )
    ],
)
basic_knowledge = Knowledge(
    name="Basic Knowledge",
    description="A basic knowledge base",
    contents_db=db,
    vector_db=PgVector(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai", table_name="vectors"),
)

---

## Coordinated Agentic RAG Team

**URL:** llms-txt#coordinated-agentic-rag-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/search_coordination/coordinated_agentic_rag

This example demonstrates how multiple specialized agents can coordinate to provide comprehensive RAG (Retrieval-Augmented Generation) responses by dividing search and analysis tasks across team members.

```python cookbook/examples/teams/search_coordination/01_coordinated_agentic_rag.py theme={null}
"""
This example demonstrates how multiple specialized agents can coordinate to provide
comprehensive RAG (Retrieval-Augmented Generation) responses by dividing search
and analysis tasks across team members.

Team Composition:
- Knowledge Searcher: Searches knowledge base for relevant information
- Content Analyzer: Analyzes and synthesizes retrieved content
- Response Synthesizer: Creates final comprehensive response with sources

Setup:
1. Run: `pip install agno anthropic cohere lancedb tantivy sqlalchemy`
2. Export your ANTHROPIC_API_KEY and CO_API_KEY
3. Run this script to see coordinated RAG in action
"""

from agno.agent import Agent
from agno.knowledge.embedder.cohere import CohereEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reranker.cohere import CohereReranker
from agno.models.anthropic import Claude
from agno.team.team import Team
from agno.vectordb.lancedb import LanceDb, SearchType

---

## Sequence of functions and agents

**URL:** llms-txt#sequence-of-functions-and-agents

Source: https://docs.agno.com/examples/concepts/workflows/01-basic-workflows/sequence_of_functions_and_agents

This example demonstrates how to use a sequence of functions and agents in a workflow.

This example demonstrates **Workflows** combining custom functions with agents and teams
in a sequential execution pattern. This shows how to mix different component types for
maximum flexibility in your workflow design.

**When to use**: Linear processes where you need custom data preprocessing between AI agents,
or when combining multiple component types (functions, agents, teams) in sequence.

```python sequence_of_functions_and_agents.py theme={null}
from textwrap import dedent

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.types import StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## Structured Output Agent

**URL:** llms-txt#structured-output-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/portkey/structured_output

```python cookbook/models/portkey/structured_output.py theme={null}
from typing import List

from agno.agent import Agent, RunOutput  # noqa
from agno.models.portkey import Portkey
from pydantic import BaseModel, Field

class MovieScript(BaseModel):
    setting: str = Field(
        ..., description="Provide a nice setting for a blockbuster movie."
    )
    ending: str = Field(
        ...,
        description="Ending of the movie. If not available, provide a happy ending.",
    )
    genre: str = Field(
        ...,
        description="Genre of the movie. If not available, select action, thriller or romantic comedy.",
    )
    name: str = Field(..., description="Give a name to this movie")
    characters: List[str] = Field(..., description="Name of characters for this movie.")
    storyline: str = Field(
        ..., description="3 sentence storyline for the movie. Make it exciting!"
    )

agent = Agent(
    model=Portkey(id="@first-integrati-707071/gpt-5-nano"),
    output_schema=MovieScript,
    markdown=True,
)

---

## 4. Create agent with knowledge search enabled

**URL:** llms-txt#4.-create-agent-with-knowledge-search-enabled

**Contents:**
  - What Happens When You Add Content
  - What Happens During a Conversation
- Key Components Working Together
- Choosing Your Chunking Strategy
- Managing Your Knowledge Base

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,  # Required for automatic search
    knowledge_filters={"type": "policy"}  # Optional filtering
)
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
<Note>
  **Smart Defaults**: Agno provides sensible defaults to get you started quickly:

  * **Embedder**: If no embedder is specified, Agno automatically uses `OpenAIEmbedder` with default settings
  * **Chunking**: If no chunking strategy is provided to readers, Agno defaults to `FixedSizeChunking(chunk_size=5000)`
  * **Search Type**: Vector databases default to `SearchType.vector` for semantic search

  This means you can start with minimal configuration and customize as needed!
</Note>

### What Happens When You Add Content

When you call `knowledge.add_content()`, here's what happens:

1. **A reader parses your file** - Agno picks the right reader (PDFReader, CSVReader, WebsiteReader, etc.) based on your file type and extracts the text
2. **Content gets chunked** - Your chosen chunking strategy breaks the text into digestible pieces, whether by semantic boundaries, fixed sizes, or document structure
3. **Embeddings are created** - Each chunk is converted into a vector embedding using your embedder (OpenAI, SentenceTransformer, etc.)
4. **Status is tracked** - Content moves through states: PROCESSING → COMPLETED or FAILED
5. **Everything is stored** - Chunks, embeddings, and metadata all land in your vector database, ready for search

### What Happens During a Conversation

When your agent receives a question:

1. **The agent decides** - Should I search for more context or answer from what I already know?
2. **Query gets embedded** - If searching, your question becomes a vector using the same embedder
3. **Similar chunks are found** - `knowledge.search()` or `knowledge.async_search()` finds chunks with vectors close to your question
4. **Filters are applied** - Any metadata filters you configured narrow down the results
5. **Agent synthesizes the answer** - Retrieved context + your question = accurate, grounded response

## Key Components Working Together

* **Readers** - Agno's reader factory provides specialized parsers: PDFReader, CSVReader, WebsiteReader, MarkdownReader, and more for different content types.

* **Chunking Strategies** - Choose from FixedSizeChunking, SemanticChunking, or RecursiveChunking to optimize how documents are broken down for search.

* **Embedders** - Support for OpenAIEmbedder, SentenceTransformerEmbedder, and other embedding models to convert text into searchable vectors.

* **Vector Databases** - PgVector for production, LanceDB for development, or PineconeDB for managed services - each with hybrid search capabilities.

## Choosing Your Chunking Strategy

How you split content dramatically affects search quality. Agno gives you several strategies to match your content type:

* **Fixed Size** - Splits at consistent character counts. Fast and predictable, great for uniform content
* **Semantic** - Uses embeddings to find natural topic boundaries. Best for complex docs where meaning matters
* **Recursive** - Respects document structure (paragraphs, sections). Good balance of speed and context
* **Document** - Preserves natural document divisions. Perfect for well-structured content
* **CSV Row** - Treats each row as a unit. Essential for tabular data
* **Markdown** - Honors heading hierarchy. Ideal for documentation

Learn more about [choosing the right chunking strategy](/concepts/knowledge/chunking/overview) for your use case.

## Managing Your Knowledge Base

Once content is loaded, you'll want to check status, search, and manage what's there:
```

---

## Create a Recipe Expert Agent with knowledge of Thai recipes

**URL:** llms-txt#create-a-recipe-expert-agent-with-knowledge-of-thai-recipes

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=dedent("""\
        You are a passionate and knowledgeable Thai cuisine expert! 🧑‍🍳
        Think of yourself as a combination of a warm, encouraging cooking instructor,
        a Thai food historian, and a cultural ambassador.

Follow these steps when answering questions:
        1. If the user asks a about Thai cuisine, ALWAYS search your knowledge base for authentic Thai recipes and cooking information
        2. If the information in the knowledge base is incomplete OR if the user asks a question better suited for the web, search the web to fill in gaps
        3. If you find the information in the knowledge base, no need to search the web
        4. Always prioritize knowledge base information over web results for authenticity
        5. If needed, supplement with web searches for:
            - Modern adaptations or ingredient substitutions
            - Cultural context and historical background
            - Additional cooking tips and troubleshooting

Communication style:
        1. Start each response with a relevant cooking emoji
        2. Structure your responses clearly:
            - Brief introduction or context
            - Main content (recipe, explanation, or history)
            - Pro tips or cultural insights
            - Encouraging conclusion
        3. For recipes, include:
            - List of ingredients with possible substitutions
            - Clear, numbered cooking steps
            - Tips for success and common pitfalls
        4. Use friendly, encouraging language

Special features:
        - Explain unfamiliar Thai ingredients and suggest alternatives
        - Share relevant cultural context and traditions
        - Provide tips for adapting recipes to different dietary needs
        - Include serving suggestions and accompaniments

End each response with an uplifting sign-off like:
        - 'Happy cooking! ขอให้อร่อย (Enjoy your meal)!'
        - 'May your Thai cooking adventure bring joy!'
        - 'Enjoy your homemade Thai feast!'

Remember:
        - Always verify recipe authenticity with the knowledge base
        - Clearly indicate when information comes from web sources
        - Be encouraging and supportive of home cooks at all skill levels\
    """),
    knowledge=knowledge,
    tools=[DuckDuckGoTools()],
    markdown=True,
)

agent.print_response(
    "How do I make chicken and galangal in coconut milk soup", stream=True
)
agent.print_response("What is the history of Thai curry?", stream=True)
agent.print_response("What ingredients do I need for Pad Thai?", stream=True)

---

## Initialize AgentOps

**URL:** llms-txt#initialize-agentops

---

## Setup our AgentOS with MCP enabled

**URL:** llms-txt#setup-our-agentos-with-mcp-enabled

**Contents:**
- Define a local test client

agent_os = AgentOS(
    description="Example app with MCP enabled",
    agents=[web_research_agent],
    enable_mcp_server=True,  # This enables a LLM-friendly MCP server at /mcp
)

app = agent_os.get_app()

if __name__ == "__main__":
    """Run your AgentOS.

You can see view your LLM-friendly MCP server at:
    http://localhost:7777/mcp

"""
    agent_os.serve(app="enable_mcp_example:app")
python test_client.py theme={null}
import asyncio

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.mcp import MCPTools

**Examples:**

Example 1 (unknown):
```unknown
## Define a local test client
```

---

## Filter by metadata

**URL:** llms-txt#filter-by-metadata

**Contents:**
- Next Steps

knowledge.add_content(
    path="docs/",
    filters={"department": "engineering", "clearance": "public"}
)
```

<CardGroup cols={2}>
  <Card title="Content Types" icon="file-lines" href="/concepts/knowledge/content_types">
    Learn about different ways to add information to your knowledge base
  </Card>

<Card title="Search & Retrieval" icon="magnifying-glass" href="/concepts/knowledge/core-concepts/search-retrieval">
    Understand how agents find and use information
  </Card>

<Card title="Readers" icon="book-open" href="/concepts/knowledge/readers">
    Explore content parsing and ingestion options
  </Card>

<Card title="Chunking" icon="scissors" href="/concepts/knowledge/chunking/overview">
    Optimize how content is broken down for search
  </Card>
</CardGroup>

---

## Cancel Agent Run

**URL:** llms-txt#cancel-agent-run

Source: https://docs.agno.com/reference-api/schema/agents/cancel-agent-run

post /agents/{agent_id}/runs/{run_id}/cancel
Cancel a currently executing agent run. This will attempt to stop the agent's execution gracefully.

**Note:** Cancellation may not be immediate for all operations.

---

## Async Streaming Agent

**URL:** llms-txt#async-streaming-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/xai/basic_async_stream

```python cookbook/models/xai/basic_async_stream.py theme={null}
import asyncio
from typing import Iterator

from agno.agent import Agent, RunOutputEvent
from agno.models.xai import xAI

agent = Agent(model=xAI(id="grok-3"), markdown=True)

---

## Agentic RAG with LightRAG

**URL:** llms-txt#agentic-rag-with-lightrag

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/agentic_search/lightrag/agentic_rag_with_lightrag

This example demonstrates how to implement Agentic RAG using LightRAG as the vector database, with support for PDF documents, Wikipedia content, and web URLs.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your API keys">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/agentic_search" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your API keys">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## WhatsApp Agent with User Memory

**URL:** llms-txt#whatsapp-agent-with-user-memory

**Contents:**
- Code
- Usage
- Key Features

Source: https://docs.agno.com/examples/agent-os/interfaces/whatsapp/agent_with_user_memory

Personalized WhatsApp agent that remembers user information and preferences

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set Environment Variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

* **Memory Management**: Remembers user names, hobbies, preferences, and activities
* **Google Search**: Access to current information during conversations
* **Personalized Responses**: Uses stored memories for contextualized replies
* **Friendly AI**: Acts as personal AI friend with engaging conversation
* **Gemini Powered**: Fast, intelligent responses with multimodal capabilities

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Image to Image Agent

**URL:** llms-txt#image-to-image-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/multimodal/image-to-image

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Recipe RAG Image Agent

**URL:** llms-txt#recipe-rag-image-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/tools/models/openai/rag-recipe-image

This example demonstrates a multi-modal RAG agent that uses Groq and OpenAITools to search a PDF recipe knowledge base and generate a step-by-step visual guide for recipes.

<Steps>
  <Step title="Install dependencies">
    
  </Step>

<Step title="Run the example">
    
  </Step>
</Steps>

By default, the generated image will be saved to `tmp/recipe_image.png`.

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install dependencies">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run the example">
```

---

## Create individual specialized agents

**URL:** llms-txt#create-individual-specialized-agents

researcher = Agent(
    name="Researcher",
    role="Expert at finding information",
    tools=[DuckDuckGoTools()],
    model=OpenAIChat(id="gpt-5-mini"),
)

writer = Agent(
    name="Writer",
    role="Expert at writing clear, engaging content",
    model=OpenAIChat(id="gpt-5-mini"),
)

---

## json_mode_agent.print_response("New York")

**URL:** llms-txt#json_mode_agent.print_response("new-york")

**Contents:**
- Usage

bash  theme={null}
    export GROQ_API_KEY=xxx
    bash  theme={null}
    pip install -U groq agno
    bash Mac theme={null}
      python cookbook/models/groq/structured_output.py
      bash Windows theme={null}
      python cookbook/models/groq/structured_output.py
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

## PDF Input URL Agent

**URL:** llms-txt#pdf-input-url-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/vertexai/claude/pdf_input_url

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your environment variables">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Authenticate your CLI session">
    `gcloud auth application-default login `

<Note>You dont need to authenticate your CLI every time. </Note>
  </Step>

<Step title="Install libraries">`pip install -U anthropic agno `</Step>

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set your environment variables">
    <CodeGroup>
```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Authenticate your CLI session">
    `gcloud auth application-default login `

    <Note>You dont need to authenticate your CLI every time. </Note>
  </Step>

  <Step title="Install libraries">`pip install -U anthropic agno `</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Session Caching

**URL:** llms-txt#session-caching

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/session/08_cache_session

This example demonstrates how to enable session caching in memory for faster access to session data, improving performance when working with persistent databases.

```python 08_cache_session.py theme={null}
"""Example of how to cache the session in memory for faster access."""

from agno.agent.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat

---

## Teams with Memory

**URL:** llms-txt#teams-with-memory

Source: https://docs.agno.com/concepts/teams/memory

Learn how to use teams with memory.

The team can also manage user memories, just like agents:

See more in the [Memory](/concepts/memory/overview) section.

---

## Get OS Configuration

**URL:** llms-txt#get-os-configuration

Source: https://docs.agno.com/reference-api/schema/core/get-os-configuration

get /config
Retrieve the complete configuration of the AgentOS instance, including:

- Available models and databases
- Registered agents, teams, and workflows
- Chat, session, memory, knowledge, and evaluation configurations
- Available interfaces and their routes

---

## Audio Sentiment Analysis Agent

**URL:** llms-txt#audio-sentiment-analysis-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/multimodal/audio-sentiment-analysis

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Run agent with input="Trending startups and products."

**URL:** llms-txt#run-agent-with-input="trending-startups-and-products."

response: RunOutput = agent.run(input="Trending startups and products.")

---

## Initialize the Agent with various configurations including the knowledge base and storage

**URL:** llms-txt#initialize-the-agent-with-various-configurations-including-the-knowledge-base-and-storage

agent = Agent(
    session_id="session_id",  # use any unique identifier to identify the run
    user_id="user",  # user identifier to identify the user
    model=model,
    knowledge=knowledge,
    db=db,
)

---

## When loading the knowledge base, we can attach metadata that will be used for filtering

**URL:** llms-txt#when-loading-the-knowledge-base,-we-can-attach-metadata-that-will-be-used-for-filtering

---

## Qdrant Agent Knowledge

**URL:** llms-txt#qdrant-agent-knowledge

**Contents:**
- Setup
- Example
- Qdrant Params
- Developer Resources

Source: https://docs.agno.com/concepts/vectordb/qdrant

Follow the instructions in the [Qdrant Setup Guide](https://qdrant.tech/documentation/guides/installation/) to install Qdrant locally. Here is a guide to get API keys: [Qdrant API Keys](https://qdrant.tech/documentation/cloud/authentication/).

<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      Qdrant also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>

<Tip className="mt-4">
      Using <code>aload()</code> and <code>aprint\_response()</code> with asyncio provides non-blocking operations, making your application more responsive under load.
    </Tip>
  </div>
</Card>

<Snippet file="vectordb_qdrant_params.mdx" />

## Developer Resources

* View [Cookbook (Sync)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/qdrant_db/qdrant_db.py)
* View [Cookbook (Async)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/qdrant_db/async_qdrant_db.py)

**Examples:**

Example 1 (unknown):
```unknown
<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      Qdrant also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>
```

---

## Initialize the Agent with the knowledge

**URL:** llms-txt#initialize-the-agent-with-the-knowledge

**Contents:**
- Usage
- Params

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
)

if __name__ == "__main__":
    # Comment out after first run
    asyncio.run(
        knowledge.add_content_async(
            topics=["web3 latest trends 2025"],
            reader=WebSearchReader(
                max_results=3,
                search_engine="duckduckgo",
                chunk=True,
            ),
        )
    )

# Create and use the agent
    asyncio.run(
        agent.aprint_response(
            "What are the latest AI trends according to the search results?",
            markdown=True,
        )
    )

bash  theme={null}
    pip install -U requests beautifulsoup4 agno openai
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Mac theme={null}
      python examples/concepts/knowledge/readers/web_search_reader_async.py
      bash Windows theme={null}
      python examples/concepts/knowledge/readers/web_search_reader_async.py
      ```
    </CodeGroup>
  </Step>
</Steps>

<Snippet file="web-search-reader-reference.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Set environment variables">
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

## Add from URL to the knowledge base

**URL:** llms-txt#add-from-url-to-the-knowledge-base

**Contents:**
- Custom knowledge retrieval
- Knowledge storage
  - Contents database
  - Vector databases
  - Adding contents
- Example: Agentic RAG Agent
- Developer Resources

asyncio.run(
    knowledge.add_content_async(
        name="Recipes",
        url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
        metadata={"user_tag": "Recipes from website"},
    )
)

agent = Agent(
    name="My Agent",
    description="Agno 2.0 Agent Implementation",
    knowledge=knowledge,
    search_knowledge=True,
)

agent.print_response(
    "How do I make chicken and galangal in coconut milk soup?",
    markdown=True,
)
python  theme={null}
def knowledge_retriever(agent: Agent, query: str, num_documents: Optional[int], **kwargs) -> Optional[list[dict]]:
  ...
python  theme={null}
def knowledge_retriever(agent: Agent, query: str, num_documents: Optional[int], **kwargs) -> Optional[list[dict]]:
  ...

agent = Agent(
    knowledge_retriever=knowledge_retriever,
    search_knowledge=True,
)
python  theme={null}
...
knowledge = Knowledge(
    name="Basic SDK Knowledge Base",
    description="Agno 2.0 Knowledge Implementation",
    vector_db=vector_db,
    contents_db=contents_db,
)

asyncio.run(
    knowledge.add_content_async(
        name="CV",
        path="cookbook/knowledge/testing_resources/cv_1.pdf",
        metadata={"user_tag": "Engineering Candidates"},
    )
)
bash  theme={null}
    docker run -d \
      -e POSTGRES_DB=ai \
      -e POSTGRES_USER=ai \
      -e POSTGRES_PASSWORD=ai \
      -e PGDATA=/var/lib/postgresql/data/pgdata \
      -v pgvolume:/var/lib/postgresql/data \
      -p 5532:5432 \
      --name pgvector \
      agnohq/pgvector:16
    bash Mac theme={null}
      pip install -U pgvector pypdf psycopg sqlalchemy
      bash Windows theme={null}
      pip install -U pgvector pypdf psycopg sqlalchemy
      python agentic_rag.py theme={null}
    import asyncio
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from agno.knowledge.knowledge import Knowledge
    from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

db = PostgresDb(
        db_url=db_url,
        knowledge_table="knowledge_contents",
    )

knowledge = Knowledge(
        contents_db=db,
        vector_db=PgVector(
            table_name="recipes",
            db_url=db_url,
        )
    )

agent = Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        db=db,
        knowledge=knowledge,
        markdown=True,
    )
    if __name__ == "__main__":
        asyncio.run(
            knowledge.add_content_async(
                name="Recipes",
                url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
                metadata={"user_tag": "Recipes from website"}
            )
        )
        # Create and use the agent
        asyncio.run(
            agent.aprint_response(
                "How do I make chicken and galangal in coconut milk soup?",
                markdown=True,
            )
        )
    python  theme={null}
    python agentic_rag.py
    ```
  </Step>
</Steps>

## Developer Resources

* View the [Agent schema](/reference/agents/agent)
* View the [Knowledge schema](/reference/knowledge/knowledge)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/knowledge/)

**Examples:**

Example 1 (unknown):
```unknown
We can give our agent access to the knowledge base in the following ways:

* We can set `search_knowledge=True` to add a `search_knowledge_base()` tool to the Agent. `search_knowledge` is `True` **by default** if you add `knowledge` to an Agent.
* We can set `add_knowledge_to_context=True` to automatically add references from the knowledge base to the Agent's context, based in your user message. This is the traditional RAG approach.

## Custom knowledge retrieval

If you need complete control over the knowledge base search, you can pass your own `knowledge_retriever` function with the following signature:
```

Example 2 (unknown):
```unknown
Example of how to configure an agent with a custom retriever:
```

Example 3 (unknown):
```unknown
This function is called during `search_knowledge_base()` and is used by the Agent to retrieve references from the knowledge base.

<Tip>
  Async retrievers are supported. Simply create an async function and pass it to
  the `knowledge_retriever` parameter.
</Tip>

## Knowledge storage

Knowledge content is tracked in a "Contents DB" and vectorized and stored in a "Vector DB".

### Contents database

The Contents DB is a database that stores the name, description, metadata and other information for any content you add to the knowledge base.

Below is the schema for the Contents DB:

| Field            | Type   | Description                                                                                         |
| ---------------- | ------ | --------------------------------------------------------------------------------------------------- |
| `id`             | `str`  | The unique identifier for the knowledge content.                                                    |
| `name`           | `str`  | The name of the knowledge content.                                                                  |
| `description`    | `str`  | The description of the knowledge content.                                                           |
| `metadata`       | `dict` | The metadata for the knowledge content.                                                             |
| `type`           | `str`  | The type of the knowledge content.                                                                  |
| `size`           | `int`  | The size of the knowledge content. Applicable only to files.                                        |
| `linked_to`      | `str`  | The ID of the knowledge content that this content is linked to.                                     |
| `access_count`   | `int`  | The number of times this content has been accessed.                                                 |
| `status`         | `str`  | The status of the knowledge content.                                                                |
| `status_message` | `str`  | The message associated with the status of the knowledge content.                                    |
| `created_at`     | `int`  | The timestamp when the knowledge content was created.                                               |
| `updated_at`     | `int`  | The timestamp when the knowledge content was last updated.                                          |
| `external_id`    | `str`  | The external ID of the knowledge content. Used when external vector stores are used, like LightRAG. |

This data is best displayed on the [knowledge page of the AgentOS UI](https://os.agno.com/knowledge).

### Vector databases

Vector databases offer the best solution for retrieving relevant results from dense information quickly.

### Adding contents

The typical way content is processed when being added to the knowledge base is:

<Steps>
  <Step title="Parse the content">
    A reader is used to parse the content based on the type of content that is
    being inserted
  </Step>

  <Step title="Chunk the information">
    The content is broken down into smaller chunks to ensure our search query
    returns only relevant results.
  </Step>

  <Step title="Embed each chunk">
    The chunks are converted into embedding vectors and stored in a vector
    database.
  </Step>
</Steps>

For example, to add a PDF to the knowledge base:
```

Example 4 (unknown):
```unknown
<Tip>
  See more details on [Loading the Knowledge
  Base](/concepts/knowledge/overview#loading-the-knowledge).
</Tip>

<Note>
  Knowledge filters are currently supported on the following knowledge base
  types: <b>PDF</b>, <b>PDF\_URL</b>, <b>Text</b>, <b>JSON</b>, and <b>DOCX</b>.
  For more details, see the [Knowledge Filters
  documentation](/concepts/knowledge/filters/overview).
</Note>

## Example: Agentic RAG Agent

Let's build a **RAG Agent** that answers questions from a PDF.

<Steps>
  <Step title="Set up the database">
    Let's use `Postgres` as both our contents and vector databases.

    Install [docker desktop](https://docs.docker.com/desktop/install/mac-install/) and run **Postgres** on port **5532** using:
```

---

## Zep Async Memory Tools

**URL:** llms-txt#zep-async-memory-tools

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/tools/database/zep_async

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API keys">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Teams with Knowledge

**URL:** llms-txt#teams-with-knowledge

Source: https://docs.agno.com/concepts/teams/knowledge

Learn how to use teams with knowledge bases.

Teams can use a knowledge base to store and retrieve information, just like agents:

```python  theme={null}
from pathlib import Path

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.lancedb import LanceDb

---

## List Memories

**URL:** llms-txt#list-memories

Source: https://docs.agno.com/reference-api/schema/memory/list-memories

get /memories
Retrieve paginated list of user memories with filtering and search capabilities. Filter by user, agent, team, topics, or search within memory content.

---

## Response Synthesizer Agent - Specialized in creating comprehensive responses

**URL:** llms-txt#response-synthesizer-agent---specialized-in-creating-comprehensive-responses

response_synthesizer = Agent(
    name="Response Synthesizer",
    model=Claude(id="claude-3-7-sonnet-latest"),
    role="Create comprehensive final response with proper citations",
    instructions=[
        "Synthesize information from team members into a comprehensive response.",
        "Include proper source citations and references.",
        "Ensure accuracy and completeness of the final answer.",
        "Structure the response clearly with appropriate formatting.",
    ],
    markdown=True,
)

---

## Add from local file to the knowledge base

**URL:** llms-txt#add-from-local-file-to-the-knowledge-base

asyncio.run(
    knowledge.add_content_async(
        name="CV",
        path="cookbook/knowledge/testing_resources/cv_1.pdf",
        metadata={"user_tag": "Engineering Candidates"},
        skip_if_exists=True,  # True by default
    )
)

---

## Weaviate Agent Knowledge

**URL:** llms-txt#weaviate-agent-knowledge

**Contents:**
- Setup
- Example

Source: https://docs.agno.com/concepts/vectordb/weaviate

Follow steps mentioned in [Weaviate setup guide](https://weaviate.io/developers/weaviate/quickstart) to setup Weaviate.

Install weaviate packages

```python agent_with_knowledge.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.search import SearchType
from agno.vectordb.weaviate import Distance, VectorIndex, Weaviate

vector_db = Weaviate(
    collection="recipes",
    search_type=SearchType.hybrid,
    vector_index=VectorIndex.HNSW,
    distance=Distance.COSINE,
    local=True,  # Set to False if using Weaviate Cloud and True if using local instance
)

**Examples:**

Example 1 (unknown):
```unknown
Run weaviate
```

Example 2 (unknown):
```unknown
or
```

Example 3 (unknown):
```unknown
## Example
```

---

## VectorDB controls search strategy; Knowledge controls retrieval size

**URL:** llms-txt#vectordb-controls-search-strategy;-knowledge-controls-retrieval-size

**Contents:**
- Making Search Work Better
  - Add Rich Metadata
  - Use Descriptive Filenames
  - Structure Content Logically
  - Test with Real Queries
  - Analyze What's Being Retrieved
- Advanced Search Features
  - Custom Retrieval Logic for Agents
  - Search with Filtering
  - Working with Different Content Types

vector_db = PgVector(table_name="embeddings_table", db_url=db_url, search_type=SearchType.hybrid)
knowledge = Knowledge(vector_db=vector_db, max_results=5)
python  theme={null}
knowledge.add_content(
    path="policies/",
    metadata={"type": "policy", "department": "HR", "audience": "employees"},
)
python  theme={null}
"hr_employee_handbook_2024.pdf"  # ✅ Clear and descriptive
"document1.pdf"                  # ❌ Generic and unhelpful
python  theme={null}
test_queries = [
    "What's our vacation policy?",
    "How do I submit expenses?",
    "Remote work guidelines",
]

for q in test_queries:
    results = knowledge.search(q)
    print(q, "->", results[0].content[:100] + "..." if results else "No results")
python  theme={null}
async def my_retriever(query: str, num_documents: int = 5, filters: dict | None = None, **kwargs):
    # Example: reformulate query, then search with metadata filters
    refined = query.replace("vacation", "paid time off")
    docs = await knowledge.async_search(refined, max_results=num_documents, filters=filters)
    return [d.to_dict() for d in docs]

agent.knowledge_retriever = my_retriever
python  theme={null}
results = knowledge.search(
    "deployment process",
    filters={"department": "engineering", "type": "documentation"},
)
python  theme={null}
from agno.knowledge.reader.pdf_reader import PdfReader

**Examples:**

Example 1 (unknown):
```unknown
## Making Search Work Better

### Add Rich Metadata

Metadata helps filter and organize results:
```

Example 2 (unknown):
```unknown
### Use Descriptive Filenames

File names can help with search relevance in some backends:
```

Example 3 (unknown):
```unknown
### Structure Content Logically

Well-organized content searches better:

* Use clear headings and sections
* Include relevant terminology naturally (don't keyword-stuff)
* Add summaries at the top of long documents
* Cross-reference related topics

### Test with Real Queries

The best way to know if search is working? Try it with actual questions:
```

Example 4 (unknown):
```unknown
### Analyze What's Being Retrieved

Ask yourself:

* Are results actually relevant to the query?
* Is important information missing from results?
* Are results in a sensible order? (If not, try adding a reranker)
* Should you adjust chunk sizes or metadata?

## Advanced Search Features

### Custom Retrieval Logic for Agents

Provide a `knowledge_retriever` callable to implement your own decisioning (e.g., reformulation, follow-up searches, domain rules). The agent will call this when fetching documents.
```

---

## AgentQL

**URL:** llms-txt#agentql

**Contents:**
- Prerequisites
- Example
- Toolkit Params
- Toolkit Functions
- Developer Resources

Source: https://docs.agno.com/concepts/tools/toolkits/web_scrape/agentql

**AgentQLTools** enable an Agent to browse and scrape websites using the AgentQL API.

The following example requires the `agentql` library and an API token which can be obtained from [AgentQL](https://agentql.com/).

The following agent will open a web browser and scrape all the text from the page.

<Note>
  AgentQL will open up a browser instance (don't close it) and do scraping on
  the site.
</Note>

| Parameter                      | Type   | Default | Description                                       |
| ------------------------------ | ------ | ------- | ------------------------------------------------- |
| `api_key`                      | `str`  | `None`  | API key for AgentQL                               |
| `scrape`                       | `bool` | `True`  | Whether to use the scrape text tool               |
| `agentql_query`                | `str`  | `None`  | Custom AgentQL query                              |
| `enable_scrape_website`        | `bool` | `True`  | Enable the scrape\_website functionality.         |
| `enable_custom_scrape_website` | `bool` | `True`  | Enable the custom\_scrape\_website functionality. |
| `all`                          | `bool` | `False` | Enable all functionality.                         |

| Function                | Description                                          |
| ----------------------- | ---------------------------------------------------- |
| `scrape_website`        | Used to scrape all text from a web page              |
| `custom_scrape_website` | Uses the custom `agentql_query` to scrape a web page |

## Developer Resources

* View [Tools](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/agentql.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/agentql_tools.py)

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown
## Example

The following agent will open a web browser and scrape all the text from the page.
```

---

## Agent that returns a structured output

**URL:** llms-txt#agent-that-returns-a-structured-output

structured_output_agent = Agent(
    model=xAI(id="grok-2-latest"),
    description="You write movie scripts.",
    output_schema=MovieScript,
)

---

## Create the vector database

**URL:** llms-txt#create-the-vector-database

**Contents:**
- Usage

vector_db = LanceDb(
    table_name="recipes",  # Table name in the vector database
    uri=db_url,  # Location to initiate/create the vector database
    embedder=embedder,  # Without using this, it will use OpenAIChat embeddings by default
)

knowledge = Knowledge(
    vector_db=vector_db,
)

knowledge.add_content(
    name="Recipes", url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"
)

db = SqliteDb(db_file="data.db")

agent = Agent(
    session_id="session_id", 
    user_id="user",  
    model=model,
    knowledge=knowledge,
    db=db,
)

agent.print_response(
    "What is the first step of making Gluai Buat Chi from the knowledge base?",
    markdown=True,
)
bash  theme={null}
    pip install -U lancedb sqlalchemy agno
    bash Mac theme={null}
      python cookbook/agents/rag/rag_with_lance_db_and_sqlite.py
      bash Windows theme={null}
      python cookbook/agents/rag/rag_with_lance_db_and_sqlite.py
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

  <Step title="Install Ollama">
    Follow the installation instructions at [Ollama's website](https://ollama.ai)
  </Step>

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## RAG Agent

**URL:** llms-txt#rag-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/ibm/knowledge

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Set up PostgreSQL with pgvector">
    You need a PostgreSQL database with the pgvector extension installed. Adjust the `db_url` in the code to match your database configuration.
  </Step>

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="For subsequent runs">
    After the first run, comment out the `knowledge_base.load(recreate=True)` line to avoid reloading the PDF.
  </Step>
</Steps>

This example shows how to integrate a knowledge base with IBM WatsonX. It loads a PDF from a URL, processes it into a vector database (PostgreSQL with pgvector in this case), and then creates an agent that can query this knowledge base.

Note: You need to install several packages (`pgvector`, `pypdf`, etc.) and have a PostgreSQL database with the pgvector extension available.

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

  <Step title="Set up PostgreSQL with pgvector">
    You need a PostgreSQL database with the pgvector extension installed. Adjust the `db_url` in the code to match your database configuration.
  </Step>

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## run: RunOutput = agent.run("write a two sentence horror story")

**URL:** llms-txt#run:-runoutput-=-agent.run("write-a-two-sentence-horror-story")

---

## Wikipedia

**URL:** llms-txt#wikipedia

**Contents:**
- Prerequisites
- Example
- Toolkit Params
- Toolkit Functions
- Developer Resources

Source: https://docs.agno.com/concepts/tools/toolkits/search/wikipedia

**WikipediaTools** enable an Agent to search wikipedia a website and add its contents to the knowledge base.

The following example requires the `wikipedia` library.

The following agent will run seach wikipedia for "ai" and print the response.

| Name        | Type        | Default | Description                                                                                                        |
| ----------- | ----------- | ------- | ------------------------------------------------------------------------------------------------------------------ |
| `knowledge` | `Knowledge` | -       | The knowledge base associated with Wikipedia, containing various data and resources linked to Wikipedia's content. |
| `all`       | `bool`      | `False` | Enable all functionality.                                                                                          |

| Function Name                                | Description                                                                                            |
| -------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| `search_wikipedia_and_update_knowledge_base` | This function searches wikipedia for a topic, adds the results to the knowledge base and returns them. |
| `search_wikipedia`                           | Searches Wikipedia for a query.                                                                        |

## Developer Resources

* View [Tools](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/wikipedia.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/wikipedia_tools.py)

**Examples:**

Example 1 (unknown):
```unknown
## Example

The following agent will run seach wikipedia for "ai" and print the response.
```

---

## Create an agent with ReasoningTools

**URL:** llms-txt#create-an-agent-with-reasoningtools

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[ReasoningTools(add_instructions=True)],
    instructions=dedent("""\
        You are an expert problem-solving assistant with strong analytical skills! 🧠
        Use step-by-step reasoning to solve the problem.
        \
    """),
)

---

## Async Filtering

**URL:** llms-txt#async-filtering

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/async-filtering

```python  theme={null}
import asyncio

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.lancedb import LanceDb

---

## Singlestore for Agent

**URL:** llms-txt#singlestore-for-agent

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/db/singlestore/singlestore_for_agent

Agno supports using Singlestore as a storage backend for Agents using the `SingleStoreDb` class.

Obtain the credentials for Singlestore from [here](https://portal.singlestore.com/)

```python singlestore_for_agent.py theme={null}
from os import getenv

from agno.agent import Agent
from agno.db.singlestore.singlestore import SingleStoreDb
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Memory Tools

**URL:** llms-txt#memory-tools

**Contents:**
- Example

Source: https://docs.agno.com/concepts/tools/reasoning_tools/memory-tools

The `MemoryTools` toolkit enables Agents to manage user memories through create, update, and delete operations. This toolkit integrates with a provided database where memories are stored.

The toolkit implements a "Think → Operate → Analyze" cycle that allows an Agent to:

1. Think through memory management requirements and plan operations
2. Execute memory operations (add, update, delete) on the database
3. Analyze the results to ensure operations completed successfully and meet requirements

This approach gives Agents the ability to persistently store, retrieve, and manage user information, preferences, and context across conversations.

The toolkit includes the following tools:

* `think`: A scratchpad for planning memory operations, brainstorming content, and refining approaches. These thoughts remain internal to the Agent and are not shown to users.
* `get_memories`: Gets a list of memories for the current user from the database.
* `add_memory`: Creates new memories in the database with specified content and optional topics.
* `update_memory`: Modifies existing memories by memory ID, allowing updates to content and topics.
* `delete_memory`: Removes memories from the database by memory ID.
* `analyze`: Evaluates whether memory operations completed successfully and produced the expected results.

Here's an example of how to use the `MemoryTools` toolkit:

```python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.memory import MemoryTools

---

## memories = agent.get_user_memories(user_id=john_doe_id)

**URL:** llms-txt#memories-=-agent.get_user_memories(user_id=john_doe_id)

---

## Video Caption Agent

**URL:** llms-txt#video-caption-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/multimodal/video-caption

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## structured_output_response: RunOutput = structured_output_agent.arun("New York")

**URL:** llms-txt#structured_output_response:-runoutput-=-structured_output_agent.arun("new-york")

---

## Gathering Multiple Async Agents

**URL:** llms-txt#gathering-multiple-async-agents

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/async/gather_agents

This example demonstrates how to run multiple async agents concurrently using asyncio.gather() to generate research reports on different AI providers simultaneously.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/async" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## ************* Create AgentOS *************

**URL:** llms-txt#*************-create-agentos-*************

agent_os = AgentOS(agents=[agno_agent])
app = agent_os.get_app()

---

## ContentsDB is required for AgentOS Knowledge page

**URL:** llms-txt#contentsdb-is-required-for-agentos-knowledge-page

contents_db = PostgresDb(
    db_url="postgresql+psycopg://user:pass@localhost:5432/db"
)

vector_db = PgVector(table_name="vectors", db_url="http://my-postgress:5432")

knowledge = Knowledge(
    vector_db=vector_db,
    contents_db=contents_db  # Must be provided for AgentOS
)

knowledge_agent = Agent(
    name="Knowledge Agent",
    knowledge=knowledge
)

---

## Create an AI Voice Interaction Agent

**URL:** llms-txt#create-an-ai-voice-interaction-agent

agent = Agent(
    model=OpenAIChat(
        id="gpt-5-mini-audio-preview",
        modalities=["text", "audio"],
        audio={"voice": "sage", "format": "wav"},
    ),
    description=dedent("""\
        You are an expert in audio processing and voice interaction, capable of understanding
        and analyzing spoken content while providing natural, engaging voice responses.
        You excel at comprehending context, emotion, and nuance in speech.\
    """),
    instructions=dedent("""\
        As a voice interaction specialist, follow these guidelines:
        1. Listen carefully to audio input to understand both content and context
        2. Provide clear, concise responses that address the main points
        3. When generating voice responses, maintain a natural, conversational tone
        4. Consider the speaker's tone and emotion in your analysis
        5. If the audio is unclear, ask for clarification

Focus on creating engaging and helpful voice interactions!\
    """),
)

---

## Define agents

**URL:** llms-txt#define-agents

hackernews_agent = Agent(
    name="Hackernews Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[HackerNewsTools()],
    role="Extract key insights and content from Hackernews posts",
)
web_agent = Agent(
    name="Web Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    role="Search the web for the latest news and trends",
)

---

## Setup your Agent with the database

**URL:** llms-txt#setup-your-agent-with-the-database

---

## Finance Agent: Gets financial data using YFinance tools

**URL:** llms-txt#finance-agent:-gets-financial-data-using-yfinance-tools

finance_agent = Agent(
    name="Finance Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[YFinanceTools()],
    instructions="Use tables to display data",
    markdown=True,
)

---

## Run the Agent

**URL:** llms-txt#run-the-agent

**Contents:**
- Knowledge Tools
- Memory Tools

reasoning_agent.print_response(
    "What are the fastest cars in the market? Only the report, no other text.",
    stream=True,
    show_full_reasoning=True,
    stream_events=True,
)
python knowledge_tools.py theme={null}
import os
from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.tools.knowledge import KnowledgeTools
from agno.vectordb.lancedb import LanceDb, SearchType

agno_docs = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

knowledge_tools = KnowledgeTools(
    knowledge=agno_docs,
    think=True,
    search=True,
    analyze=True,
    add_few_shot=True,
)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[knowledge_tools],
    markdown=True,
)

agno_docs.add_content(
    url="https://docs.agno.com/llms-full.txt"
)

agent.print_response("How do I build multi-agent teams with Agno?", stream=True)
python memory_tools.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.memory import MemoryTools

**Examples:**

Example 1 (unknown):
```unknown
See the [Reasoning Tools](/concepts/tools/reasoning_tools/reasoning-tools) documentation for more details.

## Knowledge Tools

The Knowledge Tools take the Reasoning Tools one step further by allowing the Agent to **search** a knowledge base and **analyze** the results of their actions.

**KnowledgeTools = `think` + `search` + `analyze`**
```

Example 2 (unknown):
```unknown
See the [Knowledge Tools](/concepts/tools/reasoning_tools/knowledge-tools) documentation for more details.

## Memory Tools

The Memory Tools allow the Agent to use memories to reason about the question and work through it step by step.
```

---

## Create an agent with Zoom capabilities

**URL:** llms-txt#create-an-agent-with-zoom-capabilities

agent = Agent(tools=[zoom_tools])

---

## Agentic Memory

**URL:** llms-txt#agentic-memory

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/memory/02-agentic-memory

This example shows you how to use persistent memory with an Agent.

During each run the Agent can create/update/delete user memories.

To enable this, set `enable_agentic_memory=True` in the Agent config.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Setup team with in-memory database

**URL:** llms-txt#setup-team-with-in-memory-database

**Contents:**
- Developer Resources

db = InMemoryDb()
team = Team(
    name="Research Team",
    members=[hn_researcher, web_searcher],
    db=db,
)

team.print_response("Find top AI news")
```

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/db/in_memory/in_memory_storage_for_team.py)

---

## Agent with Image Input

**URL:** llms-txt#agent-with-image-input

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/aws/bedrock/image_agent

AWS Bedrock supports image input with models like `amazon.nova-pro-v1:0`. You can use this to analyze images and get information about them.

```python cookbook/models/aws/bedrock/image_agent.py theme={null}
from pathlib import Path
from agno.agent import Agent
from agno.media import Image
from agno.models.aws import AwsBedrock
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=AwsBedrock(id="amazon.nova-pro-v1:0"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

image_path = Path(__file__).parent.joinpath("sample.jpg")

---

## First agent for article summarization

**URL:** llms-txt#first-agent-for-article-summarization

article_agent = Agent(
    name="Article Summarization Agent",
    role="Summarize articles from URLs",
    id="article-summarizer",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[Newspaper4kTools()],
    instructions=[
        "You are a content summarization specialist.",
        "Extract key information from articles and create concise summaries.",
        "Focus on main points, facts, and insights.",
    ],
)

---

## Update Memory

**URL:** llms-txt#update-memory

Source: https://docs.agno.com/reference-api/schema/memory/update-memory

patch /memories/{memory_id}
Update an existing user memory's content and topics. Replaces the entire memory content and topic list with the provided values.

---

## Chat Interface

**URL:** llms-txt#chat-interface

**Contents:**
- Overview
- Chat Interfaces
  - Chat with an Agent
  - Work with a Team
  - Run a Workflow
- Troubleshooting
- Related Examples

Source: https://docs.agno.com/agent-os/features/chat-interface

Use AgentOS chat to talk to agents, collaborate with teams, and run workflows

The AgentOS chat is the home for day‑to‑day work with your AI system. From one screen you can:

* Chat with individual agents
* Collaborate with agent teams
* Trigger and monitor workflows
* Review sessions, knowledge, memory, and metrics

It’s designed to feel familiar—type a message, attach files, and get live, streaming responses. Each agent, team, and workflow maintains its own context so you can switch between tasks without losing your place.

### Chat with an Agent

* Select an agent from the right panel.
* Ask a question like “What tools do you have access to?”
* Agents keep their own history, tools, and instructions; switching agents won’t mix contexts.

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/MMgohmDbM-qeNPya/videos/agentos-agent-chat.mp4?fit=max&auto=format&n=MMgohmDbM-qeNPya&q=85&s=45ae6af616b33280bc431ff63f77cabb" type="video/mp4" data-path="videos/agentos-agent-chat.mp4" />
  </video>
</Frame>

<Info>
  **Learn more about Agents**: Dive deeper into agent configuration, tools,
  memory, and advanced features in our [Agents
  Documentation](/concepts/agents/overview).
</Info>

* Switch the top toggle to Teams and pick a team.
* A team delegates tasks to its members and synthesizes their responses into a cohesive response.
* Use the chat stream to watch how the team divides and solves the task.

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/CnjZpOWVs1q9bnAO/videos/agentos-teams-chat.mp4?fit=max&auto=format&n=CnjZpOWVs1q9bnAO&q=85&s=b9b6e4ba67bcf79396cef64c58ff7e9a" type="video/mp4" data-path="videos/agentos-teams-chat.mp4" />
  </video>
</Frame>

<Info>
  **Learn more about Teams**: Explore team modes, coordination strategies, and
  multi-agent collaboration in our [Teams
  Documentation](/concepts/teams/overview).
</Info>

* Switch to Workflows and choose one.
* Provide the input (plain text or structured, depending on the workflow).
* Watch execution live: steps stream as they start, produce output, and finish.

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/CnjZpOWVs1q9bnAO/videos/agentos-workflows-chat.mp4?fit=max&auto=format&n=CnjZpOWVs1q9bnAO&q=85&s=6bfc2fbab99d64e53129e80b49a6be8e" type="video/mp4" data-path="videos/agentos-workflows-chat.mp4" />
  </video>
</Frame>

<Info>
  **Learn more about Workflows**: Discover workflow types, advanced patterns,
  and automation strategies in our [Workflows
  Documentation](/concepts/workflows/overview).
</Info>

* The page loads but nothing responds: verify your AgentOS app is running.
* Can’t see previous chats: you may be in a new session—open the Sessions panel and pick an older one.
* File didn’t attach: try a common format (png, jpg, pdf, csv, docx, txt, mp3, mp4) and keep size reasonable.

<CardGroup cols={2}>
  <Card title="Demo AgentOS" icon="play" href="/examples/agent-os/demo">
    Comprehensive demo with agents, knowledge, and evaluation system
  </Card>

<Card title="Advanced Demo" icon="rocket" href="/examples/agent-os/demo">
    Advanced demo with knowledge, storage, and multiple agents
  </Card>

<Card title="Slack Interface" icon="slack" href="/examples/agent-os/interfaces/slack/basic">
    Deploy agents to Slack channels
  </Card>

<Card title="WhatsApp Interface" icon="message" href="/examples/agent-os/interfaces/whatsapp/basic">
    Connect agents to WhatsApp messaging
  </Card>
</CardGroup>

---

## List All Teams

**URL:** llms-txt#list-all-teams

Source: https://docs.agno.com/reference-api/schema/teams/list-all-teams

get /teams
Retrieve a comprehensive list of all teams configured in this OS instance.

**Returns team information including:**
- Team metadata (ID, name, description, execution mode)
- Model configuration for team coordination
- Team member roster with roles and capabilities
- Knowledge sharing and memory configurations

---

## Web Extraction Agent

**URL:** llms-txt#web-extraction-agent

**Contents:**
  - Key Capabilities
  - Use Cases
- Code
- Usage

Source: https://docs.agno.com/examples/use-cases/agents/web_extraction_agent

This agent demonstrates how to build an intelligent web scraper that can extract comprehensive, structured information from any webpage. Using OpenAI's GPT-4 model and the Firecrawl tool, it transforms raw web content into organized, actionable data.

* **Page Metadata Extraction**: Captures title, description, and key features
* **Content Section Parsing**: Identifies and extracts main content with headings
* **Link Discovery**: Finds important related pages and resources
* **Contact Information**: Locates contact details when available
* **Contextual Metadata**: Gathers additional site information for context

* **Research & Analysis**: Quickly gather information from multiple web sources
* **Competitive Intelligence**: Monitor competitor websites and features
* **Content Monitoring**: Track changes and updates on specific pages
* **Knowledge Base Building**: Extract structured data for documentation
* **Data Collection**: Gather information for market research or analysis

The agent outputs structured data in a clean, organized format that makes web content easily digestible and actionable. It's particularly useful when you need to process large amounts of web content quickly and consistently.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Create Knowledge Instance with Weaviate

**URL:** llms-txt#create-knowledge-instance-with-weaviate

knowledge = Knowledge(
    name="Basic SDK Knowledge Base",
    description="Agno 2.0 Knowledge Implementation with Weaviate",
    vector_db=vector_db,
)

knowledge.add_content(
    name="Recipes",
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
    metadata={"doc_type": "recipe_book"},
    skip_if_exists=True,
)

---

## Create an Agent with the AWSLambdaTool

**URL:** llms-txt#create-an-agent-with-the-awslambdatool

agent = Agent(
    tools=[AWSLambdaTools(region_name="us-east-1")],
    name="AWS Lambda Agent",
    )

---

## Image File Input Agent

**URL:** llms-txt#image-file-input-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/mistral/image_file_input_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Postgres for Agent

**URL:** llms-txt#postgres-for-agent

**Contents:**
- Usage
  - Run PgVector
- Params
- Developer Resources

Source: https://docs.agno.com/examples/concepts/db/postgres/postgres_for_agent

Agno supports using PostgreSQL as a storage backend for Agents using the `PostgresDb` class.

Install [docker desktop](https://docs.docker.com/desktop/install/mac-install/) and run **PgVector** on port **5532** using:

<Snippet file="db-postgres-params.mdx" />

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/db/postgres/postgres_for_agent.py)

**Examples:**

Example 1 (unknown):
```unknown

```

---

## Create knowledge base

**URL:** llms-txt#create-knowledge-base

**Contents:**
- Usage

knowledge = Knowledge(
    vector_db=vector_db,
)

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
)

if __name__ == "__main__":
    # Comment out after first run
    asyncio.run(
        knowledge.add_content_async(
            name="Recipes",
            url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
        )
    )

# Create and use the agent
    asyncio.run(agent.aprint_response("How to make Tom Kha Gai", markdown=True))
bash  theme={null}
    pip install -U weaviate-client pypdf openai agno
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Weaviate Cloud theme={null}
      # 1. Create account at https://console.weaviate.cloud/
      # 2. Create a cluster and copy the "REST endpoint" and "Admin" API Key
      # 3. Set environment variables:
      export WCD_URL="your-cluster-url" 
      export WCD_API_KEY="your-api-key"
      # 4. Set local=False in the code
      bash Local Development theme={null}
      # 1. Install Docker from https://docs.docker.com/get-docker/
      # 2. Run Weaviate locally:
      docker run -d \
          -p 8080:8080 \
          -p 50051:50051 \
          --name weaviate \
          cr.weaviate.io/semitechnologies/weaviate:1.28.4
      # 3. Set local=True in the code
      bash Mac theme={null}
      python cookbook/knowledge/vector_db/weaviate_db/async_weaviate_db.py
      bash Windows theme={null}
      python cookbook/knowledge/vector_db/weaviate_db/async_weaviate_db.py
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

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Setup Weaviate">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Social Media Agent

**URL:** llms-txt#social-media-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/use-cases/agents/social_media_agent

Social Media Agent Example with Dummy Dataset

This example demonstrates how to create an agent that:

1. Analyzes a dummy dataset of tweets
2. Leverages LLM capabilities to perform sophisticated sentiment analysis
3. Provides insights about the overall sentiment around a topic

```python cookbook/examples/agents/social_media_agent.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.x import XTools

---

## MongoDB Agent Knowledge

**URL:** llms-txt#mongodb-agent-knowledge

**Contents:**
- Setup
- Example

Source: https://docs.agno.com/concepts/vectordb/mongodb

Follow the instructions in the [MongoDB Setup Guide](https://www.mongodb.com/docs/atlas/getting-started/) to get connection string

Install MongoDB packages

```python agent_with_knowledge.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.mongodb import MongoDb

**Examples:**

Example 1 (unknown):
```unknown
## Example
```

---

## Create an Agent with the DALL-E tool

**URL:** llms-txt#create-an-agent-with-the-dall-e-tool

**Contents:**
- Usage

agent = Agent(
    tools=[DalleTools()],
    name="DALL-E Image Generator",
    add_history_to_context=True,
    db=SqliteDb(db_file="tmp/test.db"),
)

agent.print_response(
    "Generate an image of a Siamese white furry cat sitting on a couch?",
    markdown=True,
)

agent.print_response(
    "Which type of animal and the breed are we talking about?", markdown=True
)
bash  theme={null}
    pip install -U openai agno
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch agent_using_multimodal_tool_response_in_runs.py
    bash Mac theme={null}
      python agent_using_multimodal_tool_response_in_runs.py
      bash Windows theme={null}
      python agent_using_multimodal_tool_response_in_runs.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/multimodal" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## 10-message conversation where agent updates memory 7 times:

**URL:** llms-txt#10-message-conversation-where-agent-updates-memory-7-times:

---

## Agent with Ollama Parser Model

**URL:** llms-txt#agent-with-ollama-parser-model

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/parser_model_ollama

This example demonstrates how to use an Ollama model as a parser for structured output, combining different models for generation and parsing.

```python parser_model_ollama.py theme={null}
import random
from typing import List

from agno.agent import Agent, RunOutput
from agno.models.ollama import Ollama
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from rich.pretty import pprint

class NationalParkAdventure(BaseModel):
    park_name: str = Field(..., description="Name of the national park")
    best_season: str = Field(
        ...,
        description="Optimal time of year to visit this park (e.g., 'Late spring to early fall')",
    )
    signature_attractions: List[str] = Field(
        ...,
        description="Must-see landmarks, viewpoints, or natural features in the park",
    )
    recommended_trails: List[str] = Field(
        ...,
        description="Top hiking trails with difficulty levels (e.g., 'Angel's Landing - Strenuous')",
    )
    wildlife_encounters: List[str] = Field(
        ..., description="Animals visitors are likely to spot, with viewing tips"
    )
    photography_spots: List[str] = Field(
        ...,
        description="Best locations for capturing stunning photos, including sunrise/sunset spots",
    )
    camping_options: List[str] = Field(
        ..., description="Available camping areas, from primitive to RV-friendly sites"
    )
    safety_warnings: List[str] = Field(
        ..., description="Important safety considerations specific to this park"
    )
    hidden_gems: List[str] = Field(
        ..., description="Lesser-known spots or experiences that most visitors miss"
    )
    difficulty_rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Overall park difficulty for average visitor (1=easy, 5=very challenging)",
    )
    estimated_days: int = Field(
        ...,
        ge=1,
        le=14,
        description="Recommended number of days to properly explore the park",
    )
    special_permits_needed: List[str] = Field(
        default=[],
        description="Any special permits or reservations required for certain activities",
    )

agent = Agent(
    model=OpenAIChat(id="o3"),
    description="You help people plan amazing national park adventures and provide detailed park guides.",
    output_schema=NationalParkAdventure,
    parser_model=Ollama(id="Osmosis/Osmosis-Structure-0.6B"),
)

national_parks = [
    "Yellowstone National Park",
    "Yosemite National Park",
    "Grand Canyon National Park",
    "Zion National Park",
    "Grand Teton National Park",
    "Rocky Mountain National Park",
    "Acadia National Park",
    "Mount Rainier National Park",
    "Great Smoky Mountains National Park",
    "Rocky National Park",
]

---

## MCP enabled AgentOS

**URL:** llms-txt#mcp-enabled-agentos

Source: https://docs.agno.com/agent-os/mcp/mcp

Learn how to enable MCP functionality in your AgentOS

Model Context Protocol (MCP) gives Agents the ability to interact with external systems through a standardized interface.
To turn your AgentOS into an MCP server, you can set `enable_mcp_server=True` when creating your AgentOS instance.

```python enable_mcp_example.py theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Website Reader (Async)

**URL:** llms-txt#website-reader-(async)

**Contents:**
- Code
- Usage
- Params

Source: https://docs.agno.com/examples/concepts/knowledge/readers/website/website-reader-async

The **Website Reader** with asynchronous processing crawls and processes entire websites efficiently, following links to create comprehensive knowledge bases from web content.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Set environment variables">
    
  </Step>

<Snippet file="run-pgvector-step.mdx" />

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

<Snippet file="website-reader-reference.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Create an agent with ApifyTools

**URL:** llms-txt#create-an-agent-with-apifytools

agent = Agent(
    tools=[
        ApifyTools(
            actors=["apify/rag-web-browser"],  # Specify which Apify Actors to use, use multiple ones if needed
            apify_api_token="your_apify_api_key"  # Or set the APIFY_API_TOKEN environment variable 
        )
    ],
        markdown=True
)

---

## Setup the agent

**URL:** llms-txt#setup-the-agent

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    db=db,
    session_id="session_storage",
    add_history_to_context=True,
    # Activate session caching. The session will be cached in memory for faster access.
    cache_session=True,
)

---

## pprint(movie_agent.content)

**URL:** llms-txt#pprint(movie_agent.content)

**Contents:**
- Usage

movie_agent.print_response("New York")
bash  theme={null}
    export IBM_WATSONX_API_KEY=xxx
    export IBM_WATSONX_PROJECT_ID=xxx
    bash  theme={null}
    pip install -U ibm-watsonx-ai pydantic rich agno
    bash Mac theme={null}
      python cookbook/models/ibm/watsonx/structured_output.py
      bash Windows theme={null}
      python cookbook\models\ibm\watsonx\structured_output.py
      ```
    </CodeGroup>
  </Step>
</Steps>

This example shows how to use structured output with IBM WatsonX. It defines a Pydantic model `MovieScript` with various fields and their descriptions, then creates an agent using this model as the `output_schema`. The model's output will be parsed into this structured format.

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

## Basic Agent Events Handling

**URL:** llms-txt#basic-agent-events-handling

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/events/basic_agent_events

This example demonstrates how to handle and monitor various agent events during execution, including run lifecycle events, tool calls, and content streaming.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/events" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## LightRAG Agent Knowledge

**URL:** llms-txt#lightrag-agent-knowledge

**Contents:**
- Setup
- Example
- LightRAG Params
- Developer Resources

Source: https://docs.agno.com/concepts/vectordb/lightrag

## Developer Resources

* View [Cookbook (Sync)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/lance_db/lance_db.py)
* View [Cookbook (Hybrid Search)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/lance_db/lance_db_hybrid_search.py)

---

## AgentOSConfig

**URL:** llms-txt#agentosconfig

**Contents:**
- Using a YAML Configuration File

Source: https://docs.agno.com/reference/agent-os/configuration

<Snippet file="agent-os-configuration-reference.mdx" />

## Using a YAML Configuration File

You can also provide your AgentOS configuration via a YAML file.

You can define all the previously mentioned configuration options in the file:

```yaml  theme={null}

---

## Milvus Agent Knowledge

**URL:** llms-txt#milvus-agent-knowledge

**Contents:**
- Setup
- Initialize Milvus
- Example

Source: https://docs.agno.com/concepts/vectordb/milvus

Set the uri and token for your Milvus server.

* If you only need a local vector database for small scale data or prototyping, setting the uri as a local file, e.g.`./milvus.db`, is the most convenient method, as it automatically utilizes [Milvus Lite](https://milvus.io/docs/milvus_lite.md) to store all data in this file.
* If you have large scale data, say more than a million vectors, you can set up a more performant Milvus server on [Docker or Kubernetes](https://milvus.io/docs/quickstart.md).
  In this setup, please use the server address and port as your uri, e.g.`http://localhost:19530`. If you enable the authentication feature on Milvus, use `your_username:your_password` as the token, otherwise don't set the token.
* If you use [Zilliz Cloud](https://zilliz.com/cloud), the fully managed cloud service for Milvus, adjust the `uri` and `token`, which correspond to the [Public Endpoint and API key](https://docs.zilliz.com/docs/on-zilliz-cloud-console#cluster-details) in Zilliz Cloud.

```python agent_with_knowledge.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.milvus import Milvus

vector_db = Milvus(
    collection="recipes",
    uri="./milvus.db",
)

**Examples:**

Example 1 (unknown):
```unknown
## Initialize Milvus

Set the uri and token for your Milvus server.

* If you only need a local vector database for small scale data or prototyping, setting the uri as a local file, e.g.`./milvus.db`, is the most convenient method, as it automatically utilizes [Milvus Lite](https://milvus.io/docs/milvus_lite.md) to store all data in this file.
* If you have large scale data, say more than a million vectors, you can set up a more performant Milvus server on [Docker or Kubernetes](https://milvus.io/docs/quickstart.md).
  In this setup, please use the server address and port as your uri, e.g.`http://localhost:19530`. If you enable the authentication feature on Milvus, use `your_username:your_password` as the token, otherwise don't set the token.
* If you use [Zilliz Cloud](https://zilliz.com/cloud), the fully managed cloud service for Milvus, adjust the `uri` and `token`, which correspond to the [Public Endpoint and API key](https://docs.zilliz.com/docs/on-zilliz-cloud-console#cluster-details) in Zilliz Cloud.

## Example
```

---

## Load the knowledge base

**URL:** llms-txt#load-the-knowledge-base

knowledge = Knowledge(
    vector_db=vector_db,
)

knowledge.add_content(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
)

---

## Create agents

**URL:** llms-txt#create-agents

greeter_agent = Agent(
    name="Greeter",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="Greet the user warmly and introduce yourself.",
    markdown=True,
)

contextual_agent = Agent(
    name="Contextual Assistant",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions="Continue the conversation with context. You already know the user.",
    markdown=True,
)

---

## You can also override the entire `system_message` for the memory manager

**URL:** llms-txt#you-can-also-override-the-entire-`system_message`-for-the-memory-manager

**Contents:**
- Usage

memory_manager = MemoryManager(
    model=OpenAIChat(id="gpt-5-mini"),
    additional_instructions="""
    IMPORTANT: Don't store any memories about the user's name. Just say "The User" instead of referencing the user's name.
    """,
    db=db,
)

john_doe_id = "john_doe@example.com"

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    db=db,
    memory_manager=memory_manager,
    enable_user_memories=True,
    user_id=john_doe_id,
)

agent.print_response(
    "My name is John Doe and I like to swim and play soccer.", stream=True
)

agent.print_response("I dont like to swim", stream=True)

memories = agent.get_user_memories(user_id=john_doe_id)

print("John Doe's memories:")
pprint(memories)

bash  theme={null}
    pip install -U agno
    bash Mac theme={null}
      python cookbook/memory/04_custom_memory_manager.py
      bash Windows theme={null}
      python cookbook/memory/04_custom_memory_manager.py
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

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Share Memory between Agents

**URL:** llms-txt#share-memory-between-agents

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/memory/03-agents-share-memory

This example demonstrates how to share memory between Agents.

This means that memories created by one Agent, will be available to the other Agents.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Alex River is not in the knowledge base, so the Agent should not find any information about him

**URL:** llms-txt#alex-river-is-not-in-the-knowledge-base,-so-the-agent-should-not-find-any-information-about-him

**Contents:**
- Usage

agent.print_response(
    "Do you think Alex Rivera is a good candidate?",
    markdown=True,
)
bash  theme={null}
    pip install -U agno sqlalchemy psycopg pgvector openai    
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Mac theme={null}
      python cookbook/knowledge/basic_operations/08_include_exclude_files.py
      bash Windows theme={null}
      python cookbook/knowledge/basic_operations/08_include_exclude_files.py
      ```
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run the example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## AI Support Team

**URL:** llms-txt#ai-support-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/use-cases/teams/ai_support_team

This example illustrates how to create an AI support team that can route customer inquiries to the appropriate agent based on the nature of the inquiry.

```python cookbook/examples/teams/route_mode/ai_customer_support_team.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.website_reader import WebsiteReader
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools
from agno.tools.slack import SlackTools
from agno.vectordb.pgvector import PgVector

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="website_documents",
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
    ),
)

knowledge.add_content(
    url="https://docs.agno.com/introduction",
    reader=WebsiteReader(
        # Number of links to follow from the seed URLs
        max_links=10,
    ),
)
support_channel = "testing"
feedback_channel = "testing"

doc_researcher_agent = Agent(
    name="Doc researcher Agent",
    role="Search the knowledge base for information",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools(), ExaTools()],
    knowledge=knowledge,
    search_knowledge=True,
    instructions=[
        "You are a documentation expert for given product. Search the knowledge base thoroughly to answer user questions.",
        "Always provide accurate information based on the documentation.",
        "If the question matches an FAQ, provide the specific FAQ answer from the documentation.",
        "When relevant, include direct links to specific documentation pages that address the user's question.",
        "If you're unsure about an answer, acknowledge it and suggest where the user might find more information.",
        "Format your responses clearly with headings, bullet points, and code examples when appropriate.",
        "Always verify that your answer directly addresses the user's specific question.",
        "If you cannot find the answer in the documentation knowledge base, use the DuckDuckGoTools or ExaTools to search the web for relevant information to answer the user's question.",
    ],
)

escalation_manager_agent = Agent(
    name="Escalation Manager Agent",
    role="Escalate the issue to the slack channel",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[SlackTools()],
    instructions=[
        "You are an escalation manager responsible for routing critical issues to the support team.",
        f"When a user reports an issue, always send it to the #{support_channel} Slack channel with all relevant details using the send_message toolkit function.",
        "Include the user's name, contact information (if available), and a clear description of the issue.",
        "After escalating the issue, respond to the user confirming that their issue has been escalated.",
        "Your response should be professional and reassuring, letting them know the support team will address it soon.",
        "Always include a ticket or reference number if available to help the user track their issue.",
        "Never attempt to solve technical problems yourself - your role is strictly to escalate and communicate.",
    ],
)

feedback_collector_agent = Agent(
    name="Feedback Collector Agent",
    role="Collect feedback from the user",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[SlackTools()],
    description="You are an AI agent that can collect feedback from the user.",
    instructions=[
        "You are responsible for collecting user feedback about the product or feature requests.",
        f"When a user provides feedback or suggests a feature, use the Slack tool to send it to the #{feedback_channel} channel using the send_message toolkit function.",
        "Include all relevant details from the user's feedback in your Slack message.",
        "After sending the feedback to Slack, respond to the user professionally, thanking them for their input.",
        "Your response should acknowledge their feedback and assure them that it will be taken into consideration.",
        "Be warm and appreciative in your tone, as user feedback is valuable for improving our product.",
        "Do not promise specific timelines or guarantee that their suggestions will be implemented.",
    ],
)

customer_support_team = Team(
    name="Customer Support Team",
    model=OpenAIChat(id="gpt-5-mini"),
    members=[doc_researcher_agent, escalation_manager_agent, feedback_collector_agent],
    markdown=True,
    debug_mode=True,
    show_members_responses=True,
    determine_input_for_members=False,
    respond_directly=True,
    instructions=[
        "You are the lead customer support agent responsible for classifying and routing customer inquiries.",
        "Carefully analyze each user message and determine if it is: a question that needs documentation research, a bug report that requires escalation, or product feedback.",
        "For general questions about the product, route to the doc_researcher_agent who will search documentation for answers.",
        "If the doc_researcher_agent cannot find an answer to a question, escalate it to the escalation_manager_agent.",
        "For bug reports or technical issues, immediately route to the escalation_manager_agent.",
        "For feature requests or product feedback, route to the feedback_collector_agent.",
        "Always provide a clear explanation of why you're routing the inquiry to a specific agent.",
        "After receiving a response from the appropriate agent, relay that information back to the user in a professional and helpful manner.",
        "Ensure a seamless experience for the user by maintaining context throughout the conversation.",
    ],
)

---

## Agentic RAG with Infinity Reranker

**URL:** llms-txt#agentic-rag-with-infinity-reranker

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/agentic_search/agentic_rag_infinity_reranker

This example demonstrates how to implement Agentic RAG using Infinity Reranker, which provides high-performance, local reranking capabilities for improved document retrieval without external API calls.

```python agentic_rag_infinity_reranker.py theme={null}
"""This cookbook shows how to implement Agentic RAG using Infinity Reranker.

Infinity is a high-performance inference server for text-embeddings, reranking, and classification models.
It provides fast and efficient reranking capabilities for RAG applications.

1. Install Dependencies
Run: pip install agno anthropic infinity-client lancedb

2. Set up Infinity Server
You have several options to deploy Infinity:

---

## memory_manager = MemoryManager(model=OpenAIChat(id="gpt-5-mini"))

**URL:** llms-txt#memory_manager-=-memorymanager(model=openaichat(id="gpt-5-mini"))

---

## Agent Ops

**URL:** llms-txt#agent-ops

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/integrations/observability/agent_ops

This example shows how to add observability to your agno agent with Agent Ops.

```python cookbook/integrations/observability/agent_ops.py theme={null}
import agentops
from agno.agent import Agent
from agno.models.openai import OpenAIChat

---

## Filtering on Weaviate

**URL:** llms-txt#filtering-on-weaviate

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/vector-dbs/filtering_weaviate

Learn how to filter knowledge base searches using Pdf documents with user-specific metadata in Weaviate.

```python  theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.weaviate import Distance, VectorIndex, Weaviate

---

## Create a knowledge base with PgVector

**URL:** llms-txt#create-a-knowledge-base-with-pgvector

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="knowledge_documents",
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai"
    ),
)

---

## agent.print_response("Send an email with the subject 'Hello' and the body 'Hello, world!'", stream=True)

**URL:** llms-txt#agent.print_response("send-an-email-with-the-subject-'hello'-and-the-body-'hello,-world!'",-stream=true)

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch user_input_required_stream.py
    bash Mac theme={null}
      python user_input_required_stream.py
      bash Windows   theme={null}
      python user_input_required_stream.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Agent that uses JSON mode

**URL:** llms-txt#agent-that-uses-json-mode

json_mode_agent = Agent(
    model=Together(id="meta-llama/Meta-Llama-3.1-8B-Instruct-Turbo"),
    description="You write movie scripts.",
    output_schema=MovieScript,
    use_json_mode=True,
)

---

## Initial Retriever Agent - Specialized in broad initial retrieval

**URL:** llms-txt#initial-retriever-agent---specialized-in-broad-initial-retrieval

initial_retriever = Agent(
    name="Initial Retriever",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Perform broad initial retrieval to gather candidate information",
    knowledge=reranked_knowledge,
    search_knowledge=True,
    instructions=[
        "Perform comprehensive initial retrieval from the knowledge base.",
        "Cast a wide net to gather all potentially relevant information.",
        "Focus on recall rather than precision in this initial phase.",
        "Retrieve diverse content that might be relevant to the query.",
    ],
    markdown=True,
)

---

## Create MCP-enabled agent

**URL:** llms-txt#create-mcp-enabled-agent

agent = Agent(
    id="agno-agent",
    name="Agno Agent",
    tools=[mcp_tools],
)

---

## Filtering

**URL:** llms-txt#filtering

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/filtering

```python  theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.lancedb import LanceDb

---

## Define how the agent should gather data

**URL:** llms-txt#define-how-the-agent-should-gather-data

**Contents:**
  - 3b. Define the Analysis Framework

data_collection_strategy = dedent("""
    DATA COLLECTION STRATEGY:
    - Use X Tools to gather direct social media mentions with full engagement metrics
    - Use Exa Tools to find broader web discussions, articles, and forum conversations
    - Cross-reference findings between social and web sources for comprehensive coverage
""")

print("Data collection strategy defined")
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
### 3b. Define the Analysis Framework
```

---

## Second agent for news research

**URL:** llms-txt#second-agent-for-news-research

news_research_agent = Agent(
    name="News Research Agent",
    role="Research and find related news",
    id="news-research",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    instructions=[
        "You are a news research analyst.",
        "Find relevant and recent news articles on given topics.",
        "Always provide reliable sources and context.",
    ],
)

---

## Setup your evaluator Agent

**URL:** llms-txt#setup-your-evaluator-agent

**Contents:**
- Accuracy with Tools
- Accuracy with given output
- Accuracy with asynchronous functions

evaluator_agent = Agent(
    model=OpenAIChat(id="gpt-5"),
    output_schema=AccuracyAgentResponse,  # We want the evaluator agent to return an AccuracyAgentResponse
    # You can provide any additional evaluator instructions here:
    # instructions="",
)

evaluation = AccuracyEval(
    model=OpenAIChat(id="o4-mini"),
    agent=Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[CalculatorTools()]),
    input="What is 10*5 then to the power of 2? do it step by step",
    expected_output="2500",
    # Use your evaluator Agent
    evaluator_agent=evaluator_agent,
    # Further adjusting the guidelines
    additional_guidelines="Agent output should include the steps and the final answer.",
)

result: Optional[AccuracyResult] = evaluation.run(print_results=True)
assert result is not None and result.avg_score >= 8
python accuracy_with_tools.py theme={null}
from typing import Optional

from agno.agent import Agent
from agno.eval.accuracy import AccuracyEval, AccuracyResult
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools

evaluation = AccuracyEval(
    name="Tools Evaluation",
    model=OpenAIChat(id="o4-mini"),
    agent=Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        tools=[CalculatorTools()],
    ),
    input="What is 10!?",
    expected_output="3628800",
)

result: Optional[AccuracyResult] = evaluation.run(print_results=True)
assert result is not None and result.avg_score >= 8
python accuracy_with_given_answer.py theme={null}
from typing import Optional

from agno.eval.accuracy import AccuracyEval, AccuracyResult
from agno.models.openai import OpenAIChat

evaluation = AccuracyEval(
    name="Given Answer Evaluation",
    model=OpenAIChat(id="o4-mini"),
    input="What is 10*5 then to the power of 2? do it step by step",
    expected_output="2500",
)
result_with_given_answer: Optional[AccuracyResult] = evaluation.run_with_output(
    output="2500", print_results=True
)
assert result_with_given_answer is not None and result_with_given_answer.avg_score >= 8
python async_accuracy.py theme={null}
"""This example shows how to run an Accuracy evaluation asynchronously."""

import asyncio
from typing import Optional

from agno.agent import Agent
from agno.eval.accuracy import AccuracyEval, AccuracyResult
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools

evaluation = AccuracyEval(
    model=OpenAIChat(id="o4-mini"),
    agent=Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        tools=[CalculatorTools()],
    ),
    input="What is 10*5 then to the power of 2? do it step by step",
    expected_output="2500",
    additional_guidelines="Agent output should include the steps and the final answer.",
    num_iterations=3,
)

**Examples:**

Example 1 (unknown):
```unknown
<Frame>
  <img height="200" src="https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/accuracy_basic.png?fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=60f989f94bfe8b9147e0fe439e1d27d2" style={{ borderRadius: '8px' }} data-og-width="2046" data-og-height="1354" data-path="images/evals/accuracy_basic.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/accuracy_basic.png?w=280&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=a37037fd28a47087de5fedc599c4346b 280w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/accuracy_basic.png?w=560&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=b73acf915f02a759ae8c2353fdf6ec77 560w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/accuracy_basic.png?w=840&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=dc6425d6eb0243364b9fafd500495a15 840w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/accuracy_basic.png?w=1100&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=33690c95f75c292fb1347da676cfaa53 1100w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/accuracy_basic.png?w=1650&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=28e03442ad38b0576c1607a6abcd1593 1650w, https://mintcdn.com/agno-v2/3rn2Dg1ZNvoQRtu4/images/evals/accuracy_basic.png?w=2500&fit=max&auto=format&n=3rn2Dg1ZNvoQRtu4&q=85&s=60af642df61c82e5f7eaa7833d9df73f 2500w" />
</Frame>

## Accuracy with Tools

You can also run the `AccuracyEval` with tools.
```

Example 2 (unknown):
```unknown
## Accuracy with given output

For comprehensive evaluation, run with a given output:
```

Example 3 (unknown):
```unknown
## Accuracy with asynchronous functions

Evaluate accuracy with asynchronous functions:
```

---

## SingleStore Agent Knowledge

**URL:** llms-txt#singlestore-agent-knowledge

**Contents:**
- Setup
- Example
- SingleStore Params
- Developer Resources

Source: https://docs.agno.com/concepts/vectordb/singlestore

After running the container, set the environment variables:

SingleStore supports both cloud-based and local deployments. For step-by-step guidance on setting up your cloud deployment, please refer to the [SingleStore Setup Guide](https://docs.singlestore.com/cloud/connect-to-singlestore/connect-with-mysql/connect-with-mysql-client/connect-to-singlestore-helios-using-tls-ssl/).

## SingleStore Params

<Snippet file="vectordb_singlestore_params.mdx" />

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/singlestore_db/singlestore_db.py)

**Examples:**

Example 1 (unknown):
```unknown
After running the container, set the environment variables:
```

Example 2 (unknown):
```unknown
SingleStore supports both cloud-based and local deployments. For step-by-step guidance on setting up your cloud deployment, please refer to the [SingleStore Setup Guide](https://docs.singlestore.com/cloud/connect-to-singlestore/connect-with-mysql/connect-with-mysql-client/connect-to-singlestore-helios-using-tls-ssl/).

## Example
```

---

## Step 4: Create the complete agent

**URL:** llms-txt#step-4:-create-the-complete-agent

**Contents:**
  - 4e. Spin-up the infrastructure for our project:
  - 4f. Test Your Complete Agent
- Step 5: Test and experiment via AgentOS

social_media_agent = Agent(
    name="Social Media Intelligence Analyst",
    model=model,
    tools=tools,
    instructions=complete_instructions,
    markdown=True,
    show_tool_calls=True,
)

def analyze_brand_sentiment(query: str, tweet_count: int = 20):
    """Execute comprehensive social media intelligence analysis."""
    prompt = f"""
    Conduct comprehensive social media intelligence analysis for: "{query}"

ANALYSIS PARAMETERS:
    - Twitter Analysis: {tweet_count} most recent tweets with engagement metrics
    - Web Intelligence: Related articles, discussions, and broader context via Exa
    - Cross-Platform Synthesis: Correlate social sentiment with web discussions
    - Strategic Focus: Brand positioning, competitive analysis, risk assessment

METHODOLOGY:
    1. Gather direct social media mentions and engagement data
    2. Search for related web discussions and broader context
    3. Analyze sentiment patterns and engagement indicators
    4. Identify cross-platform themes and influence networks
    5. Generate strategic recommendations with evidence backing

Provide comprehensive intelligence report following the structured format.
    """

return social_media_agent.print_response(prompt, stream=True)

if __name__ == "__main__":
    # Test the complete agent
    analyze_brand_sentiment("Agno OR AgnoAGI", tweet_count=25)
bash  theme={null}
ag infra up
bash  theme={null}
python app/social_media_agent.py
bash  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
### 4e. Spin-up the infrastructure for our project:

Now that we have completed our agent, we can spin-up the infrastructure for our project:
```

Example 2 (unknown):
```unknown
Your [AgentOS](/agent-os/introduction) API is now running. We are ready to start building!

### 4f. Test Your Complete Agent
```

Example 3 (unknown):
```unknown
You should see your agent:

1. **Use X Tools** to gather Twitter data with engagement metrics
2. **Use Exa Tools** to find broader web context
3. **Generate a structured report** following your defined format
4. **Provide strategic recommendations** based on the analysis

## Step 5: Test and experiment via AgentOS

**Why API-first?** The AgentOS infrastructure automatically exposes your agent as a REST API, making it ready for production integration without additional deployment work.

Your agent is automatically available via the AgentOS API. Let's test it!

**Find your API endpoint:**
```

---

## Set up SQL storage for the agent's data

**URL:** llms-txt#set-up-sql-storage-for-the-agent's-data

db = SqliteDb(db_file="data.db")

---

## Basic Agent Instructions

**URL:** llms-txt#basic-agent-instructions

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/context_management/instructions

This example demonstrates how to provide basic instructions to an agent to guide its response behavior and storytelling style.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/context_management" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Setup basic research agent

**URL:** llms-txt#setup-basic-research-agent

web_research_agent = Agent(
    id="web-research-agent",
    name="Web Research Agent",
    model=Claude(id="claude-sonnet-4-0"),
    db=db,
    tools=[DuckDuckGoTools()],
    add_history_to_context=True,
    num_history_runs=3,
    add_datetime_to_context=True,
    enable_session_summaries=True,
    markdown=True,
)

---

## Setup the reasoning Agent

**URL:** llms-txt#setup-the-reasoning-agent

**Contents:**
- Usage

agent = Agent(
    model=OpenAIResponses(
        id="o4-mini",
        reasoning_summary="auto",  # Requesting a reasoning summary
    ),
    tools=[DuckDuckGoTools(search=True)],
    instructions="Use tables to display the analysis",
    markdown=True,
)

agent.print_response(
    "Write a brief report comparing NVDA to TSLA",
    stream=True,
    stream_events=True,
)
bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    pip install -U openai agno ddgs
    bash Mac theme={null}
        python cookbook/reasoning/models/openai/reasoning_summary.py
      bash Windows theme={null}
        python cookbook/reasoning/models/openai/reasoning_summary.py
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

## Example prompts to try:

**URL:** llms-txt#example-prompts-to-try:

**Contents:**
- Usage

"""
Explore Agno's capabilities with these queries:
1. "What are the different types of agents in Agno?"
2. "How does Agno handle knowledge base management?"
3. "What embedding models does Agno support?"
4. "How can I implement custom tools in Agno?"
5. "What storage options are available for workflow caching?"
6. "How does Agno handle streaming responses?"
7. "What types of LLM providers does Agno support?"
8. "How can I implement custom knowledge sources?"
"""

bash  theme={null}
    export OPENAI_API_KEY=****
    bash  theme={null}
    pip install -U agno openai lancedb tantivy inquirer
    bash Mac theme={null}
      python cookbook/examples/agents/deep_knowledge.py
      bash Windows theme={null}
      python cookbook/examples/agents/deep_knowledge.py
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

## Session Caching for Performance

**URL:** llms-txt#session-caching-for-performance

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/session/cache_session

This example demonstrates how to enable session caching to store team sessions in memory for faster access and improved performance.

```python cookbook/examples/teams/session/08_cache_session.py theme={null}
"""Example of how to cache the team session in memory for faster access."""

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.team import Team

---

## Filtering on PgVector

**URL:** llms-txt#filtering-on-pgvector

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/vector-dbs/filtering_pgvector

Learn how to filter knowledge base searches using Pdf documents with user-specific metadata in PgVector.

```python  theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.pgvector import PgVector

---

## Performance Quick Wins

**URL:** llms-txt#performance-quick-wins

**Contents:**
- When to Optimize
- The 80/20 of Performance
  - 1. Pick the Right Vector Database

Source: https://docs.agno.com/concepts/knowledge/advanced/performance-tips

Practical tips to optimize Agno knowledge base performance, improve search quality, and speed up content loading.

Most knowledge bases work great with Agno's defaults. But if you're seeing slow searches, memory issues, or poor results, a few strategic changes can make a big difference.

Don't prematurely optimize. Focus on performance when you notice:

* **Slow search** - Queries taking more than 2-3 seconds
* **Memory issues** - Out of memory errors during content loading
* **Poor results** - Search returning irrelevant chunks or missing obvious matches
* **Slow loading** - Content processing taking unusually long

If things are working fine, stick with the defaults and focus on building your application.

## The 80/20 of Performance

These five changes give you the biggest performance boost for the least effort:

### 1. Pick the Right Vector Database

Your database choice has the biggest impact on performance at scale:

```python  theme={null}
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.pgvector import PgVector

---

## Search & Retrieval

**URL:** llms-txt#search-&-retrieval

**Contents:**
- How Agents Search Knowledge
- Agentic Search: The Smart Difference
  - Traditional RAG vs. Agentic RAG
- Configuring Search in Agno
  - Types of Search Strategies
- What Affects Search Quality
  - Content Chunking Strategy
  - Embedding Model Quality
  - Practical Configuration

Source: https://docs.agno.com/concepts/knowledge/core-concepts/search-retrieval

Understand how agents intelligently search and retrieve information from knowledge bases to provide accurate, contextual responses.

When an agent needs information to answer a question, it doesn't dump everything into the prompt. Instead, it searches for just the most relevant pieces. This focused approach is what makes knowledge-powered agents both effective and efficient—they get exactly what they need, when they need it.

## How Agents Search Knowledge

Think of an agent's search process like a skilled researcher who knows what to look for and where to find it:

<Steps>
  <Step title="Query Analysis">
    The agent analyzes the user's question to understand what type of
    information would be helpful.
  </Step>

<Step title="Search Strategy">
    Based on the analysis, the system formulates one or more searches (vector,
    keyword, or hybrid).
  </Step>

<Step title="Information Retrieval">
    The knowledge base returns the most relevant content chunks.
  </Step>

<Step title="Context Integration">
    The retrieved information is combined with the original question to generate
    a comprehensive response.
  </Step>
</Steps>

## Agentic Search: The Smart Difference

What makes Agno's approach special? Agents can programmatically decide when to search and how to use results. Think of it as giving your agent the keys to the library instead of handing it a fixed stack of books. You can even plug in custom retrieval logic to match your specific needs.

**Key capabilities:**

* **Automatic Decision Making** - The agent can choose to search when it needs additional information—or skip it when not necessary.

* **Smart Query Generation** - Implement logic to reformulate queries for better recall—like expanding "vacation" to include "PTO" and "time off."

* **Multi-Step Search** - If the first search isn't enough, run follow-up searches with refined queries.

* **Context Synthesis** - Combine information from multiple results to produce a thorough, grounded answer.

### Traditional RAG vs. Agentic RAG

Here's how they compare in practice:

<Tabs>
  <Tab title="Traditional RAG">
    
  </Tab>

<Tab title="Agentic RAG">
    
  </Tab>
</Tabs>

## Configuring Search in Agno

You configure search behavior on your vector database, and Knowledge uses those settings when retrieving documents. It's a simple setup:

### Types of Search Strategies

Agno gives you three main approaches. Pick the one that fits your content and how users ask questions:

#### Vector Similarity Search

Finds content by meaning, not just matching words. When you ask "How do I reset my password?", it finds documents about "changing credentials" even though the exact words don't match.

* Your query becomes a vector (list of numbers capturing meaning)
* The system finds content with similar vectors
* Results are ranked by how close the meanings are

**Best for:** Conceptual questions where users might phrase things differently than your docs.

Classic text search—looks for exact words and phrases in your content. When using PgVector, this leverages Postgres's full-text search under the hood.

* Matches specific words and phrases
* Supports search operators (where your backend allows)
* Works great when users know the exact terminology

**Best for:** Finding specific terms, product names, error codes, or technical identifiers.

The best of both worlds—combines semantic understanding with exact-match precision. This is usually your best bet for production.

* Runs both vector similarity and keyword matching
* Merges results intelligently
* Can add a reranker on top for even better ordering

**Best for:** Most real-world applications where you want both accuracy and flexibility.

<Tip>
  We recommend starting with <b>hybrid search with reranking</b> for strong
  recall and precision.
</Tip>

## What Affects Search Quality

### Content Chunking Strategy

How you split your content matters a lot:

* **Smaller chunks** (200-500 chars): Super precise, but might miss the big picture
* **Larger chunks** (1000-2000 chars): Better context, but less targeted
* **Semantic chunking**: Splits at natural topic boundaries—usually the sweet spot

### Embedding Model Quality

Your embedder is what turns text into vectors that capture meaning:

* **General-purpose** (like OpenAI's text-embedding-3-small): Works well for most content
* **Domain-specific**: Better for specialized fields like medical or legal docs
* **Multilingual**: Essential if you're working in multiple languages

### Practical Configuration

```python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
</Tab>

  <Tab title="Agentic RAG">
```

Example 2 (unknown):
```unknown
</Tab>
</Tabs>

## Configuring Search in Agno

You configure search behavior on your vector database, and Knowledge uses those settings when retrieving documents. It's a simple setup:
```

Example 3 (unknown):
```unknown
### Types of Search Strategies

Agno gives you three main approaches. Pick the one that fits your content and how users ask questions:

#### Vector Similarity Search

Finds content by meaning, not just matching words. When you ask "How do I reset my password?", it finds documents about "changing credentials" even though the exact words don't match.

**How it works:**

* Your query becomes a vector (list of numbers capturing meaning)
* The system finds content with similar vectors
* Results are ranked by how close the meanings are

**Best for:** Conceptual questions where users might phrase things differently than your docs.

#### Keyword Search

Classic text search—looks for exact words and phrases in your content. When using PgVector, this leverages Postgres's full-text search under the hood.

**How it works:**

* Matches specific words and phrases
* Supports search operators (where your backend allows)
* Works great when users know the exact terminology

**Best for:** Finding specific terms, product names, error codes, or technical identifiers.

#### Hybrid Search

The best of both worlds—combines semantic understanding with exact-match precision. This is usually your best bet for production.

**How it works:**

* Runs both vector similarity and keyword matching
* Merges results intelligently
* Can add a reranker on top for even better ordering

**Best for:** Most real-world applications where you want both accuracy and flexibility.
```

Example 4 (unknown):
```unknown
<Tip>
  We recommend starting with <b>hybrid search with reranking</b> for strong
  recall and precision.
</Tip>

## What Affects Search Quality

### Content Chunking Strategy

How you split your content matters a lot:

* **Smaller chunks** (200-500 chars): Super precise, but might miss the big picture
* **Larger chunks** (1000-2000 chars): Better context, but less targeted
* **Semantic chunking**: Splits at natural topic boundaries—usually the sweet spot

### Embedding Model Quality

Your embedder is what turns text into vectors that capture meaning:

* **General-purpose** (like OpenAI's text-embedding-3-small): Works well for most content
* **Domain-specific**: Better for specialized fields like medical or legal docs
* **Multilingual**: Essential if you're working in multiple languages

### Practical Configuration
```

---

## Test agentic knowledge filtering

**URL:** llms-txt#test-agentic-knowledge-filtering

**Contents:**
- Usage

team_with_knowledge.print_response(
    "Tell me about Jordan Mitchell's work and experience with user_id as jordan_mitchell"
)
bash  theme={null}
    pip install agno openai lancedb
    bash  theme={null}
    export OPENAI_API_KEY=****
    bash  theme={null}
    python cookbook/examples/teams/knowledge/03_team_with_agentic_knowledge_filters.py
    ```
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install required libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Markdown Reader

**URL:** llms-txt#markdown-reader

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/markdown/markdown-reader

The **Markdown Reader** processes Markdown files synchronously and converts them into documents that can be used with Agno's knowledge system.

```python examples/concepts/knowledge/readers/markdown_reader_sync.py theme={null}
from pathlib import Path

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.markdown_reader import MarkdownReader
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="markdown_documents",
        db_url=db_url,
    ),
)

---

## Web search agent with tool hooks

**URL:** llms-txt#web-search-agent-with-tool-hooks

website_agent = Agent(
    name="Website Agent",
    id="website-agent",
    role="Search the website for information",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools(cache_results=True)],
    instructions=[
        "Search the website for information",
    ],
    tool_hooks=[logger_hook],
)

---

## Knowledge Contents DB

**URL:** llms-txt#knowledge-contents-db

**Contents:**
- What is Contents DB?
- Why Use ContentsDB?
  - Content Visibility and Control
  - Powerful Management Capabilities
  - Required for AgentOS
- Setting Up ContentsDB
  - Choose Your Database
  - Basic Setup Example

Source: https://docs.agno.com/concepts/knowledge/content_db

Learn how to add a Content DB to your Knowledge.

The Contents Database (Contents DB) is an optional component that enhances Knowledge with content tracking and management features. It acts as a control layer that maintains detailed records of all content added to your `Knowledge`.

## What is Contents DB?

Contents DB is a table in your database that keeps track of what content you've added to your Knowledge base.
While your vector database stores the actual content for search, this table tracks what you've added, when you added it, and its processing status.

* **Vector Database**: Stores embeddings and chunks for semantic search
* **Contents Database**: Tracks content metadata, status, and when coupled with [AgentOS Knowledge](/agent-os/features/knowledge-management), provides management of your knowledge via API.

## Why Use ContentsDB?

### Content Visibility and Control

Without ContentsDB, managing your knowledge and vectors is difficult - you can search it, but you can't manage individual pieces of content or alter all the vectors created from a single piece of content.

With ContentsDB, you gain full visibility:

* See all content that has been added
* Track processing status of each item
* View metadata and file information
* Monitor access patterns and usage

### Powerful Management Capabilities

* **Edit names, descriptions and metadata** for existing content
* **Delete specific content** and automatically clean up associated vectors
* **Update content** without rebuilding the entire knowledge base
* **Batch operations** for managing multiple content items
* **Status tracking** to monitor processing success/failure

### Required for AgentOS

If you're using AgentOS, ContentsDB is **mandatory** for the Knowledge page functionality. The AgentOS web interface relies on ContentsDB to display and manage your knowledge content.

## Setting Up ContentsDB

### Choose Your Database

Agno supports multiple database backends for ContentsDB:

* **[PostgreSQL](/concepts/db/postgres)** - Recommended for production
* **[SQLite](/concepts/db/sqlite)** - Great for development and single-user applications
* **[MySQL](/concepts/db/mysql)** - Enterprise-ready relational database
* **[MongoDB](/concepts/db/mongodb)** - Document-based NoSQL option
* **[Redis](/concepts/db/redis)** - In-memory option for high performance
* **[In-Memory](/concepts/db/in_memory)** - Temporary storage for testing
* **Cloud Options** - [DynamoDB](/concepts/db/dynamodb), [Firestore](/concepts/db/firestore), [GCS](/concepts/db/gcs)

### Basic Setup Example

```python  theme={null}
from agno.knowledge import Knowledge
from agno.db.postgres import PostgresDb
from agno.vectordb.pgvector import PgVector

---

## Add from GCS

**URL:** llms-txt#add-from-gcs

**Contents:**
- Usage
- Params

asyncio.run(
    knowledge.add_content_async(
        name="GCS PDF",
        remote_content=GCSContent(
            bucket_name="thai-recepies", blob_name="ThaiRecipes.pdf"
        ),
        metadata={"remote_content": "GCS"},
    )
)

agent = Agent(
    name="My Agent",
    description="Agno 2.0 Agent Implementation",
    knowledge=knowledge,
    search_knowledge=True,
    debug_mode=True,
)

agent.print_response(
    "What is the best way to make a Thai curry?",
    markdown=True,
)
bash  theme={null}
    pip install -U agno sqlalchemy psycopg pgvector google-cloud-storage
    bash Mac theme={null}
      python cookbook/knowledge/basic_operations/07_from_gcs.py
      bash Windows theme={null}
      python cookbook/knowledge/basic_operations/07_from_gcs.py
      ```
    </CodeGroup>
  </Step>
</Steps>

<Snippet file="gcs-remote-content-params.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Configure Google Cloud credentials">
    Set up your GCS credentials using one of these methods:

    * Service Account Key: Set `GOOGLE_APPLICATION_CREDENTIALS` environment variable
    * gcloud CLI: `gcloud auth application-default login`
    * Workload Identity (if running on Google Cloud)
  </Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run the example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Data Analyst Agent

**URL:** llms-txt#data-analyst-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/langdb/data_analyst

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Agno documentation knowledge base

**URL:** llms-txt#agno-documentation-knowledge-base

agno_assist_knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_assist_knowledge",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

---

## agent.print_response("Hi my name is John and I live in New York")

**URL:** llms-txt#agent.print_response("hi-my-name-is-john-and-i-live-in-new-york")

---

## Example usage with Knowledge

**URL:** llms-txt#example-usage-with-knowledge

**Contents:**
- Usage

knowledge = Knowledge(
    vector_db=PgVector(
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        table_name="jina_embeddings",
        embedder=JinaEmbedder(
            late_chunking=True,  # Better handling of long documents
            timeout=30.0,  # Configure request timeout
        ),
    ),
    max_results=2,
)

bash  theme={null}
    export JINA_API_KEY=xxx
    bash  theme={null}
    pip install -U sqlalchemy psycopg pgvector aiohttp requests agno
    bash  theme={null}
    docker run -d \
      -e POSTGRES_DB=ai \
      -e POSTGRES_USER=ai \
      -e POSTGRES_PASSWORD=ai \
      -e PGDATA=/var/lib/postgresql/data/pgdata \
      -v pgvolume:/var/lib/postgresql/data \
      -p 5532:5432 \
      --name pgvector \
      agnohq/pgvector:16
    bash Mac theme={null}
      python cookbook/knowledge/embedders/jina_embedder.py
      bash Windows theme={null}
      python cookbook/knowledge/embedders/jina_embedder.py 
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

  <Step title="Run PgVector">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

---

## ************* Run AgentOS *************

**URL:** llms-txt#*************-run-agentos-*************

**Contents:**
- What is the AgentOS?
- The Complete Agentic Solution
- Getting started

if __name__ == "__main__":
    agent_os.serve(app="agno_agent:app", reload=True)
```

## What is the AgentOS?

AgentOS is a high-performance runtime for multi-agent systems. Key features include:

1. **Pre-built FastAPI runtime**: AgentOS ships with a ready-to-use FastAPI app for orchestrating your agents, teams, and workflows. This gives you a major head start in building your AI product.

2. **Integrated Control Plane**: The [AgentOS UI](https://os.agno.com) connects directly to your runtime, letting you test, monitor, and manage your system in real time. This gives you unmatched visibility and control over your system.

3. **Private by Design**: AgentOS runs entirely in your cloud, ensuring complete data privacy. No data ever leaves your system. This is ideal for security-conscious enterprises.

Here's what the [AgentOS UI](https://os.agno.com) looks like in action:

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/aEfJPs-hg36UsUPO/videos/agno-agent-chat.mp4?fit=max&auto=format&n=aEfJPs-hg36UsUPO&q=85&s=b8ac56bfb2e9436799299fcafa746d4a" type="video/mp4" data-path="videos/agno-agent-chat.mp4" />
  </video>
</Frame>

## The Complete Agentic Solution

For companies building agents, Agno provides the complete solution:

* The fastest framework for building agents, multi-agent teams and agentic workflows.
* A ready-to-use FastAPI app that gets you building AI products on day one.
* A control plane for testing, monitoring and managing your system.

We bring a novel architecture that no other framework provides, your AgentOS runs securely in your cloud, and the control plane connects directly to it from your browser. You don't need to send data to any external services or pay retention costs, you get complete privacy and control.

If you're new to Agno, follow the [quickstart](/introduction/quickstart) to build your first Agent and run it using the AgentOS.

After that, checkout the [examples gallery](/examples/introduction) and build real-world applications with Agno.

<Tip>
  If you're looking for Agno 1.0 docs, please visit [docs-v1.agno.com](https://docs-v1.agno.com).

We also have a [migration guide](/how-to/v2-migration) for those coming from Agno 1.0.
</Tip>

---

## Create AgentOS

**URL:** llms-txt#create-agentos

**Contents:**
- Testing the Example

agent_os = AgentOS(
    id="agentos-hitl",
    agents=[agent],
)

app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="hitl_confirmation:app", port=7777)
bash  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
## Testing the Example

Once the server is running, test the HITL flow:
```

---

## Competitor Analysis Agent

**URL:** llms-txt#competitor-analysis-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/use-cases/agents/competitor_analysis_agent

This example demonstrates how to build a sophisticated competitor analysis agent that combines powerful search and scraping capabilities with advanced reasoning tools to provide
comprehensive competitive intelligence. The agent performs deep analysis of competitors including
market positioning, product offerings, and strategic insights.

* Company discovery using Firecrawl search
* Website scraping and content analysis
* Competitive intelligence gathering
* SWOT analysis with reasoning
* Strategic recommendations
* Structured thinking and analysis

Example queries to try:

* "Analyze OpenAI's main competitors in the LLM space"
* "Compare Uber vs Lyft in the ride-sharing market"
* "Analyze Tesla's competitive position vs traditional automakers"
* "Research fintech competitors to Stripe"
* "Analyze Nike vs Adidas in the athletic apparel market"

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Image Compare Agent

**URL:** llms-txt#image-compare-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/mistral/image_compare_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Initialize the Agent with the knowledge base and filters

**URL:** llms-txt#initialize-the-agent-with-the-knowledge-base-and-filters

**Contents:**
- Usage

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    debug_mode=True,
)

agent.print_response(
    "Tell me about Jordan Mitchell's experience and skills",
    knowledge_filters={"user_id": "jordan_mitchell"},
    markdown=True,
)

bash  theme={null}
    pip install -U agno surrealdb openai
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    docker run --rm --pull always -p 8000:8000 surrealdb/surrealdb:latest start --user root --pass root     
    bash Mac theme={null}
      python cookbook/knowledge/filters/vector_dbs/filtering_surrealdb.py
      bash Windows theme={null}
      python cookbook/knowledge/filters/vector_dbs/filtering_surrealdb.py
      ```
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run SurrealDB">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run the example">
    <CodeGroup>
```

---

## Capturing Agent Response as Variable

**URL:** llms-txt#capturing-agent-response-as-variable

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/response_as_variable

This example demonstrates how to capture and work with agent responses as variables, enabling programmatic access to response data and metadata.

```python response_as_variable.py theme={null}
from typing import Iterator  # noqa
from rich.pretty import pprint
from agno.agent import Agent, RunOutput
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[
        DuckDuckGoTools(
            stock_price=True,
            analyst_recommendations=True,
            company_info=True,
            company_news=True,
        )
    ],
    instructions=["Use tables where possible"],
    markdown=True,
)

run_response: RunOutput = agent.run("What is the stock price of NVDA")
pprint(run_response)

---

## Human-in-the-Loop in Agents

**URL:** llms-txt#human-in-the-loop-in-agents

**Contents:**
- Types of Human-in-the-Loop
- Pausing Agent Execution
- User Confirmation

Source: https://docs.agno.com/concepts/hitl/overview

Learn how to control the flow of an agent's execution in Agno.

Human-in-the-Loop (HITL) in Agno enable you to implement patterns where human oversight and input are required during agent execution. This is crucial for:

* Validating sensitive operations
* Reviewing tool calls before execution
* Gathering user input for decision-making
* Managing external tool execution

## Types of Human-in-the-Loop

Agno supports four main types of human-in-the-loop flows:

1. **User Confirmation**: Require explicit user approval before executing tool calls
2. **User Input**: Gather specific information from users during execution
3. **Dynamic User Input**: Have the agent collect user input as it needs it
4. **External Tool Execution**: Execute tools outside of the agent's control

<Note>
  Currently Agno only supports user control flows for `Agent`. `Team` and `Workflow` will be supported in the near future!
</Note>

## Pausing Agent Execution

Human-in-the-loop flows interrupt the agent's execution and require human oversight. The run can then be continued by calling the `continue_run` method.

The `continue_run` method continues with the state of the agent at the time of the pause.  You can also pass the `RunOutput` of a specific run to the `continue_run` method, or pass the `run_id` and list of updated tools in the `updated_tools` parameter.

User confirmation allows you to pause execution and require explicit user approval before proceeding with tool calls. This is useful for:

* Sensitive operations
* API calls that modify data
* Actions with significant consequences

The following example shows how to implement user confirmation.

```python  theme={null}
from agno.tools import tool
from agno.agent import Agent
from agno.models.openai import OpenAIChat

@tool(requires_confirmation=True)
def sensitive_operation(data: str) -> str:
    """Perform a sensitive operation that requires confirmation."""
    # Implementation here
    return "Operation completed"

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[sensitive_operation],
)

**Examples:**

Example 1 (unknown):
```unknown
The `continue_run` method continues with the state of the agent at the time of the pause.  You can also pass the `RunOutput` of a specific run to the `continue_run` method, or pass the `run_id` and list of updated tools in the `updated_tools` parameter.

## User Confirmation

User confirmation allows you to pause execution and require explicit user approval before proceeding with tool calls. This is useful for:

* Sensitive operations
* API calls that modify data
* Actions with significant consequences

The following example shows how to implement user confirmation.
```

---

## LangChain

**URL:** llms-txt#langchain

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/langchain/langchain-db

```python cookbook/knowledge/vector_db/langchain/langchain_db.py theme={null}
import pathlib
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.langchaindb import LangChainVectorDb
from langchain.text_splitter import CharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.document_loaders import TextLoader
from langchain_openai import OpenAIEmbeddings

---

## Setup in-memory database

**URL:** llms-txt#setup-in-memory-database

---

## The Agent sessions and runs will now be stored in SQLite

**URL:** llms-txt#the-agent-sessions-and-runs-will-now-be-stored-in-sqlite

**Contents:**
- Params
- Developer Resources

agent.print_response("How many people live in Canada?")
agent.print_response("What is their national anthem?")
agent.print_response("List my messages one by one")

<Snippet file="db-sqlite-params.mdx" />

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/db/sqllite/sqlite_for_agent.py)

---

## "[Bug] Async tools in team of agents not awaited properly, causing runtime errors ",

**URL:** llms-txt#"[bug]-async-tools-in-team-of-agents-not-awaited-properly,-causing-runtime-errors-",

---

## ------------------------------------------------------------------------------

**URL:** llms-txt#------------------------------------------------------------------------------

**Contents:**
- Usage

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
)

agent.print_response(
    "Tell me about Jordan Mitchell's experience and skills",
    knowledge_filters={"user_id": "jordan_mitchell"},
    markdown=True,
)

bash  theme={null}
    pip install -U agno weaviate-client openai
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Weaviate Cloud theme={null}
      # 1. Create account at https://console.weaviate.cloud/
      # 2. Create a cluster and copy the "REST endpoint" and "Admin" API Key
      # 3. Set environment variables:
      export WCD_URL="your-cluster-url" 
      export WCD_API_KEY="your-api-key"
      # 4. Set local=False in the code
      bash Local Development theme={null}
      # 1. Install Docker from https://docs.docker.com/get-docker/
      # 2. Run Weaviate locally:
      docker run -d \
          -p 8080:8080 \
          -p 50051:50051 \
          --name weaviate \
          cr.weaviate.io/semitechnologies/weaviate:1.28.4
      # 3. Set local=True in the code
      bash Mac theme={null}
      python cookbook/knowledge/filters/vector_dbs/filtering_weaviate.py
      bash Windows theme={null}
      python cookbook/knowledge/filters/vector_dbs/filtering_weaviate.py
      ```
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Setup Weaviate">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Run the agent (non-streaming)

**URL:** llms-txt#run-the-agent-(non-streaming)

print("Running with reasoning_model specified (non-streaming)...")
response = agent_with_reasoning_model.run(
    "What is the sum of the first 10 natural numbers?"
)

---

## Agent with Metrics

**URL:** llms-txt#agent-with-metrics

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/groq/metrics

```python cookbook/models/groq/metrics.py theme={null}
from agno.agent import Agent, RunOutput
from agno.models.groq import Groq
from agno.tools.yfinance import YFinanceTools
from agno.utils.pprint import pprint_run_response
from rich.pretty import pprint

agent = Agent(
    model=Groq(id="llama-3.3-70b-versatile"),
    tools=[YFinanceTools(stock_price=True)],
    markdown=True,
)

run_output: RunOutput = agent.run("What is the stock price of NVDA")
pprint_run_response(run_output)

---

## Async Postgres for Agent

**URL:** llms-txt#async-postgres-for-agent

**Contents:**
- Usage
  - Run PgVector
- Params
- Developer Resources

Source: https://docs.agno.com/examples/concepts/db/async_postgres/async_postgres_for_agent

Agno supports using [PostgreSQL](https://www.postgresql.org/) asynchronously, with the `AsyncPostgresDb` class.

Install [docker desktop](https://docs.docker.com/desktop/install/mac-install/) and run **PgVector** on port **5532** using:

<Snippet file="db-async-postgres-params.mdx" />

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/db/async_postgres/async_postgres_for_agent.py)

**Examples:**

Example 1 (unknown):
```unknown

```

---

## Agent

**URL:** llms-txt#agent

**Contents:**
- Parameters
- Functions
  - `run`
  - `arun`
  - `continue_run`
  - `acontinue_run`
  - `print_response`
  - `aprint_response`
  - `cli_app`
  - `acli_app`

Source: https://docs.agno.com/reference/agents/agent

| Parameter                          | Type                                                             | Default    | Description                                                                                                                                                                                                                      |
| ---------------------------------- | ---------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `model`                            | `Optional[Model]`                                                | `None`     | Model to use for this Agent                                                                                                                                                                                                      |
| `name`                             | `Optional[str]`                                                  | `None`     | Agent name                                                                                                                                                                                                                       |
| `id`                               | `Optional[str]`                                                  | `None`     | Agent ID (autogenerated UUID if not set)                                                                                                                                                                                         |
| `user_id`                          | `Optional[str]`                                                  | `None`     | Default user\_id to use for this agent                                                                                                                                                                                           |
| `session_id`                       | `Optional[str]`                                                  | `None`     | Default session\_id to use for this agent (autogenerated if not set)                                                                                                                                                             |
| `session_state`                    | `Optional[Dict[str, Any]]`                                       | `None`     | Default session state (stored in the database to persist across runs)                                                                                                                                                            |
| `add_session_state_to_context`     | `bool`                                                           | `False`    | Set to True to add the session\_state to the context                                                                                                                                                                             |
| `enable_agentic_state`             | `bool`                                                           | `False`    | Set to True to give the agent tools to update the session\_state dynamically                                                                                                                                                     |
| `overwrite_db_session_state`       | `bool`                                                           | `False`    | Set to True to overwrite the session state in the database with the session state provided in the run                                                                                                                            |
| `cache_session`                    | `bool`                                                           | `False`    | If True, cache the current Agent session in memory for faster access                                                                                                                                                             |
| `search_session_history`           | `Optional[bool]`                                                 | `False`    | Set this to `True` to allow searching through previous sessions.                                                                                                                                                                 |
| `num_history_sessions`             | `Optional[int]`                                                  | `None`     | Specify the number of past sessions to include in the search. It's advisable to keep this number to 2 or 3 for now, as a larger number might fill up the context length of the model, potentially leading to performance issues. |
| `dependencies`                     | `Optional[Dict[str, Any]]`                                       | `None`     | Dependencies available for tools and prompt functions                                                                                                                                                                            |
| `add_dependencies_to_context`      | `bool`                                                           | `False`    | If True, add the dependencies to the user prompt                                                                                                                                                                                 |
| `db`                               | `Optional[BaseDb]`                                               | `None`     | Database to use for this agent                                                                                                                                                                                                   |
| `memory_manager`                   | `Optional[MemoryManager]`                                        | `None`     | Memory manager to use for this agent                                                                                                                                                                                             |
| `enable_agentic_memory`            | `bool`                                                           | `False`    | Enable the agent to manage memories of the user                                                                                                                                                                                  |
| `enable_user_memories`             | `bool`                                                           | `False`    | If True, the agent creates/updates user memories at the end of runs                                                                                                                                                              |
| `add_memories_to_context`          | `Optional[bool]`                                                 | `None`     | If True, the agent adds a reference to the user memories in the response                                                                                                                                                         |
| `enable_session_summaries`         | `bool`                                                           | `False`    | If True, the agent creates/updates session summaries at the end of runs                                                                                                                                                          |
| `add_session_summary_to_context`   | `Optional[bool]`                                                 | `None`     | If True, the agent adds session summaries to the context                                                                                                                                                                         |
| `session_summary_manager`          | `Optional[SessionSummaryManager]`                                | `None`     | Session summary manager                                                                                                                                                                                                          |
| `add_history_to_context`           | `bool`                                                           | `False`    | Add the chat history of the current session to the messages sent to the Model                                                                                                                                                    |
| `num_history_runs`                 | `int`                                                            | `3`        | Number of historical runs to include in the messages.                                                                                                                                                                            |
| `knowledge`                        | `Optional[Knowledge]`                                            | `None`     | Agent Knowledge                                                                                                                                                                                                                  |
| `knowledge_filters`                | `Optional[Dict[str, Any]]`                                       | `None`     | Knowledge filters to apply to the knowledge base                                                                                                                                                                                 |
| `enable_agentic_knowledge_filters` | `Optional[bool]`                                                 | `None`     | Let the agent choose the knowledge filters                                                                                                                                                                                       |
| `add_knowledge_to_context`         | `bool`                                                           | `False`    | Enable RAG by adding references from Knowledge to the user prompt                                                                                                                                                                |
| `knowledge_retriever`              | `Optional[Callable[..., Optional[List[Union[Dict, str]]]]]`      | `None`     | Function to get references to add to the user\_message                                                                                                                                                                           |
| `references_format`                | `Literal["json", "yaml"]`                                        | `"json"`   | Format of the references                                                                                                                                                                                                         |
| `metadata`                         | `Optional[Dict[str, Any]]`                                       | `None`     | Metadata stored with this agent                                                                                                                                                                                                  |
| `tools`                            | `Optional[List[Union[Toolkit, Callable, Function, Dict]]]`       | `None`     | A list of tools provided to the Model                                                                                                                                                                                            |
| `tool_call_limit`                  | `Optional[int]`                                                  | `None`     | Maximum number of tool calls allowed for a single run                                                                                                                                                                            |
| `tool_choice`                      | `Optional[Union[str, Dict[str, Any]]]`                           | `None`     | Controls which (if any) tool is called by the model                                                                                                                                                                              |
| `max_tool_calls_from_history`      | `Optional[int]`                                                  | `None`     | Maximum number of tool calls from history to keep in context. If None, all tool calls from history are included. If set to N, only the last N tool calls from history are added to the context for memory management             |
| `tool_hooks`                       | `Optional[List[Callable]]`                                       | `None`     | Functions that will run between tool calls                                                                                                                                                                                       |
| `pre_hooks`                        | `Optional[Union[List[Callable[..., Any]], List[BaseGuardrail]]]` | `None`     | Functions called right after agent-session is loaded, before processing starts                                                                                                                                                   |
| `post_hooks`                       | `Optional[Union[List[Callable[..., Any]], List[BaseGuardrail]]]` | `None`     | Functions called after output is generated but before the response is returned                                                                                                                                                   |
| `reasoning`                        | `bool`                                                           | `False`    | Enable reasoning by working through the problem step by step                                                                                                                                                                     |
| `reasoning_model`                  | `Optional[Model]`                                                | `None`     | Model to use for reasoning                                                                                                                                                                                                       |
| `reasoning_agent`                  | `Optional[Agent]`                                                | `None`     | Agent to use for reasoning                                                                                                                                                                                                       |
| `reasoning_min_steps`              | `int`                                                            | `1`        | Minimum number of reasoning steps                                                                                                                                                                                                |
| `reasoning_max_steps`              | `int`                                                            | `10`       | Maximum number of reasoning steps                                                                                                                                                                                                |
| `read_chat_history`                | `bool`                                                           | `False`    | Add a tool that allows the Model to read the chat history                                                                                                                                                                        |
| `search_knowledge`                 | `bool`                                                           | `True`     | Add a tool that allows the Model to search the knowledge base                                                                                                                                                                    |
| `update_knowledge`                 | `bool`                                                           | `False`    | Add a tool that allows the Model to update the knowledge base                                                                                                                                                                    |
| `read_tool_call_history`           | `bool`                                                           | `False`    | Add a tool that allows the Model to get the tool call history                                                                                                                                                                    |
| `send_media_to_model`              | `bool`                                                           | `True`     | If False, media (images, videos, audio, files) is only available to tools and not sent to the LLM                                                                                                                                |
| `store_media`                      | `bool`                                                           | `True`     | If True, store media in the database                                                                                                                                                                                             |
| `store_tool_messages`              | `bool`                                                           | `True`     | If True, store tool results in the database                                                                                                                                                                                      |
| `store_history_messages`           | `bool`                                                           | `True`     | If True, store history messages in the database                                                                                                                                                                                  |
| `system_message`                   | `Optional[Union[str, Callable, Message]]`                        | `None`     | Provide the system message as a string or function                                                                                                                                                                               |
| `system_message_role`              | `str`                                                            | `"system"` | Role for the system message                                                                                                                                                                                                      |
| `build_context`                    | `bool`                                                           | `True`     | Set to False to skip context building                                                                                                                                                                                            |
| `description`                      | `Optional[str]`                                                  | `None`     | A description of the Agent that is added to the start of the system message                                                                                                                                                      |
| `instructions`                     | `Optional[Union[str, List[str], Callable]]`                      | `None`     | List of instructions for the agent                                                                                                                                                                                               |
| `expected_output`                  | `Optional[str]`                                                  | `None`     | Provide the expected output from the Agent                                                                                                                                                                                       |
| `additional_context`               | `Optional[str]`                                                  | `None`     | Additional context added to the end of the system message                                                                                                                                                                        |
| `markdown`                         | `bool`                                                           | `False`    | If markdown=true, add instructions to format the output using markdown                                                                                                                                                           |
| `add_name_to_context`              | `bool`                                                           | `False`    | If True, add the agent name to the instructions                                                                                                                                                                                  |
| `add_datetime_to_context`          | `bool`                                                           | `False`    | If True, add the current datetime to the instructions to give the agent a sense of time                                                                                                                                          |
| `add_location_to_context`          | `bool`                                                           | `False`    | If True, add the current location to the instructions to give the agent a sense of place                                                                                                                                         |
| `timezone_identifier`              | `Optional[str]`                                                  | `None`     | Allows for custom timezone for datetime instructions following the TZ Database format (e.g. "Etc/UTC")                                                                                                                           |
| `resolve_in_context`               | `bool`                                                           | `True`     | If True, resolve session\_state, dependencies, and metadata in the user and system messages                                                                                                                                      |
| `additional_input`                 | `Optional[List[Union[str, Dict, BaseModel, Message]]]`           | `None`     | A list of extra messages added after the system message and before the user message                                                                                                                                              |
| `user_message_role`                | `str`                                                            | `"user"`   | Role for the user message                                                                                                                                                                                                        |
| `build_user_context`               | `bool`                                                           | `True`     | Set to False to skip building the user context                                                                                                                                                                                   |
| `retries`                          | `int`                                                            | `0`        | Number of retries to attempt                                                                                                                                                                                                     |
| `delay_between_retries`            | `int`                                                            | `1`        | Delay between retries (in seconds)                                                                                                                                                                                               |
| `exponential_backoff`              | `bool`                                                           | `False`    | If True, the delay between retries is doubled each time                                                                                                                                                                          |
| `input_schema`                     | `Optional[Type[BaseModel]]`                                      | `None`     | Provide an input schema to validate the input                                                                                                                                                                                    |
| `output_schema`                    | `Optional[Type[BaseModel]]`                                      | `None`     | Provide a response model to get the response as a Pydantic model                                                                                                                                                                 |
| `parser_model`                     | `Optional[Model]`                                                | `None`     | Provide a secondary model to parse the response from the primary model                                                                                                                                                           |
| `parser_model_prompt`              | `Optional[str]`                                                  | `None`     | Provide a prompt for the parser model                                                                                                                                                                                            |
| `output_model`                     | `Optional[Model]`                                                | `None`     | Provide an output model to structure the response from the main model                                                                                                                                                            |
| `output_model_prompt`              | `Optional[str]`                                                  | `None`     | Provide a prompt for the output model                                                                                                                                                                                            |
| `parse_response`                   | `bool`                                                           | `True`     | If True, the response from the Model is converted into the output\_schema                                                                                                                                                        |
| `structured_outputs`               | `Optional[bool]`                                                 | `None`     | Use model enforced structured\_outputs if supported (e.g. OpenAIChat)                                                                                                                                                            |
| `use_json_mode`                    | `bool`                                                           | `False`    | If `output_schema` is set, sets the response mode of the model, i.e. if the model should explicitly respond with a JSON object instead of a Pydantic model                                                                       |
| `save_response_to_file`            | `Optional[str]`                                                  | `None`     | Save the response to a file                                                                                                                                                                                                      |
| `stream`                           | `Optional[bool]`                                                 | `None`     | Stream the response from the Agent                                                                                                                                                                                               |
| `stream_events`                    | `bool`                                                           | `False`    | Stream the intermediate steps from the Agent                                                                                                                                                                                     |
| `store_events`                     | `bool`                                                           | `False`    | Persist the events on the run response                                                                                                                                                                                           |
| `events_to_skip`                   | `Optional[List[RunEvent]]`                                       | `None`     | Specify which event types to skip when storing events on the RunOutput                                                                                                                                                           |
| `role`                             | `Optional[str]`                                                  | `None`     | If this Agent is part of a team, this is the role of the agent in the team                                                                                                                                                       |
| `debug_mode`                       | `bool`                                                           | `False`    | Enable debug logs                                                                                                                                                                                                                |
| `debug_level`                      | `Literal[1, 2]`                                                  | `1`        | Debug level for logging                                                                                                                                                                                                          |
| `telemetry`                        | `bool`                                                           | `True`     | Log minimal telemetry for analytics                                                                                                                                                                                              |

* `input` (Union\[str, List, Dict, Message, BaseModel, List\[Message]]): The input to send to the agent
* `stream` (Optional\[bool]): Whether to stream the response
* `stream_events` (Optional\[bool]): Whether to stream intermediate steps
* `user_id` (Optional\[str]): User ID to use
* `session_id` (Optional\[str]): Session ID to use
* `session_state` (Optional\[Dict\[str, Any]]): Session state to use. By default, merged with the session state in the db.
* `audio` (Optional\[Sequence\[Audio]]): Audio files to include
* `images` (Optional\[Sequence\[Image]]): Image files to include
* `videos` (Optional\[Sequence\[Video]]): Video files to include
* `files` (Optional\[Sequence\[File]]): Files to include
* `retries` (Optional\[int]): Number of retries to attempt
* `knowledge_filters` (Optional\[Dict\[str, Any]]): Knowledge filters to apply
* `add_history_to_context` (Optional\[bool]): Whether to add history to context
* `add_dependencies_to_context` (Optional\[bool]): Whether to add dependencies to context
* `add_session_state_to_context` (Optional\[bool]): Whether to add session state to context
* `dependencies` (Optional\[Dict\[str, Any]]): Dependencies to use for this run
* `metadata` (Optional\[Dict\[str, Any]]): Metadata to use for this run
* `debug_mode` (Optional\[bool]): Whether to enable debug mode

Run the agent asynchronously.

* `input` (Union\[str, List, Dict, Message, BaseModel, List\[Message]]): The input to send to the agent
* `stream` (Optional\[bool]): Whether to stream the response
* `user_id` (Optional\[str]): User ID to use
* `session_id` (Optional\[str]): Session ID to use
* `session_state` (Optional\[Dict\[str, Any]]): Session state to use. By default, merged with the session state in the db.
* `audio` (Optional\[Sequence\[Audio]]): Audio files to include
* `images` (Optional\[Sequence\[Image]]): Image files to include
* `videos` (Optional\[Sequence\[Video]]): Video files to include
* `files` (Optional\[Sequence\[File]]): Files to include
* `stream_events` (Optional\[bool]): Whether to stream intermediate steps
* `retries` (Optional\[int]): Number of retries to attempt
* `knowledge_filters` (Optional\[Dict\[str, Any]]): Knowledge filters to apply
* `add_history_to_context` (Optional\[bool]): Whether to add history to context
* `add_dependencies_to_context` (Optional\[bool]): Whether to add dependencies to context
* `add_session_state_to_context` (Optional\[bool]): Whether to add session state to context
* `dependencies` (Optional\[Dict\[str, Any]]): Dependencies to use for this run
* `metadata` (Optional\[Dict\[str, Any]]): Metadata to use for this run
* `debug_mode` (Optional\[bool]): Whether to enable debug mode

* `Union[RunOutput, AsyncIterator[RunOutputEvent]]`: Either a RunOutput or an iterator of RunOutputEvents, depending on the `stream` parameter

* `run_response` (Optional\[RunOutput]): The run response to continue
* `run_id` (Optional\[str]): The run ID to continue
* `updated_tools` (Optional\[List\[ToolExecution]]): Updated tools to use, required if the run is resumed using `run_id`
* `stream` (Optional\[bool]): Whether to stream the response
* `stream_events` (Optional\[bool]): Whether to stream intermediate steps
* `user_id` (Optional\[str]): User ID to use
* `session_id` (Optional\[str]): Session ID to use
* `retries` (Optional\[int]): Number of retries to attempt
* `knowledge_filters` (Optional\[Dict\[str, Any]]): Knowledge filters to apply
* `dependencies` (Optional\[Dict\[str, Any]]): Dependencies to use for this run
* `debug_mode` (Optional\[bool]): Whether to enable debug mode

* `Union[RunOutput, Iterator[RunOutputEvent]]`: Either a RunOutput or an iterator of RunOutputEvents, depending on the `stream` parameter

Continue a run asynchronously.

* `run_response` (Optional\[RunOutput]): The run response to continue
* `run_id` (Optional\[str]): The run ID to continue
* `updated_tools` (Optional\[List\[ToolExecution]]): Updated tools to use, required if the run is resumed using `run_id`
* `stream` (Optional\[bool]): Whether to stream the response
* `stream_events` (Optional\[bool]): Whether to stream intermediate steps
* `user_id` (Optional\[str]): User ID to use
* `session_id` (Optional\[str]): Session ID to use
* `retries` (Optional\[int]): Number of retries to attempt
* `knowledge_filters` (Optional\[Dict\[str, Any]]): Knowledge filters to apply
* `dependencies` (Optional\[Dict\[str, Any]]): Dependencies to use for this run
* `debug_mode` (Optional\[bool]): Whether to enable debug mode

* `Union[RunOutput, AsyncIterator[Union[RunOutputEvent, RunOutput]]]`: Either a RunOutput or an iterator of RunOutputEvents, depending on the `stream` parameter

Run the agent and print the response.

* `input` (Union\[List, Dict, str, Message, BaseModel, List\[Message]]): The input to send to the agent
* `session_id` (Optional\[str]): Session ID to use
* `session_state` (Optional\[Dict\[str, Any]]): Session state to use. By default, merged with the session state in the db.
* `user_id` (Optional\[str]): User ID to use
* `audio` (Optional\[Sequence\[Audio]]): Audio files to include
* `images` (Optional\[Sequence\[Image]]): Image files to include
* `videos` (Optional\[Sequence\[Video]]): Video files to include
* `files` (Optional\[Sequence\[File]]): Files to include
* `stream` (Optional\[bool]): Whether to stream the response
* `stream_events` (Optional\[bool]): Whether to stream intermediate steps
* `markdown` (Optional\[bool]): Whether to format output as markdown
* `show_message` (bool): Whether to show the input message
* `show_reasoning` (bool): Whether to show reasoning steps
* `show_full_reasoning` (bool): Whether to show full reasoning information
* `console` (Optional\[Any]): Console to use for output
* `tags_to_include_in_markdown` (Optional\[Set\[str]]): Tags to include in markdown content
* `knowledge_filters` (Optional\[Dict\[str, Any]]): Knowledge filters to apply
* `add_history_to_context` (Optional\[bool]): Whether to add history to context
* `dependencies` (Optional\[Dict\[str, Any]]): Dependencies to use for this run
* `add_dependencies_to_context` (Optional\[bool]): Whether to add dependencies to context
* `add_session_state_to_context` (Optional\[bool]): Whether to add session state to context
* `metadata` (Optional\[Dict\[str, Any]]): Metadata to use for this run
* `debug_mode` (Optional\[bool]): Whether to enable debug mode

### `aprint_response`

Run the agent and print the response asynchronously.

* `input` (Union\[List, Dict, str, Message, BaseModel, List\[Message]]): The input to send to the agent
* `session_id` (Optional\[str]): Session ID to use
* `session_state` (Optional\[Dict\[str, Any]]): Session state to use. By default, merged with the session state in the db.
* `user_id` (Optional\[str]): User ID to use
* `audio` (Optional\[Sequence\[Audio]]): Audio files to include
* `images` (Optional\[Sequence\[Image]]): Image files to include
* `videos` (Optional\[Sequence\[Video]]): Video files to include
* `files` (Optional\[Sequence\[File]]): Files to include
* `stream` (Optional\[bool]): Whether to stream the response
* `stream_events` (Optional\[bool]): Whether to stream intermediate steps
* `markdown` (Optional\[bool]): Whether to format output as markdown
* `show_message` (bool): Whether to show the message
* `show_reasoning` (bool): Whether to show reasoning
* `show_full_reasoning` (bool): Whether to show full reasoning
* `console` (Optional\[Any]): Console to use for output
* `tags_to_include_in_markdown` (Optional\[Set\[str]]): Tags to include in markdown content
* `knowledge_filters` (Optional\[Dict\[str, Any]]): Knowledge filters to apply
* `add_history_to_context` (Optional\[bool]): Whether to add history to context
* `add_dependencies_to_context` (Optional\[bool]): Whether to add dependencies to context
* `add_session_state_to_context` (Optional\[bool]): Whether to add session state to context
* `dependencies` (Optional\[Dict\[str, Any]]): Dependencies to use for this run
* `metadata` (Optional\[Dict\[str, Any]]): Metadata to use for this run
* `debug_mode` (Optional\[bool]): Whether to enable debug mode

Run an interactive command-line interface to interact with the agent.

* `input` (Optional\[str]): The input to send to the agent
* `session_id` (Optional\[str]): Session ID to use
* `user_id` (Optional\[str]): User ID to use
* `user` (str): Name for the user (default: "User")
* `emoji` (str): Emoji for the user (default: ":sunglasses:")
* `stream` (bool): Whether to stream the response (default: False)
* `markdown` (bool): Whether to format output as markdown (default: False)
* `exit_on` (Optional\[List\[str]]): List of commands to exit the CLI
* `**kwargs`: Additional keyword arguments

Run an interactive command-line interface to interact with the agent asynchronously.

* `input` (Optional\[str]): The input to send to the agent
* `session_id` (Optional\[str]): Session ID to use
* `user_id` (Optional\[str]): User ID to use
* `user` (str): Name for the user (default: "User")
* `emoji` (str): Emoji for the user (default: ":sunglasses:")
* `stream` (bool): Whether to stream the response (default: False)
* `markdown` (bool): Whether to format output as markdown (default: False)
* `exit_on` (Optional\[List\[str]]): List of commands to exit the CLI
* `**kwargs`: Additional keyword arguments

Cancel a run by run ID.

* `run_id` (str): The run ID to cancel

* `bool`: True if the run was successfully cancelled

Get the run output for the given run ID.

* `run_id` (str): The run ID
* `session_id` (str): Session ID to use

* `Optional[RunOutput]`: The run output

### get\_last\_run\_output

Get the last run output for the session.

* `session_id` (str): Session ID to use

* `Optional[RunOutput]`: The last run output

Get the session for the given session ID.

* `session_id` (str): Session ID to use

* `Optional[AgentSession]`: The agent session

### get\_session\_summary

Get the session summary for the given session ID.

* `session_id` (str): Session ID to use

* Session summary for the given session

### get\_user\_memories

Get the user memories for the given user ID.

* `user_id` (str): User ID to use

* `Optional[List[UserMemory]]`: The user memories

### aget\_user\_memories

Get the user memories for the given user ID asynchronously.

* `user_id` (str): User ID to use

* `Optional[List[UserMemory]]`: The user memories

### get\_session\_state

Get the session state for the given session ID.

* `session_id` (str): Session ID to use

* `Dict[str, Any]`: The session state

### update\_session\_state

Update the session state for the given session ID.

* `session_id` (str): Session ID to use
* `session_state_updates` (Dict\[str, Any]): The session state keys and values to update. Overwrites the existing session state.

* `Dict[str, Any]`: The updated session state

### get\_session\_metrics

Get the session metrics for the given session ID.

* `session_id` (str): Session ID to use

* `Optional[Metrics]`: The session metrics

* `session_id` (str): Session ID to delete

Save a session to the database.

* `session` (AgentSession): The session to save

Save a session to the database asynchronously.

* `session` (AgentSession): The session to save

Rename the agent and update the session.

* `name` (str): The new name for the agent
* `session_id` (str): Session ID to use

### get\_session\_name

Get the session name for the given session ID.

* `session_id` (str): Session ID to use

* `str`: The session name

### set\_session\_name

Set the session name.

* `session_id` (str): Session ID to use
* `autogenerate` (bool): Whether to autogenerate the name
* `session_name` (Optional\[str]): The name to set

* `AgentSession`: The updated session

### get\_messages\_for\_session

Get the messages for the given session ID.

* `session_id` (str): Session ID to use

* `List[Message]`: The messages for the session

### get\_chat\_history

Get the chat history for the given session ID.

* `session_id` (str): Session ID to use

* `List[Message]`: The chat history

Add a tool to the agent.

* `tool` (Union\[Toolkit, Callable, Function, Dict]): The tool to add

Replace the tools of the agent.

* `tools` (List\[Union\[Toolkit, Callable, Function, Dict]]): The tools to set

---

## Create a Context-Aware Agent that can access real-time HackerNews data

**URL:** llms-txt#create-a-context-aware-agent-that-can-access-real-time-hackernews-data

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    # Each function in the context is evaluated when the agent is run,
    # think of it as dependency injection for Agents
    dependencies={"top_hackernews_stories": get_top_hackernews_stories},
    # Alternatively, you can manually add the context to the instructions. This gets resolved automatically
    instructions=dedent("""\
        You are an insightful tech trend observer! 📰

Here are the top stories on HackerNews:
        {top_hackernews_stories}\
    """),
    markdown=True,
)

---

## Basic Async Agent Usage

**URL:** llms-txt#basic-async-agent-usage

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/async/basic

This example demonstrates basic asynchronous agent usage with different response handling methods including direct response, print response, and pretty print response.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/async" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## agent.print_response(crypto_prompt, stream=True)

**URL:** llms-txt#agent.print_response(crypto_prompt,-stream=true)

**Contents:**
- Usage
- Customization Options
- Example Prompts

bash  theme={null}
    export OPENAI_API_KEY=xxx
    export EXA_API_KEY=xxx
    export FIRECRAWL_API_KEY=xxx
    bash  theme={null}
    pip install -U agno openai exa-py agno firecrawl
    bash Mac theme={null}
      python cookbook/examples/agents/media_trend_analysis_agent.py
      bash Windows theme={null}
      python cookbook/examples/agents/media_trend_analysis_agent.py
      python  theme={null}

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

## Initialize your Agent passing the database

**URL:** llms-txt#initialize-your-agent-passing-the-database

**Contents:**
  - Adding session history to the context

agent = Agent(db=db)
python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SQLiteDb

**Examples:**

Example 1 (unknown):
```unknown
<Note>
  It's recommended to add `id` for better management and easier identification of database. You can add it to your database configuration like this:
</Note>

### Adding session history to the context

Agents with a `db` will persist their [sessions](/concepts/agents/sessions) in the database. You can also automatically add the persisted history to the context, effectively enabling Agents to persist sessions:
```

---

## Image Agent with Memory

**URL:** llms-txt#image-agent-with-memory

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/together/image_agent_memory

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Delete Memory

**URL:** llms-txt#delete-memory

Source: https://docs.agno.com/reference-api/schema/memory/delete-memory

delete /memories/{memory_id}
Permanently delete a specific user memory. This action cannot be undone.

---

## Create Your First AgentOS

**URL:** llms-txt#create-your-first-agentos

**Contents:**
- Prerequisites
- Installation
- Minimal Setup
- Running Your OS
- Connecting to the Control Plane
- Next Steps

Source: https://docs.agno.com/agent-os/creating-your-first-os

Quick setup guide to get your first AgentOS instance running locally

Get started with AgentOS by setting up a minimal local instance.
This guide will have you running your first agent in minutes, with optional paths to add advanced features through our examples.

<Check>
  AgentOS is a FastAPI app that you can run locally or in your cloud. If you want to build AgentOS using an existing FastAPI app, check out the [Custom FastAPI App](/agent-os/customize/custom-fastapi) guide.
</Check>

* Python 3.9+
* An LLM provider API key (e.g., `OPENAI_API_KEY`)

Create and activate a virtual environment:

Install dependencies:

Access your running instance:

* **App Interface**: `http://localhost:7777` - Use this URL when connecting to the AgentOS control plane
* **API Documentation**: `http://localhost:7777/docs` - Interactive API documentation and testing
* **Configuration**: `http://localhost:7777/config` - View AgentOS configuration
* **API Reference**: View the [AgentOS API documentation](/reference-api/overview) for programmatic access

## Connecting to the Control Plane

With your AgentOS now running locally (`http://localhost:7777`), you can connect it to the AgentOS control plane for a enhanced management experience. The control plane provides a centralized interface to interact with your agents, manage knowledge bases, track sessions, and monitor performance.

<CardGroup cols={2}>
  <Card title="Connect to Control Plane" icon="link" href="/agent-os/connecting-your-os">
    Connect your running OS to the AgentOS control plane interface
  </Card>

<Card title="Browse Examples" icon="code" href="/examples/agent-os/demo">
    Explore comprehensive examples for advanced AgentOS configurations
  </Card>
</CardGroup>

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown
</CodeGroup>

Install dependencies:
```

Example 3 (unknown):
```unknown
## Minimal Setup

Create `my_os.py`:
```

Example 4 (unknown):
```unknown
## Running Your OS

Start your AgentOS:
```

---

## Setup the team

**URL:** llms-txt#setup-the-team

**Contents:**
- Usage

team = Team(
    model=OpenAIChat(id="gpt-5-mini"),
    members=[agent],
    db=db,
    session_id="team_session_cache",
    add_history_to_context=True,
    # Activate session caching. The session will be cached in memory for faster access.
    cache_session=True,
)

team.print_response("Tell me a new interesting fact about space")
bash  theme={null}
    pip install agno psycopg2-binary
    bash  theme={null}
    export OPENAI_API_KEY=****
    bash  theme={null}
    cookbook/run_pgvector.sh
    bash  theme={null}
    python cookbook/examples/teams/session/08_cache_session.py
    ```
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install required libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Start PostgreSQL database">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Setup your Agent using a reasoning model with high reasoning effort

**URL:** llms-txt#setup-your-agent-using-a-reasoning-model-with-high-reasoning-effort

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini", reasoning_effort="high"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

---

## Airbnb MCP agent

**URL:** llms-txt#airbnb-mcp-agent

Source: https://docs.agno.com/examples/concepts/tools/mcp/airbnb

Using the [Airbnb MCP server](https://github.com/openbnb-org/mcp-server-airbnb) to create an Agent that can search for Airbnb listings:

---

## Memori

**URL:** llms-txt#memori

**Contents:**
- Prerequisites
- Example
- Toolkit Params
- Toolkit Functions
- Developer Resources

Source: https://docs.agno.com/concepts/tools/toolkits/others/memori

MemoriTools provides persistent memory capabilities for agents with conversation history, user preferences, and long-term context.

The following example requires the `memorisdk` library.

The following agent can maintain persistent memory across conversations:

| Parameter                    | Type             | Default                           | Description                                                             |
| ---------------------------- | ---------------- | --------------------------------- | ----------------------------------------------------------------------- |
| `database_connect`           | `Optional[str]`  | `sqlite:///agno_memori_memory.db` | Database connection string (SQLite, PostgreSQL, etc.).                  |
| `namespace`                  | `Optional[str]`  | `"agno_default"`                  | Namespace for organizing memories (e.g., "agent\_v1", "user\_session"). |
| `conscious_ingest`           | `bool`           | `True`                            | Whether to use conscious memory ingestion.                              |
| `auto_ingest`                | `bool`           | `True`                            | Whether to automatically ingest conversations into memory.              |
| `verbose`                    | `bool`           | `False`                           | Enable verbose logging from Memori.                                     |
| `config`                     | `Optional[Dict]` | `None`                            | Additional Memori configuration.                                        |
| `auto_enable`                | `bool`           | `True`                            | Automatically enable the memory system on initialization.               |
| `enable_search_memory`       | `bool`           | `True`                            | Enable memory search functionality.                                     |
| `enable_record_conversation` | `bool`           | `True`                            | Enable conversation recording functionality.                            |
| `enable_get_memory_stats`    | `bool`           | `True`                            | Enable memory statistics retrieval.                                     |
| `all`                        | `bool`           | `False`                           | Enable all available tools.                                             |

| Function              | Description                                   |
| --------------------- | --------------------------------------------- |
| `search_memory`       | Search through stored memories using queries. |
| `record_conversation` | Add important information or facts to memory. |
| `get_memory_stats`    | Get statistics about the memory system.       |

You can use `include_tools` or `exclude_tools` to modify the list of tools the agent has access to. Learn more about [selecting tools](/concepts/tools/selecting-tools).

## Developer Resources

* View [Tools Source](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/memori.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/memori_tools.py)
* [Memori SDK Documentation](https://docs.memori.ai/)
* [Memory Management Best Practices](https://memori.ai/best-practices)

**Examples:**

Example 1 (unknown):
```unknown
## Example

The following agent can maintain persistent memory across conversations:
```

---

## Create Memory

**URL:** llms-txt#create-memory

Source: https://docs.agno.com/reference-api/schema/memory/create-memory

post /memories
Create a new user memory with content and associated topics. Memories are used to store contextual information for users across conversations.

---

## Weaviate Async

**URL:** llms-txt#weaviate-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/weaviate-db/async-weaviate-db

```python cookbook/knowledge/vector_db/weaviate_db/async_weaviate_db.py theme={null}

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.search import SearchType
from agno.vectordb.weaviate import Distance, VectorIndex, Weaviate

vector_db = Weaviate(
    collection="recipes_async",
    search_type=SearchType.hybrid,
    vector_index=VectorIndex.HNSW,
    distance=Distance.COSINE,
    local=True,  # Set to False if using Weaviate Cloud and True if using local instance
)

---

## Agent Flex Tier

**URL:** llms-txt#agent-flex-tier

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/openai/responses/agent_flex_tier

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Setup basic agent

**URL:** llms-txt#setup-basic-agent

**Contents:**
- Usage

agno_support_agent = Agent(
    id="agno-support-agent",
    name="Agno Support Agent",
    model=Claude(id="claude-sonnet-4-0"),
    db=db,
    tools=[mcp_tools],
    add_history_to_context=True,
    num_history_runs=3,
    markdown=True,
)

agent_os = AgentOS(
    description="Example app with MCP Tools",
    agents=[agno_support_agent],
)

app = agent_os.get_app()

if __name__ == "__main__":
    """Run your AgentOS.

You can see test your AgentOS at:
    http://localhost:7777/docs

"""
    # Don't use reload=True here, this can cause issues with the lifespan
    agent_os.serve(app="mcp_tools_example:app")

bash  theme={null}
    export ANTHROPIC_API_KEY=your_anthropic_api_key
    bash  theme={null}
    pip install -U agno anthropic fastapi uvicorn sqlalchemy pgvector psycopg
    bash  theme={null}
    # Using Docker
    docker run -d \
      --name agno-postgres \
      -e POSTGRES_DB=ai \
      -e POSTGRES_USER=ai \
      -e POSTGRES_PASSWORD=ai \
      -p 5532:5432 \
      pgvector/pgvector:pg17
    bash Mac theme={null}
      python cookbook/agent_os/mcp/mcp_tools_example.py
      bash Windows theme={null}
      python cookbook/agent_os/mcp/mcp_tools_example.py
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

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Setup PostgreSQL Database">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run Server">
    <CodeGroup>
```

---

## Define agents for different tasks

**URL:** llms-txt#define-agents-for-different-tasks

news_agent = Agent(
    name="News Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[HackerNewsTools()],
    instructions="You are a news researcher. Get the latest tech news and summarize key points.",
)

search_agent = Agent(
    name="Search Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are a search specialist. Find relevant information on given topics.",
)

analysis_agent = Agent(
    name="Analysis Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are an analyst. Analyze the provided information and give insights.",
)

summary_agent = Agent(
    name="Summary Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are a summarizer. Create concise summaries of the provided content.",
)

research_step = Step(
    name="Research Step",
    agent=news_agent,
)

search_step = Step(
    name="Search Step",
    agent=search_agent,
)

def print_stored_events(run_response: WorkflowRunOutput, example_name):
    """Helper function to print stored events in a nice format"""
    print(f"\n--- {example_name} - Stored Events ---")
    if run_response.events:
        print(f"Total stored events: {len(run_response.events)}")
        for i, event in enumerate(run_response.events, 1):
            print(f"  {i}. {event.event}")
    else:
        print("No events stored")
    print()

print("=== Simple Step Workflow with Event Storage ===")
step_workflow = Workflow(
    name="Simple Step Workflow",
    description="Basic workflow demonstrating step event storage",
    db=SqliteDb(
        session_table="workflow_session",
        db_file="tmp/workflow.db",
    ),
    steps=[research_step, search_step],
    store_events=True,
    events_to_skip=[
        WorkflowRunEvent.step_started,
        WorkflowRunEvent.workflow_completed,
        RunEvent.run_content,
        RunEvent.run_started,
        RunEvent.run_completed,
    ],  # Skip step started events to reduce noise
)

print("Running Step workflow with streaming...")
for event in step_workflow.run(
    input="AI trends in 2024",
    stream=True,
    stream_events=True,
):
    # Filter out RunContentEvent from printing to reduce noise
    if not isinstance(
        event, (RunContentEvent, ToolCallStartedEvent, ToolCallCompletedEvent)
    ):
        print(
            f"Event: {event.event if hasattr(event, 'event') else type(event).__name__}"
        )
run_response = step_workflow.get_last_run_output()

print("\nStep workflow completed!")
print(
    f"Total events stored: {len(run_response.events) if run_response and run_response.events else 0}"
)

---

## Stock price and analyst data agent with structured output

**URL:** llms-txt#stock-price-and-analyst-data-agent-with-structured-output

stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat("gpt-5-mini"),
    output_schema=StockAnalysis,
    role="Searches the web for information on a stock.",
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
)

---

## Clean AgentOS setup with tuple middleware pattern! ✨

**URL:** llms-txt#clean-agentos-setup-with-tuple-middleware-pattern!-✨

agent_os = AgentOS(
    description="JWT Protected AgentOS",
    agents=[research_agent],
    base_app=app,
)

---

## Firestore for Agent

**URL:** llms-txt#firestore-for-agent

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/db/firestore/firestore_for_agent

Agno supports using Firestore as a storage backend for Agents using the `FirestoreDb` class.

You need to provide a `project_id` parameter to the `FirestoreDb` class. Firestore will connect automatically using your Google Cloud credentials.

```python firestore_for_agent.py theme={null}
from agno.agent import Agent
from agno.db.firestore import FirestoreDb
from agno.tools.duckduckgo import DuckDuckGoTools

PROJECT_ID = "agno-os-test"  # Use your project ID here

---

## ZDR Reasoning Agent

**URL:** llms-txt#zdr-reasoning-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/openai/responses/zdr_reasoning_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Use default memory manager

**URL:** llms-txt#use-default-memory-manager

memory = MemoryManager(model=Claude(id="claude-3-5-sonnet-latest"), db=memory_db)
jane_doe_id = "jane_doe@example.com"

---

## Setup a basic agent with the SQLite database

**URL:** llms-txt#setup-a-basic-agent-with-the-sqlite-database

**Contents:**
- Usage

agent = Agent(
    db=db,
    enable_user_memories=True,
)

agent.print_response("My name is John Doe and I like to play basketball on the weekends.")
agent.print_response("What's do I do in weekends?")
bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    pip install -U agno openai
    bash Mac/Linux theme={null}
      python cookbook/memory/db/mem-sqlite-memory.py
      bash Windows theme={null}
      python cookbook/memory/db/mem-sqlite-memory.py
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

  <Step title="Set environment variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## for the agent to know what to call.

**URL:** llms-txt#for-the-agent-to-know-what-to-call.

@tool(external_execution=True)
def execute_shell_command(command: str) -> str:
    """Execute a shell command.

Args:
        command (str): The shell command to execute

Returns:
        str: The output of the shell command
    """
    if (
        command.startswith("ls ")
        or command == "ls"
        or command.startswith("cat ")
        or command.startswith("head ")
    ):
        return subprocess.check_output(command, shell=True).decode("utf-8")
    raise Exception(f"Unsupported command: {command}")

agent = Agent(
    model=OpenAIResponses(id="gpt-4.1-mini"),
    tools=[execute_shell_command],
    markdown=True,
)

run_response = asyncio.run(agent.arun("What files do I have in my current directory?"))

---

## Startup Analyst Agent

**URL:** llms-txt#startup-analyst-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/use-cases/agents/startup-analyst-agent

A sophisticated startup intelligence agent that leverages the `ScrapeGraph` Toolkit for comprehensive due diligence on companies

* Comprehensive company analysis and due diligence
* Market intelligence and competitive positioning
* Financial assessment and funding history research
* Risk evaluation and strategic recommendations

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Set environment variables">
    
  </Step>

<Step title="Run the agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## ArXiv Reader

**URL:** llms-txt#arxiv-reader

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/arxiv/arxiv-reader

The **ArXiv Reader** allows you to search and read academic papers from the ArXiv preprint repository, converting them into vector embeddings for your knowledge base.

```python examples/concepts/knowledge/readers/arxiv_reader.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.arxiv_reader import ArxivReader
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

---

## The runs for the team leader and all team members are here

**URL:** llms-txt#the-runs-for-the-team-leader-and-all-team-members-are-here

**Contents:**
  - 3. Memory
  - 4. Knowledge
  - 5. Metrics
  - 6. Teams
  - 7. Workflows
  - 7. Apps -> Interfaces
  - 8. Playground -> AgentOS

team_session.runs
python v1_memory.py theme={null}
from agno.agent import Agent
from agno.memory.v2.db.sqlite import SqliteMemoryDb
from agno.memory.v2.memory import Memory

memory_db = SqliteMemoryDb(table_name="memory", db_file="agno.db")
memory = Memory(db=memory_db)

agent = Agent(memory=memory)
python v2_memory.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="agno.db")

agent = Agent(db=db, enable_user_memories=True)
python v2_memory_set_table.py theme={null}
db = SqliteDb(db_file="agno.db", memory_table="your_memory_table_name")
python v2_memory_db_methods.py theme={null}
agent.get_user_memories(user_id="123")
python  theme={null}
from agno.app.agui.app import AGUIApp

agui_app = AGUIApp(agent=agent)
app = agui_app.get_app()
agui_app.serve(port=8000)
python  theme={null}
from agno.os import AgentOS
from agno.os.interfaces.agui import AGUI

agent_os = AgentOS(agents=[agent], interfaces=[AGUI(agent=agent)])
app = agent_os.get_app()
agent_os.serve(port=8000)
```

1. **Update imports**: Replace app imports with interface imports
2. **Use AgentOS**: Wrap agents with `AgentOS` and specify interfaces
3. **Update serving**: Use `agent_os.serve()` instead of `app.serve()`

### 8. Playground -> AgentOS

Our `Playground` has been deprecated. Our new [AgentOS](/agent-os/introduction) offering will substitute all usecases.

See [AgentOS](/agent-os/introduction) for more details!

**Examples:**

Example 1 (unknown):
```unknown
<Tip>
  See more changes in the [Storage Updates](/how-to/v2-changelog#storage)
  section of the changelog.
</Tip>

### 3. Memory

Memory gives an Agent the ability to recall relevant information.

This is how Memory looks like on V1:
```

Example 2 (unknown):
```unknown
These are the changes we have made for v2:

3.1. The `MemoryDb` classes have been deprecated. The main `Db` classes are to be used.
3.2. The `Memory` class has been deprecated. You now just need to set `enable_user_memories=True` on an Agent with a `db` for Memory to work.
```

Example 3 (unknown):
```unknown
3.3. The generated memories will be stored in the `memories_table`. By default, the `agno_memories` will be used. It will be created if needed. You can also set the memory table like this:
```

Example 4 (unknown):
```unknown
3.4. The methods you previously had access to through the Memory class, are now direclty available on the relevant `db` object. For example:
```

---

## Run the agent

**URL:** llms-txt#run-the-agent

**Contents:**
- Usage

structured_output_agent.print_response("New York")

bash  theme={null}
    ollama pull llama3.2
    bash  theme={null}
    pip install -U ollama agno
    bash Mac theme={null}
      python cookbook/models/ollama/structured_output.py
      bash Windows theme={null}
      python cookbook/models/ollama/structured_output.py
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

  <Step title="Install Ollama">
    Follow the [Ollama installation guide](https://github.com/ollama/ollama?tab=readme-ov-file#macos) and run:
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

## This won't use the session history, but instead will use the memory tools to get the memories

**URL:** llms-txt#this-won't-use-the-session-history,-but-instead-will-use-the-memory-tools-to-get-the-memories

agent.print_response("What have you remembered about me?", stream=True, user_id="john_doe@example.com")
python  theme={null}
from agno.tools.memory import MemoryTools

memory_tools = MemoryTools(
    db=my_database,
    enable_think=True,            # Enable the think tool (true by default)
    enable_get_memories=True,     # Enable the get_memories tool (true by default)
    enable_add_memory=True,       # Enable the add_memory tool (true by default)
    enable_update_memory=True,    # Enable the update_memory tool (true by default)
    enable_delete_memory=True,    # Enable the delete_memory tool (true by default)
    enable_analyze=True,          # Enable the analyze tool (true by default)
    add_instructions=True,        # Add default instructions
    instructions=None,            # Optional custom instructions
    add_few_shot=True,           # Add few-shot examples
    few_shot_examples=None,      # Optional custom few-shot examples
)
```

**Examples:**

Example 1 (unknown):
```unknown
Here is how you can configure the toolkit:
```

---

## Create agent with both Google Search and URL context enabled

**URL:** llms-txt#create-agent-with-both-google-search-and-url-context-enabled

agent = Agent(
    model=Gemini(id="gemini-2.5-flash", search=True, url_context=True),
    markdown=True,
)

---

## Get Memory by ID

**URL:** llms-txt#get-memory-by-id

Source: https://docs.agno.com/reference-api/schema/memory/get-memory-by-id

get /memories/{memory_id}
Retrieve detailed information about a specific user memory by its ID.

---

## Create a knowledge base with the PDFs from the data/pdfs directory

**URL:** llms-txt#create-a-knowledge-base-with-the-pdfs-from-the-data/pdfs-directory

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="pdf_documents",
        db_url=db_url,
    )
)

---

## Memories

**URL:** llms-txt#memories

**Contents:**
- Overview
- Accessing Memories
- Memory Management
- Privacy and Control
- Useful Links

Source: https://docs.agno.com/agent-os/features/memories

View and manage persistent memory storage for your agents in AgentOS

The Memories feature in AgentOS provides a centralized view of information that agents have learned and stored about you as a user. Memory gives agents the ability to recall information about you across conversations, enabling personalized and contextual interactions.

* Memories are created and updated during an agent run
* Each memory is tied to a specific user ID and contains learned information
* Memories include content, topics, timestamps, and the input that generated them
* Agents with memory enabled can learn about you and provide more relevant responses over time

<Note>
  <strong>Prerequisites</strong>: Your AgentOS must be connected and active. If
  you see "Disconnected" or "Inactive," review your{" "}
  <a href="/agent-os/connecting-your-os">connection settings</a>.
</Note>

## Accessing Memories

* Open the `Memory` section in the sidebar.
* View all stored memories in a chronological table format.
* Click the `Refresh` button to sync the latest memory updates.

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/04J6ekYOTyb3RbcL/videos/memory-table-usage.mp4?fit=max&auto=format&n=04J6ekYOTyb3RbcL&q=85&s=4afbe866cc00ed3799f270e642fa842f" type="video/mp4" data-path="videos/memory-table-usage.mp4" />
  </video>
</Frame>

The memory interface allows you to:

1. **Create memories** - Create memories your agents can reference during chat sessions
2. **View by topics** - See memories organized by thematic categories
3. **Edit memories** - Update or correct stored information as needed
4. **Delete memories** - Remove outdated or incorrect information
5. **Monitor memory creation** - See when and from what inputs memories were generated

<Tip>
  Memories are automatically generated from your conversations, but you can also
  manually create, edit, or remove them.
</Tip>

## Privacy and Control

* All memories are tied to a specific user ID and stored in your AgentOS database
* Memories are only accessible to agents within your connected OS instance
* Memory data remains within your deployment and is never shared externally

<CardGroup cols={2}>
  <Card title="Memory Concepts" icon="brain" href="/concepts/memory/overview">
    Learn how memory works and how agents learn about users
  </Card>

<Card title="Privacy & Security" icon="shield-check" href="/agent-os/security">
    Understand data protection and privacy features
  </Card>
</CardGroup>

---

## Media Trend Analysis Agent

**URL:** llms-txt#media-trend-analysis-agent

**Contents:**
  - What It Does
  - Key Features
- Code

Source: https://docs.agno.com/examples/use-cases/agents/media_trend_analysis_agent

The Media Trend Analysis Agent Example demonstrates a sophisticated AI-powered tool designed to analyze media trends, track digital conversations, and provide actionable insights across various online platforms. This agent combines web search capabilities with content scraping to deliver comprehensive trend analysis reports.

This agent specializes in:

* **Trend Identification**: Detects emerging patterns and shifts in media coverage
* **Source Analysis**: Identifies key influencers and authoritative sources
* **Data Extraction**: Gathers information from news sites, social platforms, and digital media
* **Insight Generation**: Provides actionable recommendations based on trend analysis
* **Future Forecasting**: Predicts potential developments based on current patterns

* **Multi-Source Analysis**: Combines Exa search tools with Firecrawl scraping capabilities
* **Intelligent Filtering**: Uses keyword-based searches with date filtering for relevant results
* **Smart Scraping**: Only scrapes content when search results are insufficient
* **Structured Reporting**: Generates comprehensive markdown reports with executive summaries
* **Real-time Data**: Analyzes current trends with configurable time windows

```python cookbook/examples/agents/media_trend_analysis_agent.py theme={null}
"""Please install dependencies using:
pip install openai exa-py agno firecrawl
"""

from datetime import datetime, timedelta
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools
from agno.tools.firecrawl import FirecrawlTools

def calculate_start_date(days: int) -> str:
    """Calculate start date based on number of days."""
    start_date = datetime.now() - timedelta(days=days)
    return start_date.strftime("%Y-%m-%d")

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[
        ExaTools(start_published_date=calculate_start_date(30), type="keyword"),
        FirecrawlTools(scrape=True),
    ],
    description=dedent("""\
        You are an expert media trend analyst specializing in:
        1. Identifying emerging trends across news and digital platforms
        2. Recognizing pattern changes in media coverage
        3. Providing actionable insights based on data
        4. Forecasting potential future developments
    """),
    instructions=[
        "Analyze the provided topic according to the user's specifications:",
        "1. Use keywords to perform targeted searches",
        "2. Identify key influencers and authoritative sources",
        "3. Extract main themes and recurring patterns",
        "4. Provide actionable recommendations",
        "5. if got sources less then 2, only then scrape them using firecrawl tool, dont crawl it  and use them to generate the report",
        "6. growth rate should be in percentage , and if not possible dont give growth rate",
    ],
    expected_output=dedent("""\
    # Media Trend Analysis Report

## Executive Summary
    {High-level overview of findings and key metrics}

## Trend Analysis
    ### Volume Metrics
    - Peak discussion periods: {dates}
    - Growth rate: {percentage or dont show this}

## Source Analysis
    ### Top Sources
    1. {Source 1}

## Actionable Insights
    1. {Insight 1}
       - Evidence: {data points}
       - Recommended action: {action}

## Future Predictions
    1. {Prediction 1}
       - Supporting evidence: {evidence}

## References
    {Detailed source list with links}
    """),
    markdown=True,
    add_datetime_to_context=True,
)

---

## Setup paths for knowledge storage

**URL:** llms-txt#setup-paths-for-knowledge-storage

cwd = Path(__file__).parent
tmp_dir = cwd.joinpath("tmp")
tmp_dir.mkdir(parents=True, exist_ok=True)

---

## - Complex memory reasoning within the conversation flow

**URL:** llms-txt#--complex-memory-reasoning-within-the-conversation-flow

**Contents:**
- Mitigation Strategy #2: Use a Cheaper Model for Memory Operations

python  theme={null}
from agno.memory import MemoryManager
from agno.models.openai import OpenAIChat

**Examples:**

Example 1 (unknown):
```unknown
## Mitigation Strategy #2: Use a Cheaper Model for Memory Operations

If you do need agentic memory, use a less expensive model for memory management while keeping a powerful model for conversation:
```

---

## run: RunOutput = asyncio.run(agent.arun("Share a 2 sentence horror story"))

**URL:** llms-txt#run:-runoutput-=-asyncio.run(agent.arun("share-a-2-sentence-horror-story"))

---

## agent.print_response("What files do I have in my current directory?")

**URL:** llms-txt#agent.print_response("what-files-do-i-have-in-my-current-directory?")

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch external_tool_execution_async_responses.py
    bash Mac theme={null}
      python external_tool_execution_async_responses.py
      bash Windows   theme={null}
      python external_tool_execution_async_responses.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Run the agent (non-streaming) using agent.run() to get the response

**URL:** llms-txt#run-the-agent-(non-streaming)-using-agent.run()-to-get-the-response

print("Running with KnowledgeTools (non-streaming)...")
response = agent.run(
    "What does Paul Graham explain here with respect to need to read?", stream=False
)

---

## All logging coming from the Agent will use our custom logger.

**URL:** llms-txt#all-logging-coming-from-the-agent-will-use-our-custom-logger.

**Contents:**
- Multiple Loggers
- Using Named Loggers

agent = Agent()
agent.print_response("What can I do to improve my sleep?")
python  theme={null}
configure_agno_logging(
    custom_default_logger=custom_agent_logger,
    custom_agent_logger=custom_agent_logger,
    custom_team_logger=custom_team_logger,
    custom_workflow_logger=custom_workflow_logger,
)
```

## Using Named Loggers

As it's conventional in Python, you can also provide custom loggers just by setting loggers with specific names. This is useful if you want to set them up using configuration files.

* `agno.agent` will be used for all Agent logs
* `agno.team` will be used for all Team logs
* `agno.workflow` will be used for all Workflow logs

These loggers will be automatically picked up if they are set.

**Examples:**

Example 1 (unknown):
```unknown
## Multiple Loggers

Notice that you can also configure different loggers for your Agents, Teams and Workflows:
```

---

## Include and Exclude Files

**URL:** llms-txt#include-and-exclude-files

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/basic-operations/include-exclude-files

```python 08_include_exclude_files.py theme={null}
import asyncio
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector

---

## Agent that uses a JSON schema output

**URL:** llms-txt#agent-that-uses-a-json-schema-output

**Contents:**
- Usage

agent = Agent(
    model=Llama(id="Llama-4-Maverick-17B-128E-Instruct-FP8", temperature=0.1),
    output_schema=MovieScript,
)

agent.print_response("New York")
bash  theme={null}
    export LLAMA_API_KEY=YOUR_API_KEY
    bash  theme={null}
    pip install llama-api-client agno
    bash Mac theme={null}
      python cookbook/models/meta/structured_output.py
      bash Windows theme={null}
      python cookbook/models/meta/structured_output.py
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

  <Step title="Set your LLAMA API key">
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

## LanceDB

**URL:** llms-txt#lancedb

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/lance-db/lance-db

```python cookbook/knowledge/vector_db/lance_db/lance_db.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb

vector_db = LanceDb(
    table_name="vectors",
    uri="tmp/lancedb",
)

knowledge = Knowledge(
    name="Basic SDK Knowledge Base",
    description="Agno 2.0 Knowledge Implementation with LanceDB",
    vector_db=vector_db,
)

knowledge.add_content(
        name="Recipes",
        url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
        metadata={"doc_type": "recipe_book"},
    )

agent = Agent(knowledge=knowledge)
agent.print_response("List down the ingredients to make Massaman Gai", markdown=True)

vector_db.delete_by_name("Recipes")

---

## Setup your Agent using an extra reasoning model

**URL:** llms-txt#setup-your-agent-using-an-extra-reasoning-model

deepseek_plus_claude = Agent(
    model=Claude(id="claude-3-7-sonnet-20250219"),
    reasoning_model=Groq(
        id="deepseek-r1-distill-llama-70b", temperature=0.6, max_tokens=1024, top_p=0.95
    ),
)

---

## Knowledge Base

**URL:** llms-txt#knowledge-base

**Contents:**
- LanceDb Params
- Developer Resources

knowledge_base = Knowledge(
    vector_db=vector_db,
)

def lancedb_agent(user: str = "user"):
    agent = Agent(
        knowledge=knowledge_base,
        debug_mode=True,
    )

while True:
        message = Prompt.ask(f"[bold] :sunglasses: {user} [/bold]")
        if message in ("exit", "bye"):
            break
        agent.print_response(message, session_id=f"{user}_session")

if __name__ == "__main__":
    # Comment out after first run
    knowledge_base.add_content(
        url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"
    )

typer.run(lancedb_agent)
python async_lance_db.py theme={null}
    # install lancedb - `pip install lancedb`
    import asyncio

from agno.agent import Agent
    from agno.knowledge.knowledge import Knowledge
    from agno.vectordb.lancedb import LanceDb

# Initialize LanceDB
    vector_db = LanceDb(
        table_name="recipes",
        uri="tmp/lancedb",  # You can change this path to store data elsewhere
    )

# Create knowledge base
    knowledge_base = Knowledge(
        vector_db=vector_db,
    )
    agent = Agent(knowledge=knowledge_base, debug_mode=True)

if __name__ == "__main__":
        # Load knowledge base asynchronously
        asyncio.run(knowledge_base.add_content_async(
                url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"
            )
        )

# Create and use the agent asynchronously
        asyncio.run(agent.aprint_response("How to make Tom Kha Gai", markdown=True))
    ```

<Tip className="mt-4">
      Use <code>aload()</code> and <code>aprint\_response()</code> methods with <code>asyncio.run()</code> for non-blocking operations in high-throughput applications.
    </Tip>
  </div>
</Card>

<Snippet file="vectordb_lancedb_params.mdx" />

## Developer Resources

* View [Cookbook (Sync)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/lance_db/lance_db.py)

**Examples:**

Example 1 (unknown):
```unknown
<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      LanceDB also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>
```

---

## Get AgentOS Metrics

**URL:** llms-txt#get-agentos-metrics

Source: https://docs.agno.com/reference-api/schema/metrics/get-agentos-metrics

get /metrics
Retrieve AgentOS metrics and analytics data for a specified date range. If no date range is specified, returns all available metrics.

---

## Setup Postgres

**URL:** llms-txt#setup-postgres

**Contents:**
- Usage

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
db = PostgresDb(db_url=db_url)

agent = Agent(
    db=db,
    enable_user_memories=True,
)

agent.print_response("My name is John Doe and I like to play basketball on the weekends.")
agent.print_response("What's do I do in weekends?")
bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    pip install -U agno openai sqlalchemy 'psycopg[binary]'
    bash Mac/Linux theme={null}
      python cookbook/memory/db/mem-postgres-memory.py
      bash Windows theme={null}
      python cookbook/memory/db/mem-postgres-memory.py
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

  <Step title="Set environment variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## YouTube Reader (Async)

**URL:** llms-txt#youtube-reader-(async)

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/youtube/youtube-reader-async

The **YouTube Reader** allows you to extract transcripts from YouTube videos and convert them into vector embeddings for your knowledge base.

```python examples/concepts/knowledge/readers/youtube_reader.py theme={null}
import asyncio

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.youtube_reader import YouTubeReader
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

---

## Basic Agent with Streaming

**URL:** llms-txt#basic-agent-with-streaming

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/portkey/basic_stream

```python cookbook/models/portkey/basic_stream.py theme={null}
from agno.agent import Agent
from agno.models.portkey import Portkey

agent = Agent(
    model=Portkey(
        id="@first-integrati-707071/gpt-5-nano",
    ),
    markdown=True,
)

---

## When initializing the knowledge, we can attach metadata that will be used for filtering

**URL:** llms-txt#when-initializing-the-knowledge,-we-can-attach-metadata-that-will-be-used-for-filtering

---

## agent.print_response("I like to play basketball and hike in the mountains")

**URL:** llms-txt#agent.print_response("i-like-to-play-basketball-and-hike-in-the-mountains")

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai psycopg2-binary
    bash  theme={null}
    # Make sure PostgreSQL is running
    # Update connection string in the code as needed
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch 03_session_summary.py
    bash Mac theme={null}
      python 03_session_summary.py
      bash Windows theme={null}
      python 03_session_summary.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/session" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Setup PostgreSQL">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## print(video_agent.run_response.videos)

**URL:** llms-txt#print(video_agent.run_response.videos)

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch generate_video_using_models_lab.py
    bash Mac theme={null}
      python generate_video_using_models_lab.py
      bash Windows   theme={null}
      python generate_video_using_models_lab.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/multimodal" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Replace a memory

**URL:** llms-txt#replace-a-memory

**Contents:**
- Usage
- Usage

print("\nReplacing memory")
assert memory_id_1 is not None
memory.replace_user_memory(
    memory_id=memory_id_1,
    memory=UserMemory(memory="The user's name is Jane Mary Doe", topics=["name"]),
    user_id=jane_doe_id,
)
print("Memory replaced")
memories = memory.get_user_memories(user_id=jane_doe_id)
print("Memories:")
pprint(memories)
bash  theme={null}
    pip install -U agno
    bash Mac theme={null}
      python cookbook/memory/memory_manager/01_standalone_memory.py
      bash Windows theme={null}
      python cookbook/memory/memory_manager/01_standalone_memory.py
      ```
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Context Analyzer Agent - Specialized in context analysis

**URL:** llms-txt#context-analyzer-agent---specialized-in-context-analysis

context_analyzer = Agent(
    name="Context Analyzer",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Analyze context and relevance of reranked results",
    knowledge=validation_knowledge,
    search_knowledge=True,
    instructions=[
        "Analyze the context and relevance of reranked results.",
        "Cross-validate information against the validation knowledge base.",
        "Assess the quality and accuracy of retrieved content.",
        "Identify the most contextually appropriate information.",
    ],
    markdown=True,
)

---

## Create research agents

**URL:** llms-txt#create-research-agents

hackernews_agent = Agent(
    name="HackerNews Researcher",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[HackerNewsTools()],
    role="Research trending topics and discussions on HackerNews",
    instructions=[
        "Search for relevant discussions and articles",
        "Focus on high-quality posts with good engagement",
        "Extract key insights and technical details",
    ],
)

web_researcher = Agent(
    name="Web Researcher",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    role="Conduct comprehensive web research",
    instructions=[
        "Search for authoritative sources and documentation",
        "Find recent articles and blog posts",
        "Gather diverse perspectives on the topics",
    ],
)

---

## SurrealDB Agent Knowledge

**URL:** llms-txt#surrealdb-agent-knowledge

**Contents:**
- Setup
- Example

Source: https://docs.agno.com/concepts/vectordb/surrealdb

```python agent_with_knowledge.py theme={null}
from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.surrealdb import SurrealDb
from surrealdb import Surreal

**Examples:**

Example 1 (unknown):
```unknown
or
```

Example 2 (unknown):
```unknown
## Example
```

---

## Audio Input Agent

**URL:** llms-txt#audio-input-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/openai/chat/audio_input_agent

```python cookbook/models/openai/chat/audio_input_agent.py theme={null}
import requests
from agno.agent import Agent, RunOutput  # noqa
from agno.media import Audio
from agno.models.openai import OpenAIChat

---

## You can set the debug mode on the agent for all runs to have more verbose output

**URL:** llms-txt#you-can-set-the-debug-mode-on-the-agent-for-all-runs-to-have-more-verbose-output

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    debug_mode=True,
)

agent.print_response(input="Tell me a joke.")

---

## Choose the AI model for your agent

**URL:** llms-txt#choose-the-ai-model-for-your-agent

model = OpenAIChat(id="gpt-5-mini")
print(f"Model selected: {model.id}")
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
We can now test our model setup:
```

---

## GitHub MCP agent

**URL:** llms-txt#github-mcp-agent

Source: https://docs.agno.com/examples/concepts/tools/mcp/github

Using the [GitHub MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/github) to create an Agent that can explore, analyze and provide insights about GitHub repositories:

```python  theme={null}
"""🐙 MCP GitHub Agent - Your Personal GitHub Explorer!

This example shows how to create a GitHub agent that uses MCP to explore,
analyze, and provide insights about GitHub repositories. The agent leverages the Model
Context Protocol (MCP) to interact with GitHub, allowing it to answer questions
about issues, pull requests, repository details and more.

Example prompts to try:
- "List open issues in the repository"
- "Show me recent pull requests"
- "What are the repository statistics?"
- "Find issues labeled as bugs"
- "Show me contributor activity"

Run: `pip install agno mcp openai` to install the dependencies
Environment variables needed:
- Create a GitHub personal access token following these steps:
    - https://github.com/modelcontextprotocol/servers/tree/main/src/github#setup
- export GITHUB_TOKEN: Your GitHub personal access token
"""

import asyncio
import os
from textwrap import dedent

from agno.agent import Agent
from agno.tools.mcp import MCPTools
from mcp import StdioServerParameters

async def run_agent(message: str) -> None:
    """Run the GitHub agent with the given message."""

# Initialize the MCP server
    server_params = StdioServerParameters(
        command="npx",
        args=["-y", "@modelcontextprotocol/server-github"],
    )

# Create a client session to connect to the MCP server
    async with MCPTools(server_params=server_params) as mcp_tools:
        agent = Agent(
            tools=[mcp_tools],
            instructions=dedent("""\
                You are a GitHub assistant. Help users explore repositories and their activity.

- Use headings to organize your responses
                - Be concise and focus on relevant information\
            """),
            markdown=True,
                    )

# Run the agent
        await agent.aprint_response(message, stream=True)

---

## It uses the default model of the Agent

**URL:** llms-txt#it-uses-the-default-model-of-the-agent

**Contents:**
- Usage

reasoning_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini", max_tokens=1200),
    reasoning=True,
    markdown=True,
)
reasoning_agent.print_response(
    "Give me steps to write a python script for fibonacci series",
    stream=True,
    show_full_reasoning=True,
)
bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    pip install -U openai agno
    bash Mac theme={null}
      python cookbook/reasoning/agents/default_chain_of_thought.py
      bash Windows theme={null}
      python cookbook/reasoning/agents/default_chain_of_thought.py
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

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Chat with your agent

**URL:** llms-txt#chat-with-your-agent

**Contents:**
- What Just Happened?
- Next Steps: Explore Advanced Features
- Troubleshooting

if __name__ == "__main__":
    agent.print_response("What is Agno Knowledge?", stream=True)
bash  theme={null}
python knowledge_agent.py
```

## What Just Happened?

When you ran the code, here's what occurred behind the scenes:

1. **Content Processing**: Your text was chunked into smaller pieces and converted to vector embeddings
2. **Intelligent Search**: The agent analyzed your question and searched for relevant information
3. **Contextual Response**: The agent combined the retrieved knowledge with your question to provide an accurate answer
4. **Source Attribution**: The response is based on your specific content, not generic training data

## Next Steps: Explore Advanced Features

<CardGroup cols={2}>
  <Card title="Content Types" icon="file-lines" href="/concepts/knowledge/content_types">
    Learn about different ways to add content: files, URLs, databases, and more.
  </Card>

<Card title="Chunking Strategies" icon="scissors" href="/concepts/knowledge/chunking/overview">
    Optimize how your content is broken down for better search results.
  </Card>

<Card title="Vector Databases" icon="database" href="/concepts/vectordb/overview">
    Choose the right storage solution for your needs and scale.
  </Card>

<Card title="Search Types" icon="magnifying-glass" href="/concepts/knowledge/core-concepts/search-retrieval">
    Explore different search strategies: vector, keyword, and hybrid search.
  </Card>
</CardGroup>

<AccordionGroup>
  <Accordion title="Agent isn't using knowledge in responses">
    Make sure you set `search_knowledge=True` when creating your agent and consider adding explicit instructions to search the knowledge base.
  </Accordion>

<Accordion title="Vector database connection errors">
    For local development, try LanceDB instead of PostgreSQL. For production, ensure your database connection string is correct.
  </Accordion>

<Accordion title="Content not being found in searches">
    Your content might need better chunking. Try different chunking strategies or smaller chunk sizes for more precise retrieval.
  </Accordion>
</AccordionGroup>

<Card title="Ready for Core Concepts?" icon="graduation-cap" href="/concepts/knowledge/core-concepts/knowledge-bases">
  Dive deeper into understanding knowledge bases and how they power intelligent agents
</Card>

**Examples:**

Example 1 (unknown):
```unknown
Run it:
```

---

## Browser Search Agent

**URL:** llms-txt#browser-search-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/groq/browser_search

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Run agent and return the response as a variable

**URL:** llms-txt#run-agent-and-return-the-response-as-a-variable

**Contents:**
- Multi-Turn Sessions
  - History in Context
- Session Summaries
  - Customize Session Summaries

response = agent.run("Tell me a 5 second short story about a robot")
print(response.content)
print(response.run_id)
print(response.session_id)
python  theme={null}
    from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/data.db")

agent = Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        db=db,
        add_history_to_context=True,
        num_history_runs=3,
    )

user_1_id = "user_101"
    user_2_id = "user_102"

user_1_session_id = "session_101"
    user_2_session_id = "session_102"

# Start the session with user 1
    agent.print_response(
        "Tell me a 5 second short story about a robot.",
        user_id=user_1_id,
        session_id=user_1_session_id,
    )
    # Continue the session with user 1
    agent.print_response("Now tell me a joke.", user_id=user_1_id, session_id=user_1_session_id)

# Start the session with user 2
    agent.print_response("Tell me about quantum physics.", user_id=user_2_id, session_id=user_2_session_id)

# Continue the session with user 2
    agent.print_response("What is the speed of light?", user_id=user_2_id, session_id=user_2_session_id)

# Ask the agent to give a summary of the conversation, this will use the history from the previous messages (but only for user 1)
    agent.print_response(
        "Give me a summary of our conversation.",
        user_id=user_1_id,
        session_id=user_1_session_id,
    )
    shell  theme={null}
    pip install agno openai
    shell  theme={null}
    export OPENAI_API_KEY=xxx
    shell  theme={null}
    python multi_user_multi_session.py
    python  theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.db.in_memory import InMemoryDb

agent = Agent(model=OpenAIChat(id="gpt-5-mini"), db=InMemoryDb())

agent.print_response("Hi, I'm John. Nice to meet you!")

agent.print_response("What is my name?", add_history_to_context=True)
python session_summary.py theme={null}
    from agno.agent import Agent
    from agno.models.google.gemini import Gemini
    from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/data.db")

user_id = "jon_hamm@example.com"
    session_id = "1001"

agent = Agent(
        model=Gemini(id="gemini-2.0-flash-exp"),
        db=db,
        enable_session_summaries=True,
    )

agent.print_response(
        "What can you tell me about quantum computing?",
        stream=True,
        user_id=user_id,
        session_id=session_id,
    )

agent.print_response(
        "I would also like to know about LLMs?",
        stream=True,
        user_id=user_id,
        session_id=session_id
    )

session_summary = agent.get_session_summary(session_id=session_id)
    print(f"Session summary: {session_summary.summary}")
    shell  theme={null}
    pip install google-genai agno
    shell  theme={null}
    export GOOGLE_API_KEY=xxx
    shell  theme={null}
    python session_summary.py
    python  theme={null}
from agno.agent import Agent
from agno.session import SessionSummaryManager
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

**Examples:**

Example 1 (unknown):
```unknown
## Multi-Turn Sessions

Each user that is interacting with an Agent gets a unique set of sessions and you can have multiple users interacting with the same Agent at the same time.

Set a `user_id` to connect a user to their sessions with the Agent.

In the example below, we set a `session_id` to demo how to have multi-turn conversations with multiple users at the same time.

<Steps>
  <Step title="Multi-user, multi-session example">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run the example">
    Install libraries
```

Example 3 (unknown):
```unknown
Export your key
```

Example 4 (unknown):
```unknown
Run the example
```

---

## Slack Agent with User Memory

**URL:** llms-txt#slack-agent-with-user-memory

**Contents:**
- Code
- Usage
- Key Features

Source: https://docs.agno.com/examples/agent-os/interfaces/slack/agent_with_user_memory

Personalized Slack agent that remembers user information and preferences

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set Environment Variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

* **Memory Management**: Remembers user names, hobbies, preferences, and activities
* **Google Search Integration**: Access to current information during conversations
* **Personalized Responses**: Uses stored memories for contextualized replies
* **Slack Integration**: Works with direct messages and group conversations
* **Claude Powered**: Advanced reasoning and conversation capabilities

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Deep Knowledge Agent

**URL:** llms-txt#deep-knowledge-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/groq/deep_knowledge

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Agent with Input Schema as TypedDict

**URL:** llms-txt#agent-with-input-schema-as-typeddict

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/input_schema_on_agent_as_typed_dict

This example demonstrates how to define an input schema for an agent using `TypedDict`, ensuring structured input validation.

```python input_schema_on_agent_as_typed_dict.py theme={null}
from typing import List, Optional, TypedDict

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.hackernews import HackerNewsTools

---

## PDF Input Local Agent

**URL:** llms-txt#pdf-input-local-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/vertexai/claude/pdf_input_local

```python cookbook/models/vertexai/claude/pdf_input_local.py theme={null}
from pathlib import Path

from agno.agent import Agent
from agno.media import File
from agno.models.vertexai.claude import Claude
from agno.utils.media import download_file

pdf_path = Path(__file__).parent.joinpath("ThaiRecipes.pdf")

---

## Create agent with reasoning=True (default model COT)

**URL:** llms-txt#create-agent-with-reasoning=true-(default-model-cot)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    reasoning=True,
    markdown=True,
)

---

## Memory Creation

**URL:** llms-txt#memory-creation

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/memory/memory_manager/02-memory-creation

Create user memories with an Agent by providing a either text or a list of messages.

```python memory_manager/memory_creation.py theme={null}
from agno.db.postgres import PostgresDb
from agno.memory import MemoryManager, UserMemory
from agno.models.message import Message
from agno.models.openai import OpenAIChat
from rich.pretty import pprint

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

memory_db = PostgresDb(db_url=db_url)

memory = MemoryManager(model=OpenAIChat(id="gpt-5-mini"), db=memory_db)

john_doe_id = "john_doe@example.com"
memory.add_user_memory(
    memory=UserMemory(
        memory="""
I enjoy hiking in the mountains on weekends,
reading science fiction novels before bed,
cooking new recipes from different cultures,
playing chess with friends,
and attending live music concerts whenever possible.
Photography has become a recent passion of mine, especially capturing landscapes and street scenes.
I also like to meditate in the mornings and practice yoga to stay centered.
"""
    ),
    user_id=john_doe_id,
)

memories = memory.get_user_memories(user_id=john_doe_id)
print("John Doe's memories:")
pprint(memories)

jane_doe_id = "jane_doe@example.com"

---

## run: RunOutput = agent.run("What is Portkey and why would I use it as an AI gateway?")

**URL:** llms-txt#run:-runoutput-=-agent.run("what-is-portkey-and-why-would-i-use-it-as-an-ai-gateway?")

---

## ChromaDB Agent Knowledge

**URL:** llms-txt#chromadb-agent-knowledge

**Contents:**
- Setup
- Example

Source: https://docs.agno.com/concepts/vectordb/chroma

```python agent_with_knowledge.py theme={null}
import asyncio

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.chroma import ChromaDb

**Examples:**

Example 1 (unknown):
```unknown
## Example
```

---

## What are Vector Databases?

**URL:** llms-txt#what-are-vector-databases?

**Contents:**
- Supported Vector Databases
- Popular Choices by Use Case
- Next Steps

Source: https://docs.agno.com/concepts/vectordb/overview

Vector databases enable us to store information as embeddings and search for "results similar" to our input query using cosine similarity or full text search. These results are then provided to the Agent as context so it can respond in a context-aware manner using Retrieval Augmented Generation (RAG).

Here's how vector databases are used with Agents:

<Steps>
  <Step title="Chunk the information">
    Break down the knowledge into smaller chunks to ensure our search query
    returns only relevant results.
  </Step>

<Step title="Load the knowledge base">
    Convert the chunks into embedding vectors and store them in a vector
    database.
  </Step>

<Step title="Search the knowledge base">
    When the user sends a message, we convert the input message into an
    embedding and "search" for nearest neighbors in the vector database.
  </Step>
</Steps>

Many vector databases also support hybrid search, which combines the power of vector similarity search with traditional keyword-based search. This approach can significantly improve the relevance and accuracy of search results, especially for complex queries or when dealing with diverse types of data.

Hybrid search typically works by:

1. Performing a vector similarity search to find semantically similar content.
2. Conducting a keyword-based search to identify exact or close matches.
3. Combining the results using a weighted approach to provide the most relevant information.

This capability allows for more flexible and powerful querying, often yielding better results than either method alone.

<Card title="⚡ Asynchronous Operations">
  <p>Several vector databases support asynchronous operations, offering improved performance through non-blocking operations, concurrent processing, reduced latency, and seamless integration with FastAPI and async agents.</p>

<Tip className="mt-4">
    When building with Agno, use the <code>aload</code> methods for async knowledge base loading in production environments.
  </Tip>
</Card>

## Supported Vector Databases

The following VectorDb are currently supported:

* [PgVector](../vectordb/pgvector)\*
* [Cassandra](../vectordb/cassandra)
* [ChromaDb](../vectordb/chroma)
* [Couchbase](../vectordb/couchbase)\*
* [Clickhouse](../vectordb/clickhouse)
* [LanceDb](../vectordb/lancedb)\*
* [LightRAG](../vectordb/lightrag)
* [Milvus](../vectordb/milvus)
* [MongoDb](../vectordb/mongodb)
* [Pinecone](../vectordb/pinecone)\*
* [Qdrant](../vectordb/qdrant)
* [Singlestore](../vectordb/singlestore)
* [Weaviate](../vectordb/weaviate)

\*hybrid search supported

Each of these databases has its own strengths and features, including varying levels of support for hybrid search and async operations. Be sure to check the specific documentation for each to understand how to best leverage their capabilities in your projects.

## Popular Choices by Use Case

<CardGroup cols={2}>
  <Card title="Development & Testing" icon="laptop-code" href="/concepts/vectordb/lancedb">
    **LanceDB** - Fast, local, no setup required
  </Card>

<Card title="Production at Scale" icon="server" href="/concepts/vectordb/pgvector">
    **PgVector** - Reliable, scalable, full SQL support
  </Card>

<Card title="Managed Service" icon="cloud" href="/concepts/vectordb/pinecone">
    **Pinecone** - Fully managed, no operations overhead
  </Card>

<Card title="High Performance" icon="gauge" href="/concepts/vectordb/qdrant">
    **Qdrant** - Optimized for speed and advanced features
  </Card>
</CardGroup>

<CardGroup cols={2}>
  <Card title="Getting Started" icon="rocket" href="/concepts/knowledge/getting-started">
    Build your first knowledge base with a vector database
  </Card>

<Card title="Embeddings" icon="vector-square" href="/concepts/knowledge/embedder/overview">
    Learn about creating vector representations of your content
  </Card>

<Card title="Search & Retrieval" icon="magnifying-glass" href="/concepts/knowledge/core-concepts/search-retrieval">
    Understand how vector search works with your data
  </Card>

<Card title="Performance Tips" icon="gauge" href="/concepts/knowledge/advanced/performance-tips">
    Optimize your vector database for speed and scale
  </Card>
</CardGroup>

---

## Create your agents

**URL:** llms-txt#create-your-agents

agno_agent = Agent(
    name="Agno Agent",
    model=OpenAIChat(id="gpt-4.1"),
    tools=[MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp")],
    db=db,
    enable_user_memories=True,
    knowledge=knowledge,
    markdown=True,
)

simple_agent = Agent(
    name="Simple Agent",
    role="Simple agent",
    id="simple_agent",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=["You are a simple agent"],
    db=db,
    enable_user_memories=True,
)

research_agent = Agent(
    name="Research Agent",
    role="Research agent",
    id="research_agent",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=["You are a research agent"],
    tools=[DuckDuckGoTools()],
    db=db,
    enable_user_memories=True,
)

---

## Filtering on ChromaDB

**URL:** llms-txt#filtering-on-chromadb

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/vector-dbs/filtering_chroma_db

Learn how to filter knowledge base searches using Pdf documents with user-specific metadata in ChromaDB.

```python  theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.chroma import ChromaDb

---

## Upstash Async

**URL:** llms-txt#upstash-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/upstash-db/async-upstash-db

```python cookbook/knowledge/vector_db/upstash_db/upstash_db.py theme={null}
import asyncio
import os

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.upstashdb import UpstashVectorDb

---

## Test your knowledge-powered agent

**URL:** llms-txt#test-your-knowledge-powered-agent

**Contents:**
  - Complete Example

if __name__ == "__main__":
    # Your agent will automatically search its knowledge to answer
    agent.print_response(
        "What is the company policy on remote work?",
        stream=True
    )
python knowledge_agent.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.lancedb import LanceDb
from agno.models.openai import OpenAIChat

**Examples:**

Example 1 (unknown):
```unknown
### Complete Example

Here's the full working example:
```

---

## Configuration for the Memory page

**URL:** llms-txt#configuration-for-the-memory-page

memory:
  display_name: <DISPLAY_NAME>
  dbs:
    - <DB_ID>
      domain_config:
        display_name: <DISPLAY_NAME>
    ...

---

## WhatsApp Agent with Media Support

**URL:** llms-txt#whatsapp-agent-with-media-support

**Contents:**
- Code
- Usage
- Key Features

Source: https://docs.agno.com/examples/agent-os/interfaces/whatsapp/agent_with_media

WhatsApp agent that analyzes images, videos, and audio using multimodal AI

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set Environment Variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

* **Multimodal AI**: Gemini 2.0 Flash for image, video, and audio processing
* **Image Analysis**: Object recognition, scene understanding, text extraction
* **Video Processing**: Content analysis and summarization
* **Audio Support**: Voice message transcription and response
* **Context Integration**: Combines media analysis with conversation history

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Response Composer Agent - Specialized in response composition

**URL:** llms-txt#response-composer-agent---specialized-in-response-composition

response_composer = Agent(
    name="Response Composer",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Compose comprehensive responses with proper source attribution",
    instructions=[
        "Combine validated information from all team members.",
        "Create well-structured, comprehensive responses.",
        "Include proper source attribution and data provenance.",
        "Ensure clarity and coherence in the final response.",
        "Format responses for optimal user experience.",
    ],
    markdown=True,
)

---

## Image Generation Agent (Streaming)

**URL:** llms-txt#image-generation-agent-(streaming)

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/gemini/image_generation_stream

```python cookbook/models/google/gemini/image_generation_stream.py theme={null}
from io import BytesIO

from agno.agent import Agent, RunOutput  # noqa
from agno.models.google import Gemini
from PIL import Image

---

## Transcription Agent

**URL:** llms-txt#transcription-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/groq/transcription_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## AgentOS Connection Issues

**URL:** llms-txt#agentos-connection-issues

**Contents:**
- Browser Compatibility
  - Recommended Browsers
  - Browsers with Known Issues
- Solutions
  - For Brave Users
  - For Other Browsers

Source: https://docs.agno.com/faq/agentos-connection

If you're experiencing connection issues with AgentOS, particularly when trying to connect to **local instances**, this guide will help you resolve them.

## Browser Compatibility

Some browsers have security restrictions that prevent connections to localhost domains due to mixed content security issues. Here's what you need to know about different browsers:

### Recommended Browsers

* **Chrome & Edge**: These browsers work well with local connections by default and are our recommended choices
* **Firefox**: Generally works well with local connections

### Browsers with Known Issues

* **Safari**: May block local connections due to its strict security policies
* **Brave**: Blocks local connections by default due to its shield feature

If you're using Brave browser, you can try these steps:

1. Click on the Brave shield icon in the address bar
2. Turn off the shield for the current site
3. Refresh the endpoint and try connecting again

<video autoPlay muted controls className="w-full aspect-video" src="https://mintcdn.com/agno-v2/Xj0hQoiFt0n7bXOq/videos/agentos-brave-issue.mp4?fit=max&auto=format&n=Xj0hQoiFt0n7bXOq&q=85&s=80ec713d1ca11cc06366c5460388fdd8" data-path="videos/agentos-brave-issue.mp4" />

### For Other Browsers

If you're using Safari or experiencing issues with other browsers, you can use one of these solutions:

#### 1. Use Chrome or Edge

The simplest solution is to use Chrome or Edge browsers which have better support for local connections.

#### 2. Use Tunneling Services

You can use tunneling services to expose your local endpoint to the internet:

1. Install ngrok from [ngrok.com](https://ngrok.com)
2. Run your local server
3. Create a tunnel with ngrok:

4. Use the provided ngrok URL on [AgentOS](https://os.agno.com).

##### Using Cloudflare Tunnel

1. Install Cloudflare Tunnel (cloudflared) from [Cloudflare's website](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)
2. Authenticate with Cloudflare
3. Create a tunnel:

4. Use the provided Cloudflare URL on [AgentOS](https://os.agno.com).

**Examples:**

Example 1 (unknown):
```unknown
4. Use the provided ngrok URL on [AgentOS](https://os.agno.com).

##### Using Cloudflare Tunnel

1. Install Cloudflare Tunnel (cloudflared) from [Cloudflare's website](https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/)
2. Authenticate with Cloudflare
3. Create a tunnel:
```

---

## Non-Reasoning Model Agent

**URL:** llms-txt#non-reasoning-model-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/reasoning/agents/non-reasoning-model

This example demonstrates how to use a non-reasoning model as a reasoning model.

For reasoning, we recommend using a Reasoning Agent (with `reasoning=True`), or to use an appropriate reasoning model with `reasoning_model=`.

```python cookbook/reasoning/agents/default_chain_of_thought.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat

reasoning_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    reasoning_model=OpenAIChat(
        id="gpt-5-mini", # This model will be used for reasoning, although it is not a native reasoning model.
        max_tokens=1200,
    ),
    markdown=True,
)
reasoning_agent.print_response(
    "Give me steps to write a python script for fibonacci series",
    stream=True,
    show_full_reasoning=True,
)

---

## Load PDF knowledge base using hybrid search

**URL:** llms-txt#load-pdf-knowledge-base-using-hybrid-search

knowledge_base = Knowledge(
    vector_db=hybrid_db,
)

knowledge_base.add_content(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"
)

---

## Agent with Async Tool Usage

**URL:** llms-txt#agent-with-async-tool-usage

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/meta/async_tool_use

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your LLAMA API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set your LLAMA API key">
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

## Company information agent with structured output

**URL:** llms-txt#company-information-agent-with-structured-output

company_info_agent = Agent(
    name="Company Info Searcher",
    model=OpenAIChat("gpt-5-mini"),
    role="Searches the web for information on a stock.",
    output_schema=CompanyAnalysis,
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
)

---

## hackernews_agent.print_response(

**URL:** llms-txt#hackernews_agent.print_response(

---

## Team with Reasoning Tools

**URL:** llms-txt#team-with-reasoning-tools

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/reasoning/teams/reasoning-finance-team

This is a multi-agent team reasoning example with reasoning tools.

<Tip>
  Enabling the reasoning option on the team leader helps optimize delegation and enhances multi-agent collaboration by selectively invoking deeper reasoning when required.
</Tip>

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

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

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Basic Reasoning Agent

**URL:** llms-txt#basic-reasoning-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/reasoning/agents/basic-cot

This example demonstrates how to configure a basic Reasoning Agent, using the `reasoning=True` flag.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

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

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Agent with URL Context and Search

**URL:** llms-txt#agent-with-url-context-and-search

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/gemini/url_context_with_search

```python cookbook/models/google/gemini/url_context_with_search.py theme={null}
"""Combine URL context with Google Search for comprehensive web analysis.

from agno.agent import Agent
from agno.models.google import Gemini

---

## Async Agent with Streaming

**URL:** llms-txt#async-agent-with-streaming

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/vllm/async_basic_stream

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install Libraries">
    
  </Step>

<Step title="Start vLLM server">
    
  </Step>

<Step title="Run Agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install Libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Start vLLM server">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
```

---

## (Optional) Set up your Cassandra DB

**URL:** llms-txt#(optional)-set-up-your-cassandra-db

**Contents:**
- Developer Resources

session = cluster.connect()
session.execute(
    """
    CREATE KEYSPACE IF NOT EXISTS testkeyspace
    WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 }
    """
)

knowledge_base = Knowledge(
    vector_db=Cassandra(table_name="recipes", keyspace="testkeyspace", session=session, embedder=MistralEmbedder()),
)

knowledge_base.add_content(
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"
)

agent = Agent(
    model=MistralChat(provider="mistral-large-latest", api_key=os.getenv("MISTRAL_API_KEY")),
    knowledge=knowledge_base,
)

agent.print_response(
    "What are the health benefits of Khao Niew Dam Piek Maphrao Awn?", markdown=True, show_full_reasoning=True
)
python async_cassandra.py theme={null}
    import asyncio

from agno.agent import Agent
    from agno.knowledge.embedder.mistral import MistralEmbedder
    from agno.knowledge.knowledge import Knowledge
    from agno.models.mistral import MistralChat
    from agno.vectordb.cassandra import Cassandra

try:
        from cassandra.cluster import Cluster  # type: ignore
    except (ImportError, ModuleNotFoundError):
        raise ImportError(
            "Could not import cassandra-driver python package.Please install it with pip install cassandra-driver."
        )

session = cluster.connect()
    session.execute(
        """
        CREATE KEYSPACE IF NOT EXISTS testkeyspace
        WITH REPLICATION = { 'class' : 'SimpleStrategy', 'replication_factor' : 1 }
        """
    )

knowledge_base = Knowledge(
        vector_db=Cassandra(
            table_name="recipes",
            keyspace="testkeyspace",
            session=session,
            embedder=MistralEmbedder(),
        ),
    )

agent = Agent(
        model=MistralChat(),
        knowledge=knowledge_base,
    )

if __name__ == "__main__":
        asyncio.run(knowledge_base.add_content_async(
            url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
            )
        )

# Create and use the agent
        asyncio.run(
            agent.aprint_response(
                "What are the health benefits of Khao Niew Dam Piek Maphrao Awn?",
                markdown=True,
            )
        )
    ```

<Tip className="mt-4">
      Use <code>aload()</code> and <code>aprint\_response()</code> methods with <code>asyncio.run()</code> for non-blocking operations in high-throughput applications.
    </Tip>
  </div>
</Card>

## Developer Resources

* View [Cookbook (Sync)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/cassandra_db/cassandra_db.py)
* View [Cookbook (Async)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/cassandra_db/async_cassandra_db.py)

**Examples:**

Example 1 (unknown):
```unknown
<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      Cassandra also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>
```

---

## AgentOS API

**URL:** llms-txt#agentos-api

**Contents:**
- Authentication
- Running your Agent / Team / Workflow
  - Passing agent parameters

Source: https://docs.agno.com/agent-os/api

Learn how to use the AgentOS API to interact with your agentic system

AgentOS is a RESTful API that provides access to your agentic system.

* **Run Agents / Teams / Workflows**: Create new runs for your agents, teams and workflows, either with a new session or a existing one.
* **Manage Sessions**: Retrieve, update and delete sessions.
* **Manage Memories**: Retrieve, update and delete memories.
* **Manage Knowledge**: Manage the content of your knowledge base.
* **Manage Evals**: Retrieve, create, delete and update evals.

<Note>
  This is the same API that powers the AgentOS Control Plane. However, the same endpoints can be used to power your own application!
</Note>

See the full [API reference](/reference-api/overview) for more details.

AgentOS supports bearer-token authentication to secure your instance.
When a Security Key is configured, all API routes require an `Authorization: Bearer <token>` header for access. Without a key configured, authentication is disabled.

For more details, see the [AgentOS Security](/agent-os/security) guide.

## Running your Agent / Team / Workflow

The AgentOS API provides endpoints:

* **Run an Agent**: `POST /agents/{agent_id}/runs`  (See the [API reference](/reference-api/schema/agents/create-agent-run))
* **Run a Team**: `POST /teams/{team_id}/runs`  (See the [API reference](/reference-api/schema/teams/create-team-run))
* **Run a Workflow**: `POST /workflows/{workflow_id}/runs`  (See the [API reference](/reference-api/schema/workflows/execute-workflow))

These endpoints support form-based input. Below is an example of how to run an agent with the API:

### Passing agent parameters

Agent, Team and Workflow `run()` and `arun()` endpoints all support additional parameters. See the [Agent arun schema](/reference/agents/agent#arun), [Team arun schema](/reference/teams/team#arun), [Workflow arun schema](/reference/workflows/workflow#arun) for more details.

To pass these parameters to your agent, team or workflow, via the AgentOS API, you can simply specify them as form-based parameters.

Below is an example where `dependencies` are passed to the agent:

```python dependencies_to_agent.py theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.os import AgentOS

**Examples:**

Example 1 (unknown):
```unknown
### Passing agent parameters

Agent, Team and Workflow `run()` and `arun()` endpoints all support additional parameters. See the [Agent arun schema](/reference/agents/agent#arun), [Team arun schema](/reference/teams/team#arun), [Workflow arun schema](/reference/workflows/workflow#arun) for more details.

To pass these parameters to your agent, team or workflow, via the AgentOS API, you can simply specify them as form-based parameters.

Below is an example where `dependencies` are passed to the agent:
```

---

## Connecting Your AgentOS

**URL:** llms-txt#connecting-your-agentos

**Contents:**
- Overview
- Step-by-Step Connection Process
  - 1. Access the Connection Dialog
  - 2. Choose Your Environment
  - 3. Configure Connection Settings
  - 4. Test and Connect
- Verifying Your Connection
- Securing Your Connection
- Managing Connected OS Instances
  - Switching Between OS Instances

Source: https://docs.agno.com/agent-os/connecting-your-os

Step-by-step guide to connect your local AgentOS to the AgentOS Control Plane

Connecting your AgentOS is the critical first step to using the AgentOS Control Plane. This process establishes a connection between your running AgentOS instance and the Control Plane, allowing you to manage, monitor, and interact with your agents through the browser.

<Note>
  **Prerequisites**: You need a running AgentOS instance before you can connect
  it to the Control Plane. If you haven't created one yet, check out our [Creating
  Your First OS](/agent-os/creating-your-first-os) guide.
</Note>

See the [AgentOS Control Plane](/agent-os/control-plane) documentation for more information about the Control Plane.

## Step-by-Step Connection Process

### 1. Access the Connection Dialog

In the Agno platform:

1. Click on the team/organization dropdown in the top navigation bar
2. Click the **"+"** (plus) button next to "Add new OS"
3. The "Connect your AgentOS" dialog will open

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/MMgohmDbM-qeNPya/videos/agent-os-connect-os.mp4?fit=max&auto=format&n=MMgohmDbM-qeNPya&q=85&s=c427bf5bbd76c0495540b49aa64f5604" type="video/mp4" data-path="videos/agent-os-connect-os.mp4" />
  </video>
</Frame>

### 2. Choose Your Environment

Select **"Local"** for development or **"Live"** for production:

* **Local**: Connects to an AgentOS running on your local machine
* **Live**: Connects to a production AgentOS running on your infrastructure

<Note>Live AgentOS connections require a PRO subscription.</Note>

### 3. Configure Connection Settings

* **Default Local**: `http://localhost:7777`
* **Custom Local**: You can change the port if your AgentOS runs on a different port
* **Live**: Enter your production HTTPS URL

<Warning>
  Make sure your AgentOS is actually running on the specified endpoint before
  attempting to connect.
</Warning>

Give your AgentOS a descriptive name:

* Use clear, descriptive names like "Development OS" or "Production Chat Bot"
* This name will appear in your OS list and help you identify different instances

Add tags to organize your AgentOS instances:

* Examples: `development`, `production`, `chatbot`, `research`
* Tags help filter and organize multiple OS instances
* Click the **"+"** button to add multiple tags

### 4. Test and Connect

1. Click the **"CONNECT"** button
2. The platform will attempt to establish a connection to your AgentOS
3. If successful, you'll see your new OS in the organization dashboard

## Verifying Your Connection

Once connected, you should see:

1. **OS Status**: "Running" indicator in the platform
2. **Available Features**: Chat, Knowledge, Memory, Sessions, etc. should be accessible
3. **Agent List**: Your configured agents should appear in the chat interface

## Securing Your Connection

Protect your AgentOS APIs and Control Plane access with bearer-token authentication. Security keys provide essential protection for both development and production environments.

* Generate unique security keys per AgentOS instance
* Rotate keys easily through the organization settings
* Configure bearer-token authentication on your server

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/xm93WWN8gg4nzCGE/videos/agentos-security-key.mp4?fit=max&auto=format&n=xm93WWN8gg4nzCGE&q=85&s=0a87c2a894982a3eb075fe282a21c491" type="video/mp4" data-path="videos/agentos-security-key.mp4" />
  </video>
</Frame>

<Note>
  For complete security setup instructions, including environment configuration
  and best practices, see the [Security Key](/agent-os/security) documentation.
</Note>

## Managing Connected OS Instances

### Switching Between OS Instances

1. Use the dropdown in the top navigation bar
2. Select the OS instance you want to work with
3. All platform features will now connect to the selected OS

### Disconnecting an OS

1. Go to the organization settings
2. Find the OS in your list
3. Click the delete option

<Warning>
  Disconnecting an OS doesn't stop the AgentOS instance - it only removes it
  from the platform interface.
</Warning>

Once your AgentOS is successfully connected:

<CardGroup cols={2}>
  <Card title="Explore the Chat Interface" icon="comment" href="/agent-os/features/chat-interface">
    Start having conversations with your connected agents
  </Card>

<Card title="Manage Knowledge" icon="brain" href="/agent-os/features/knowledge-management">
    Upload and organize your knowledge bases
  </Card>

<Card title="Monitor Sessions" icon="chart-line" href="/agent-os/features/session-tracking">
    Track and analyze your agent interactions
  </Card>
</CardGroup>

---

## agent = Agent(

**URL:** llms-txt#agent-=-agent(

---

## Async Agents with Delayed Execution

**URL:** llms-txt#async-agents-with-delayed-execution

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/async/delay

This example demonstrates how to run multiple async agents with delayed execution, gathering results from different AI providers to write comprehensive reports.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/async" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Create a knowledge containing information from a URL

**URL:** llms-txt#create-a-knowledge-containing-information-from-a-url

agno_docs = Knowledge(
    # Use LanceDB as the vector database and store embeddings in the `agno_docs` table
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

---

## Cheap model for memory operations (60x less expensive)

**URL:** llms-txt#cheap-model-for-memory-operations-(60x-less-expensive)

memory_manager = MemoryManager(
    db=db,
    model=OpenAIChat(id="gpt-4o-mini")
)

---

## Integrate with AgentOS

**URL:** llms-txt#integrate-with-agentos

**Contents:**
- Access AgentOS Routes

agent_os = AgentOS(
    agents=[Agent(id="basic-agent", model=OpenAIChat(id="gpt-5-mini"))], 
    base_app=app
)

app = agent_os.get_app()
python  theme={null}
agent_os = AgentOS(agents=[agent])
app = agent_os.get_app()

**Examples:**

Example 1 (unknown):
```unknown
## Access AgentOS Routes

You can programmatically access and inspect the routes added by AgentOS:
```

---

## Agent State

**URL:** llms-txt#agent-state

**Contents:**
- Code

Source: https://docs.agno.com/examples/getting-started/07-agent-state

This example shows how to create an agent that maintains state across interactions. It demonstrates a simple counter mechanism, but this pattern can be extended to more complex state management like maintaining conversation context, user preferences, or tracking multi-step processes.

Example prompts to try:

* "Increment the counter 3 times and tell me the final count"
* "What's our current count? Add 2 more to it"
* "Let's increment the counter 5 times, but tell me each step"
* "Add 4 to our count and remind me where we started"
* "Increase the counter twice and summarize our journey"

```python agent_state.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def increment_counter(session_state) -> str:
    """Increment the counter in session state."""
    # Initialize counter if it doesn't exist
    if "count" not in session_state:
        session_state["count"] = 0

# Increment the counter
    session_state["count"] += 1

return f"Counter incremented! Current count: {session_state['count']}"

def get_counter(session_state) -> str:
    """Get the current counter value."""
    count = session_state.get("count", 0)
    return f"Current count: {count}"

---

## agent.print_response(

**URL:** llms-txt#agent.print_response(

---

## Create team with knowledge base integration

**URL:** llms-txt#create-team-with-knowledge-base-integration

**Contents:**
- Usage

team_with_knowledge = Team(
    name="Team with Knowledge",
    members=[web_agent],
    model=OpenAIChat(id="gpt-5-mini"),
    knowledge=agno_docs_knowledge,
    show_members_responses=True,
    markdown=True,
)

if __name__ == "__main__":
    team_with_knowledge.print_response("Tell me about the Agno framework", stream=True)
bash  theme={null}
    pip install agno ddgs lancedb
    bash  theme={null}
    export OPENAI_API_KEY=****
    bash  theme={null}
    python cookbook/examples/teams/knowledge/01_team_with_knowledge.py
    ```
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install required libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Agent can now search this knowledge

**URL:** llms-txt#agent-can-now-search-this-knowledge

**Contents:**
  - Choosing an embedder
  - Supported embedders
  - Best Practices
  - Batch Embeddings

agent = Agent(knowledge=knowledge, search_knowledge=True)
agent.print_response("What color is the sky?")
python  theme={null}
from agno.knowledge.embedder.openai import OpenAIEmbedder

embedder=OpenAIEmbedder(
    id="text-embedding-3-small",
    dimensions=1536,
    enable_batch=True,
    batch_size=100
)
```

The following embedders currently support batching:

* [Azure OpenAI](/concepts/knowledge/embedder/azure_openai)
* [Cohere](/concepts/knowledge/embedder/cohere)
* [Fireworks](/concepts/knowledge/embedder/fireworks)
* [Gemini](/concepts/knowledge/embedder/gemini)
* [Jina](/concepts/knowledge/embedder/jina)
* [Mistral](/concepts/knowledge/embedder/mistral)
* [Nebius](/concepts/knowledge/embedder/nebius)
* [OpenAI](/concepts/knowledge/embedder/openai)
* [Together](/concepts/knowledge/embedder/together)
* [Voyage AI](/concepts/knowledge/embedder/voyageai)

**Examples:**

Example 1 (unknown):
```unknown
### Choosing an embedder

Pick based on your constraints:

* **Hosted vs local**: Prefer local (e.g., Ollama, FastEmbed) for offline or strict data residency; hosted (OpenAI, Gemini, Voyage) for best quality and convenience.
* **Latency and cost**: Smaller models are cheaper/faster; larger models often retrieve better.
* **Language support**: Ensure your embedder supports the languages you expect.
* **Dimension compatibility**: Match your vector DB's expected embedding size if it's fixed.

#### Quick Comparison

| Embedder        | Type         | Best For                          | Cost    | Performance |
| --------------- | ------------ | --------------------------------- | ------- | ----------- |
| **OpenAI**      | Hosted       | General use, proven quality       | \$\$    | Excellent   |
| **Ollama**      | Local        | Privacy, offline, no API costs    | Free    | Good        |
| **Voyage AI**   | Hosted       | Specialized retrieval tasks       | \$\$\$  | Excellent   |
| **Gemini**      | Hosted       | Google ecosystem, multilingual    | \$\$    | Excellent   |
| **FastEmbed**   | Local        | Fast local embeddings             | Free    | Good        |
| **HuggingFace** | Local/Hosted | Open source models, customization | Free/\$ | Variable    |

### Supported embedders

The following embedders are supported:

* [OpenAI](/concepts/knowledge/embedder/openai)
* [Cohere](/concepts/knowledge/embedder/cohere)
* [Gemini](/concepts/knowledge/embedder/gemini)
* [AWS Bedrock](/concepts/knowledge/embedder/aws_bedrock)
* [Azure OpenAI](/concepts/knowledge/embedder/azure_openai)
* [Fireworks](/concepts/knowledge/embedder/fireworks)
* [HuggingFace](/concepts/knowledge/embedder/huggingface)
* [Jina](/concepts/knowledge/embedder/jina)
* [Mistral](/concepts/knowledge/embedder/mistral)
* [Nebius](/concepts/knowledge/embedder/nebius)
* [Ollama](/concepts/knowledge/embedder/ollama)
* [Qdrant FastEmbed](/concepts/knowledge/embedder/qdrant_fastembed)
* [Together](/concepts/knowledge/embedder/together)
* [Voyage AI](/concepts/knowledge/embedder/voyageai)

### Best Practices

<Tip>
  **Chunk your content wisely**: Split long docs into 300–1,000 token chunks with 10-20% overlap. This balances context preservation with retrieval precision.
</Tip>

<Tip>
  **Store rich metadata**: Include titles, source URLs, timestamps, and permissions with each chunk. This enables filtering and better context in responses.
</Tip>

<Tip>
  **Test your retrieval quality**: Use a small set of test queries to evaluate if you're finding the right chunks. Adjust chunking strategy and embedder if needed.
</Tip>

<Warning>
  **Re-embed when you change models**: If you switch embedders, you must re-embed all your content. Vectors from different models aren't compatible.
</Warning>

### Batch Embeddings

Many embedding providers support processing multiple texts in a single API call, known as batch embedding. This approach offers several advantages: it reduces the number of API requests,
helps avoid rate limits, and significantly improves performance when processing large amounts of text.

To enable batch processing, set the `enable_batch` flag to `True` when configuring your embedder.
The `batch_size` paramater can be used to control the amount of texts sent per batch.
```

---

## In-Memory Storage for Teams

**URL:** llms-txt#in-memory-storage-for-teams

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/db/in_memory/in_memory_for_team

Example using `InMemoryDb` with teams for multi-agent coordination.

```python  theme={null}
from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

---

## Reasoning Analyst Agent - Specialized in logical analysis

**URL:** llms-txt#reasoning-analyst-agent---specialized-in-logical-analysis

reasoning_analyst = Agent(
    name="Reasoning Analyst",
    model=Claude(id="claude-sonnet-4-20250514"),
    role="Apply logical reasoning to analyze gathered information",
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "Analyze information using structured reasoning approaches.",
        "Identify logical connections and relationships.",
        "Apply deductive and inductive reasoning where appropriate.",
        "Break down complex topics into logical components.",
        "Use reasoning tools to structure your analysis.",
    ],
    markdown=True,
)

---

## Agent with PDF Input (URL)

**URL:** llms-txt#agent-with-pdf-input-(url)

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/gemini/pdf_input_url

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Secondary Searcher Agent - Targeted and specialized search

**URL:** llms-txt#secondary-searcher-agent---targeted-and-specialized-search

secondary_searcher = Agent(
    name="Secondary Searcher",
    model=Claude(id="claude-3-7-sonnet-latest"),
    role="Perform targeted searches on specific topics and edge cases",
    knowledge=knowledge_secondary,
    search_knowledge=True,
    instructions=[
        "Perform targeted searches on specific aspects of the query.",
        "Look for edge cases, technical details, and specialized information.",
        "Use infinity reranking to find the most precise matches.",
        "Focus on details that complement the primary search results.",
    ],
    markdown=True,
)

---

## Setup our AgentOS app

**URL:** llms-txt#setup-our-agentos-app

**Contents:**
- Usage
- Key Features
- Team Members

agent_os = AgentOS(
    teams=[research_team],
    interfaces=[AGUI(team=research_team)],
)
app = agent_os.get_app()

if __name__ == "__main__":
    """Run our AgentOS.

You can see the configuration and available apps at:
    http://localhost:7777/config

"""
    agent_os.serve(app="research_team:app", reload=True)
bash  theme={null}
    export OPENAI_API_KEY=your_openai_api_key
    bash  theme={null}
    pip install -U agno
    bash Mac theme={null}
      python cookbook/os/interfaces/agui/research_team.py
      bash Windows theme={null}
      python cookbook/os/interfaces/agui/research_team.py
      ```
    </CodeGroup>
  </Step>
</Steps>

* **Multi-Agent Collaboration**: Researcher and writer working together
* **Specialized Roles**: Distinct expertise and responsibilities
* **Transparent Process**: See individual agent contributions
* **Coordinated Workflow**: Structured research-to-content pipeline
* **Web Interface**: Professional team interaction through AG-UI

* **Researcher**: Information gathering and analysis specialist
* **Writer**: Content creation and structuring expert
* **Workflow**: Sequential collaboration from research to final content

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Setup your Agent with the Database

**URL:** llms-txt#setup-your-agent-with-the-database

**Contents:**
- Params
- Developer Resources

agent = Agent(db=db)
```

<Snippet file="db-postgres-params.mdx" />

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/db/postgres/postgres_for_agent.py)

---

## Web Search Agent: Fetches financial information from the web

**URL:** llms-txt#web-search-agent:-fetches-financial-information-from-the-web

web_search_agent = Agent(
    name="Web Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[DuckDuckGoTools()],
    instructions="Always include sources",
    markdown=True,
)

---

## Streaming Agent with Parser Model

**URL:** llms-txt#streaming-agent-with-parser-model

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/parser_model_stream

This example demonstrates how to use a parser model with streaming output, combining Claude for parsing and OpenAI for generation.

```python parser_model_stream.py theme={null}
import random
from typing import Iterator, List

from agno.agent import Agent, RunOutputEvent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from pydantic import BaseModel, Field
from rich.pretty import pprint  # noqa

class NationalParkAdventure(BaseModel):
    park_name: str = Field(..., description="Name of the national park")
    best_season: str = Field(
        ...,
        description="Optimal time of year to visit this park (e.g., 'Late spring to early fall')",
    )
    signature_attractions: List[str] = Field(
        ...,
        description="Must-see landmarks, viewpoints, or natural features in the park",
    )
    recommended_trails: List[str] = Field(
        ...,
        description="Top hiking trails with difficulty levels (e.g., 'Angel's Landing - Strenuous')",
    )
    wildlife_encounters: List[str] = Field(
        ..., description="Animals visitors are likely to spot, with viewing tips"
    )
    photography_spots: List[str] = Field(
        ...,
        description="Best locations for capturing stunning photos, including sunrise/sunset spots",
    )
    camping_options: List[str] = Field(
        ..., description="Available camping areas, from primitive to RV-friendly sites"
    )
    safety_warnings: List[str] = Field(
        ..., description="Important safety considerations specific to this park"
    )
    hidden_gems: List[str] = Field(
        ..., description="Lesser-known spots or experiences that most visitors miss"
    )
    difficulty_rating: int = Field(
        ...,
        ge=1,
        le=5,
        description="Overall park difficulty for average visitor (1=easy, 5=very challenging)",
    )
    estimated_days: int = Field(
        ...,
        ge=1,
        le=14,
        description="Recommended number of days to properly explore the park",
    )
    special_permits_needed: List[str] = Field(
        default=[],
        description="Any special permits or reservations required for certain activities",
    )

agent = Agent(
    parser_model=Claude(id="claude-sonnet-4-20250514"),
    description="You help people plan amazing national park adventures and provide detailed park guides.",
    output_schema=NationalParkAdventure,
    model=OpenAIChat(id="gpt-5-mini"),
)

---

## Hybrid Searcher Agent - Specialized in hybrid search

**URL:** llms-txt#hybrid-searcher-agent---specialized-in-hybrid-search

hybrid_searcher = Agent(
    name="Hybrid Searcher",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Perform hybrid search combining vector and text search",
    knowledge=hybrid_knowledge,
    search_knowledge=True,
    instructions=[
        "Combine vector similarity and text search for comprehensive results.",
        "Find information that matches both semantic and lexical criteria.",
        "Use PostgreSQL's hybrid search capabilities for best coverage.",
        "Ensure retrieval of both conceptually and textually relevant content.",
    ],
    markdown=True,
)

---

## Agentic Knowledge Filters

**URL:** llms-txt#agentic-knowledge-filters

**Contents:**
- Step 1: Attach Metadata
- How It Works
- 🌟 See Agentic Filters in Action!
- When to Use Agentic Filtering
- Try It Out!
- Developer Resources

Agentic filtering lets the Agent automatically extract filter criteria from your query text, making the experience more natural and interactive.

## Step 1: Attach Metadata

There are two ways to attach metadata to your documents:

1. **Attach Metadata When Initializing the Knowledge Base**

2. **Attach Metadata When Loading Documents One by One**

When you enable agentic filtering (`enable_agentic_knowledge_filters=True`), the Agent analyzes your query and applies filters based on the metadata it detects.

In this example, the Agent will automatically use:

* `user_id = "jordan_mitchell"`
* `document_type = "cv"`

## 🌟 See Agentic Filters in Action!

Experience how agentic filters automatically extract relevant metadata from your query.

<img src="https://mintcdn.com/agno-v2/Y7twezR0wF2re1xh/images/agentic_filters.png?fit=max&auto=format&n=Y7twezR0wF2re1xh&q=85&s=2bf046e2fb9607b1db6e8a1b5ee0ead0" alt="Agentic Filters in Action" data-og-width="1740" width="1740" data-og-height="715" height="715" data-path="images/agentic_filters.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/Y7twezR0wF2re1xh/images/agentic_filters.png?w=280&fit=max&auto=format&n=Y7twezR0wF2re1xh&q=85&s=0245d20f27f0679692757ba76db108bc 280w, https://mintcdn.com/agno-v2/Y7twezR0wF2re1xh/images/agentic_filters.png?w=560&fit=max&auto=format&n=Y7twezR0wF2re1xh&q=85&s=24d9bd1af34e8846247939e2d74b27ac 560w, https://mintcdn.com/agno-v2/Y7twezR0wF2re1xh/images/agentic_filters.png?w=840&fit=max&auto=format&n=Y7twezR0wF2re1xh&q=85&s=04efcadbf12c4616ef040032fb9b33ff 840w, https://mintcdn.com/agno-v2/Y7twezR0wF2re1xh/images/agentic_filters.png?w=1100&fit=max&auto=format&n=Y7twezR0wF2re1xh&q=85&s=1a905546407daa3fc8a19a2972bc4153 1100w, https://mintcdn.com/agno-v2/Y7twezR0wF2re1xh/images/agentic_filters.png?w=1650&fit=max&auto=format&n=Y7twezR0wF2re1xh&q=85&s=b86573d2610c92c819677f366619146e 1650w, https://mintcdn.com/agno-v2/Y7twezR0wF2re1xh/images/agentic_filters.png?w=2500&fit=max&auto=format&n=Y7twezR0wF2re1xh&q=85&s=46ae6ac18ae5b147a8c7eee02c45cfff 2500w" />

*The Agent intelligently narrows down results based on your query.*

## When to Use Agentic Filtering

* When you want a more conversational, user-friendly experience.
* When users may not know the exact filter syntax.

* Enable `enable_agentic_knowledge_filters=True` on your Agent.
* Ask questions naturally, including filter info in your query.
* See how the Agent narrows down results automatically!

## Developer Resources

* [Agentic filtering](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/filters/agentic_filtering.py)

**Examples:**

Example 1 (unknown):
```unknown
2. **Attach Metadata When Loading Documents One by One**
```

Example 2 (unknown):
```unknown
***

## How It Works

When you enable agentic filtering (`enable_agentic_knowledge_filters=True`), the Agent analyzes your query and applies filters based on the metadata it detects.

**Example:**
```

---

## AgentSession

**URL:** llms-txt#agentsession

**Contents:**
- AgentSession Attributes
- AgentSession Methods
  - `upsert_run(run: RunOutput)`
  - `get_run(run_id: str) -> Optional[RunOutput]`
  - `get_messages_from_last_n_runs(...) -> List[Message]`
  - `get_session_summary() -> Optional[SessionSummary]`
  - `get_chat_history() -> List[Message]`

Source: https://docs.agno.com/reference/agents/session

## AgentSession Attributes

| Parameter      | Type                        | Default  | Description                                                        |
| -------------- | --------------------------- | -------- | ------------------------------------------------------------------ |
| `session_id`   | `str`                       | Required | Session UUID                                                       |
| `agent_id`     | `Optional[str]`             | `None`   | ID of the agent that this session is associated with               |
| `team_id`      | `Optional[str]`             | `None`   | ID of the team that this session is associated with                |
| `user_id`      | `Optional[str]`             | `None`   | ID of the user interacting with this agent                         |
| `workflow_id`  | `Optional[str]`             | `None`   | ID of the workflow that this session is associated with            |
| `session_data` | `Optional[Dict[str, Any]]`  | `None`   | Session Data: session\_name, session\_state, images, videos, audio |
| `metadata`     | `Optional[Dict[str, Any]]`  | `None`   | Metadata stored with this agent                                    |
| `agent_data`   | `Optional[Dict[str, Any]]`  | `None`   | Agent Data: agent\_id, name and model                              |
| `runs`         | `Optional[List[RunOutput]]` | `None`   | List of all runs in the session                                    |
| `summary`      | `Optional[SessionSummary]`  | `None`   | Summary of the session                                             |
| `created_at`   | `Optional[int]`             | `None`   | The unix timestamp when this session was created                   |
| `updated_at`   | `Optional[int]`             | `None`   | The unix timestamp when this session was last updated              |

## AgentSession Methods

### `upsert_run(run: RunOutput)`

Adds a RunOutput to the runs list. If a run with the same `run_id` already exists, it updates the existing run.

### `get_run(run_id: str) -> Optional[RunOutput]`

Retrieves a specific run by its `run_id`.

### `get_messages_from_last_n_runs(...) -> List[Message]`

Gets messages from the last N runs with various filtering options:

* `agent_id`: Filter by agent ID
* `team_id`: Filter by team ID
* `last_n`: Number of recent runs to include
* `skip_role`: Skip messages with specific role
* `skip_status`: Skip runs with specific statuses
* `skip_history_messages`: Whether to skip history messages

### `get_session_summary() -> Optional[SessionSummary]`

Get the session summary for the session

### `get_chat_history() -> List[Message]`

Get the chat history for the session

---

## In-Memory Storage for Agents

**URL:** llms-txt#in-memory-storage-for-agents

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/db/in_memory/in_memory_for_agent

Example using `InMemoryDb` with agent.

```python  theme={null}
from agno.agent import Agent
from agno.db.in_memory import InMemoryDb

---

## run_response = agent.continue_run(run_id=run_response.run_id, updated_tools=run_response.tools)

**URL:** llms-txt#run_response-=-agent.continue_run(run_id=run_response.run_id,-updated_tools=run_response.tools)

pprint.pprint_run_response(run_response)

---

## Medical research agent

**URL:** llms-txt#medical-research-agent

medical_agent = Agent(
    name="Medical Agent",
    model=Claude(id="claude-3-5-sonnet-latest"),
    role="Medical researcher",
    tools=[PubmedTools()],
    instructions=[
        "You are a medical agent that can answer questions about medical topics.",
        "Always search for recent medical literature and evidence.",
    ],
)

---

## Deep Research Agent

**URL:** llms-txt#deep-research-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/use-cases/agents/deep_research_agent_exa

This example demonstrates how to use the Exa research tool for complex,
structured research tasks with automatic citation tracking.

```python cookbook/examples/agents/deep_research_agent_exa.py theme={null}
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[ExaTools(research=True, research_model="exa-research-pro")],
    instructions=dedent("""
        You are an expert research analyst with access to advanced research tools.
        
        When you are given a schema to use, pass it to the research tool as output_schema parameter to research tool.

The research tool has two parameters:
        - instructions (str): The research topic/question 
        - output_schema (dict, optional): A JSON schema for structured output

Example: If user says "Research X. Use this schema {'type': 'object', ...}", you must call research tool with the schema.

If no schema is provided, the tool will auto-infer an appropriate schema.

Present the findings exactly as provided by the research tool.
    """),
)

---

## Create a database connection

**URL:** llms-txt#create-a-database-connection

db = SqliteDb(
    db_file="tmp/memory.db"
)

memory_tools = MemoryTools(
    db=db,
)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[memory_tools],
    markdown=True,
)

agent.print_response(
    "My name is John Doe and I like to hike in the mountains on weekends. "
    "I like to travel to new places and experience different cultures. "
    "I am planning to travel to Africa in December. ",
    user_id="john_doe@example.com",
    stream=True
)

---

## Agent with Tools Stream

**URL:** llms-txt#agent-with-tools-stream

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/llama_cpp/tool_use_stream

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install LlamaCpp">
    Follow the [LlamaCpp installation guide](https://github.com/ggerganov/llama.cpp) and start the server:

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install LlamaCpp">
    Follow the [LlamaCpp installation guide](https://github.com/ggerganov/llama.cpp) and start the server:
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

## This is the function that the agent will use to retrieve documents

**URL:** llms-txt#this-is-the-function-that-the-agent-will-use-to-retrieve-documents

**Contents:**
- Usage

def knowledge_retriever(
    query: str, agent: Optional[Agent] = None, num_documents: int = 5, **kwargs
) -> Optional[list[dict]]:
    """
    Custom knowledge retriever function to search the vector database for relevant documents.

Args:
        query (str): The search query string
        agent (Agent): The agent instance making the query
        num_documents (int): Number of documents to retrieve (default: 5)
        **kwargs: Additional keyword arguments

Returns:
        Optional[list[dict]]: List of retrieved documents or None if search fails
    """
    try:
        qdrant_client = QdrantClient(url="http://localhost:6333")
        query_embedding = embedder.get_embedding(query)
        results = qdrant_client.query_points(
            collection_name="thai-recipes",
            query=query_embedding,
            limit=num_documents,
        )
        results_dict = results.model_dump()
        if "points" in results_dict:
            return results_dict["points"]
        else:
            return None
    except Exception as e:
        print(f"Error during vector database search: {str(e)}")
        return None

def main():
    """Main function to demonstrate agent usage."""
    # Initialize agent with custom knowledge retriever
    # Remember to set search_knowledge=True to use agentic_rag or add_reference=True for traditional RAG
    # search_knowledge=True is default when you add a knowledge base but is needed here
    agent = Agent(
        knowledge_retriever=knowledge_retriever,
        search_knowledge=True,
        instructions="Search the knowledge base for information",
    )

# Example query
    query = "List down the ingredients to make Massaman Gai"
    agent.print_response(query, markdown=True)

if __name__ == "__main__":
    main()
bash  theme={null}
    pip install -U agno openai qdrant-client
    bash  theme={null}
    docker run -p 6333:6333 qdrant/qdrant
    bash  theme={null}
    export OPENAI_API_KEY=your_openai_api_key_here
    bash Mac theme={null}
      python cookbook/knowledge/custom_retriever/retriever.py
      bash Windows theme={null}
      python cookbook/knowledge/custom_retriever/retriever.py
      ```
    </CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run Qdrant">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Set OpenAI API key">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run the example">
    <CodeGroup>
```

---

## Run periodically or before high-cost operations

**URL:** llms-txt#run-periodically-or-before-high-cost-operations

**Contents:**
- Mitigation Strategy #5: Set Tool Call Limits
- Common Pitfalls
  - The user\_id Pitfall

prune_old_memories(db, user_id="john_doe@example.com")
python  theme={null}
agent = Agent(
    db=db,
    enable_agentic_memory=True,
    tool_call_limit=5  # Prevents excessive memory operations
)
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
## Mitigation Strategy #5: Set Tool Call Limits

Prevent runaway memory operations by limiting tool calls per conversation:
```

Example 2 (unknown):
```unknown
## Common Pitfalls

### The user\_id Pitfall

**The Problem:** Forgetting to set `user_id` causes all memories to default to `user_id="default"`, mixing different users' memories together.
```

---

## Create Knowledge Instance

**URL:** llms-txt#create-knowledge-instance

knowledge = Knowledge(
    name="Basic SDK Knowledge Base",
    description="Agno 2.0 Knowledge Implementation",
    contents_db=contents_db,
    vector_db=PgVector(
        table_name="vectors", db_url="postgresql+psycopg://ai:ai@localhost:5532/ai"
    ),
)

---

## Initialize the academic research agent with scholarly capabilities

**URL:** llms-txt#initialize-the-academic-research-agent-with-scholarly-capabilities

research_scholar = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[
        ExaTools(
            start_published_date=datetime.now().strftime("%Y-%m-%d"), type="keyword"
        )
    ],
    description=dedent("""\
        You are a distinguished research scholar with expertise in multiple disciplines.
        Your academic credentials include: 📚

- Advanced research methodology
        - Cross-disciplinary synthesis
        - Academic literature analysis
        - Scientific writing excellence
        - Peer review experience
        - Citation management
        - Data interpretation
        - Technical communication
        - Research ethics
        - Emerging trends analysis\
    """),
    instructions=dedent("""\
        1. Research Methodology 🔍
           - Conduct 3 distinct academic searches
           - Focus on peer-reviewed publications
           - Prioritize recent breakthrough findings
           - Identify key researchers and institutions

2. Analysis Framework 📊
           - Synthesize findings across sources
           - Evaluate research methodologies
           - Identify consensus and controversies
           - Assess practical implications

3. Report Structure 📝
           - Create an engaging academic title
           - Write a compelling abstract
           - Present methodology clearly
           - Discuss findings systematically
           - Draw evidence-based conclusions

4. Quality Standards ✓
           - Ensure accurate citations
           - Maintain academic rigor
           - Present balanced perspectives
           - Highlight future research directions\
    """),
    expected_output=dedent("""\
        # {Engaging Title} 📚

## Abstract
        {Concise overview of the research and key findings}

## Introduction
        {Context and significance}
        {Research objectives}

## Methodology
        {Search strategy}
        {Selection criteria}

## Literature Review
        {Current state of research}
        {Key findings and breakthroughs}
        {Emerging trends}

## Analysis
        {Critical evaluation}
        {Cross-study comparisons}
        {Research gaps}

## Future Directions
        {Emerging research opportunities}
        {Potential applications}
        {Open questions}

## Conclusions
        {Summary of key findings}
        {Implications for the field}

## References
        {Properly formatted academic citations}

---
        Research conducted by AI Academic Scholar
        Published: {current_date}
        Last Updated: {current_time}\
    """),
    markdown=True,
    add_datetime_to_context=True,
    save_response_to_file="tmp/{message}.md",
)

---

## Control Plane

**URL:** llms-txt#control-plane

**Contents:**
- OS Management
- User Management
  - Inviting Members
  - Member Roles
- General Settings
- Feature Access
- Next Steps

Source: https://docs.agno.com/agent-os/control-plane

The main web interface for interacting with and managing your AgentOS instances

The AgentOS Control Plane is your primary web interface for accessing and managing all AgentOS features. This intuitive dashboard serves as the central hub where you interact with your agents, manage knowledge bases, track sessions, monitor performance, and control user access.

<Frame>
  <img src="https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-full-screenshot.png?fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=47cda181dd5fe3e35b00952cc2fc1e85" alt="AgentOS Control Plane Dashboard" style={{ borderRadius: "0.5rem" }} data-og-width="3477" width="3477" data-og-height="2005" height="2005" data-path="images/agentos-full-screenshot.png" data-optimize="true" data-opv="3" srcset="https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-full-screenshot.png?w=280&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=64b3f57b511b5082368b71ab2461fc91 280w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-full-screenshot.png?w=560&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=611e80fc18ec8b4d10f2c01711242bea 560w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-full-screenshot.png?w=840&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=d3d30a7be52757d5d2a444385094d2c0 840w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-full-screenshot.png?w=1100&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=e94a89850b6d5f063a1f5b13c9503002 1100w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-full-screenshot.png?w=1650&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=8a17eadbd7c02cdc2fb6f9e234f4ac61 1650w, https://mintcdn.com/agno-v2/Is_2Bv3MNVYdZh1v/images/agentos-full-screenshot.png?w=2500&fit=max&auto=format&n=Is_2Bv3MNVYdZh1v&q=85&s=2450b803257dcc93c2621c855964fb2b 2500w" />
</Frame>

Connect and inspect your OS runtimes from a single interface. Switch between local development and live production instances, monitor connection health, and configure endpoints for your different environments.

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/CnjZpOWVs1q9bnAO/videos/agentos-select-os.mp4?fit=max&auto=format&n=CnjZpOWVs1q9bnAO&q=85&s=c6514be6950c2e9c7b103f071ac85b11" type="video/mp4" data-path="videos/agentos-select-os.mp4" />
  </video>
</Frame>

Manage your organization members and their access to AgentOS features. Configure your organization name, invite team members, and control permissions from a centralized interface.

Add new team members to your organization by entering their email addresses. You can invite multiple users at once by separating emails with commas or pressing Enter/Tab between addresses.

Control what each member can access:

* **Owner**: Full administrative access including billing and member management
* **Member**: Access to AgentOS features and collaboration capabilities

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/CnjZpOWVs1q9bnAO/videos/agentos-invite-member.mp4?fit=max&auto=format&n=CnjZpOWVs1q9bnAO&q=85&s=f54f71b63fd4b2110e211e0d1f0602c6" type="video/mp4" data-path="videos/agentos-invite-member.mp4" />
  </video>
</Frame>

Configure your account preferences and organization settings. Access your profile information, manage billing and subscription details, and adjust organization-wide preferences from a centralized settings interface.

The control plane provides direct access to all main AgentOS capabilities through an intuitive interface:

<Note>
  **Getting Started Tip**: The control plane is your gateway to all AgentOS
  features. Start by connecting your OS instance, then explore each feature
  section to familiarize yourself with the interface.
</Note>

<CardGroup cols={2}>
  <Card title="Chat Interface" icon="comment" href="/agent-os/features/chat-interface">
    Start conversations with your agents and access multi-agent interactions
  </Card>

<Card title="Knowledge Management" icon="book" href="/concepts/knowledge/overview">
    Upload and organize documents with search and browsing capabilities
  </Card>

<Card title="Memory System" icon="brain" href="/concepts/memory/overview">
    Browse stored memories and search through conversation history
  </Card>

<Card title="Session Tracking" icon="clock" href="/concepts/agents/sessions">
    Track and analyze agent interactions and performance
  </Card>

<Card title="Evaluation & Testing" icon="chart-bar" href="/concepts/evals/overview">
    Test and evaluate agent performance with comprehensive metrics
  </Card>

<Card title="Metrics & Monitoring" icon="chart-line" href="/concepts/agents/metrics">
    Monitor system performance and usage analytics
  </Card>
</CardGroup>

Ready to get started with the AgentOS control plane? Here's what you need to do:

<CardGroup cols={2}>
  <Card title="Create Your First OS" icon="plus" href="/agent-os/creating-your-first-os">
    Set up a new AgentOS instance from scratch using our templates
  </Card>

<Card title="Connect Your AgentOS" icon="link" href="/agent-os/connecting-your-os">
    Learn how to connect your local development environment to the platform
  </Card>
</CardGroup>

---

## Initialize the agent with a tech-savvy personality and clear instructions

**URL:** llms-txt#initialize-the-agent-with-a-tech-savvy-personality-and-clear-instructions

agent = Agent(
    description="A Tech News Assistant that fetches and summarizes Hacker News stories",
    instructions=dedent("""\
        You are an enthusiastic Tech Reporter

Your responsibilities:
        - Present Hacker News stories in an engaging and informative way
        - Provide clear summaries of the information you gather

Style guide:
        - Use emoji to make your responses more engaging
        - Keep your summaries concise but informative
        - End with a friendly tech-themed sign-off\
    """),
    tools=[get_top_hackernews_stories],
    markdown=True,
)

---

## Shared knowledge base for the reasoning team

**URL:** llms-txt#shared-knowledge-base-for-the-reasoning-team

knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs_reasoning_team",
        search_type=SearchType.hybrid,
        embedder=CohereEmbedder(id="embed-v4.0"),
        reranker=CohereReranker(model="rerank-v3.5"),
    ),
)

---

## Build a Social Media Intelligence Agent with Agno, X Tools, and Exa

**URL:** llms-txt#build-a-social-media-intelligence-agent-with-agno,-x-tools,-and-exa

**Contents:**
- What You'll Build
- Prerequisites and Setup

Source: https://docs.agno.com/tutorials/social-media-agent

Create a professional-grade social media intelligence system using Agno.

In this tutorial, we will build a multi-agent intelligence system. It will monitor X (Twitter), perform sentiment analysis, and generate reports using Agno framework.

We will be using the following components:

* **Agno** - The fastest framework for building agents.
* **X Tools** - Provides real-time, structured data directly from Twitter/X API with engagement metrics
* **Exa Tools** - Deliver semantic web search for broader context discovery across blogs, forums, and news
* **GPT-5 Mini** - OpenAI's new model. Well suited for contextually-aware sentiment analysis and strategic pattern detection

This system will combine direct social media data with broader web intelligence, to provide comprehensive brand monitoring that captures both immediate social sentiment and emerging discussions before they reach mainstream attention.

Your social media intelligence system will:

* Track brand and competitor mentions across X and the broader web
* Perform weighted sentiment analysis that accounts for influence and engagement
* Detect viral content, controversy signals, and high-influence discussions
* Generate executive-ready reports with strategic recommendations
* Serve insights via [AgentOS](/agent-os/introduction) API for integration with your applications

## Prerequisites and Setup

Before we get started, we need to setup our environment:

1. Install Python, Git and get your API keys:

* Install **Python >= 3.9** and **Git**
* Get API keys for:
  * **X (Twitter) Developer Account** ([Apply here](https://developer.twitter.com/en/apply-for-access))
  * **OpenAI API** ([Get key](https://platform.openai.com/api-keys))
  * **Exa API** ([Sign up](https://exa.ai))

2. Setup your Python environment:

3. Install our Python dependencies:

````bash  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
3. Install our Python dependencies:
```

---

## Workflow Patterns

**URL:** llms-txt#workflow-patterns

**Contents:**
- Building Blocks
- Advanced Patterns

Source: https://docs.agno.com/concepts/workflows/workflow-patterns/overview

Master deterministic workflow patterns including sequential, parallel, conditional, and looping execution for reliable multi-agent automation.

Build deterministic, production-ready workflows that orchestrate agents, teams, and functions with predictable execution patterns. This comprehensive guide covers all workflow types, from simple sequential processes to complex branching logic with parallel execution and dynamic routing.

Unlike free-form agent interactions, these patterns provide structured automation with consistent, repeatable results ideal for production systems.

The core building blocks of Agno Workflows are:

| Component     | Purpose                         |
| ------------- | ------------------------------- |
| **Step**      | Basic execution unit            |
| **Agent**     | AI assistant with specific role |
| **Team**      | Coordinated group of agents     |
| **Function**  | Custom Python logic             |
| **Parallel**  | Concurrent execution            |
| **Condition** | Conditional execution           |
| **Loop**      | Iterative execution             |
| **Router**    | Dynamic routing                 |

Agno Workflows support multiple execution patterns that can be combined to build sophisticated automation systems.
Each pattern serves specific use cases and can be composed together for complex workflows.

<CardGroup cols={2}>
  <Card title="Sequential Workflows" icon="arrow-right" href="/concepts/workflows/workflow-patterns/sequential">
    Linear execution with step-by-step processing
  </Card>

<Card title="Parallel Workflows" icon="arrows-split-up-and-left" href="/concepts/workflows/workflow-patterns/parallel-workflow">
    Concurrent execution for independent tasks
  </Card>

<Card title="Conditional Workflows" icon="code-branch" href="/concepts/workflows/workflow-patterns/conditional-workflow">
    Branching logic based on conditions
  </Card>

<Card title="Iterative Workflows" icon="rotate" href="/concepts/workflows/workflow-patterns/iterative-workflow">
    Loop-based execution with quality controls
  </Card>

<Card title="Branching Workflows" icon="sitemap" href="/concepts/workflows/workflow-patterns/branching-workflow">
    Dynamic routing and path selection
  </Card>

<Card title="Grouped Steps" icon="layer-group" href="/concepts/workflows/workflow-patterns/grouped-steps-workflow">
    Reusable step sequences and modular design
  </Card>
</CardGroup>

<CardGroup cols={2}>
  <Card title="Function-Based Workflows" icon="function" href="/concepts/workflows/workflow-patterns/custom-function-step-workflow">
    Pure Python workflows with complete control
  </Card>

<Card title="Multi-Pattern Combinations" icon="puzzle-piece" href="/concepts/workflows/workflow-patterns/advanced-workflow-patterns">
    Complex workflows combining multiple patterns
  </Card>
</CardGroup>

---

## Refresh the context

**URL:** llms-txt#refresh-the-context

agent.context["memory"] = zep_tools.get_zep_memory(memory_type="context")

---

## Agent Same Run Image Analysis

**URL:** llms-txt#agent-same-run-image-analysis

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/multimodal/agent_same_run_image_analysis

This example demonstrates how to create an agent that generates an image using DALL-E and then analyzes the generated image in the same run, providing insights about the image's contents.

```python agent_same_run_image_analysis.py theme={null}
from agno.agent import Agent
from agno.tools.dalle import DalleTools

---

## Secondary knowledge base for cross-validation

**URL:** llms-txt#secondary-knowledge-base-for-cross-validation

validation_knowledge = Knowledge(
    vector_db=LanceDb(
        table_name="recipes_validation",
        uri="tmp/lancedb",
        search_type=SearchType.vector,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

---

## Reasoning Agent Events Handling

**URL:** llms-txt#reasoning-agent-events-handling

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/events/reasoning_agent_events

This example demonstrates how to handle and monitor reasoning events when using an agent with reasoning capabilities, including reasoning steps and content generation.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Create a Python file">
    Create a Python file and add the above code.

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/events" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## run_response = asyncio.run(agent.acontinue_run(run_id=run_response.run_id))

**URL:** llms-txt#run_response-=-asyncio.run(agent.acontinue_run(run_id=run_response.run_id))

pprint.pprint_run_response(run_response)

---

## Answer Synthesizer Agent - Specialized in synthesis

**URL:** llms-txt#answer-synthesizer-agent---specialized-in-synthesis

answer_synthesizer = Agent(
    name="Answer Synthesizer",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Synthesize retrieved information into comprehensive answers",
    instructions=[
        "Combine information from the Primary Retriever and Context Expander.",
        "Create a comprehensive, well-structured response.",
        "Ensure logical flow and coherence in the final answer.",
        "Include relevant details while maintaining clarity.",
        "Organize information in a user-friendly format.",
    ],
    markdown=True,
)

---

## Simple Agent Evals

**URL:** llms-txt#simple-agent-evals

**Contents:**
- Evaluation Dimensions
- Quick Start

Source: https://docs.agno.com/concepts/evals/overview

Learn how to evaluate your Agno Agents and Teams across three key dimensions - accuracy (using LLM-as-a-judge), performance (runtime and memory), and reliability (tool calls).

**Evals** is a way to measure the quality of your Agents and Teams. Agno provides 3 dimensions for evaluating Agents:

## Evaluation Dimensions

<CardGroup cols={3}>
  <Card title="Accuracy" icon="bullseye" href="/concepts/evals/accuracy">
    The accuracy of the Agent's response using LLM-as-a-judge methodology.
  </Card>

<Card title="Performance" icon="stopwatch" href="/concepts/evals/performance">
    The performance of the Agent's response, including latency and memory footprint.
  </Card>

<Card title="Reliability" icon="shield-check" href="/concepts/evals/reliability">
    The reliability of the Agent's response, including tool calls and error handling.
  </Card>
</CardGroup>

Here's a simple example of running an accuracy evaluation:

```python quick_eval.py theme={null}
from typing import Optional
from agno.agent import Agent
from agno.eval.accuracy import AccuracyEval, AccuracyResult
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools

---

## What is Memory?

**URL:** llms-txt#what-is-memory?

**Contents:**
- How Memory Works
- Getting Started with Memory

Source: https://docs.agno.com/concepts/memory/overview

Give your agents the ability to remember user preferences, context, and past interactions for truly personalized experiences.

Imagine a customer support agent that remembers your product preferences from last week, or a personal assistant that knows you prefer morning meetings, but only after you've had coffee. This is the power of Memory in Agno.

When relevant information appears in a conversation, like a user's name, preferences, or habits, an Agent with Memory automatically stores it in your database. Later, when that information becomes relevant again, the agent retrieves and uses it naturally in the conversation. The agent is effectively **learning about each user** across interactions.

<Tip>
  **Memory ≠ Session History:** Memory stores learned user facts ("Sarah prefers email"), [session history](/concepts/agents/sessions#session-history) stores conversation messages for continuity ("what did we just discuss?").
</Tip>

## Getting Started with Memory

Setting up memory is straightforward: just connect a database and enable the memory feature. Here's a basic setup:

```python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

---

## Initialize the research agent with advanced journalistic capabilities

**URL:** llms-txt#initialize-the-research-agent-with-advanced-journalistic-capabilities

research_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools(), Newspaper4kTools()],
    description=dedent("""\
        You are an elite investigative journalist with decades of experience at the New York Times.
        Your expertise encompasses: 📰

- Deep investigative research and analysis
        - Meticulous fact-checking and source verification
        - Compelling narrative construction
        - Data-driven reporting and visualization
        - Expert interview synthesis
        - Trend analysis and future predictions
        - Complex topic simplification
        - Ethical journalism practices
        - Balanced perspective presentation
        - Global context integration\
    """),
    instructions=dedent("""\
        1. Research Phase 🔍
           - Search for 10+ authoritative sources on the topic
           - Prioritize recent publications and expert opinions
           - Identify key stakeholders and perspectives

2. Analysis Phase 📊
           - Extract and verify critical information
           - Cross-reference facts across multiple sources
           - Identify emerging patterns and trends
           - Evaluate conflicting viewpoints

3. Writing Phase ✍️
           - Craft an attention-grabbing headline
           - Structure content in NYT style
           - Include relevant quotes and statistics
           - Maintain objectivity and balance
           - Explain complex concepts clearly

4. Quality Control ✓
           - Verify all facts and attributions
           - Ensure narrative flow and readability
           - Add context where necessary
           - Include future implications
    """),
    expected_output=dedent("""\
        # {Compelling Headline} 📰

## Executive Summary
        {Concise overview of key findings and significance}

## Background & Context
        {Historical context and importance}
        {Current landscape overview}

## Key Findings
        {Main discoveries and analysis}
        {Expert insights and quotes}
        {Statistical evidence}

## Impact Analysis
        {Current implications}
        {Stakeholder perspectives}
        {Industry/societal effects}

## Future Outlook
        {Emerging trends}
        {Expert predictions}
        {Potential challenges and opportunities}

## Expert Insights
        {Notable quotes and analysis from industry leaders}
        {Contrasting viewpoints}

## Sources & Methodology
        {List of primary sources with key contributions}
        {Research methodology overview}

---
        Research conducted by AI Investigative Journalist
        New York Times Style Report
        Published: {current_date}
        Last Updated: {current_time}\
    """),
    markdown=True,
    add_datetime_to_context=True,
)

---

## Agent Sessions

**URL:** llms-txt#agent-sessions

**Contents:**
- Single session

Source: https://docs.agno.com/concepts/agents/sessions

Learn about Agent sessions and managing conversation history.

When we call `Agent.run()`, it creates a stateless, singular Agent run.

But what if we want to continue this conversation i.e. have a multi-turn conversation? That's where "Sessions" come in. A session is collection of consecutive runs.

In practice, a session is a multi-turn conversation between a user and an Agent. Using a `session_id`, we can connect the conversation history and state across multiple runs.

Here are the core concepts:

* **Session:** A session is collection of consecutive runs like a multi-turn conversation between a user and an Agent. Sessions are identified by a `session_id` and house all runs, metrics, state and other data that belong to the session.
* **Run:** Every interaction (i.e. chat or turn) with an Agent is called a **run**. Runs are identified by a `run_id` and `Agent.run()` creates a new `run_id` when called.
* **Messages:** are the individual messages sent between the model and the Agent. Messages are the communication protocol between the Agent and model.

See [Session Storage](/concepts/agents/storage) for more details on how sessions are stored.

Here we have an example where a single run is created with an Agent. A `run_id` is automatically generated, as well as a `session_id` (because we didn't provide one tot yet associated with a user.

```python  theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat

agent = Agent(model=OpenAIChat(id="gpt-5-mini"))

---

## ClickHouse

**URL:** llms-txt#clickhouse

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/clickhouse-db/clickhouse-db

```python cookbook/knowledge/vector_db/clickhouse_db/clickhouse.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.clickhouse import Clickhouse

vector_db = Clickhouse(
    table_name="recipe_documents",
    host="localhost",
    port=8123,
    username="ai",
    password="ai",
)

knowledge = Knowledge(
    name="My Clickhouse Knowledge Base",
    description="This is a knowledge base that uses a Clickhouse DB",
    vector_db=vector_db,
)

knowledge.add_content(
    name="Recipes",
    url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
    metadata={"doc_type": "recipe_book"},
)

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
    read_chat_history=True,
)

agent.print_response("How do I make pad thai?", markdown=True)

vector_db.delete_by_name("Recipes")

---

## Step 1: Initialize knowledge base with documents and metadata

**URL:** llms-txt#step-1:-initialize-knowledge-base-with-documents-and-metadata

---

## agent.print_response("New York")

**URL:** llms-txt#agent.print_response("new-york")

**Contents:**
- Usage

bash  theme={null}
    export FIREWORKS_API_KEY=xxx
    bash  theme={null}
    pip install -U openai agno
    bash Mac theme={null}
      python cookbook/models/fireworks/structured_output.py
      bash Windows theme={null}
      python cookbook/models/fireworks/structured_output.py
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

## Ask the agent to give a summary of the conversation, this will use the history from the previous messages (but only for user 1)

**URL:** llms-txt#ask-the-agent-to-give-a-summary-of-the-conversation,-this-will-use-the-history-from-the-previous-messages-(but-only-for-user-1)

**Contents:**
- Conversation history
- Session Summaries
  - Customize Session Summaries

team.print_response(
    "Give me a summary of our conversation.",
    user_id=user_2_id,
    session_id=user_2_session_id,
)
python  theme={null}
from agno.agent import Agent
from agno.team import Team
from agno.models.google.gemini import Gemini
from agno.db.sqlite import SqliteDb

db = SqliteDb(db_file="tmp/data.db")

user_id = "jon_hamm@example.com"
session_id = "1001"

team = Team(
    model=Gemini(id="gemini-2.0-flash-001"),
    members=[
        Agent(name="Agent 1", role="You answer questions in English"),
        Agent(name="Agent 2", role="You answer questions in Chinese"),
    ],
    db=db,
    enable_session_summaries=True,
)

team.print_response(
    "What can you tell me about quantum computing?",
    stream=True,
    user_id=user_id,
    session_id=session_id,
)

team.print_response(
    "I would also like to know about LLMs?",
    stream=True,
    user_id=user_id,
    session_id=session_id
)

session_summary = team.get_session_summary(session_id=session_id)
print(f"Session summary: {session_summary.summary}")
python  theme={null}
from agno.team import Team
from agno.session import SessionSummaryManager
from agno.models.openai import OpenAIChat
from agno.db.sqlite import SqliteDb

**Examples:**

Example 1 (unknown):
```unknown
## Conversation history

Teams with storage enabled automatically have access to the run history of the session (also called the "conversation history" or "chat history").

To learn more, see the [Conversation History](/concepts/teams/chat_history) documentation.

## Session Summaries

The Team can store a condensed representations of the session, useful when chat histories gets too long. This is called a "Session Summary" in Agno.

To enable session summaries, set `enable_session_summaries=True` on the `Team`.
```

Example 2 (unknown):
```unknown
### Customize Session Summaries

You can adjust the session summaries by providing a custom `session_summary_prompt` to the `Team`.

The `SessionSummaryManager` class is responsible for handling the model used to create and update session summaries.
You can adjust it to personalize how summaries are created and updated:
```

---

## Create a Creative AI Video Director Agent

**URL:** llms-txt#create-a-creative-ai-video-director-agent

video_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[ModelsLabTools()],
    description=dedent("""\
        You are an experienced AI video director with expertise in various video styles,
        from nature scenes to artistic animations. You have a deep understanding of motion,
        timing, and visual storytelling through video content.\
    """),
    instructions=dedent("""\
        As an AI video director, follow these guidelines:
        1. Analyze the user's request carefully to understand the desired style and mood
        2. Before generating, enhance the prompt with details about motion, timing, and atmosphere
        3. Use the `generate_media` tool with detailed, well-crafted prompts
        4. Provide a brief explanation of the creative choices made
        5. If the request is unclear, ask for clarification about style preferences

The video will be displayed in the UI automatically below your response.
        Always aim to create captivating and meaningful videos that bring the user's vision to life!\
    """),
    markdown=True,
)

---

## Define the research agents

**URL:** llms-txt#define-the-research-agents

hackernews_agent = Agent(
    name="HackerNews Researcher",
    instructions="You are a researcher specializing in finding the latest tech news and discussions from Hacker News. Focus on startup trends, programming topics, and tech industry insights.",
    tools=[HackerNewsTools()],
)

web_agent = Agent(
    name="Web Researcher",
    instructions="You are a comprehensive web researcher. Search across multiple sources including news sites, blogs, and official documentation to gather detailed information.",
    tools=[DuckDuckGoTools()],
)

reasoning_agent = Agent(
    name="Reasoning Agent",
    instructions="You are an expert analyst who creates comprehensive reports by analyzing and synthesizing information from multiple sources. Create well-structured, insightful reports.",
)

---

## AgentOS Configuration

**URL:** llms-txt#agentos-configuration

**Contents:**
- Configuration file
- Code

Source: https://docs.agno.com/examples/agent-os/extra_configuration

Passing extra configuration to your AgentOS

## Configuration file

We will first create a YAML file with the extra configuration we want to pass to our AgentOS:

```python cookbook/agent_os/os_config/yaml_config.py theme={null}
"""Example showing how to pass extra configuration to your AgentOS."""

from pathlib import Path

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.team import Team
from agno.vectordb.pgvector import PgVector
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow

**Examples:**

Example 1 (unknown):
```unknown
## Code
```

---

## Custom Memory Instructions

**URL:** llms-txt#custom-memory-instructions

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/memory/memory_manager/03-custom-memory-instructions

Create user memories with an Agent by providing a either text or a list of messages.

```python memory_manager/custom_memory_instructions.py theme={null}
from agno.db.postgres import PostgresDb
from agno.memory import MemoryManager
from agno.models.anthropic.claude import Claude
from agno.models.message import Message
from agno.models.openai import OpenAIChat
from rich.pretty import pprint

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

memory_db = PostgresDb(db_url=db_url)

memory = MemoryManager(
    model=OpenAIChat(id="gpt-5-mini"),
    memory_capture_instructions="""\
                    Memories should only include details about the user's academic interests.
                    Only include which subjects they are interested in.
                    Ignore names, hobbies, and personal interests.
                    """,
    db=memory_db,
)

john_doe_id = "john_doe@example.com"

memory.create_user_memories(
    input="""\
My name is John Doe.

I enjoy hiking in the mountains on weekends,
reading science fiction novels before bed,
cooking new recipes from different cultures,
playing chess with friends.

I am interested to learn about the history of the universe and other astronomical topics.
""",
    user_id=john_doe_id,
)

memories = memory.get_user_memories(user_id=john_doe_id)
print("John Doe's memories:")
pprint(memories)

---

## Readers

**URL:** llms-txt#readers

**Contents:**
- What are Readers?
- How Readers Work

Source: https://docs.agno.com/concepts/knowledge/readers

Learn how to use readers to convert raw data into searchable knowledge for your Agents.

Readers are the first step in the process of creating Knowledge from content.
They transform raw content from various sources into structured `Document` objects that can be embedded, chunked, and stored in vector databases.

A **Reader** is a specialized component that knows how to parse and extract content from specific data sources or file formats. Think of readers as translators that convert different content formats into a standardized format that Agno can work with.

Every piece of content that enters your knowledge base must pass through a reader first. The reader's job is to:

1. **Parse** the raw content from its original format
2. **Extract** the meaningful text and metadata
3. **Structure** the content into `Document` objects
4. **Apply chunking** strategies to break large content into manageable pieces

All readers inherit from the base `Reader` class and follow a consistent pattern:

```python  theme={null}

---

## Image Transcribe Document Agent

**URL:** llms-txt#image-transcribe-document-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/mistral/image_transcribe_document_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## async_response = await agent.arun(

**URL:** llms-txt#async_response-=-await-agent.arun(

---

## Capture Reasoning Content with Knowledge Tools

**URL:** llms-txt#capture-reasoning-content-with-knowledge-tools

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/reasoning/tools/capture-reasoning-content-knowledge-tools

```python cookbook/reasoning/tools/capture_reasoning_content_knowledge_tools.py theme={null}
import asyncio
from textwrap import dedent

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.tools.knowledge import KnowledgeTools
from agno.vectordb.lancedb import LanceDb, SearchType

---

## Create an agent with the analysis tool function

**URL:** llms-txt#create-an-agent-with-the-analysis-tool-function

**Contents:**
- Usage

agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    tools=[analyze_user],
    name="User Analysis Agent",
    description="An agent specialized in analyzing users using integrated data sources.",
    instructions=[
        "You are a user analysis expert with access to user analysis tools.",
        "When asked to analyze any user, use the analyze_user tool.",
        "This tool has access to user profiles and current context through integrated data sources.",
        "After getting tool results, provide additional insights and recommendations based on the analysis.",
        "Be thorough in your analysis and explain what the tool found."
    ],
)

print("=== Tool Dependencies Access Example ===\n")

response = agent.run(
    input="Please analyze user 'john_doe' and provide insights about their professional background and preferences.",
    dependencies={
        "user_profile": {
            "name": "John Doe",
            "preferences": ["AI/ML", "Software Engineering", "Finance"],
            "location": "San Francisco, CA",
            "role": "Senior Software Engineer",
        },
        "current_context": get_current_context,
    },
    session_id="test_tool_dependencies",
)

print(f"\nAgent Response: {response.content}")
bash  theme={null}
    pip install -U agno openai
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch access_dependencies_in_tool.py
    bash Mac theme={null}
      python access_dependencies_in_tool.py
      bash Windows theme={null}
      python access_dependencies_in_tool.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/dependencies" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## memory_manager.clear()

**URL:** llms-txt#memory_manager.clear()

---

## Create an Creative AI Artist Agent

**URL:** llms-txt#create-an-creative-ai-artist-agent

image_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DalleTools()],
    description=dedent("""\
        You are an experienced AI artist with expertise in various artistic styles,
        from photorealism to abstract art. You have a deep understanding of composition,
        color theory, and visual storytelling.\
    """),
    instructions=dedent("""\
        As an AI artist, follow these guidelines:
        1. Analyze the user's request carefully to understand the desired style and mood
        2. Before generating, enhance the prompt with artistic details like lighting, perspective, and atmosphere
        3. Use the `create_image` tool with detailed, well-crafted prompts
        4. Provide a brief explanation of the artistic choices made
        5. If the request is unclear, ask for clarification about style preferences

Always aim to create visually striking and meaningful images that capture the user's vision!\
    """),
    markdown=True,
    db=SqliteDb(session_table="test_agent", db_file="tmp/test.db"),
)

---

## Create a team with these agents

**URL:** llms-txt#create-a-team-with-these-agents

content_team = Team(
    name="Content Team",
    members=[researcher, writer],
    instructions="You are a team of researchers and writers that work together to create high-quality content.",
    model=OpenAIChat(id="gpt-5-mini"),
    show_members_responses=True,
)

---

## Initialize the Agno agent with the new storage backend and a DuckDuckGo search tool.

**URL:** llms-txt#initialize-the-agno-agent-with-the-new-storage-backend-and-a-duckduckgo-search-tool.

agent1 = Agent(
    db=db,
    tools=[DuckDuckGoTools()],
    add_history_to_context=True,
    debug_mode=False,
)

---

## Streaming Agent

**URL:** llms-txt#streaming-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/vertexai/claude/basic_stream

```python cookbook/models/vertexai/claude/basic_stream.py theme={null}
from typing import Iterator  # noqa
from agno.agent import Agent, RunOutputEvent  # noqa
from agno.models.vertexai.claude import Claude

agent = Agent(model=Claude(id="claude-sonnet-4@20250514"), markdown=True)

---

## Create a knowledge base with the PPTX documents

**URL:** llms-txt#create-a-knowledge-base-with-the-pptx-documents

knowledge = Knowledge(
    # Table name: ai.pptx_documents
    vector_db=PgVector(
        table_name="pptx_documents",
        db_url=db_url,
    ),
)

---

## Agentic Chunking

**URL:** llms-txt#agentic-chunking

Source: https://docs.agno.com/reference/knowledge/chunking/agentic

Agentic chunking is an intelligent method of splitting documents into smaller chunks by using a model to determine natural breakpoints in the text.
Rather than splitting text at fixed character counts, it analyzes the content to find semantically meaningful boundaries like paragraph breaks and topic transitions.

<Snippet file="chunking-agentic.mdx" />

---

## Filter content during search

**URL:** llms-txt#filter-content-during-search

**Contents:**
- AgentOS Integration
  - Required Setup for AgentOS

results = knowledge.search(
    query="technical documentation",
    filters={"department": "engineering", "version": "2.1"}
)
python  theme={null}
from agno.os import AgentOS
from agno.db.postgres import PostgresDb
from agno.agent import Agent

**Examples:**

Example 1 (unknown):
```unknown
## AgentOS Integration

### Required Setup for AgentOS

When using AgentOS, ContentsDB is mandatory for the Knowledge management interface:
```

---

## Create an agent with the knowledge base

**URL:** llms-txt#create-an-agent-with-the-knowledge-base

**Contents:**
- Usage
- Params

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
)

if __name__ == "__main__":
    asyncio.run(
        knowledge.add_content_async(
            path="cookbook/knowledge/testing_resources/cv_1.pdf",
        )
    )
    # Create and use the agent
    asyncio.run(
        agent.aprint_response(
            "What skills does an applicant require to apply for the Software Engineer position?",
            markdown=True,
        )
    )
bash  theme={null}
    pip install -U pypdf sqlalchemy psycopg pgvector agno openai  
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Mac theme={null}
      python examples/concepts/knowledge/readers/pdf_reader_async.py
      bash Windows theme={null}
      python examples/concepts/knowledge/readers/pdf_reader_async.py
      ```
    </CodeGroup>
  </Step>
</Steps>

<Snippet file="pdf-reader-reference.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Get Memory Topics

**URL:** llms-txt#get-memory-topics

Source: https://docs.agno.com/reference-api/schema/memory/get-memory-topics

get /memory_topics
Retrieve all unique topics associated with memories in the system. Useful for filtering and categorizing memories by topic.

---

## Travel Agent

**URL:** llms-txt#travel-agent

Source: https://docs.agno.com/examples/use-cases/agents/travel-planner

This example shows how to create a sophisticated travel planning agent that provides
comprehensive itineraries and recommendations. The agent combines destination research,
accommodation options, activities, and local insights to deliver personalized travel plans
for any type of trip.

Example prompts to try:

* "Plan a 5-day cultural exploration trip to Kyoto for a family of 4"
* "Create a romantic weekend getaway in Paris with a \$2000 budget"
* "Organize a 7-day adventure trip to New Zealand for solo travel"
* "Design a tech company offsite in Barcelona for 20 people"
* "Plan a luxury honeymoon in Maldives for 10 days"

```python travel_planner.py theme={null}
from textwrap import dedent

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.exa import ExaTools

travel_agent = Agent(
    name="Globe Hopper",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[ExaTools()],
    markdown=True,
    description=dedent("""\
        You are Globe Hopper, an elite travel planning expert with decades of experience! 🌍

Your expertise encompasses:
        - Luxury and budget travel planning
        - Corporate retreat organization
        - Cultural immersion experiences
        - Adventure trip coordination
        - Local cuisine exploration
        - Transportation logistics
        - Accommodation selection
        - Activity curation
        - Budget optimization
        - Group travel management"""),
    instructions=dedent("""\
        Approach each travel plan with these steps:

1. Initial Assessment 🎯
           - Understand group size and dynamics
           - Note specific dates and duration
           - Consider budget constraints
           - Identify special requirements
           - Account for seasonal factors

2. Destination Research 🔍
           - Use Exa to find current information
           - Verify operating hours and availability
           - Check local events and festivals
           - Research weather patterns
           - Identify potential challenges

3. Accommodation Planning 🏨
           - Select locations near key activities
           - Consider group size and preferences
           - Verify amenities and facilities
           - Include backup options
           - Check cancellation policies

4. Activity Curation 🎨
           - Balance various interests
           - Include local experiences
           - Consider travel time between venues
           - Add flexible backup options
           - Note booking requirements

5. Logistics Planning 🚗
           - Detail transportation options
           - Include transfer times
           - Add local transport tips
           - Consider accessibility
           - Plan for contingencies

6. Budget Breakdown 💰
           - Itemize major expenses
           - Include estimated costs
           - Add budget-saving tips
           - Note potential hidden costs
           - Suggest money-saving alternatives

Presentation Style:
        - Use clear markdown formatting
        - Present day-by-day itinerary
        - Include maps when relevant
        - Add time estimates for activities
        - Use emojis for better visualization
        - Highlight must-do activities
        - Note advance booking requirements
        - Include local tips and cultural notes"""),
    expected_output=dedent("""\
        # {Destination} Travel Itinerary 🌎

## Overview
        - **Dates**: {dates}
        - **Group Size**: {size}
        - **Budget**: {budget}
        - **Trip Style**: {style}

## Accommodation 🏨
        {Detailed accommodation options with pros and cons}

### Day 1
        {Detailed schedule with times and activities}

### Day 2
        {Detailed schedule with times and activities}

[Continue for each day...]

## Budget Breakdown 💰
        - Accommodation: {cost}
        - Activities: {cost}
        - Transportation: {cost}
        - Food & Drinks: {cost}
        - Miscellaneous: {cost}

## Important Notes ℹ️
        {Key information and tips}

## Booking Requirements 📋
        {What needs to be booked in advance}

## Local Tips 🗺️
        {Insider advice and cultural notes}

---
        Created by Globe Hopper
        Last Updated: {current_time}"""),
    add_datetime_to_context=True,
    )

---

## Create a fresh agent with reasoning_model for streaming

**URL:** llms-txt#create-a-fresh-agent-with-reasoning_model-for-streaming

streaming_agent_with_model = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    reasoning_model=OpenAIChat(id="gpt-5-mini"),
    markdown=True,
)

---

## agent.print_response("Fetch the top 2 hackernews stories", stream=True)

**URL:** llms-txt#agent.print_response("fetch-the-top-2-hackernews-stories",-stream=true)

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai httpx rich
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch confirmation_required_stream.py
    bash Mac theme={null}
      python confirmation_required_stream.py
      bash Windows   theme={null}
      python confirmation_required_stream.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Prompt the agent to solve the problem

**URL:** llms-txt#prompt-the-agent-to-solve-the-problem

**Contents:**
- Usage

reasoning_agent.print_response("Is 9.11 bigger or 9.9?", stream=True)
bash  theme={null}
    export GROQ_API_KEY=xxx
    bash  theme={null}
    pip install -U groq agno
    bash Mac theme={null}
      python cookbook/models/groq/reasoning_agent.py
      bash Windows theme={null}
      python cookbook/models/groq/reasoning_agent.py
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

## Stock price analysis agent

**URL:** llms-txt#stock-price-analysis-agent

stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat("gpt-5-mini"),
    output_schema=StockAnalysis,
    role="Searches for stock price and analyst information",
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
    instructions=[
        "Provide detailed stock analysis with price information",
        "Include analyst recommendations when available",
    ],
)

---

## 1. Create memories by setting `enable_user_memories=True` in the Agent

**URL:** llms-txt#1.-create-memories-by-setting-`enable_user_memories=true`-in-the-agent

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
)
team = Team(
    model=OpenAIChat(id="gpt-5-mini"),
    members=[agent],
    db=db,
    enable_user_memories=True,
)

team.print_response(
    "My name is John Doe and I like to hike in the mountains on weekends.",
    stream=True,
    user_id=john_doe_id,
    session_id=session_id,
)

team.print_response(
    "What are my hobbies?", stream=True, user_id=john_doe_id, session_id=session_id
)

---

## Create agents with tools that use workflow session state

**URL:** llms-txt#create-agents-with-tools-that-use-workflow-session-state

shopping_assistant = Agent(
    name="Shopping Assistant",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[add_item, remove_item, list_items],
    instructions=[
        "You are a helpful shopping assistant.",
        "You can help users manage their shopping list by adding, removing, and listing items.",
        "Always use the provided tools to interact with the shopping list.",
        "Be friendly and helpful in your responses.",
    ],
)

list_manager = Agent(
    name="List Manager",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[list_items, remove_all_items],
    instructions=[
        "You are a list management specialist.",
        "You can view the current shopping list and clear it when needed.",
        "Always show the current list when asked.",
        "Confirm actions clearly to the user.",
    ],
)

---

## Create initial agent with expensive model

**URL:** llms-txt#create-initial-agent-with-expensive-model

expensive_agent = Agent(
    model=OpenAIChat(id="gpt-4o"),
    instructions="You are a helpful assistant for technical discussions.",
    db=db,
    add_history_to_context=True,
)

---

## Async Basic Agent

**URL:** llms-txt#async-basic-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/xai/basic_async

```python cookbook/models/xai/basic_async.py theme={null}
import asyncio

from agno.agent import Agent, RunOutput
from agno.models.xai import xAI

agent = Agent(model=xAI(id="grok-3"), markdown=True)

---

## ❌ Doesn't work as expected - automatic memory is disabled

**URL:** llms-txt#❌-doesn't-work-as-expected---automatic-memory-is-disabled

agent = Agent(
    db=db,
    enable_user_memories=True,
    enable_agentic_memory=True  # This disables automatic behavior
)

---

## Agent with Vertex AI

**URL:** llms-txt#agent-with-vertex-ai

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/gemini/vertexai

```python cookbook/models/google/gemini/vertexai.py theme={null}
"""
To use Vertex AI, with the Gemini Model class, you need to set the following environment variables:

export GOOGLE_GENAI_USE_VERTEXAI="true"
export GOOGLE_CLOUD_PROJECT="your-project-id"
export GOOGLE_CLOUD_LOCATION="your-location"

Or you can set the following parameters in the `Gemini` class:

gemini = Gemini(
    vertexai=True,
    project_id="your-google-cloud-project-id",
    location="your-google-cloud-location",
)
"""

from agno.agent import Agent, RunOutput  # noqa
from agno.models.google import Gemini

agent = Agent(model=Gemini(id="gemini-2.0-flash-001"), markdown=True)

---

## In-memory for testing

**URL:** llms-txt#in-memory-for-testing

**Contents:**
- Core Functionality
  - Contents DB Schema
  - Content Metadata Tracking

from agno.db.in_memory import InMemoryDb
contents_db = InMemoryDb()
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
## Core Functionality

### Contents DB Schema

If you have a Contents DB configured for your Knowledge, the content metadata will be stored in a contents table in your database.

The schema for the contents table is as follows:

| Field            | Type   | Description                                                                               |
| ---------------- | ------ | ----------------------------------------------------------------------------------------- |
| `id`             | `str`  | The unique identifier for the content.                                                    |
| `name`           | `str`  | The name of the content.                                                                  |
| `description`    | `str`  | The description of the content.                                                           |
| `metadata`       | `dict` | The metadata for the content.                                                             |
| `type`           | `str`  | The type of the content.                                                                  |
| `size`           | `int`  | The size of the content. Applicable only to files.                                        |
| `linked_to`      | `str`  | The ID of the content that this content is linked to.                                     |
| `access_count`   | `int`  | The number of times this content has been accessed.                                       |
| `status`         | `str`  | The status of the content.                                                                |
| `status_message` | `str`  | The message associated with the status of the content.                                    |
| `created_at`     | `int`  | The timestamp when the content was created.                                               |
| `updated_at`     | `int`  | The timestamp when the content was last updated.                                          |
| `external_id`    | `str`  | The external ID of the content. Used when external vector stores are used, like LightRAG. |

This data is best displayed on the [knowledge page of the AgentOS UI](https://os.agno.com/knowledge).

### Content Metadata Tracking
```

---

## Team with Nested Shared State

**URL:** llms-txt#team-with-nested-shared-state

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/state/team_with_nested_shared_state

This example demonstrates a hierarchical team structure with nested shared state management for complex multi-agent coordination in a shopping list and meal planning system.

```python cookbook/examples/teams/state/team_with_nested_shared_state.py theme={null}
"""
This example demonstrates the nested Team functionality in a hierarchical team structure.
Each team and agent has a clearly defined role that guides their behavior and specialization:

Team Hierarchy & Roles:
├── Shopping List Team (Orchestrator)
│   Role: "Orchestrate comprehensive shopping list management and meal planning"
│   ├── Shopping Management Team (Operations Specialist)
│   │   Role: "Execute precise shopping list operations through delegation"
│   │   └── Shopping List Agent
│   │       Role: "Maintain and modify the shopping list with precision and accuracy"
│   └── Meal Planning Team (Culinary Expert)
│       Role: "Transform shopping list ingredients into creative meal suggestions"
│       └── Recipe Suggester Agent
│           Role: "Create innovative and practical recipe suggestions"

from agno.agent.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team

db = SqliteDb(db_file="tmp/example.db")

---

## === Setup database and agent ===

**URL:** llms-txt#===-setup-database-and-agent-===

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

agent = Agent(
    id="demo-agent",
    name="Demo Agent",
    model=OpenAIChat(id="gpt-4o"),
    db=db,
    tools=[DuckDuckGoTools()],
    markdown=True,
)

agent_os = AgentOS(
    description="Essential middleware demo with rate limiting and logging",
    agents=[agent],
)

app = agent_os.get_app()

---

## Create AgentOS app

**URL:** llms-txt#create-agentos-app

**Contents:**
  - AgentOS Features Enabled by ContentsDB
- Next Steps

app = AgentOS(
    description="Example app for basic agent with knowledge capabilities",
    id="knowledge-demo",
    agents=[knowledge_agent],
)
```

### AgentOS Features Enabled by ContentsDB

With ContentsDB, the AgentOS Knowledge page provides:

* **Content Browser**: View all uploaded content with metadata
* **Upload Interface**: Add new content through the web UI
* **Status Monitoring**: Real-time processing status updates
* **Metadata Editor**: Update content metadata through forms
* **Content Management**: Delete or modify content entries
* **Search and Filtering**: Find content by metadata attributes
* **Bulk Operations**: Manage multiple content items at once

Check out the [AgentOS Knowledge](/agent-os/features/knowledge-management) page for more in-depth information.

<CardGroup cols={2}>
  <Card title="Vector Databases" icon="database" href="/concepts/vectordb/overview">
    Understand the embedding storage layer
  </Card>

<Card title="AgentOS" icon="server" href="/agent-os/introduction">
    Use your Knowledge in Agno AgentOS
  </Card>

<Card title="Database Setup" icon="wrench" href="/concepts/db/overview">
    Detailed database configuration guides
  </Card>

<Card title="Getting Started" icon="rocket" href="/concepts/knowledge/getting-started">
    Build your first knowledge-powered agent
  </Card>
</CardGroup>

---

## Run the Agent. This will store a memory in our "my_memory_table"

**URL:** llms-txt#run-the-agent.-this-will-store-a-memory-in-our-"my_memory_table"

agent.print_response("I love sushi!", user_id="123")

---

## Zep

**URL:** llms-txt#zep

**Contents:**
- Prerequisites
- Example

Source: https://docs.agno.com/concepts/tools/toolkits/database/zep

**ZepTools** enable an Agent to interact with a Zep memory system, providing capabilities to store, retrieve, and search memory data associated with user sessions.

The ZepTools require the `zep-cloud` Python package and a Zep API key.

The following example demonstrates how to create an agent with access to Zep memory:

```python cookbook/tools/zep_tools.py theme={null}
import time

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.zep import ZepTools

**Examples:**

Example 1 (unknown):
```unknown

```

Example 2 (unknown):
```unknown
## Example

The following example demonstrates how to create an agent with access to Zep memory:
```

---

## Simple async function to run an Agent.

**URL:** llms-txt#simple-async-function-to-run-an-agent.

async def arun_agent():
    agent = Agent(
        model=OpenAIChat(id="gpt-5-mini"),
        system_message="Be concise, reply with one sentence.",
    )
    response = await agent.arun("What is the capital of France?")
    return response

performance_eval = PerformanceEval(func=arun_agent, num_iterations=10)

---

## Couchbase Agent Knowledge

**URL:** llms-txt#couchbase-agent-knowledge

**Contents:**
- Setup
  - Local Setup (Docker)
  - Managed Setup (Capella)
  - Environment Variables
  - Install Dependencies
- Example

Source: https://docs.agno.com/concepts/vectordb/couchbase

### Local Setup (Docker)

Run Couchbase locally using Docker:

1. Access the Couchbase UI at: [http://localhost:8091](http://localhost:8091)
2. Login with username: `Administrator` and password: `password`
3. Create a bucket named `recipe_bucket`, a scope `recipe_scope`, and a collection `recipes`

### Managed Setup (Capella)

For a managed cluster, use [Couchbase Capella](https://cloud.couchbase.com/):

* Follow Capella's UI to create a database, bucket, scope, and collection

### Environment Variables

Set up your environment variables:

For Capella, set `COUCHBASE_CONNECTION_STRING` to your Capella connection string.

### Install Dependencies

```python agent_with_knowledge.py theme={null}
import os
import time
from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.couchbase import CouchbaseSearch
from couchbase.options import ClusterOptions, KnownConfigProfiles
from couchbase.auth import PasswordAuthenticator
from couchbase.management.search import SearchIndex

**Examples:**

Example 1 (unknown):
```unknown
1. Access the Couchbase UI at: [http://localhost:8091](http://localhost:8091)
2. Login with username: `Administrator` and password: `password`
3. Create a bucket named `recipe_bucket`, a scope `recipe_scope`, and a collection `recipes`

### Managed Setup (Capella)

For a managed cluster, use [Couchbase Capella](https://cloud.couchbase.com/):

* Follow Capella's UI to create a database, bucket, scope, and collection

### Environment Variables

Set up your environment variables:
```

Example 2 (unknown):
```unknown
For Capella, set `COUCHBASE_CONNECTION_STRING` to your Capella connection string.

### Install Dependencies
```

Example 3 (unknown):
```unknown
## Example
```

---

## Only use agentic memory when you specifically need:

**URL:** llms-txt#only-use-agentic-memory-when-you-specifically-need:

---

## Initialize the Agent

**URL:** llms-txt#initialize-the-agent

agent = Agent(
    model=OpenAIChat(),
    tools=[zep_tools],
    dependencies={"memory": zep_tools.get_zep_memory(memory_type="context")},
    add_dependencies_to_context=True,
)

---

## Image Editing Agent

**URL:** llms-txt#image-editing-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/gemini/image_editing

```python cookbook/models/google/gemini/image_editing.py theme={null}
from io import BytesIO

from agno.agent import Agent, RunOutput  # noqa
from agno.media import Image
from agno.models.google import Gemini
from PIL import Image as PILImage

---

## Memory with SQLite

**URL:** llms-txt#memory-with-sqlite

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/memory/db/mem-sqlite-memory

```python cookbook/memory/db/mem-sqlite-memory.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb

---

## Video to Shorts Agent

**URL:** llms-txt#video-to-shorts-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/multimodal/video-to-shorts

```python  theme={null}
import subprocess
import time
from pathlib import Path

from agno.agent import Agent
from agno.media import Video
from agno.models.google import Gemini
from agno.utils.log import logger
from google.generativeai import get_file, upload_file

video_path = Path(__file__).parent.joinpath("sample.mp4")
output_dir = Path("tmp/shorts")

agent = Agent(
    name="Video2Shorts",
    description="Process videos and generate engaging shorts.",
    model=Gemini(id="gemini-2.0-flash-exp"),
    markdown=True,
    debug_mode=True,
    instructions=[
        "Analyze the provided video directly—do NOT reference or analyze any external sources or YouTube videos.",
        "Identify engaging moments that meet the specified criteria for short-form content.",
        """Provide your analysis in a **table format** with these columns:
   - Start Time | End Time | Description | Importance Score""",
        "Ensure all timestamps use MM:SS format and importance scores range from 1-10. ",
        "Focus only on segments between 15 and 60 seconds long.",
        "Base your analysis solely on the provided video content.",
        "Deliver actionable insights to improve the identified segments for short-form optimization.",
    ],
)

---

## Please download a sample audio file to test this Agent and upload using:

**URL:** llms-txt#please-download-a-sample-audio-file-to-test-this-agent-and-upload-using:

**Contents:**
- Usage

audio_path = Path(__file__).parent.joinpath("sample.mp3")

agent.print_response(
    "Tell me about this audio",
    audio=[Audio(filepath=audio_path)],
    stream=True,
)
bash  theme={null}
    export GOOGLE_API_KEY=xxx
    bash  theme={null}
    pip install -U google-genai agno
    bash Mac theme={null}
      python cookbook/models/google/gemini/audio_input_local_file_upload.py
      bash Windows theme={null}
      python cookbook/models/google/gemini/audio_input_local_file_upload.py
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

## Initialize the A2A interface specifying the agents to expose

**URL:** llms-txt#initialize-the-a2a-interface-specifying-the-agents-to-expose

**Contents:**
- A2A API
- Developer Resources

a2a = A2A(agents=[agent])

agent_os = AgentOS(
    agents=[agent],
    interfaces=[a2a], # Pass the A2A interface to the AgentOS using the `interfaces` parameter
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(app="a2a-interface-initialization:app", reload=True)
```

Using the A2A interface, you can run your Agents, Teams and Workflows passing A2A compatible requests. You will also receive A2A compatible responses.

See the [A2A API reference](/reference-api/schema/a2a/stream-message) for more details.

## Developer Resources

* View [AgentOS Reference](/reference/agent-os/agent-os)
* View [A2A Documentation](https://a2a-protocol.org/latest/)
* View [Examples](/examples/agent-os/interfaces/a2a)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/agent_os/interfaces/a2a)

---

## Knowledge base with Infinity reranker for high performance

**URL:** llms-txt#knowledge-base-with-infinity-reranker-for-high-performance

knowledge_primary = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs_primary",
        search_type=SearchType.hybrid,
        embedder=CohereEmbedder(id="embed-v4.0"),
        reranker=InfinityReranker(
            base_url="http://localhost:7997/rerank", model="BAAI/bge-reranker-base"
        ),
    ),
)

---

## Scenario: User with 100 existing memories

**URL:** llms-txt#scenario:-user-with-100-existing-memories

agent = Agent(
    db=db,
    enable_agentic_memory=True,
    model=OpenAIChat(id="gpt-4o")
)

---

## Agent with Structured Output

**URL:** llms-txt#agent-with-structured-output

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/requesty/structured_output

```python cookbook/models/requesty/structured_output.py theme={null}
from typing import List

from agno.agent import Agent
from agno.models.requesty import Requesty
from pydantic import BaseModel, Field

class MovieScript(BaseModel):
    setting: str = Field(
        ..., description="Provide a nice setting for a blockbuster movie."
    )
    ending: str = Field(
        ...,
        description="Ending of the movie. If not available, provide a happy ending.",
    )
    genre: str = Field(
        ...,
        description="Genre of the movie. If not available, select action, thriller or romantic comedy.",
    )
    name: str = Field(..., description="Give a name to this movie")
    characters: List[str] = Field(..., description="Name of characters for this movie.")
    storyline: str = Field(
        ..., description="3 sentence storyline for the movie. Make it exciting!"
    )

---

## Agent with Tools

**URL:** llms-txt#agent-with-tools

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/vllm/tool_use

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install Libraries">
    
  </Step>

<Step title="Start vLLM server">
    
  </Step>

<Step title="Run Agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install Libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Start vLLM server">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
```

---

## Define specialized agents for meal planning conversation

**URL:** llms-txt#define-specialized-agents-for-meal-planning-conversation

meal_suggester = Agent(
    name="Meal Suggester",
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "You are a friendly meal planning assistant who suggests meal categories and cuisines.",
        "Consider the time of day, day of the week, and any context from the conversation.",
        "Keep suggestions broad (Italian, Asian, healthy, comfort food, quick meals, etc.)",
        "Ask follow-up questions to understand preferences better.",
    ],
)

recipe_specialist = Agent(
    name="Recipe Specialist",
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "You are a recipe expert who provides specific, detailed recipe recommendations.",
        "Pay close attention to the full conversation to understand user preferences and restrictions.",
        "If the user mentioned avoiding certain foods or wanting healthier options, respect that.",
        "Provide practical, easy-to-follow recipe suggestions with ingredients and basic steps.",
        "Reference the conversation naturally (e.g., 'Since you mentioned wanting something healthier...')",
    ],
)

def analyze_food_preferences(step_input: StepInput) -> StepOutput:
    """
    Smart function that analyzes conversation history to understand user food preferences
    """
    current_request = step_input.input
    conversation_context = step_input.previous_step_content or ""

# Simple preference analysis based on conversation
    preferences = {
        "dietary_restrictions": [],
        "cuisine_preferences": [],
        "avoid_list": [],
        "cooking_style": "any",
    }

# Analyze conversation for patterns
    full_context = f"{conversation_context} {current_request}".lower()

# Dietary restrictions and preferences
    if any(word in full_context for word in ["healthy", "healthier", "light", "fresh"]):
        preferences["dietary_restrictions"].append("healthy")
    if any(word in full_context for word in ["vegetarian", "veggie", "no meat"]):
        preferences["dietary_restrictions"].append("vegetarian")
    if any(word in full_context for word in ["quick", "fast", "easy", "simple"]):
        preferences["cooking_style"] = "quick"
    if any(word in full_context for word in ["comfort", "hearty", "filling"]):
        preferences["cooking_style"] = "comfort"

# Foods/cuisines to avoid (mentioned recently)
    if "italian" in full_context and (
        "had" in full_context or "yesterday" in full_context
    ):
        preferences["avoid_list"].append("Italian")
    if "chinese" in full_context and (
        "had" in full_context or "recently" in full_context
    ):
        preferences["avoid_list"].append("Chinese")

# Preferred cuisines mentioned positively
    if "love asian" in full_context or "like asian" in full_context:
        preferences["cuisine_preferences"].append("Asian")
    if "mediterranean" in full_context:
        preferences["cuisine_preferences"].append("Mediterranean")

# Create guidance for the recipe agent
    guidance = []
    if preferences["dietary_restrictions"]:
        guidance.append(
            f"Focus on {', '.join(preferences['dietary_restrictions'])} options"
        )
    if preferences["avoid_list"]:
        guidance.append(
            f"Avoid {', '.join(preferences['avoid_list'])} cuisine since user had it recently"
        )
    if preferences["cuisine_preferences"]:
        guidance.append(
            f"Consider {', '.join(preferences['cuisine_preferences'])} options"
        )
    if preferences["cooking_style"] != "any":
        guidance.append(f"Prefer {preferences['cooking_style']} cooking style")

analysis_result = f"""
        PREFERENCE ANALYSIS:
        Current Request: {current_request}

Detected Preferences:
        {chr(10).join(f"• {g}" for g in guidance) if guidance else "• No specific preferences detected"}

RECIPE AGENT GUIDANCE:
        Based on the conversation history, please provide recipe recommendations that align with these preferences.
        Reference the conversation naturally and explain why these recipes fit their needs.
    """.strip()

return StepOutput(content=analysis_result)

---

## MongoDB for Agent

**URL:** llms-txt#mongodb-for-agent

**Contents:**
- Usage
  - Run MongoDB

Source: https://docs.agno.com/examples/concepts/db/mongodb/mongodb_for_agent

Agno supports using MongoDB as a storage backend for Agents using the `MongoDb` class.

You need to provide either `db_url` or `client`. The following example uses `db_url`.

Install [docker desktop](https://docs.docker.com/desktop/install/mac-install/) and run **MongoDB** on port **27017** using:

```python mongodb_for_agent.py theme={null}
from agno.agent import Agent
from agno.db.mongo import MongoDb
from agno.tools.duckduckgo import DuckDuckGoTools

**Examples:**

Example 1 (unknown):
```unknown

```

---

## Tweet Analysis Agent

**URL:** llms-txt#tweet-analysis-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/use-cases/agents/tweet-analysis-agent

An agent that analyzes tweets and provides comprehensive brand monitoring and sentiment analysis.

* Real-time tweet analysis and sentiment classification
* Engagement metrics analysis (likes, retweets, replies)
* Brand health monitoring and competitive intelligence
* Strategic recommendations and response strategies

<Note> Check out the detailed [Social Media Agent](https://github.com/agno-agi/agno/tree/main/cookbook/examples/agents/social_media_agent.py). </Note>

* "Analyze sentiment around our brand on X for the past 10 tweets"
* "Monitor competitor mentions and compare sentiment vs our brand"
* "Generate a brand health report from recent social media activity"
* "Identify trending topics and user sentiment about our product"
* "Create a social media intelligence report for executive review"

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Set your X credentials">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run the agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
<Note> Check out the detailed [Social Media Agent](https://github.com/agno-agi/agno/tree/main/cookbook/examples/agents/social_media_agent.py). </Note>

More prompts to try:

* "Analyze sentiment around our brand on X for the past 10 tweets"
* "Monitor competitor mentions and compare sentiment vs our brand"
* "Generate a brand health report from recent social media activity"
* "Identify trending topics and user sentiment about our product"
* "Create a social media intelligence report for executive review"

## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set your API key">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set your X credentials">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Initialize Agent

**URL:** llms-txt#initialize-agent

**Contents:**
- Developer Resources

memory_agent = Agent(
    model=OpenAIChat(id="gpt-4.1"),
    db=db,
    # Give the Agent the ability to update memories
    enable_agentic_memory=True,
    # OR - Run the MemoryManager automatically after each response
    enable_user_memories=True,
    markdown=True,
)

memory_agent.print_response(
    "My name is Ava and I like to ski.",
    user_id=user_id,
    stream=True,
    stream_events=True,
)
print("Memories about Ava:")
pprint(memory_agent.get_user_memories(user_id=user_id))

memory_agent.print_response(
    "I live in san francisco, where should i move within a 4 hour drive?",
    user_id=user_id,
    stream=True,
    stream_events=True,
)
print("Memories about Ava:")
pprint(memory_agent.get_user_memories(user_id=user_id))
```

<Tip>
  `enable_agentic_memory=True` gives the Agent a tool to manage memories of the
  user, this tool passes the task to the `MemoryManager` class. You may also set
  `enable_user_memories=True` which always runs the `MemoryManager` after each
  user message.
</Tip>

<Note>
  Read more about Memory in the [Memory Overview](/concepts/memory/overview) page.
</Note>

## Developer Resources

* View the [Agent schema](/reference/agents/agent)
* View [Examples](/examples/concepts/memory)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/memory/)

---

## Notion MCP agent

**URL:** llms-txt#notion-mcp-agent

Source: https://docs.agno.com/examples/concepts/tools/mcp/notion

Using the [Notion MCP server](https://github.com/makenotion/notion-mcp-server) to create an Agent that can create, update and search for Notion pages:

---

## Primary knowledge base for main retrieval

**URL:** llms-txt#primary-knowledge-base-for-main-retrieval

primary_knowledge = Knowledge(
    vector_db=LanceDb(
        table_name="recipes_primary",
        uri="tmp/lancedb",
        search_type=SearchType.vector,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

---

## Setup the SQLite database with custom table names

**URL:** llms-txt#setup-the-sqlite-database-with-custom-table-names

db = SqliteDb(
    db_file="tmp/data.db",
    # Selecting which tables to use
    session_table="agent_sessions",
    memory_table="agent_memories",
    metrics_table="agent_metrics",
)

---

## ArXiv Reader Async

**URL:** llms-txt#arxiv-reader-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/arxiv/arxiv-reader-async

The **ArXiv Reader** with asynchronous processing allows you to search and read academic papers from the ArXiv preprint repository with better performance for concurrent operations.

```python examples/concepts/knowledge/readers/arxiv_reader_async.py theme={null}
import asyncio

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.arxiv_reader import ArxivReader
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    # Table name: ai.arxiv_documents
    vector_db=PgVector(
        table_name="arxiv_documents",
        db_url=db_url,
    ),
)

---

## Async Structured Output Agent

**URL:** llms-txt#async-structured-output-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/mistral/async_structured_output

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Stock price and analyst data agent

**URL:** llms-txt#stock-price-and-analyst-data-agent

stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Searches the web for information on a stock.",
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
)

---

## Async Basic Streaming Agent

**URL:** llms-txt#async-basic-streaming-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/perplexity/async_basic_stream

```python cookbook/models/perplexity/async_basic_stream.py theme={null}
import asyncio
from typing import Iterator  # noqa

from agno.agent import Agent, RunOutputEvent  # noqa
from agno.models.perplexity import Perplexity

agent = Agent(model=Perplexity(id="sonar"), markdown=True)

---

## Agent sessions stored in memory

**URL:** llms-txt#agent-sessions-stored-in-memory

**Contents:**
- Developer Resources

agent.print_response("Give me an easy dinner recipe")
```

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/db/in_memory/in_memory_storage_for_agent.py)

---

## Basic Slack Agent

**URL:** llms-txt#basic-slack-agent

**Contents:**
- Code
- Usage
- Key Features

Source: https://docs.agno.com/examples/agent-os/interfaces/slack/basic

Create a basic AI agent that integrates with Slack for conversations

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set Environment Variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

* **Slack Integration**: Responds to direct messages and channel mentions
* **Conversation History**: Maintains context with last 3 interactions
* **Persistent Memory**: SQLite database for session storage
* **DateTime Context**: Time-aware responses
* **GPT-4o Powered**: Intelligent conversational capabilities

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Research Team

**URL:** llms-txt#research-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/agent-os/interfaces/ag-ui/team

Multi-agent research team with specialized roles and web interface

```python cookbook/os/interfaces/agui/research_team.py theme={null}
from agno.agent.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os.app import AgentOS
from agno.os.interfaces.agui.agui import AGUI
from agno.team import Team

researcher = Agent(
    name="researcher",
    role="Research Assistant",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are a research assistant. Find information and provide detailed analysis.",
    markdown=True,
)

writer = Agent(
    name="writer",
    role="Content Writer", 
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You are a content writer. Create well-structured content based on research.",
    markdown=True,
)

research_team = Team(
    members=[researcher, writer],
    name="research_team",
    instructions="""
    You are a research team that helps users with research and content creation.
    First, use the researcher to gather information, then use the writer to create content.
    """,
    show_members_responses=True,
    get_member_information_tool=True,
    add_member_tools_to_context=True,
)

---

## Calculator agent

**URL:** llms-txt#calculator-agent

calculator_agent = Agent(
    name="Calculator Agent",
    model=Claude(id="claude-3-5-sonnet-latest"),
    role="Perform mathematical calculations",
    tools=[
        CalculatorTools()
    ],
    instructions=[
        "Perform accurate mathematical calculations.",
        "Show your work step by step.",
    ],
)

---

## Use an embedder in a knowledge base

**URL:** llms-txt#use-an-embedder-in-a-knowledge-base

knowledge = Knowledge(
    vector_db=PgVector(
        db_url="postgresql+psycopg://ai:ai@localhost:5532/ai",
        table_name="gemini_embeddings",
        embedder=GeminiEmbedder(),
    ),
    max_results=2,
)
```

For more details on configuring different model providers, check our [Embeddings documentation](/concepts/knowledge/embedder/)

---

## The Agent sessions and runs will now be stored in SQLite with custom table names

**URL:** llms-txt#the-agent-sessions-and-runs-will-now-be-stored-in-sqlite-with-custom-table-names

**Contents:**
- Developer Resources

agent.print_response("How many people live in Canada?")
agent.print_response("And in Mexico?")
agent.print_response("List my messages one by one")
```

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/db/examples/selecting_tables.py)

---

## Run the Agent, effectively creating and persisting a session

**URL:** llms-txt#run-the-agent,-effectively-creating-and-persisting-a-session

agent.print_response("What is the capital of France?", session_id="123")

---

## response = agent.run(

**URL:** llms-txt#response-=-agent.run(

---

## Define a function to run the agent, decorated with weave.op()

**URL:** llms-txt#define-a-function-to-run-the-agent,-decorated-with-weave.op()

@weave.op()
def run(content: str):
    return agent.run(content)

---

## Audio Input-Output Agent

**URL:** llms-txt#audio-input-output-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/getting-started/16-audio-agent

This example shows how to create an AI agent that can process audio input and generate audio responses. You can use this agent for various voice-based interactions, from analyzing speech content to generating natural-sounding responses.

Example audio interactions to try:

* Upload a recording of a conversation for analysis
* Have the agent respond to questions with voice output
* Process different languages and accents
* Analyze tone and emotion in speech

```python audio_input_output.py theme={null}
from textwrap import dedent

import requests
from agno.agent import Agent
from agno.media import Audio
from agno.models.openai import OpenAIChat
from agno.utils.audio import write_audio_to_file

---

## Create Knowledge Instance with ChromaDB

**URL:** llms-txt#create-knowledge-instance-with-chromadb

knowledge = Knowledge(
    name="Basic SDK Knowledge Base",
    description="Agno 2.0 Knowledge Implementation with ChromaDB",
    vector_db=ChromaDb(
        collection="vectors", path="tmp/chromadb", persistent_client=True
    ),
)

knowledge.add_content(
        name="Recipes",
        url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
        metadata={"doc_type": "recipe_book"},
    )

---

## Create agents with more specific validation criteria

**URL:** llms-txt#create-agents-with-more-specific-validation-criteria

data_validator = Agent(
    name="Data Validator",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "You are a data validator. Analyze the provided data and determine if it's valid.",
        "For data to be VALID, it must meet these criteria:",
        "- user_count: Must be a positive number (> 0)",
        "- revenue: Must be a positive number (> 0)",
        "- date: Must be in a reasonable date format (YYYY-MM-DD)",
        "",
        "Return exactly 'VALID' if all criteria are met.",
        "Return exactly 'INVALID' if any criteria fail.",
        "Also briefly explain your reasoning.",
    ],
)

data_processor = Agent(
    name="Data Processor",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="Process and transform the validated data.",
)

report_generator = Agent(
    name="Report Generator",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="Generate a final report from processed data.",
)

def early_exit_validator(step_input: StepInput) -> StepOutput:
    """
    Custom function that checks data quality and stops workflow early if invalid
    """
    # Get the validation result from previous step
    validation_result = step_input.previous_step_content or ""

if "INVALID" in validation_result.upper():
        return StepOutput(
            content="❌ Data validation failed. Workflow stopped early to prevent processing invalid data.",
            stop=True,  # Stop the entire workflow here
        )
    else:
        return StepOutput(
            content="✅ Data validation passed. Continuing with processing...",
            stop=False,  # Continue normally
        )

---

## Working with Memories

**URL:** llms-txt#working-with-memories

**Contents:**
- Customizing the Memory Manager

Source: https://docs.agno.com/concepts/memory/working-with-memories

Customize how memories are created, control context inclusion, share memories across agents, and use memory tools for advanced workflows.

The basic memory setup covers most use cases, but sometimes you need more control. This guide covers advanced patterns for customizing memory behavior, controlling what gets stored, and building complex multi-agent systems with shared memory.

## Customizing the Memory Manager

The `MemoryManager` controls which LLM creates and updates memories, plus how those memories are generated. You can customize it to use a specific model, add privacy rules, or change how memories are extracted:

```python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.memory import MemoryManager
from agno.models.openai import OpenAIChat

---

## PDF Reader Async

**URL:** llms-txt#pdf-reader-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/pdf/pdf-reader-async

The **PDF Reader** with asynchronous processing allows you to handle PDF files efficiently and integrate them with knowledge bases.

```python examples/concepts/knowledge/readers/pdf_reader_async.py theme={null}
import asyncio

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

---

## Setup the in-memory database

**URL:** llms-txt#setup-the-in-memory-database

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    name="Research Assistant",
)

team = Team(
    model=OpenAIChat(id="gpt-5-mini"),
    members=[agent],
    db=db,
    # Set add_history_to_context=true to add the previous chat history to the context sent to the Model.
    add_history_to_context=True,
    # Number of historical responses to add to the messages.
    num_history_runs=3,
    session_id="test_session",
)

---

## Create agent with TypedDict input schema

**URL:** llms-txt#create-agent-with-typeddict-input-schema

hackernews_agent = Agent(
    name="Hackernews Agent with TypedDict",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[HackerNewsTools()],
    role="Extract key insights and content from Hackernews posts",
    input_schema=ResearchTopicDict,
)

---

## Comment out after first run

**URL:** llms-txt#comment-out-after-first-run

**Contents:**
- Developer Resources

agent.knowledge.load(recreate=False)  # type: ignore

agent.print_response("How do I make pad thai?", markdown=True)
agent.print_response("What was my last question?", stream=True)
python async_clickhouse.py theme={null}
    import asyncio

from agno.agent import Agent
    from agno.knowledge.knowledge import Knowledge
    from agno.db.sqlite import SqliteDb
    from agno.vectordb.clickhouse import Clickhouse

agent = Agent(
        db=SqliteDb(db_file="agno.db"),
        knowledge=Knowledge(
            vector_db=Clickhouse(
                table_name="recipe_documents",
                host="localhost",
                port=8123,
                username="ai",
                password="ai",
            ),
        ),
        # Enable the agent to search the knowledge base
        search_knowledge=True,
        # Enable the agent to read the chat history
        read_chat_history=True,
    )

if __name__ == "__main__":
        # Comment out after first run
        asyncio.run(agent.knowledge.add_content_async(
            url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf"
          )
        )

# Create and use the agent
        asyncio.run(agent.aprint_response("How to make Tom Kha Gai", markdown=True))
    ```

<Tip className="mt-4">
      Use <code>aload()</code> and <code>aprint\_response()</code> methods with <code>asyncio.run()</code> for non-blocking operations in high-throughput applications.
    </Tip>
  </div>
</Card>

## Developer Resources

* View [Cookbook (Sync)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/clickhouse_db/clickhouse.py)
* View [Cookbook (Async)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/clickhouse_db/async_clickhouse.py)

**Examples:**

Example 1 (unknown):
```unknown
<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      Clickhouse also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>
```

---

## Asynchronous Agent with Image Input

**URL:** llms-txt#asynchronous-agent-with-image-input

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/meta/image_input_bytes

```python cookbook/models/meta/llama/image_input_bytes.py theme={null}
from pathlib import Path

from agno.agent import Agent
from agno.media import Image
from agno.models.meta import LlamaOpenAI
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.utils.media import download_image

agent = Agent(
    model=LlamaOpenAI(id="Llama-4-Maverick-17B-128E-Instruct-FP8"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

image_path = Path(__file__).parent.joinpath("sample.jpg")

download_image(
    url="https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg",
    output_path=str(image_path),
)

---

## Image Generation Agent

**URL:** llms-txt#image-generation-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/openai/responses/image_generation_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Get the FastAPI app for the AgentOS

**URL:** llms-txt#get-the-fastapi-app-for-the-agentos

**Contents:**
- Run your AgentOS
- Connect your AgentOS
- Chat with your Agent
- Pre-built API endpoints
- Next

app = agent_os.get_app()
bash Mac theme={null}
      uv venv --python 3.12
      source .venv/bin/activate
      bash Windows theme={null}
      uv venv --python 3.12
      .venv/Scripts/activate
      bash Mac theme={null}
      uv pip install -U agno anthropic mcp 'fastapi[standard]' sqlalchemy
      bash Windows theme={null}
      uv pip install -U agno anthropic mcp 'fastapi[standard]' sqlalchemy
      bash Mac theme={null}
      export ANTHROPIC_API_KEY=sk-***
      bash Windows theme={null}
      setx ANTHROPIC_API_KEY sk-***
      shell  theme={null}
    fastapi dev agno_agent.py
    ```

This will start your AgentOS on `http://localhost:8000`
  </Step>
</Steps>

## Connect your AgentOS

Agno provides a web interface that connects to your AgentOS, use it to monitor, manage and test your agentic system. Open [os.agno.com](https://os.agno.com) and sign in to your account.

1. Click on **"Add new OS"** in the top navigation bar.
2. Select **"Local"** to connect to a local AgentOS running on your machine.
3. Enter the endpoint URL of your AgentOS. The default is `http://localhost:8000`.
4. Give your AgentOS a descriptive name like "Development OS" or "Local 8000".
5. Click **"Connect"**.

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/aEfJPs-hg36UsUPO/videos/agent-os-connect-1.mp4?fit=max&auto=format&n=aEfJPs-hg36UsUPO&q=85&s=907888debf7f055f14e0f84405ba5749" type="video/mp4" data-path="videos/agent-os-connect-1.mp4" />
  </video>
</Frame>

Once connected, you'll see your new OS with a live status indicator.

## Chat with your Agent

Next, let's chat with our Agent, go to the `Chat` section in the sidebar and select your Agent.

* Ask “What is Agno?” and the Agent will answer using the Agno MCP server.
* Agents keep their own history, tools, and instructions; switching users won’t mix context.

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/aEfJPs-hg36UsUPO/videos/agno-agent-chat.mp4?fit=max&auto=format&n=aEfJPs-hg36UsUPO&q=85&s=b8ac56bfb2e9436799299fcafa746d4a" type="video/mp4" data-path="videos/agno-agent-chat.mp4" />
  </video>
</Frame>

<Tip>
  Click on Sessions to view your Agent's conversations. This data is stored in your Agent's database, so no need for external tracing services.
</Tip>

## Pre-built API endpoints

The FastAPI app generated by your AgentOS comes with pre-built SSE-compatible API endpoints that you can use to build your product. You can always add your own routes, middleware or any other FastAPI feature, but this is such a great starting point.

Checkout the API endpoints at `/docs` of your AgentOS url, e.g. [http://localhost:8000/docs](http://localhost:8000/docs)

After running your AgentOS, dive into [core concepts](/concepts/agents/overview) and extend your Agents with more capabilities.

**Examples:**

Example 1 (unknown):
```unknown
<Check>
  There is an incredible amount of alpha in these 25 lines of code.

  You get a fully functional Agent with memory and state that can access any MCP server. It's served via a FastAPI app with pre-built endpoints that you can use to build your product.
</Check>

## Run your AgentOS

The AgentOS gives us a FastAPI application with ready-to-use API endpoints for serving, monitoring and managing our Agents. Let's run it.

<Steps>
  <Step title="Setup your virtual environment">
    <CodeGroup>
```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Install dependencies">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Cassandra Agent Knowledge

**URL:** llms-txt#cassandra-agent-knowledge

**Contents:**
- Setup
- Example

Source: https://docs.agno.com/concepts/vectordb/cassandra

Install cassandra packages

```python agent_with_knowledge.py theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.cassandra import Cassandra
from agno.knowledge.embedder.mistral import MistralEmbedder
from agno.models.mistral import MistralChat
from cassandra.cluster import Cluster

**Examples:**

Example 1 (unknown):
```unknown
Run cassandra
```

Example 2 (unknown):
```unknown
## Example
```

---

## Memory with Redis

**URL:** llms-txt#memory-with-redis

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/memory/db/mem-redis-memory

```python cookbook/memory/db/mem-redis-memory.py theme={null}
from agno.agent import Agent
from agno.db.redis import RedisDb

---

## Content Analyzer Agent - Specialized in analyzing retrieved content

**URL:** llms-txt#content-analyzer-agent---specialized-in-analyzing-retrieved-content

content_analyzer = Agent(
    name="Content Analyzer",
    model=Claude(id="claude-3-7-sonnet-latest"),
    role="Analyze and extract key insights from retrieved content",
    instructions=[
        "Analyze the content provided by the Knowledge Searcher.",
        "Extract key concepts, relationships, and important details.",
        "Identify gaps or areas needing additional clarification.",
        "Organize information logically for synthesis.",
    ],
    markdown=True,
)

---

## Run agent and return the response as a stream

**URL:** llms-txt#run-agent-and-return-the-response-as-a-stream

**Contents:**
  - Streaming all events

stream: Iterator[RunOutputEvent] = agent.run("Trending products", stream=True)
for chunk in stream:
    if chunk.event == RunEvent.run_content:
        print(chunk.content)
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
<Tip>
  For asynchronous streaming, see this [example](/examples/concepts/agent/async/streaming).
</Tip>

### Streaming all events

By default, when you stream a response, only the `RunContent` events will be streamed.

You can also stream all run events by setting `stream_events=True`.

This will provide real-time updates about the agent's internal processes, like tool calling or reasoning:

. For example:
```

---

## Step 2: Create your Agno agent

**URL:** llms-txt#step-2:-create-your-agno-agent

agent = Agent(
    name="Market Analysis Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    instructions="Provide professional market analysis with data-driven insights.",
    debug_mode=True,
)

---

## Live Search Agent

**URL:** llms-txt#live-search-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/xai/live_search_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## CSV URL Reader

**URL:** llms-txt#csv-url-reader

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/csv/csv-url-reader

The **CSV URL Reader** processes CSV files directly from URLs, allowing you to create knowledge bases from remote CSV data sources.

```python examples/concepts/knowledge/readers/csv_reader_url_async.py theme={null}
import asyncio

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

knowledge = Knowledge(
    # Table name: ai.csv_documents
    vector_db=PgVector(
        table_name="csv_documents",
        db_url=db_url,
    ),
)

---

## AgentOS Security

**URL:** llms-txt#agentos-security

**Contents:**
- Overview
- Generate a Security Key
- Security Key Authentication
  - macOS / Linux (bash or zsh)
  - Docker Compose
  - Key Rotation
  - Security Best Practices
  - Troubleshooting
- JWT Authentication

Source: https://docs.agno.com/agent-os/security

Learn how to secure your AgentOS instance with a security key

AgentOS supports bearer-token authentication to secure your instance. When a Security Key is configured, all API routes require an `Authorization: Bearer <token>` header for access. Without a key configured, authentication is disabled.

<Tip>
  You can generate a security key from the AgentOS Control Plane, which also enables secure communication between your AgentOS and the Control Plane.
</Tip>

## Generate a Security Key

From the AgentOS control plane, generate a security key or set your own.

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/xm93WWN8gg4nzCGE/videos/agentos-security-key.mp4?fit=max&auto=format&n=xm93WWN8gg4nzCGE&q=85&s=0a87c2a894982a3eb075fe282a21c491" type="video/mp4" data-path="videos/agentos-security-key.mp4" />
  </video>
</Frame>

<Tip>
  You can also create your own security key and set it on the AgentOS UI.
</Tip>

## Security Key Authentication

Set the `OS_SECURITY_KEY` environment variable where your AgentOS server runs. When present, the server automatically enforces bearer authentication on all API routes.

### macOS / Linux (bash or zsh)

<Note>
  **How it works**: AgentOS reads `OS_SECURITY_KEY` into the AgentOS router's
  internal authorization logic. If configured, requests without a valid
  `Authorization: Bearer` header return `401 Unauthorized`.
</Note>

1. In the UI, click the **Generate** icon next to "Security Key" to generate a new value
2. Update the server's `OS_SECURITY_KEY` environment variable and reload/redeploy AgentOS
3. Update all clients, workers, and CI/CD systems that call the AgentOS API

### Security Best Practices

* **Environment Isolation**: Use different keys per environment with least-privilege distribution
* **Code Safety**: Never commit keys to version control or print them in logs

* **401 Unauthorized**: Verify the header format is exactly `Authorization: Bearer <key>` and that the server has `OS_SECURITY_KEY` configured
* **Local vs Production**: Confirm your local shell exported `OS_SECURITY_KEY` before starting the application
* **Post-Rotation Failures**: Ensure all clients received the new key. Restart CI/CD runners that may cache environment variables
* **Connection Issues**: Check that your AgentOS instance is running and accessible at the configured endpoint

## JWT Authentication

AgentOS provides a middleware solution for custom JWT authentication.

Learn more about [JWT Middleware](/agent-os/customize/middleware/jwt)

<Check>
  Although the JWT Middleware is already powerful feature, Agno is working on further extending authentication capabilities and better role-based access control in AgentOS.
</Check>

**Examples:**

Example 1 (unknown):
```unknown
### Docker Compose
```

---

## Agent that can search the web for information

**URL:** llms-txt#agent-that-can-search-the-web-for-information

web_agent = Agent(
    name="Web Agent",
    role="Search the web for information",
    model=Claude(id="claude-3-5-sonnet-latest"),
    tools=[DuckDuckGoTools(cache_results=True)],
    instructions=["Always include sources"],
)

reddit_researcher = Agent(
    name="Reddit Researcher",
    role="Research a topic on Reddit",
    model=Claude(id="claude-3-5-sonnet-latest"),
    tools=[DuckDuckGoTools(cache_results=True)],
    add_name_to_context=True,
    instructions=dedent("""
    You are a Reddit researcher.
    You will be given a topic to research on Reddit.
    You will need to find the most relevant information on Reddit.
    """),
)

---

## agent.print_response("Send an email please")

**URL:** llms-txt#agent.print_response("send-an-email-please")

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch user_input_required_all_fields.py
    bash Mac theme={null}
      python user_input_required_all_fields.py
      bash Windows   theme={null}
      python user_input_required_all_fields.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Data Validator Agent - Specialized in data quality validation

**URL:** llms-txt#data-validator-agent---specialized-in-data-quality-validation

data_validator = Agent(
    name="Data Validator",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Validate retrieved data quality and relevance",
    instructions=[
        "Assess the quality and relevance of retrieved information.",
        "Check for consistency across different search results.",
        "Identify the most reliable and accurate information.",
        "Filter out any irrelevant or low-quality content.",
        "Ensure data integrity and relevance to the user's query.",
    ],
    markdown=True,
)

---

## Create agent with a specific reasoning_model

**URL:** llms-txt#create-agent-with-a-specific-reasoning_model

agent_with_reasoning_model = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    reasoning_model=OpenAIChat(id="gpt-5-mini"),  # Should default to manual COT
    markdown=True,
)

---

## Image Agent with File Upload

**URL:** llms-txt#image-agent-with-file-upload

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/gemini/image_input_file_upload

```python cookbook/models/google/gemini/image_input_file_upload.py theme={null}
from pathlib import Path

from agno.agent import Agent
from agno.media import Image
from agno.models.google import Gemini
from agno.tools.duckduckgo import DuckDuckGoTools
from google.generativeai import upload_file
from google.generativeai.types import file_types

agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

---

## Get the stored Agent session, to check the response citations

**URL:** llms-txt#get-the-stored-agent-session,-to-check-the-response-citations

**Contents:**
- Usage

session = agent.get_session()
if session and session.runs and session.runs[-1].citations:
    print("Citations:")
    print(session.runs[-1].citations)

bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    pip install -U openai agno
    bash Mac theme={null}
      python cookbook/models/openai/responses/pdf_input_url.py
      bash Windows theme={null}
      python cookbook/models/openai/responses/pdf_input_url.py
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

## Team with Knowledge Filters

**URL:** llms-txt#team-with-knowledge-filters

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/knowledge/team_with_knowledge_filters

This example demonstrates how to use knowledge filters with teams to restrict knowledge searches to specific documents or metadata criteria, enabling personalized and contextual responses based on predefined filter conditions.

```python cookbook/examples/teams/knowledge/02_team_with_knowledge_filters.py theme={null}
"""
This example demonstrates how to use knowledge filters with teams.

Knowledge filters allow you to restrict knowledge searches to specific documents
or metadata criteria, enabling personalized and contextual responses.
"""

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.lancedb import LanceDb

---

## Employee Recruiter

**URL:** llms-txt#employee-recruiter

Source: https://docs.agno.com/examples/use-cases/workflows/employee-recruiter

This example demonstrates how to migrate from the similar workflows 1.0 example to workflows 2.0 structure.

Employee Recruitment Workflow with Simulated Tools

This workflow automates the complete employee recruitment process from resume screening
to interview scheduling and email communication. It demonstrates a multi-agent system
working together to handle different aspects of the hiring pipeline.

1. **Resume Screening**: Analyzes candidate resumes against job requirements and scores them
2. **Interview Scheduling**: Schedules interviews for qualified candidates (score >= 5.0)
3. **Email Communication**: Sends professional interview invitation emails

* **Multi-Agent Architecture**: Uses specialized agents for screening, scheduling, and email writing
* **Async Streaming**: Provides real-time feedback during execution
* **Simulated Tools**: Uses mock Zoom scheduling and email sending for demonstration
* **Resume Processing**: Extracts text from PDF resumes via URLs
* **Structured Responses**: Uses Pydantic models for type-safe data handling
* **Session State**: Caches resume content to avoid re-processing

* **Screening Agent**: Evaluates candidates and provides scores/feedback
* **Scheduler Agent**: Creates interview appointments with realistic time slots
* **Email Writer Agent**: Composes professional interview invitation emails
* **Email Sender Agent**: Handles email delivery (simulated)

Usage:
python employee\_recruiter\_async\_stream.py

* message: Instructions for the recruitment process
* candidate\_resume\_urls: List of PDF resume URLs to process
* job\_description: The job posting requirements and details

* Streaming updates on each phase of the recruitment process
* Candidate screening results with scores and feedback
* Interview scheduling confirmations
* Email delivery confirmations

Note: This workflow uses simulated tools for Zoom scheduling and email sending
to demonstrate the concept, you can use the real tools in practice.

Run `pip install openai agno pypdf` to install dependencies.

```python employee_recruiter_async_stream.py theme={null}

import asyncio
import io
import random
from datetime import datetime, timedelta
from typing import Any, List

import requests
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.workflow.types import WorkflowExecutionInput
from agno.workflow.workflow import Workflow
from pydantic import BaseModel
from pypdf import PdfReader

---

## Legal Consultant

**URL:** llms-txt#legal-consultant

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/use-cases/agents/legal_consultant

This example demonstrates how to create a specialized AI agent that provides legal information and guidance based on a knowledge base of legal documents. The Legal Consultant agent is designed to help users understand legal concepts, consequences, and procedures by leveraging a vector database of legal content.

* **Legal Knowledge Base**: Integrates with a PostgreSQL vector database containing legal documents and resources
* **Document Processing**: Automatically ingests and indexes legal PDFs from authoritative sources (e.g., Department of Justice manuals)
* **Contextual Responses**: Provides relevant legal information with proper citations and sources
* **Professional Disclaimers**: Always clarifies that responses are for informational purposes only, not professional legal advice
* **Attorney Referrals**: Recommends consulting licensed attorneys for specific legal situations

* Legal research and education
* Understanding criminal penalties and consequences
* Learning about legal procedures and requirements
* Getting preliminary legal information before consulting professionals

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Filtering on Pinecone

**URL:** llms-txt#filtering-on-pinecone

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/vector-dbs/filtering_pinecone

Learn how to filter knowledge base searches using Pdf documents with user-specific metadata in Pinecone.

```python  theme={null}
from os import getenv

from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.pineconedb import PineconeDb

---

## --- Agents ---

**URL:** llms-txt#----agents----

research_agent = Agent(
    name="Blog Research Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[GoogleSearchTools()],
    description=dedent("""\
    You are BlogResearch-X, an elite research assistant specializing in discovering
    high-quality sources for compelling blog content. Your expertise includes:

- Finding authoritative and trending sources
    - Evaluating content credibility and relevance
    - Identifying diverse perspectives and expert opinions
    - Discovering unique angles and insights
    - Ensuring comprehensive topic coverage
    """),
    instructions=dedent("""\
    1. Search Strategy 🔍
       - Find 10-15 relevant sources and select the 5-7 best ones
       - Prioritize recent, authoritative content
       - Look for unique angles and expert insights
    2. Source Evaluation 📊
       - Verify source credibility and expertise
       - Check publication dates for timeliness
       - Assess content depth and uniqueness
    3. Diversity of Perspectives 🌐
       - Include different viewpoints
       - Gather both mainstream and expert opinions
       - Find supporting data and statistics
    """),
    output_schema=SearchResults,
)

content_scraper_agent = Agent(
    name="Content Scraper Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[Newspaper4kTools()],
    description=dedent("""\
    You are ContentBot-X, a specialist in extracting and processing digital content
    for blog creation. Your expertise includes:

- Efficient content extraction
    - Smart formatting and structuring
    - Key information identification
    - Quote and statistic preservation
    - Maintaining source attribution
    """),
    instructions=dedent("""\
    1. Content Extraction 📑
       - Extract content from the article
       - Preserve important quotes and statistics
       - Maintain proper attribution
       - Handle paywalls gracefully
    2. Content Processing 🔄
       - Format text in clean markdown
       - Preserve key information
       - Structure content logically
    3. Quality Control ✅
       - Verify content relevance
       - Ensure accurate extraction
       - Maintain readability
    """),
    output_schema=ScrapedArticle,
)

blog_writer_agent = Agent(
    name="Blog Writer Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    description=dedent("""\
    You are BlogMaster-X, an elite content creator combining journalistic excellence
    with digital marketing expertise. Your strengths include:

- Crafting viral-worthy headlines
    - Writing engaging introductions
    - Structuring content for digital consumption
    - Incorporating research seamlessly
    - Optimizing for SEO while maintaining quality
    - Creating shareable conclusions
    """),
    instructions=dedent("""\
    1. Content Strategy 📝
       - Craft attention-grabbing headlines
       - Write compelling introductions
       - Structure content for engagement
       - Include relevant subheadings
    2. Writing Excellence ✍️
       - Balance expertise with accessibility
       - Use clear, engaging language
       - Include relevant examples
       - Incorporate statistics naturally
    3. Source Integration 🔍
       - Cite sources properly
       - Include expert quotes
       - Maintain factual accuracy
    4. Digital Optimization 💻
       - Structure for scanability
       - Include shareable takeaways
       - Optimize for SEO
       - Add engaging subheadings

Format your blog post with this structure:
    # {Viral-Worthy Headline}

## Introduction
    {Engaging hook and context}

## {Compelling Section 1}
    {Key insights and analysis}
    {Expert quotes and statistics}

## {Engaging Section 2}
    {Deeper exploration}
    {Real-world examples}

## {Practical Section 3}
    {Actionable insights}
    {Expert recommendations}

## Key Takeaways
    - {Shareable insight 1}
    - {Practical takeaway 2}
    - {Notable finding 3}

## Sources
    {Properly attributed sources with links}
    """),
    markdown=True,
)

---

## Run the Agent. This will store a session in our "my_memory_table"

**URL:** llms-txt#run-the-agent.-this-will-store-a-session-in-our-"my_memory_table"

**Contents:**
  - Manual Memory Retrieval

agent.print_response("Hi! My name is John Doe and I like to play basketball on the weekends.")

agent.print_response("What are my hobbies?")
python  theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb

**Examples:**

Example 1 (unknown):
```unknown
### Manual Memory Retrieval

While memories are automatically recalled during conversations, you can also manually retrieve them using the `get_user_memories` method. This is useful for debugging, displaying user profiles, or building custom memory interfaces:
```

---

## Create agent with KnowledgeTools

**URL:** llms-txt#create-agent-with-knowledgetools

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[
        KnowledgeTools(
            knowledge=agno_docs,
            think=True,
            search=True,
            analyze=True,
            add_instructions=True,
        )
    ],
    instructions=dedent("""\
        You are an expert problem-solving assistant with strong analytical skills! 🧠
        Use the knowledge tools to organize your thoughts, search for information,
        and analyze results step-by-step.
        \
    """),
    markdown=True,
)

---

## Pinecone Agent Knowledge

**URL:** llms-txt#pinecone-agent-knowledge

**Contents:**
- Setup
- Example
- PineconeDb Params
- Developer Resources

Source: https://docs.agno.com/concepts/vectordb/pinecone

Follow the instructions in the [Pinecone Setup Guide](https://docs.pinecone.io/guides/get-started/quickstart) to get started quickly with Pinecone.

<Info>
  We do not yet support Pinecone v6.x.x. We are actively working to achieve
  compatibility. In the meantime, we recommend using **Pinecone v5.4.2** for the
  best experience.
</Info>

<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      Pinecone also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>

<Tip className="mt-4">
      Use <code>aload()</code> and <code>aprint\_response()</code> methods with <code>asyncio.run()</code> for non-blocking operations in high-throughput applications.
    </Tip>
  </div>
</Card>

<Snippet file="vectordb_pineconedb_params.mdx" />

## Developer Resources

* View [Cookbook (Sync)](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/vector_db/pinecone_db/pinecone_db.py)

**Examples:**

Example 1 (unknown):
```unknown
<Info>
  We do not yet support Pinecone v6.x.x. We are actively working to achieve
  compatibility. In the meantime, we recommend using **Pinecone v5.4.2** for the
  best experience.
</Info>

## Example
```

Example 2 (unknown):
```unknown
<Card title="Async Support ⚡">
  <div className="mt-2">
    <p>
      Pinecone also supports asynchronous operations, enabling concurrency and leading to better performance.
    </p>
```

---

## Setup your Agents with the same database and Memory enabled

**URL:** llms-txt#setup-your-agents-with-the-same-database-and-memory-enabled

agent_1 = Agent(db=db, enable_user_memories=True)
agent_2 = Agent(db=db, enable_user_memories=True)

---

## Secondary knowledge base for context expansion

**URL:** llms-txt#secondary-knowledge-base-for-context-expansion

context_knowledge = Knowledge(
    vector_db=LanceDb(
        table_name="recipes_context",
        uri="tmp/lancedb",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

---

## Agentic RAG with LanceDB

**URL:** llms-txt#agentic-rag-with-lancedb

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/knowledge/rag/agentic-rag-lancedb

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## - User-directed memory commands ("forget my address")

**URL:** llms-txt#--user-directed-memory-commands-("forget-my-address")

---

## Financial Analysis Agent

**URL:** llms-txt#financial-analysis-agent

finance_agent = Agent(
    name="Financial Analyst",
    model=LangDB(id="xai/grok-4"),
    tools=[YFinanceTools(stock_price=True, company_info=True)],
    instructions="Perform quantitative financial analysis"
)

---

## Agent with Input Schema

**URL:** llms-txt#agent-with-input-schema

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/input_schema_on_agent

This example demonstrates how to define an input schema for an agent using Pydantic models, ensuring structured input validation.

```python input_schema_on_agent.py theme={null}
from typing import List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.hackernews import HackerNewsTools
from pydantic import BaseModel, Field

class ResearchTopic(BaseModel):
    """Structured research topic with specific requirements"""

topic: str
    focus_areas: List[str] = Field(description="Specific areas to focus on")
    target_audience: str = Field(description="Who this research is for")
    sources_required: int = Field(description="Number of sources needed", default=5)

---

## Create specialized research agents

**URL:** llms-txt#create-specialized-research-agents

tech_researcher = Agent(
    name="Alex",
    role="Technology Researcher",
    instructions=dedent("""
        You specialize in technology and AI research.
        - Focus on latest developments, trends, and breakthroughs
        - Provide concise, data-driven insights
        - Cite your sources
    """).strip(),
)

business_analyst = Agent(
    name="Sarah",
    role="Business Analyst",
    instructions=dedent("""
        You specialize in business and market analysis.
        - Focus on companies, markets, and economic trends
        - Provide actionable business insights
        - Include relevant data and statistics
    """).strip(),
)

---

## Create team with knowledge filters

**URL:** llms-txt#create-team-with-knowledge-filters

team_with_knowledge = Team(
    name="Team with Knowledge",
    members=[
        web_agent
    ],  # If you omit the member, the leader will search the knowledge base itself.
    model=OpenAIChat(id="gpt-5-mini"),
    knowledge=knowledge_base,
    show_members_responses=True,
    markdown=True,
    knowledge_filters={
        "user_id": "jordan_mitchell"
    },  # Filter to specific user's documents
)

---

## Stagehand MCP agent

**URL:** llms-txt#stagehand-mcp-agent

**Contents:**
- Key Features
- Prerequisites
- Setup Instructions
  - 1. Clone and Build Stagehand MCP Server

Source: https://docs.agno.com/examples/concepts/tools/mcp/stagehand

A web scraping agent that uses the Stagehand MCP server to automate browser interactions and create a structured content digest from Hacker News.

* **Safe Navigation**: Proper initialization sequence prevents common browser automation errors
* **Structured Data Extraction**: Methodical approach to extracting and organizing web content
* **Flexible Output**: Creates well-structured digests with headlines, summaries, and insights

Before running this example, you'll need:

* **Browserbase Account**: Get API credentials from [Browserbase](https://browserbase.com)
* **OpenAI API Key**: Get an API Key from [OpenAI](https://platform.openai.com/settings/organization/api-keys)

## Setup Instructions

### 1. Clone and Build Stagehand MCP Server

```bash  theme={null}
git clone https://github.com/browserbase/mcp-server-browserbase

---

## Final reasoning step using reasoning agent

**URL:** llms-txt#final-reasoning-step-using-reasoning-agent

reasoning_step = Step(
    name="final_reasoning",
    agent=reasoning_agent,
    description="Apply reasoning to create final insights and recommendations",
)

workflow = Workflow(
    name="Enhanced Research Workflow",
    description="Multi-source research with custom data flow and reasoning",
    steps=[
        research_hackernews,
        research_web,
        comprehensive_report_step,  # Has access to both previous steps
        reasoning_step,  # Gets the last step output (comprehensive report)
    ],
)

if __name__ == "__main__":
    workflow.print_response(
        "Latest developments in artificial intelligence and machine learning",
        stream=True,
        stream_events=True,
    )
```

---

## Team with Custom Tools

**URL:** llms-txt#team-with-custom-tools

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/tools/team_with_custom_tools

This example demonstrates how to create a team with custom tools, using custom tools alongside agent tools to answer questions from a knowledge base and fall back to web search when needed.

```python cookbook/examples/teams/tools/01_team_with_custom_tools.py theme={null}
"""
This example demonstrates how to create a team with custom tools.

The team uses custom tools alongside agent tools to answer questions from a knowledge base
and fall back to web search when needed.
"""

from agno.agent import Agent
from agno.team.team import Team
from agno.tools import tool
from agno.tools.duckduckgo import DuckDuckGoTools

@tool()
def answer_from_known_questions(question: str) -> str:
    """Answer a question from a list of known questions

Args:
        question: The question to answer

Returns:
        The answer to the question
    """

# FAQ knowledge base
    faq = {
        "What is the capital of France?": "Paris",
        "What is the capital of Germany?": "Berlin",
        "What is the capital of Italy?": "Rome",
        "What is the capital of Spain?": "Madrid",
        "What is the capital of Portugal?": "Lisbon",
        "What is the capital of Greece?": "Athens",
        "What is the capital of Turkey?": "Ankara",
    }

# Check if question is in FAQ
    if question in faq:
        return f"From my knowledge base: {faq[question]}"
    else:
        return "I don't have that information in my knowledge base. Try asking the web search agent."

---

## The first Agent will create a Memory about the user name here:

**URL:** llms-txt#the-first-agent-will-create-a-memory-about-the-user-name-here:

agent_1.print_response("Hi! My name is John Doe")

---

## Couchbase Async

**URL:** llms-txt#couchbase-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/couchbase-db/async-couchbase-db

```python cookbook/knowledge/vector_db/couchbase_db/async_couchbase_db.py theme={null}
import asyncio
import os
import time

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.couchbase import CouchbaseSearch
from couchbase.auth import PasswordAuthenticator
from couchbase.management.search import SearchIndex
from couchbase.options import ClusterOptions, KnownConfigProfiles

---

## Knowledge Management

**URL:** llms-txt#knowledge-management

**Contents:**
- Overview
- Accessing Knowledge
- What You Can Add
- Adding Content
- Useful Links

Source: https://docs.agno.com/agent-os/features/knowledge-management

Upload, organize, and manage knowledge for your agents in AgentOS

Upload files, add web pages, or paste text to build a searchable knowledge base for your agents. AgentOS indexes content and shows processing status so you can track what’s ready to use.

<Note>
  <strong>Prerequisites</strong>: Your AgentOS must be connected and active. If
  you see “Disconnected” or “Inactive,” review your{" "}
  <a href="/agent-os/connecting-your-os">connection settings</a>.
</Note>

## Accessing Knowledge

* Open the `Knowledge` section in the sidebar.
* If multiple knowledge databases are configured, select one from the database selector in the header.
* Use the `Refresh` button to sync status and content.

* Files: `.pdf`, `.csv`, `.json`, `.txt`, `.doc`, `.docx`
* Web: Website URLs (pages) or direct file links
* Text: Type or paste content directly

<Tip>
  Available processing options (Readers and Chunkers) are provided by your OS
  and may vary by file/URL type.
</Tip>

* Click `ADD NEW CONTENT`, then choose `FILE`, `WEB`, or `TEXT`.

* Drag & drop or select files. You can also add a file URL.
* Add details per item: Name, Description, Metadata, Reader, and optional Chunker.
* Names must be unique across items.
* Save to upload one or many at once.

* Enter one or more URLs and add them to the list.
* Add details per item as above (Name, Description, Metadata, Reader/Chunker).
* Save to upload all listed URLs.

* Paste or type content.
* Set Name, optional Description/Metadata, and Reader/Chunker.
* Add Content to upload.

<CardGroup cols={2}>
  <Card title="Agent Knowledge" icon="user" href="/concepts/agents/knowledge">
    Learn how to add knowledge to agents and use RAG
  </Card>

<Card title="Team Knowledge" icon="users" href="/concepts/teams/knowledge">
    Understand knowledge sharing in team environments
  </Card>
</CardGroup>

---

## Define the custom async knowledge retriever

**URL:** llms-txt#define-the-custom-async-knowledge-retriever

---

## ************* Create Agent *************

**URL:** llms-txt#*************-create-agent-*************

agno_agent = Agent(
    name="Agno Agent",
    model=Claude(id="claude-sonnet-4-5"),
    db=SqliteDb(db_file="agno.db"),
    tools=[MCPTools(transport="streamable-http", url="https://docs.agno.com/mcp")],
    add_history_to_context=True,
    markdown=True,
)

---

## Audio to text Agent

**URL:** llms-txt#audio-to-text-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/multimodal/audio-to-text

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Primary Searcher Agent - Broad search with infinity reranking

**URL:** llms-txt#primary-searcher-agent---broad-search-with-infinity-reranking

primary_searcher = Agent(
    name="Primary Searcher",
    model=Claude(id="claude-3-7-sonnet-latest"),
    role="Perform comprehensive primary search with high-performance reranking",
    knowledge=knowledge_primary,
    search_knowledge=True,
    instructions=[
        "Conduct broad, comprehensive searches across the knowledge base.",
        "Use the infinity reranker to ensure high-quality result ranking.",
        "Focus on capturing the most relevant information first.",
        "Provide detailed context and multiple perspectives on topics.",
    ],
    markdown=True,
)

---

## Agent Metrics and Performance Monitoring

**URL:** llms-txt#agent-metrics-and-performance-monitoring

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/other/agent_metrics

This example demonstrates how to collect and analyze agent metrics including message-level metrics, run metrics, and session metrics for performance monitoring.

```python agent_metrics.py theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.utils import pprint

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools(stock_price=True)],
    markdown=True,
    session_id="test-session-metrics",
    db=PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai"),
)

---

## Create specialized agents

**URL:** llms-txt#create-specialized-agents

onboarding_agent = Agent(
    name="Onboarding Agent",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions=(
        "Welcome new users and ask about their preferences. "
        "Determine if they prefer technical or friendly assistance."
    ),
    markdown=True,
)

technical_agent = Agent(
    name="Technical Expert",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions=(
        "You are a technical expert. Provide detailed, technical answers with code examples and best practices."
    ),
    markdown=True,
)

friendly_agent = Agent(
    name="Friendly Assistant",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions=(
        "You are a friendly, casual assistant. Use simple language, emojis, and make the conversation fun."
    ),
    markdown=True,
)

general_agent = Agent(
    name="General Assistant",
    model=OpenAIChat(id="gpt-4o-mini"),
    instructions=(
        "You are a balanced assistant. Provide helpful answers that are neither too technical nor too casual."
    ),
    markdown=True,
)

---

## Knowledge Searcher Agent - Specialized in finding relevant information

**URL:** llms-txt#knowledge-searcher-agent---specialized-in-finding-relevant-information

knowledge_searcher = Agent(
    name="Knowledge Searcher",
    model=Claude(id="claude-3-7-sonnet-latest"),
    role="Search and retrieve relevant information from the knowledge base",
    knowledge=knowledge,
    search_knowledge=True,
    instructions=[
        "You are responsible for searching the knowledge base thoroughly.",
        "Find all relevant information for the user's query.",
        "Provide detailed search results with context and sources.",
        "Focus on comprehensive information retrieval.",
    ],
    markdown=True,
)

---

## Create an agent with the knowledge

**URL:** llms-txt#create-an-agent-with-the-knowledge

**Contents:**
- Usage
- Params

agent = Agent(
    knowledge=knowledge,
    search_knowledge=True,
)

async def main():
    # Add YouTube video content
    await knowledge.add_content_async(
        metadata={"source": "youtube", "type": "educational"},
        urls=[
            "https://www.youtube.com/watch?v=dQw4w9WgXcQ",  # Replace with actual educational video
            "https://www.youtube.com/watch?v=example123"   # Replace with actual video URL
        ],
        reader=YouTubeReader(),
    )

# Query the knowledge base
    await agent.aprint_response(
        "What are the main topics discussed in the videos?",
        markdown=True
    )

if __name__ == "__main__":
    asyncio.run(main())
bash  theme={null}
    pip install -U youtube-transcript-api pytube sqlalchemy psycopg pgvector agno openai
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Mac theme={null}
      python examples/concepts/knowledge/readers/youtube_reader.py
      bash Windows theme={null}
      python examples/concepts/knowledge/readers/youtube_reader.py
      ```
    </CodeGroup>
  </Step>
</Steps>

<Snippet file="youtube-reader-reference.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Team with Memory Manager

**URL:** llms-txt#team-with-memory-manager

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/memory/team_with_memory_manager

This example demonstrates how to use persistent memory with a team. After each run, user memories are created and updated, allowing the team to remember information about users across sessions and provide personalized experiences.

```python cookbook/examples/teams/memory/01_team_with_memory_manager.py theme={null}
"""
This example shows you how to use persistent memory with an Agent.

After each run, user memories are created/updated.

To enable this, set `enable_user_memories=True` in the Agent config.
"""

from uuid import uuid4

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.memory import MemoryManager  # noqa: F401
from agno.models.openai import OpenAIChat
from agno.team import Team

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
db = PostgresDb(db_url=db_url)

session_id = str(uuid4())
john_doe_id = "john_doe@example.com"

---

## Groq Llama Finance Agent

**URL:** llms-txt#groq-llama-finance-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/reasoning/tools/groq-llama-finance-agent

This example shows how to use `ReasoningTools` with a Groq Llama model.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

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

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Async Custom Retriever

**URL:** llms-txt#async-custom-retriever

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/custom_retriever/async-custom-retriever

```python async_retriever.py theme={null}
import asyncio
from typing import Optional

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.qdrant import Qdrant
from qdrant_client import AsyncQdrantClient

---

## Code execution agent

**URL:** llms-txt#code-execution-agent

code_agent = Agent(
    name="Code Agent",
    model=Claude(id="claude-3-5-sonnet-latest"),
    role="Execute and test code",
    tools=[E2BTools()],
    instructions=[
        "Execute code safely in the sandbox environment.",
        "Test code thoroughly before providing results.",
        "Provide clear explanations of code execution.",
    ],
)

---

## Create a News Reporter Agent with a fun personality

**URL:** llms-txt#create-a-news-reporter-agent-with-a-fun-personality

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=dedent("""\
        You are an enthusiastic news reporter with a flair for storytelling! 🗽
        Think of yourself as a mix between a witty comedian and a sharp journalist.

Follow these guidelines for every report:
        1. Start with an attention-grabbing headline using relevant emoji
        2. Use the search tool to find current, accurate information
        3. Present news with authentic NYC enthusiasm and local flavor
        4. Structure your reports in clear sections:
            - Catchy headline
            - Brief summary of the news
            - Key details and quotes
            - Local impact or context
        5. Keep responses concise but informative (2-3 paragraphs max)
        6. Include NYC-style commentary and local references
        7. End with a signature sign-off phrase

Sign-off examples:
        - 'Back to you in the studio, folks!'
        - 'Reporting live from the city that never sleeps!'
        - 'This is [Your Name], live from the heart of Manhattan!'

Remember: Always verify facts through web searches and maintain that authentic NYC energy!\
    """),
    tools=[DuckDuckGoTools()],
    markdown=True,
)

---

## Create a knowledge base containing information from a URL

**URL:** llms-txt#create-a-knowledge-base-containing-information-from-a-url

agno_docs = Knowledge(
    # Use LanceDB as the vector database and store embeddings in the `agno_docs` table
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)
agno_docs.add_content(
    url="https://docs.agno.com/llms-full.txt"
)

knowledge_tools = KnowledgeTools(
    knowledge=agno_docs,
    think=True,
    search=True,
    analyze=True,
    add_few_shot=True,
)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[knowledge_tools],
    markdown=True,
)

if __name__ == "__main__":
    agent.print_response("How do I build multi-agent teams with Agno?", stream=True)
python  theme={null}
from agno.tools.knowledge import KnowledgeTools

knowledge_tools = KnowledgeTools(
    knowledge=my_knowledge_base,
    think=True,                # Enable the think tool
    search=True,               # Enable the search tool
    analyze=True,              # Enable the analyze tool
    add_instructions=True,     # Add default instructions
    add_few_shot=True,         # Add few-shot examples
    few_shot_examples=None,    # Optional custom few-shot examples
)
```

**Examples:**

Example 1 (unknown):
```unknown
The toolkit comes with default instructions and few-shot examples to help the Agent use the tools effectively. Here is how you can configure them:
```

---

## Initialize LangDB tracing - must be called before creating agents

**URL:** llms-txt#initialize-langdb-tracing---must-be-called-before-creating-agents

from agno.agent import Agent
from agno.models.langdb import LangDB
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Translation Agent

**URL:** llms-txt#translation-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/use-cases/agents/translation_agent

This example demonstrates how to create an intelligent translation agent that goes beyond simple text translation. The agent:

* **Translates text** from one language to another
* **Analyzes emotional content** in the translated text
* **Selects appropriate voices** based on language and emotion
* **Creates localized voices** using Cartesia's voice localization tools
* **Generates audio output** with emotion-appropriate voice characteristics

The agent uses a step-by-step approach to ensure high-quality translation and voice generation, making it ideal for creating localized content that maintains the emotional tone of the original text.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Create an agent with Searxng

**URL:** llms-txt#create-an-agent-with-searxng

agent = Agent(tools=[searxng])

---

## Agent gets ALL database tools - overwhelming!

**URL:** llms-txt#agent-gets-all-database-tools---overwhelming!

tools = MCPTools(url="http://127.0.0.1:5001")  # 50+ tools
python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
**With MCPToolbox (3 relevant tools):**
```

---

## Create knowledge search agent

**URL:** llms-txt#create-knowledge-search-agent

web_agent = Agent(
    name="Knowledge Search Agent",
    role="Handle knowledge search",
    knowledge=knowledge_base,
    model=OpenAIChat(id="gpt-5-mini"),
)

---

## Change State On Run

**URL:** llms-txt#change-state-on-run

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/state/change_state_on_run

This example demonstrates how to manage session state across different runs for different users. It shows how session state persists within the same session but is isolated between different sessions and users.

```python change_state_on_run.py theme={null}
from agno.agent import Agent
from agno.db.in_memory import InMemoryDb
from agno.models.openai import OpenAIChat

agent = Agent(
    db=InMemoryDb(),
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="Users name is {user_name} and age is {age}",
    debug_mode=True,
)

---

## Shared knowledge base for the team

**URL:** llms-txt#shared-knowledge-base-for-the-team

knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs_team",
        search_type=SearchType.hybrid,
        embedder=CohereEmbedder(id="embed-v4.0"),
        reranker=CohereReranker(model="rerank-v3.5"),
    ),
)

---

## Ask the agent about the knowledge

**URL:** llms-txt#ask-the-agent-about-the-knowledge

**Contents:**
- Usage
- Params

agent.print_response(
    "What are the latest AI trends according to the search results?", markdown=True
)
bash  theme={null}
    pip install -U requests beautifulsoup4 agno openai
    bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash Mac theme={null}
      python examples/concepts/knowledge/readers/web_search_reader.py
      bash Windows theme={null}
      python examples/concepts/knowledge/readers/web_search_reader.py
      ```
    </CodeGroup>
  </Step>
</Steps>

<Snippet file="web-search-reader-reference.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Set environment variables">
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

## Manual Knowledge Filters

**URL:** llms-txt#manual-knowledge-filters

**Contents:**
- Step 1: Attach Metadata
- Step 2: Query with Filters
  - 1. On the Agent (applies to all queries)
  - 2. On Each Query (overrides Agent filters for that run)
- Combining Multiple Filters
- Try It Yourself!
- Developer Resources

Manual filtering gives you full control over which documents are searched by specifying filters directly in your code.

## Step 1: Attach Metadata

There are two ways to attach metadata to your documents:

1. **Attach Metadata When Initializing the Knowledge Base**

2. **Attach Metadata When Loading Documents One by One**

> 💡 **Tips:**\
> • Use **Option 1** if you have all your documents and metadata ready at once.\
> • Use **Option 2** if you want to add documents incrementally or as they become available.

## Step 2: Query with Filters

You can pass filters in two ways:

### 1. On the Agent (applies to all queries)

### 2. On Each Query (overrides Agent filters for that run)

<Note>If you pass filters both on the Agent and on the query, the query-level filters take precedence.</Note>

## Combining Multiple Filters

You can filter by multiple fields:

* Load documents with different metadata.
* Query with different filter combinations.
* Observe how the results change!

## Developer Resources

* [Manual filtering](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/filters/filtering.py)
* [Manual filtering on load](https://github.com/agno-agi/agno/blob/main/cookbook/knowledge/filters/filtering_on_load.py)

**Examples:**

Example 1 (unknown):
```unknown
2. **Attach Metadata When Loading Documents One by One**
```

Example 2 (unknown):
```unknown
***

> 💡 **Tips:**\
> • Use **Option 1** if you have all your documents and metadata ready at once.\
> • Use **Option 2** if you want to add documents incrementally or as they become available.

## Step 2: Query with Filters

You can pass filters in two ways:

### 1. On the Agent (applies to all queries)
```

Example 3 (unknown):
```unknown
### 2. On Each Query (overrides Agent filters for that run)
```

Example 4 (unknown):
```unknown
<Note>If you pass filters both on the Agent and on the query, the query-level filters take precedence.</Note>

## Combining Multiple Filters

You can filter by multiple fields:
```

---

## Basic WhatsApp Agent

**URL:** llms-txt#basic-whatsapp-agent

**Contents:**
- Code
- Usage
- Key Features

Source: https://docs.agno.com/examples/agent-os/interfaces/whatsapp/basic

Create a basic AI agent that integrates with WhatsApp Business API

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set Environment Variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

* **WhatsApp Integration**: Responds to messages automatically
* **Conversation History**: Maintains context with last 3 interactions
* **Persistent Memory**: SQLite database for session storage
* **DateTime Context**: Time-aware responses
* **Markdown Support**: Rich text formatting in messages

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## WhatsApp Image Generation Agent (Model-based)

**URL:** llms-txt#whatsapp-image-generation-agent-(model-based)

**Contents:**
- Code
- Usage
- Key Features

Source: https://docs.agno.com/examples/agent-os/interfaces/whatsapp/image_generation_model

WhatsApp agent that generates images using Gemini's built-in capabilities

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set Environment Variables">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

* **Direct Image Generation**: Gemini 2.0 Flash experimental image generation
* **Text-to-Image**: Converts descriptions into visual content
* **Multimodal Responses**: Generates both text and images
* **WhatsApp Integration**: Sends images directly through WhatsApp
* **Debug Mode**: Enhanced logging for troubleshooting

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Set Environment Variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Redis for Agent

**URL:** llms-txt#redis-for-agent

**Contents:**
- Usage
  - Run Redis

Source: https://docs.agno.com/examples/concepts/db/redis/redis_for_agent

Agno supports using Redis as a storage backend for Agents using the `RedisDb` class.

Install [docker desktop](https://docs.docker.com/desktop/install/mac-install/) and run **Redis** on port **6379** using:

```python redis_for_agent.py theme={null}
from agno.agent import Agent
from agno.db.base import SessionType
from agno.db.redis import RedisDb
from agno.tools.duckduckgo import DuckDuckGoTools

**Examples:**

Example 1 (unknown):
```unknown

```

---

## structured_output_response: RunOutput = structured_output_agent.run("New York")

**URL:** llms-txt#structured_output_response:-runoutput-=-structured_output_agent.run("new-york")

---

## Example: Ask the agent to run a SQL query

**URL:** llms-txt#example:-ask-the-agent-to-run-a-sql-query

**Contents:**
- Toolkit Params
- Toolkit Functions
- Developer Resources

agent.print_response("""
Please run a SQL query to get all users from the users table
who signed up in the last 30 days
""")
```

| Name           | Type                              | Default  | Description                                    |
| -------------- | --------------------------------- | -------- | ---------------------------------------------- |
| `connection`   | `Optional[PgConnection[DictRow]]` | `None`   | Optional existing psycopg connection object.   |
| `db_name`      | `Optional[str]`                   | `None`   | Optional name of the database to connect to.   |
| `user`         | `Optional[str]`                   | `None`   | Optional username for database authentication. |
| `password`     | `Optional[str]`                   | `None`   | Optional password for database authentication. |
| `host`         | `Optional[str]`                   | `None`   | Optional host for the database connection.     |
| `port`         | `Optional[int]`                   | `None`   | Optional port for the database connection.     |
| `table_schema` | `str`                             | `public` | Schema name to search for tables.              |

| Function               | Description                                                                                                                                                                                                                                                                            |
| ---------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `show_tables`          | Retrieves and displays a list of tables in the database. Returns the list of tables.                                                                                                                                                                                                   |
| `describe_table`       | Describes the structure of a specified table by returning its columns, data types, and nullability. Parameters include `table` (str) to specify the table name. Returns the table description.                                                                                         |
| `summarize_table`      | Summarizes a table by computing aggregates such as min, max, average, standard deviation, and non-null counts for numeric columns, or unique values and average length for text columns. Parameters include `table` (str) to specify the table name. Returns the summary of the table. |
| `inspect_query`        | Inspects an SQL query by returning the query plan using EXPLAIN. Parameters include `query` (str) to specify the SQL query. Returns the query plan.                                                                                                                                    |
| `export_table_to_path` | Exports a specified table in CSV format to a given path. Parameters include `table` (str) to specify the table name and `path` (str) to specify where to save the file. Returns the result of the export operation.                                                                    |
| `run_query`            | Executes a read-only SQL query and returns the result. Parameters include `query` (str) to specify the SQL query. Returns the result of the query execution.                                                                                                                           |

You can use `include_tools` or `exclude_tools` to modify the list of tools the agent has access to. Learn more about [selecting tools](/concepts/tools/selecting-tools).

## Developer Resources

* View [Tools](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/postgres.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/postgres_tools.py)

---

## Reranking Specialist Agent - Specialized in result optimization

**URL:** llms-txt#reranking-specialist-agent---specialized-in-result-optimization

reranking_specialist = Agent(
    name="Reranking Specialist",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Apply advanced reranking to optimize retrieval results",
    knowledge=reranked_knowledge,
    search_knowledge=True,
    instructions=[
        "Apply advanced reranking techniques to optimize result relevance.",
        "Focus on precision and ranking quality over quantity.",
        "Use the Cohere reranker to identify the most relevant content.",
        "Prioritize results that best match the user's specific needs.",
    ],
    markdown=True,
)

---

## JSON for Agent

**URL:** llms-txt#json-for-agent

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/db/json/json_for_agent

Agno supports using local JSON files as a storage backend for Agents using the `JsonDb` class.

```python json_for_agent.py theme={null}
"""Run `pip install ddgs openai` to install dependencies."""

from agno.agent import Agent
from agno.db.json import JsonDb
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Azure Cosmos DB MongoDB vCore Agent Knowledge

**URL:** llms-txt#azure-cosmos-db-mongodb-vcore-agent-knowledge

**Contents:**
- Setup
- Example

Source: https://docs.agno.com/concepts/vectordb/azure_cosmos_mongodb

Follow the instructions in the [Azure Cosmos DB Setup Guide](https://learn.microsoft.com/en-us/azure/cosmos-db/mongodb/vcore) to get the connection string.

Install MongoDB packages:

```python agent_with_knowledge.py theme={null}
import urllib.parse
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.mongodb import MongoDb

**Examples:**

Example 1 (unknown):
```unknown
## Example
```

---

## run_response: Iterator[RunOutputEvent] = agent.run("Share a 2 sentence horror story", stream=True)

**URL:** llms-txt#run_response:-iterator[runoutputevent]-=-agent.run("share-a-2-sentence-horror-story",-stream=true)

---

## Primary Retriever Agent - Specialized in main document retrieval

**URL:** llms-txt#primary-retriever-agent---specialized-in-main-document-retrieval

primary_retriever = Agent(
    name="Primary Retriever",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Retrieve primary documents and core information from knowledge base",
    knowledge=primary_knowledge,
    search_knowledge=True,
    instructions=[
        "Search the knowledge base for directly relevant information to the user's query.",
        "Focus on retrieving the most relevant and specific documents first.",
        "Provide detailed information with proper context.",
        "Ensure accuracy and completeness of retrieved information.",
    ],
    markdown=True,
)

---

## SurrealDB Async

**URL:** llms-txt#surrealdb-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/vectordb/surrealdb/async-surreal-db

```python cookbook/knowledge/vector_db/surrealdb/async_surreal_db.py theme={null}
import asyncio

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.surrealdb import SurrealDb
from surrealdb import AsyncSurreal

SURREALDB_URL = "ws://localhost:8000"
SURREALDB_USER = "root"
SURREALDB_PASSWORD = "root"
SURREALDB_NAMESPACE = "test"
SURREALDB_DATABASE = "test"

---

## Agentic Session State

**URL:** llms-txt#agentic-session-state

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/state/agentic_session_state

This example demonstrates how to enable agentic session state in teams and agents, allowing them to automatically manage and update their session state during interactions. The agents can modify the session state autonomously based on the conversation context.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install required libraries">
    
  </Step>

<Step title="Set environment variables">
    
  </Step>

<Step title="Run the agent">
    
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install required libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Initialize Agent with Cartesia tools

**URL:** llms-txt#initialize-agent-with-cartesia-tools

agent = Agent(
    name="Cartesia TTS Agent",
    description="An agent that uses Cartesia for text-to-speech.",
    tools=[CartesiaTools()],
)

response = agent.run(
    """Generate a simple greeting using Text-to-Speech:

Say "Welcome to Cartesia, the advanced  speech synthesis platform. This speech is generated by an agent."
    """
)

---

## Configuration for the Knowledge page

**URL:** llms-txt#configuration-for-the-knowledge-page

knowledge:
  display_name: <DISPLAY_NAME>
  dbs:
    - <DB_ID>
      domain_config:
        display_name: <DISPLAY_NAME>
    ...

---

## Setup your Agent using a reasoning model

**URL:** llms-txt#setup-your-agent-using-a-reasoning-model

agent = Agent(
    model=Groq(
        id="deepseek-r1-distill-llama-70b", temperature=0.6, max_tokens=1024, top_p=0.95
    ),
    markdown=True,
)

---

## Asynchronous Agent

**URL:** llms-txt#asynchronous-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/meta/async_basic

```python cookbook/models/meta/llama/async_basic.py theme={null}
import asyncio

from agno.agent import Agent, RunOutput  # noqa
from agno.models.meta import Llama

agent = Agent(
    model=Llama(id="Llama-4-Maverick-17B-128E-Instruct-FP8"),
    markdown=True
)

---

## Web search agent

**URL:** llms-txt#web-search-agent

website_agent = Agent(
    name="Website Agent",
    role="Search the website for information",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    instructions=[
        "Search the website for information",
    ],
)

---

## for route in agent_os.get_routes():

**URL:** llms-txt#for-route-in-agent_os.get_routes():

---

## Agent with PDF Input (Local file)

**URL:** llms-txt#agent-with-pdf-input-(local-file)

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/gemini/pdf_input_local

```python cookbook/models/google/gemini/pdf_input_local.py theme={null}
from pathlib import Path
from agno.agent import Agent
from agno.media import File
from agno.models.google import Gemini
from agno.utils.media import download_file

pdf_path = Path(__file__).parent.joinpath("ThaiRecipes.pdf")

---

## Alternatively, add all routes from AgentOS app to the current app

**URL:** llms-txt#alternatively,-add-all-routes-from-agentos-app-to-the-current-app

---

## Team Performance with Memory

**URL:** llms-txt#team-performance-with-memory

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/evals/performance/performance_team_with_memory

Learn how to evaluate team performance with memory tracking and growth monitoring.

This example shows how to evaluate team performance with memory tracking enabled.

```python  theme={null}
import asyncio
import random

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.eval.performance import PerformanceEval
from agno.models.openai import OpenAIChat
from agno.team.team import Team

cities = [
    "New York",
    "Los Angeles",
    "Chicago",
    "Houston",
    "Miami",
    "San Francisco",
    "Seattle",
    "Boston",
    "Washington D.C.",
    "Atlanta",
    "Denver",
    "Las Vegas",
]

---

## Agent Using Multimodal Tool Response in Runs

**URL:** llms-txt#agent-using-multimodal-tool-response-in-runs

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/multimodal/agent_using_multimodal_tool_response_in_runs

This example demonstrates how to create an agent that uses DALL-E to generate images and maintains conversation history across multiple runs, allowing the agent to remember previous interactions and images generated.

```python agent_using_multimodal_tool_response_in_runs.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.tools.dalle import DalleTools

---

## Live Search Agent Stream

**URL:** llms-txt#live-search-agent-stream

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/xai/live_search_agent_stream

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Create a reasoning agent that uses:

**URL:** llms-txt#create-a-reasoning-agent-that-uses:

---

## Create Agent Run

**URL:** llms-txt#create-agent-run

Source: https://docs.agno.com/reference-api/schema/agents/create-agent-run

post /agents/{agent_id}/runs
Execute an agent with a message and optional media files. Supports both streaming and non-streaming responses.

**Features:**
- Text message input with optional session management
- Multi-media support: images (PNG, JPEG, WebP), audio (WAV, MP3), video (MP4, WebM, etc.)
- Document processing: PDF, CSV, DOCX, TXT, JSON
- Real-time streaming responses with Server-Sent Events (SSE)
- User and session context preservation

**Streaming Response:**
When `stream=true`, returns SSE events with `event` and `data` fields.

---

## Mem0

**URL:** llms-txt#mem0

**Contents:**
- Example
- Toolkit Params
- Toolkit Functions
- Developer Resources

Source: https://docs.agno.com/concepts/tools/toolkits/others/mem0

Mem0Tools provides intelligent memory management capabilities for agents using the Mem0 memory platform.

The following agent can store and retrieve memories using Mem0:

| Parameter                    | Type             | Default | Description                                     |
| ---------------------------- | ---------------- | ------- | ----------------------------------------------- |
| `config`                     | `Optional[Dict]` | `None`  | Mem0 configuration dictionary.                  |
| `api_key`                    | `Optional[str]`  | `None`  | Mem0 API key. Uses MEM0\_API\_KEY if not set.   |
| `user_id`                    | `Optional[str]`  | `None`  | User ID for memory operations.                  |
| `org_id`                     | `Optional[str]`  | `None`  | Organization ID. Uses MEM0\_ORG\_ID if not set. |
| `project_id`                 | `Optional[str]`  | `None`  | Project ID. Uses MEM0\_PROJECT\_ID if not set.  |
| `infer`                      | `bool`           | `True`  | Enable automatic memory inference.              |
| `enable_add_memory`          | `bool`           | `True`  | Enable memory addition functionality.           |
| `enable_search_memory`       | `bool`           | `True`  | Enable memory search functionality.             |
| `enable_get_all_memories`    | `bool`           | `True`  | Enable retrieving all memories functionality.   |
| `enable_delete_all_memories` | `bool`           | `True`  | Enable memory deletion functionality.           |

| Function              | Description                                   |
| --------------------- | --------------------------------------------- |
| `add_memory`          | Store new memories or information.            |
| `search_memory`       | Search through stored memories using queries. |
| `get_all_memories`    | Retrieve all stored memories for the user.    |
| `delete_all_memories` | Delete all stored memories for the user.      |

## Developer Resources

* View [Tools Source](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/mem0.py)
* [Mem0 Documentation](https://docs.mem0.ai/)
* [Mem0 Platform](https://mem0.ai/)

---

## members=[agent],

**URL:** llms-txt#members=[agent],

---

## Basic Streaming Agent

**URL:** llms-txt#basic-streaming-agent

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/siliconflow/basic_stream

```python cookbook/models/siliconflow/basic_stream.py theme={null}
from agno.agent import Agent, RunOutputEvent  # noqa
from agno.models.siliconflow import Siliconflow

agent = Agent(model=Siliconflow(id="openai/gpt-oss-120b"), markdown=True)

---

## Running the Agent

**URL:** llms-txt#running-the-agent

agent.print_response("Tell me a new interesting fact about space")

---

## Combine model, tools, and instructions into a complete agent

**URL:** llms-txt#combine-model,-tools,-and-instructions-into-a-complete-agent

**Contents:**
  - 4b. Create the Analysis Function
  - 4c. Create a Test Function
  - 4d. Complete Working Example

social_media_agent = Agent(
    name="Social Media Intelligence Analyst",
    model=model,                 # The GPT-5 mini model we chose
    tools=tools,                 # The X and Exa tools we configured
    instructions=complete_instructions,  # The strategy we defined
    markdown=True,               # Enable rich formatting for reports
    show_tool_calls=True,        # Show transparency in data collection
)

print(f"Agent created: {social_media_agent.name}")
python  theme={null}
def analyze_brand_sentiment(query: str, tweet_count: int = 20):
    """
    Execute comprehensive social media intelligence analysis.

Args:
        query: Brand or topic search query (e.g., "Tesla OR @elonmusk")
        tweet_count: Number of recent tweets to analyze
    """

# Create a detailed prompt for the agent
    analysis_prompt = f"""
    Conduct comprehensive social media intelligence analysis for: "{query}"

ANALYSIS PARAMETERS:
    - Twitter Analysis: {tweet_count} most recent tweets with engagement metrics
    - Web Intelligence: Related articles, discussions, and broader context via Exa
    - Cross-Platform Synthesis: Correlate social sentiment with web discussions
    - Strategic Focus: Brand positioning, competitive analysis, risk assessment

METHODOLOGY:
    1. Gather direct social media mentions and engagement data
    2. Search for related web discussions and broader context
    3. Analyze sentiment patterns and engagement indicators
    4. Identify cross-platform themes and influence networks
    5. Generate strategic recommendations with evidence backing

Provide comprehensive intelligence report following the structured format.
    """

# Execute the analysis
    return social_media_agent.print_response(analysis_prompt, stream=True)

print("Analysis function created")
python  theme={null}
def test_agent():
    """Test the complete agent with a sample query."""
    print("Testing social media intelligence agent...")
    analyze_brand_sentiment("Agno OR AgnoAGI", tweet_count=10)

print("Test function ready")
python  theme={null}
"""
Complete Social Media Intelligence Agent
Built with Agno framework
"""
from pathlib import Path
from textwrap import dedent
from dotenv import load_dotenv

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.x import XTools
from agno.tools.exa import ExaTools

**Examples:**

Example 1 (unknown):
```unknown
For detailed information about each Agent parameter, see the [Agent Reference Documentation](/reference/agents/agent).

### 4b. Create the Analysis Function
```

Example 2 (unknown):
```unknown
### 4c. Create a Test Function
```

Example 3 (unknown):
```unknown
### 4d. Complete Working Example

Here's your complete `app/social_media_agent.py` file:
```

---

## Load the knowledge

**URL:** llms-txt#load-the-knowledge

knowledge.add_content(
    path="data/pptx_files",
    reader=PPTXReader(),
)

---

## agent.print_response("Send an email with the subject 'Hello' and the body 'Hello, world!'")

**URL:** llms-txt#agent.print_response("send-an-email-with-the-subject-'hello'-and-the-body-'hello,-world!'")

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch user_input_required_async.py
    bash Mac theme={null}
      python user_input_required_async.py
      bash Windows   theme={null}
      python user_input_required_async.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Memory Search

**URL:** llms-txt#memory-search

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/memory/memory_manager/04-memory-search

How to search for user memories using different retrieval methods.

* `last_n`: Retrieves the last n memories
* `first_n`: Retrieves the first n memories
* `agentic`: Retrieves memories using agentic search

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run Example">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Get User Memory Statistics

**URL:** llms-txt#get-user-memory-statistics

Source: https://docs.agno.com/reference-api/schema/memory/get-user-memory-statistics

get /user_memory_stats
Retrieve paginated statistics about memory usage by user. Provides insights into user engagement and memory distribution across users.

---

## Please download a sample video file to test this Agent

**URL:** llms-txt#please-download-a-sample-video-file-to-test-this-agent

---

## Add documents with metadata for agentic filtering

**URL:** llms-txt#add-documents-with-metadata-for-agentic-filtering

knowledge.add_contents(
    [
        {
            "path": downloaded_cv_paths[0],
            "metadata": {
                "user_id": "jordan_mitchell",
                "document_type": "cv",
                "year": 2025,
            },
        },
        {
            "path": downloaded_cv_paths[1],
            "metadata": {
                "user_id": "taylor_brooks",
                "document_type": "cv",
                "year": 2025,
            },
        },
        {
            "path": downloaded_cv_paths[2],
            "metadata": {
                "user_id": "morgan_lee",
                "document_type": "cv",
                "year": 2025,
            },
        },
        {
            "path": downloaded_cv_paths[3],
            "metadata": {
                "user_id": "casey_jordan",
                "document_type": "cv",
                "year": 2025,
            },
        },
        {
            "path": downloaded_cv_paths[4],
            "metadata": {
                "user_id": "alex_rivera",
                "document_type": "cv",
                "year": 2025,
            },
        },
    ]
)

---

## Create an agent with knowledge

**URL:** llms-txt#create-an-agent-with-knowledge

**Contents:**
- Step 2: Add Your Content
- Step 3: Chat with Your Agent

agent = Agent(
    model=OpenAIChat(id="gpt-4o-mini"),
    knowledge=knowledge,
    # Enable automatic knowledge search
    search_knowledge=True,
    instructions=[
        "Always search your knowledge base before answering questions",
        "Include source references in your responses when possible"
    ]
)
python  theme={null}
  from agno.vectordb.lancedb import LanceDb

# Local vector storage - no database setup required
  knowledge = Knowledge(
      vector_db=LanceDb(
          table_name="knowledge_documents",
          uri="tmp/lancedb"  # Local directory for storage
      ),
  )
  python  theme={null}
    # Add a specific file
    knowledge.add_content(
        path="path/to/your/document.pdf"
    )

# Add an entire directory
    knowledge.add_content(
        path="path/to/documents/"
    )
    python  theme={null}
    # Add content from a website
    knowledge.add_content(
        url="https://docs.agno.com/introduction"
    )

# Add a PDF from the web
    knowledge.add_content(
        url="https://example.com/document.pdf"
    )
    python  theme={null}
    # Add text content directly
    knowledge.add_content(
        text_content="""
        Company Policy: Remote Work Guidelines

1. Remote work is available to all full-time employees
        2. Employees must maintain regular communication with their team
        3. Home office equipment is provided up to $1000 annually
        """
    )
    python  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
<Accordion title="Don't have PostgreSQL? Use LanceDB instead">
  For a quick start without setting up PostgreSQL, use LanceDB which stores data locally:
```

Example 2 (unknown):
```unknown
</Accordion>

## Step 2: Add Your Content

Now let's add some knowledge to your agent. You can add content from various sources:

<Tabs>
  <Tab title="From Local Files">
```

Example 3 (unknown):
```unknown
</Tab>

  <Tab title="From URLs">
```

Example 4 (unknown):
```unknown
</Tab>

  <Tab title="From Text">
```

---

## Company news and information agent

**URL:** llms-txt#company-news-and-information-agent

company_info_agent = Agent(
    name="Company Info Searcher",
    model=OpenAIChat("gpt-5-mini"),
    role="Searches for company news and information",
    output_schema=CompanyAnalysis,
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            show_results=True,
            highlights=False,
        )
    ],
    instructions=[
        "Focus on company news and business information",
        "Provide comprehensive analysis of company developments",
    ],
)

---

## Markdown Reader (Async)

**URL:** llms-txt#markdown-reader-(async)

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/knowledge/readers/markdown/markdown-reader-async

The **Markdown Reader** with asynchronous processing allows you to handle Markdown files efficiently and integrate them with knowledge bases.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Set environment variables">
    
  </Step>

<Snippet file="run-pgvector-step.mdx" />

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Create knowledge search agent with filter awareness

**URL:** llms-txt#create-knowledge-search-agent-with-filter-awareness

web_agent = Agent(
    name="Knowledge Search Agent",
    role="Handle knowledge search",
    knowledge=knowledge,
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=["Always take into account filters"],
)

---

## agent.print_response("What files do I have in my current directory?", stream=True)

**URL:** llms-txt#agent.print_response("what-files-do-i-have-in-my-current-directory?",-stream=true)

**Contents:**
- Usage

bash  theme={null}
    pip install -U agno openai
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch external_tool_execution_stream.py
    bash Mac theme={null}
      python external_tool_execution_stream.py
      bash Windows   theme={null}
      python external_tool_execution_stream.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Set your API key and run the basic agent

**URL:** llms-txt#set-your-api-key-and-run-the-basic-agent

**Contents:**
- Verification

export OPENAI_API_KEY="your_openai_api_key"
uv run agent.py
bash  theme={null}

**Examples:**

Example 1 (unknown):
```unknown
This starts a PostgreSQL database with sample hotel data and an MCP Toolbox server that exposes database operations as filtered tools.

## Verification

To verify that your docker/podman setup is working correctly, you can check the database connection:
```

---

## Add a memory for the default user

**URL:** llms-txt#add-a-memory-for-the-default-user

memory.add_user_memory(
    memory=UserMemory(memory="The user's name is John Doe", topics=["name"]),
)
print("Memories:")
pprint(memory.get_user_memories())

---

## Run agent and print response to the terminal

**URL:** llms-txt#run-agent-and-print-response-to-the-terminal

**Contents:**
- Interactive CLI

agent.print_response("Trending startups and products.")
python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    db=SqliteDb(db_file="tmp/data.db"),
    add_history_to_context=True,
    num_history_runs=3,
    markdown=True,
)

**Examples:**

Example 1 (unknown):
```unknown
<Tip>
  You can set `debug_level=2` to get even more detailed logs.
</Tip>

Here's how it looks:

<Frame>
  <video autoPlay muted loop playsInline style={{ borderRadius: "0.5rem", width: "100%", height: "auto" }}>
    <source src="https://mintcdn.com/agno-v2/Xc0-_OHxxYe_vtGw/videos/debug_mode.mp4?fit=max&auto=format&n=Xc0-_OHxxYe_vtGw&q=85&s=67b080deec475663e285c22130987541" type="video/mp4" data-path="videos/debug_mode.mp4" />
  </video>
</Frame>

## Interactive CLI

Agno also comes with a pre-built interactive CLI that runs your Agent as a command-line application. You can use this to test back-and-forth conversations with your agent.
```

---

## Create specialized Hacker News research agent

**URL:** llms-txt#create-specialized-hacker-news-research-agent

hackernews_agent = Agent(
    name="Hackernews Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[HackerNewsTools()],
    role="Extract key insights and content from Hackernews posts",
    instructions=[
        "Search Hacker News for relevant articles and discussions",
        "Extract key insights and summarize findings",
        "Focus on high-quality, well-discussed posts",
    ],
)

---

## This section loads the knowledge base. Skip if your knowledge base was populated elsewhere.

**URL:** llms-txt#this-section-loads-the-knowledge-base.-skip-if-your-knowledge-base-was-populated-elsewhere.

---

## Setup your Agent with Memory

**URL:** llms-txt#setup-your-agent-with-memory

**Contents:**
- Using Memory Tools

agent = Agent(
    db=db,
    enable_user_memories=True, # This enables Memory for the Agent
    add_memories_to_context=False, # This disables adding memories to the context
)
python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.memory import MemoryTools

**Examples:**

Example 1 (unknown):
```unknown
## Using Memory Tools

Instead of automatic memory management, you can give your agent explicit tools to create, retrieve, update, and delete memories. This approach gives the agent more control and reasoning ability, so it can decide when to store something versus when to search for existing memories.

**When to use Memory Tools:**

* You want the agent to reason about whether something is worth remembering
* You need fine-grained control over memory operations (create, update, delete separately)
* You're building a system where the agent should explicitly search memories rather than having them auto-loaded
```

---

## Calculator agent that can calculate

**URL:** llms-txt#calculator-agent-that-can-calculate

**Contents:**
- Usage

calculator_agent = Agent(
    name="Calculator Agent",
    model=Claude(id="claude-3-5-sonnet-latest"),
    role="Calculate",
    tools=[
        CalculatorTools()
    ],
)

agno_assist_knowledge = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_assist_knowledge",
        search_type=SearchType.hybrid,
        embedder=OpenAIEmbedder(id="text-embedding-3-small"),
    ),
)

agno_assist = Agent(
    name="Agno Assist",
    role="You help answer questions about the Agno framework.",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="Search your knowledge before answering the question. Help me to write working code for Agno Agents.",
    tools=[
        KnowledgeTools(
            knowledge=agno_assist_knowledge, add_instructions=True, add_few_shot=True
        ),
    ],
    add_history_to_context=True,
    add_datetime_to_context=True,
)

github_agent = Agent(
    name="Github Agent",
    role="Do analysis on Github repositories",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "Use your tools to answer questions about the repo: agno-agi/agno",
        "Do not create any issues or pull requests unless explicitly asked to do so",
    ],
    tools=[
        GithubTools(
            list_issues=True,
            list_issue_comments=True,
            get_pull_request=True,
            get_issue=True,
            get_pull_request_comments=True,
        )
    ],
)

local_python_agent = Agent(
    name="Local Python Agent",
    role="Run Python code locally",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "Use your tools to run Python code locally",
    ],
    tools=[
        FileTools(base_dir=cwd),
        PythonTools(
            base_dir=Path(cwd), list_files=True, run_files=True, uv_pip_install=True
        ),
    ],
)

agent_team = Team(
    name="Multi-Purpose Team",
    model=Claude(id="claude-3-7-sonnet-latest"),
    tools=[
        ReasoningTools(add_instructions=True, add_few_shot=True),
    ],
    members=[
        web_agent,
        finance_agent,
        writer_agent,
        calculator_agent,
        agno_assist,
        github_agent,
        local_python_agent,
    ],
    instructions=[
        "You are a team of agents that can answer a variety of questions.",
        "You can use your member agents to answer the questions.",
        "You can also answer directly, you don't HAVE to forward the question to a member agent.",
        "Reason about more complex questions before delegating to a member agent.",
        "If the user is only being conversational, don't use any tools, just answer directly.",
    ],
    markdown=True,
    show_members_responses=True,
    share_member_interactions=True,
)

if __name__ == "__main__":
    # Load the knowledge base
    asyncio.run(
        agno_assist_knowledge.add_contents_async(url="https://docs.agno.com/llms-full.txt")
    )

# asyncio.run(agent_team.aprint_response("Hi! What are you capable of doing?"))

# Python code execution
    # asyncio.run(agent_team.aprint_response(dedent("""What is the right way to implement an Agno Agent that searches Hacker News for good articles?
    #                                        Create a minimal example for me and test it locally to ensure it won't immediately crash.
    #                                        Make save the created code in a file called `./python/hacker_news_agent.py`.
    #                                        Don't mock anything. Use the real information from the Agno documentation."""), stream=True))

# # Reddit research
    # asyncio.run(agent_team.aprint_response(dedent("""What should I be investing in right now?
    #                                        Find some popular subreddits and do some reseach of your own.
    #                                        Write a detailed report about your findings that could be given to a financial advisor."""), stream=True))

# Github analysis
    # asyncio.run(agent_team.aprint_response(dedent("""List open pull requests in the agno-agi/agno repository.
    #                                        Find an issue that you think you can resolve and give me the issue number,
    #                                        your suggested solution and some code snippets."""), stream=True))

# Medical research
    txt_path = Path(__file__).parent.resolve() / "medical_history.txt"
    loaded_txt = open(txt_path, "r", encoding="utf-8").read()
    agent_team.print_response(
        input=dedent(f"""I have a patient with the following medical information:\n {loaded_txt}
                         What is the most likely diagnosis?
                        """),
    )
bash  theme={null}
    pip install agno lancedb exa_py ddgs pubmed-parser
    bash  theme={null}
    export OPENAI_API_KEY=****
    export ANTHROPIC_API_KEY=****
    export GITHUB_API_KEY=****
    export EXA_API_KEY=****
    bash  theme={null}
    # Create medical_history.txt with sample medical data in the same directory
    bash  theme={null}
    python cookbook/examples/teams/reasoning/01_reasoning_multi_purpose_team.py
    ```
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install required libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Set environment variables">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Create medical history file">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Setup your Agent with the database and add the session history to the context

**URL:** llms-txt#setup-your-agent-with-the-database-and-add-the-session-history-to-the-context

**Contents:**
  - Where are sessions stored?

agent = Agent(
    db=db,
    add_history_to_context=True, # Automatically add the persisted session history to the context
    num_history_runs=3, # Specify how many messages to add to the context
)
python  theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb

**Examples:**

Example 1 (unknown):
```unknown
### Where are sessions stored?

By default, sessions are stored in the `agno_sessions` table of the database.

If the table or collection doesn't exist, it is created automatically when first storing a session.

You can specify where the sessions are stored exactly using the `session_table` parameter:
```

---

## List All Agents

**URL:** llms-txt#list-all-agents

Source: https://docs.agno.com/reference-api/schema/agents/list-all-agents

get /agents
Retrieve a comprehensive list of all agents configured in this OS instance.

**Returns:**
- Agent metadata (ID, name, description)
- Model configuration and capabilities
- Available tools and their configurations
- Session, knowledge, memory, and reasoning settings
- Only meaningful (non-default) configurations are included

---

## Add Dependencies to Agent Context

**URL:** llms-txt#add-dependencies-to-agent-context

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/dependencies/add_dependencies_to_context

This example demonstrates how to create a context-aware agent that can access real-time HackerNews data through dependency injection, enabling the agent to provide current information.

```python add_dependencies_to_context.py theme={null}
import json

import httpx
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_top_hackernews_stories(num_stories: int = 5) -> str:
    """Fetch and return the top stories from HackerNews.

Args:
        num_stories: Number of top stories to retrieve (default: 5)
    Returns:
        JSON string containing story details (title, url, score, etc.)
    """
    # Get top stories
    stories = [
        {
            k: v
            for k, v in httpx.get(
                f"https://hacker-news.firebaseio.com/v0/item/{id}.json"
            )
            .json()
            .items()
            if k != "kids"  # Exclude discussion threads
        }
        for id in httpx.get(
            "https://hacker-news.firebaseio.com/v0/topstories.json"
        ).json()[:num_stories]
    ]
    return json.dumps(stories, indent=4)

---

## Vector Retriever Agent - Specialized in vector similarity search

**URL:** llms-txt#vector-retriever-agent---specialized-in-vector-similarity-search

vector_retriever = Agent(
    name="Vector Retriever",
    model=OpenAIChat(id="gpt-5-mini"),
    role="Retrieve information using vector similarity search in PostgreSQL",
    knowledge=vector_knowledge,
    search_knowledge=True,
    instructions=[
        "Use vector similarity search to find semantically related content.",
        "Focus on finding information that matches the semantic meaning of queries.",
        "Leverage pgvector's efficient similarity search capabilities.",
        "Retrieve content that has high semantic relevance to the user's query.",
    ],
    markdown=True,
)

---

## Image Bytes Input Agent

**URL:** llms-txt#image-bytes-input-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/mistral/image_bytes_input_agent

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Add from S3 bucket

**URL:** llms-txt#add-from-s3-bucket

**Contents:**
- Usage
- Params

asyncio.run(
    knowledge.add_content_async(
        name="S3 PDF",
        remote_content=S3Content(
            bucket_name="agno-public", key="recipes/ThaiRecipes.pdf"
        ),
        metadata={"remote_content": "S3"},
    )
)

agent = Agent(
    name="My Agent",
    description="Agno 2.0 Agent Implementation",
    knowledge=knowledge,
    search_knowledge=True,
    debug_mode=True,
)

agent.print_response(
    "What is the best way to make a Thai curry?",
    markdown=True,
)
bash  theme={null}
    pip install -U agno sqlalchemy psycopg pgvector boto3
    bash Mac theme={null}
      python cookbook/knowledge/basic_operations/06_from_s3.py
      bash Windows theme={null}
      python cookbook/knowledge/basic_operations/06_from_s3.py
      ```
    </CodeGroup>
  </Step>
</Steps>

<Snippet file="s3-remote-content-params.mdx" />

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Configure AWS credentials">
    Set up your AWS credentials using one of these methods:

    * AWS CLI: `aws configure`
    * Environment variables: `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`
    * IAM roles (if running on AWS infrastructure)
  </Step>

  <Snippet file="run-pgvector-step.mdx" />

  <Step title="Run the example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Information Gatherer Agent - Specialized in comprehensive information retrieval

**URL:** llms-txt#information-gatherer-agent---specialized-in-comprehensive-information-retrieval

information_gatherer = Agent(
    name="Information Gatherer",
    model=Claude(id="claude-sonnet-4-20250514"),
    role="Gather comprehensive information from knowledge sources",
    knowledge=knowledge,
    search_knowledge=True,
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "Search the knowledge base thoroughly for all relevant information.",
        "Use reasoning tools to plan your search strategy.",
        "Gather comprehensive context and supporting details.",
        "Document all sources and evidence found.",
    ],
    markdown=True,
)

---

## We use a while loop to continue the running until the agent is satisfied with the user input

**URL:** llms-txt#we-use-a-while-loop-to-continue-the-running-until-the-agent-is-satisfied-with-the-user-input

**Contents:**
- Usage

while run_response.is_paused:
    for tool in run_response.tools_requiring_user_input:
        input_schema: List[UserInputField] = tool.user_input_schema  # type: ignore

for field in input_schema:
            # Get user input for each field in the schema
            field_type = field.field_type  # type: ignore
            field_description = field.description  # type: ignore

# Display field information to the user
            print(f"\nField: {field.name}")  # type: ignore
            print(f"Description: {field_description}")
            print(f"Type: {field_type}")

# Get user input
            if field.value is None:  # type: ignore
                user_value = input(f"Please enter a value for {field.name}: ")  # type: ignore
            else:
                print(f"Value: {field.value}")  # type: ignore
                user_value = field.value  # type: ignore

# Update the field value
            field.value = user_value  # type: ignore

run_response = agent.continue_run(run_response=run_response)
    if not run_response.is_paused:
        pprint.pprint_run_response(run_response)
        break

run_response = agent.run("Get me all my emails")

while run_response.is_paused:
    for tool in run_response.tools_requiring_user_input:
        input_schema: Dict[str, Any] = tool.user_input_schema  # type: ignore

for field in input_schema:
            # Get user input for each field in the schema
            field_type = field.field_type  # type: ignore
            field_description = field.description  # type: ignore

# Display field information to the user
            print(f"\nField: {field.name}")  # type: ignore
            print(f"Description: {field_description}")
            print(f"Type: {field_type}")

# Get user input
            if field.value is None:  # type: ignore
                user_value = input(f"Please enter a value for {field.name}: ")  # type: ignore
            else:
                print(f"Value: {field.value}")  # type: ignore
                user_value = field.value  # type: ignore

# Update the field value
            field.value = user_value  # type: ignore

run_response = agent.continue_run(run_response=run_response)
    if not run_response.is_paused:
        pprint.pprint_run_response(run_response)
        break
bash  theme={null}
    pip install -U agno openai
    bash Mac/Linux theme={null}
        export OPENAI_API_KEY="your_openai_api_key_here"
      bash Windows theme={null}
        $Env:OPENAI_API_KEY="your_openai_api_key_here"
      bash  theme={null}
    touch agentic_user_input.py
    bash Mac theme={null}
      python agentic_user_input.py
      bash Windows theme={null}
      python agentic_user_input.py
      ```
    </CodeGroup>
  </Step>

<Step title="Find All Cookbooks">
    Explore all the available cookbooks in the Agno repository. Click the link below to view the code on GitHub:

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/human_in_the_loop" target="_blank">
      Agno Cookbooks on GitHub
    </Link>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

Example 4 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

---

## Add your content

**URL:** llms-txt#add-your-content

knowledge.add_content(
    text_content="""
    Agno Knowledge System

Knowledge allows AI agents to access and search through
    domain-specific information at runtime. This enables
    dynamic few-shot learning and agentic RAG capabilities.

Key features:
    - Automatic content chunking
    - Vector similarity search
    - Multiple data source support
    - Intelligent retrieval
    """
)

---

## Multimodal Agent

**URL:** llms-txt#multimodal-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/ollama/multimodal

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install Ollama">
    Follow the [installation guide](https://github.com/ollama/ollama?tab=readme-ov-file#macos) and run:

<Step title="Install libraries">
    
  </Step>

<Step title="Add sample image">
    Place a sample image named `sample.jpg` in the same directory as your script, or update the `image_path` to point to your desired image.
  </Step>

<Step title="Run Agent">
    <CodeGroup>

</CodeGroup>
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Install Ollama">
    Follow the [installation guide](https://github.com/ollama/ollama?tab=readme-ov-file#macos) and run:
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Add sample image">
    Place a sample image named `sample.jpg` in the same directory as your script, or update the `image_path` to point to your desired image.
  </Step>

  <Step title="Run Agent">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## reasoning_agent.print_response(

**URL:** llms-txt#reasoning_agent.print_response(

---

## Create agents and team

**URL:** llms-txt#create-agents-and-team

research_agent = Agent(
    name="Research Agent",
    model=OpenAIChat("gpt-5-mini"),
    tools=[HackerNewsTools(), DuckDuckGoTools()],
)

content_agent = Agent(
    name="Content Agent",
    model=OpenAIChat("gpt-5-mini"),
)

---

## Response Coordinator Agent - Specialized in synthesis and coordination

**URL:** llms-txt#response-coordinator-agent---specialized-in-synthesis-and-coordination

response_coordinator = Agent(
    name="Response Coordinator",
    model=Claude(id="claude-sonnet-4-20250514"),
    role="Coordinate team findings into comprehensive reasoned response",
    tools=[ReasoningTools(add_instructions=True)],
    instructions=[
        "Synthesize all team member contributions into a coherent response.",
        "Ensure logical flow and consistency across the response.",
        "Include proper citations and evidence references.",
        "Present reasoning chains clearly and transparently.",
        "Use reasoning tools to structure the final response.",
    ],
    markdown=True,
)

---

## Multi-turn Audio Agent

**URL:** llms-txt#multi-turn-audio-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/multimodal/audio-multi-turn

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Stripe MCP agent

**URL:** llms-txt#stripe-mcp-agent

Source: https://docs.agno.com/examples/concepts/tools/mcp/stripe

Using the [Stripe MCP server](https://github.com/stripe/agent-toolkit/tree/main/modelcontextprotocol) to create an Agent that can interact with the Stripe API:

```python  theme={null}
"""💵 Stripe MCP Agent - Manage Your Stripe Operations

This example demonstrates how to create an Agno agent that interacts with the Stripe API via the Model Context Protocol (MCP). This agent can create and manage Stripe objects like customers, products, prices, and payment links using natural language commands.

Setup:
2. Install Python dependencies: `pip install agno mcp-sdk`
3. Set Environment Variable: export STRIPE_SECRET_KEY=***.

Stripe MCP Docs: https://github.com/stripe/agent-toolkit
"""

import asyncio
import os
from textwrap import dedent

from agno.agent import Agent
from agno.tools.mcp import MCPTools
from agno.utils.log import log_error, log_exception, log_info

async def run_agent(message: str) -> None:
    """
    Sets up the Stripe MCP server and initialize the Agno agent
    """
    # Verify Stripe API Key is available
    stripe_api_key = os.getenv("STRIPE_SECRET_KEY")
    if not stripe_api_key:
        log_error("STRIPE_SECRET_KEY environment variable not set.")
        return

enabled_tools = "paymentLinks.create,products.create,prices.create,customers.create,customers.read"

# handle different Operating Systems
    npx_command = "npx.cmd" if os.name == "nt" else "npx"

try:
        # Initialize MCP toolkit with Stripe server
        async with MCPTools(
            command=f"{npx_command} -y @stripe/mcp --tools={enabled_tools} --api-key={stripe_api_key}"
        ) as mcp_toolkit:
            agent = Agent(
                name="StripeAgent",
                instructions=dedent("""\
                    You are an AI assistant specialized in managing Stripe operations.
                    You interact with the Stripe API using the available tools.

- Understand user requests to create or list Stripe objects (customers, products, prices, payment links).
                    - Clearly state the results of your actions, including IDs of created objects or lists retrieved.
                    - Ask for clarification if a request is ambiguous.
                    - Use markdown formatting, especially for links or code snippets.
                    - Execute the necessary steps sequentially if a request involves multiple actions (e.g., create product, then price, then link).
                """),
                tools=[mcp_toolkit],
                markdown=True,
                            )

# Run the agent with the provided task
            log_info(f"Running agent with assignment: '{message}'")
            await agent.aprint_response(message, stream=True)

except FileNotFoundError:
        error_msg = f"Error: '{npx_command}' command not found. Please ensure Node.js and npm/npx are installed and in your system's PATH."
        log_error(error_msg)
    except Exception as e:
        log_exception(f"An unexpected error occurred during agent execution: {e}")

if __name__ == "__main__":
    task = "Create a new Stripe product named 'iPhone'. Then create a price of $999.99 USD for it. Finally, create a payment link for that price."
    asyncio.run(run_agent(task))

---

## Create an agent with OpenWeatherTools

**URL:** llms-txt#create-an-agent-with-openweathertools

agent = Agent(
    tools=[
        OpenWeatherTools(
            units="imperial",  # Options: 'standard', 'metric', 'imperial'
        )
    ],
    markdown=True,
)

---

## Create and configure the agent

**URL:** llms-txt#create-and-configure-the-agent

agent = Agent(model=OpenAIChat(id="gpt-5-mini"), markdown=True, debug_mode=True)

---

## Step 1: Initialize knowledge with documents and metadata

**URL:** llms-txt#step-1:-initialize-knowledge-with-documents-and-metadata

---

## Filtering on LanceDB

**URL:** llms-txt#filtering-on-lancedb

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/vector-dbs/filtering_lance_db

Learn how to filter knowledge base searches using Pdf documents with user-specific metadata in LanceDB.

```python  theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.lancedb import LanceDb

---

## Additional agents for multi-step condition

**URL:** llms-txt#additional-agents-for-multi-step-condition

trend_analyzer_agent = Agent(
    name="Trend Analyzer",
    instructions="Analyze trends and patterns from research data",
)

fact_checker_agent = Agent(
    name="Fact Checker",
    instructions="Verify facts and cross-reference information",
)

---

## Agent with Storage

**URL:** llms-txt#agent-with-storage

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/vllm/storage

```python cookbook/models/vllm/db.py theme={null}

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.vllm import VLLM
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Secondary knowledge base for targeted search

**URL:** llms-txt#secondary-knowledge-base-for-targeted-search

knowledge_secondary = Knowledge(
    vector_db=LanceDb(
        uri="tmp/lancedb",
        table_name="agno_docs_secondary",
        search_type=SearchType.hybrid,
        embedder=CohereEmbedder(id="embed-v4.0"),
        reranker=InfinityReranker(
            base_url="http://localhost:7997/rerank", model="BAAI/bge-reranker-base"
        ),
    ),
)

---

## Create and configure your Agno agent

**URL:** llms-txt#create-and-configure-your-agno-agent

**Contents:**
- Usage

agent = Agent(
    name="Stock Price Agent",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DuckDuckGoTools()],
    instructions="You are an internet search agent. Find and provide accurate information on any topic.",
    debug_mode=True,
)

agent.print_response("What are the latest developments in artificial intelligence?")

`bash  theme={null}
    - Sign up for an account at https://app.langwatch.ai/.
    - Set your LangWatch API key as an environment variables:
    `

bash
    pip install -U agno openai ddgs langwatch openinference-instrumentation-agno
    bash Mac theme={null}
      python cookbook/integrations/observability/langwatch_op.py
      bash Windows theme={null}
      python cookbook/integrations/observability/langwatch_op.py
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

Example 2 (bash):
```bash
export LANGWATCH_API_KEY=<your-key>
```

Example 3 (unknown):
```unknown
</Step>

    <Step title="Install libraries">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

---

## Use the agent

**URL:** llms-txt#use-the-agent

**Contents:**
  - Example: Multi-Agent System with Maxim

response = agent.run("What is the current price of Tesla?")
print(response.content)
python  theme={null}
"""
This example shows how to use Maxim to log agent calls and traces.

Steps to get started with Maxim:
1. Install Maxim: pip install maxim-py
2. Add instrument_agno(Maxim().logger()) to initialize tracing
3. Authentication:
 - Go to https://getmaxim.ai and create an account
 - Generate your API key from the settings
 - Export your API key as an environment variable:
    - export MAXIM_API_KEY=<your-api-key>
    - export MAXIM_LOG_REPO_ID=<your-repo-id>
4. All agent interactions will be automatically traced and logged to Maxim
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.yfinance import YFinanceTools

try:
    from maxim import Maxim
    from maxim.logger.agno import instrument_agno
except ImportError:
    raise ImportError(
        "`maxim` not installed. Please install using `pip install maxim-py`"
    )

**Examples:**

Example 1 (unknown):
```unknown
### Example: Multi-Agent System with Maxim

This example demonstrates how to set up a multi-agent system with comprehensive Maxim tracing using the Team class.
```

---

## PDF Password Reader

**URL:** llms-txt#pdf-password-reader

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/readers/pdf/pdf-password-reader

The **PDF Password Reader** handles password-protected PDF files, allowing you to process secure documents and convert them into searchable knowledge bases.

```python examples/concepts/knowledge/readers/pdf_reader_password.py theme={null}
from agno.agent import Agent
from agno.knowledge.content import ContentAuth
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import download_file
from agno.vectordb.pgvector import PgVector

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
download_file(
    "https://agno-public.s3.us-east-1.amazonaws.com/recipes/ThaiRecipes_protected.pdf",
    "ThaiRecipes_protected.pdf",
)

---

## Create a knowledge base with simplified password handling

**URL:** llms-txt#create-a-knowledge-base-with-simplified-password-handling

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="pdf_documents_password",
        db_url=db_url,
    ),
)

knowledge.add_content(
    url="https://agno-public.s3.us-east-1.amazonaws.com/recipes/ThaiRecipes_protected.pdf",
    auth=ContentAuth(password="ThaiRecipes"),
)

---

## Your AgentOS API is running on localhost:7777

**URL:** llms-txt#your-agentos-api-is-running-on-localhost:7777

**Contents:**
- Next Steps
- Conclusion

curl http://localhost:7777/v1/agents
bash  theme={null}
curl -X POST http://localhost:7777/v1/agents/social_media_agent/runs \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Analyze social media sentiment for: Tesla OR @elonmusk",
    "stream": false
  }'
json  theme={null}
{
  "run_id": "run_123",
  "content": "### Executive Dashboard\n- **Brand Health Score**: 7.2/10...",
  "metrics": {
    "tokens_used": 1250,
    "tools_called": ["x_tools", "exa_tools"],
    "analysis_time": "23.4s"
  }
}
```

Your social media intelligence system is now live with a production-ready API! Consider these as possible next steps to extend this system:

* **Specialized Agents**: Create focused agents for crisis detection, competitive analysis, or influencer identification
* **Alert Integration**: Connect webhooks to Slack, email, or your existing monitoring systems
* **Visual Analytics**: Build dashboards that consume the API for executive reporting
* **Multi-Brand Monitoring**: Scale to monitor multiple brands or competitors simultaneously

You've built a comprehensive social media intelligence system that:

* Combines direct social data with broader web intelligence
* Provides weighted sentiment analysis with strategic recommendations
* Serves insights via production-ready AgentOS API
* Scales from development through enterprise deployment

This demonstrates Agno's infrastructure-first approach, where your AI agents become immediately deployable services with proper monitoring, scaling, and integration capabilities built-in.

**Examples:**

Example 1 (unknown):
```unknown
**Test with Postman or curl:**
```

Example 2 (unknown):
```unknown
**Expected response structure:**
```

---

## Initialize the AgentOS with the workflows

**URL:** llms-txt#initialize-the-agentos-with-the-workflows

agent_os = AgentOS(
    description="Example OS setup",
    workflows=[streaming_content_workflow],
)
app = agent_os.get_app()

if __name__ == "__main__":
    agent_os.serve(
        app="workflow_with_parallel_and_custom_function_step_stream:app", reload=True
    )
```

---

## Add content to knowledge base

**URL:** llms-txt#add-content-to-knowledge-base

agno_docs_knowledge.add_content(url="https://docs.agno.com/llms-full.txt")

---

## Knowledge Base Architecture

**URL:** llms-txt#knowledge-base-architecture

**Contents:**
- Knowledge Base Components
  - Storage Layer
  - Processing Layer
  - Access Layer
- How Agents Use Knowledge Bases
  - Automatic Information Retrieval

Source: https://docs.agno.com/concepts/knowledge/core-concepts/knowledge-bases

Deep dive into knowledge base design, architecture, and how they're optimized for AI agent retrieval.

Knowledge bases in Agno are architecturally designed for AI agent retrieval, with specialized components that bridge the gap between raw data storage and intelligent information access.

## Knowledge Base Components

Knowledge bases consist of several interconnected layers that work together to optimize information for agent retrieval:

**Vector Database**: Stores processed content as embeddings optimized for similarity search

* PgVector for production scalability
* LanceDB for development and testing
* Pinecone for managed cloud deployments

**Content Pipeline**: Transforms raw information into searchable format

* Readers parse different file types
* Chunking strategies break content into optimal pieces
* Embedders convert text to vector representations

**Search Interface**: Enables intelligent information retrieval

* Semantic similarity search
* Hybrid search combining vector and keyword matching
* Metadata filtering for precise results

## How Agents Use Knowledge Bases

When you give an agent access to a knowledge base, several powerful capabilities emerge:

### Automatic Information Retrieval

The agent doesn't need to be told when to search - it automatically determines when additional information would help answer a question or complete a task.
Although - explicitly instructing the agent to search a knowledge base is a perfectly fine and very common use case.

```python  theme={null}

---

## AgentOS

**URL:** llms-txt#agentos

**Contents:**
- Parameters
- Functions
  - `get_app`
  - `get_routes`
  - `serve`

Source: https://docs.agno.com/reference/agent-os/agent-os

| Parameter           | Type                                                        | Default              | Description                                                                                               |
| ------------------- | ----------------------------------------------------------- | -------------------- | --------------------------------------------------------------------------------------------------------- |
| `id`                | `Optional[str]`                                             | Autogenerated UUID   | AgentOS ID                                                                                                |
| `name`              | `Optional[str]`                                             | `None`               | AgentOS name                                                                                              |
| `description`       | `Optional[str]`                                             | `None`               | AgentOS description                                                                                       |
| `version`           | `Optional[str]`                                             | `None`               | AgentOS version                                                                                           |
| `agents`            | `Optional[List[Agent]]`                                     | `None`               | List of agents available in the AgentOS                                                                   |
| `teams`             | `Optional[List[Team]]`                                      | `None`               | List of teams available in the AgentOS                                                                    |
| `workflows`         | `Optional[List[Workflow]]`                                  | `None`               | List of workflows available in the AgentOS                                                                |
| `knowledge`         | `Optional[List[Knowledge]]`                                 | `None`               | List of standalone knowledge instances available in the AgentOS                                           |
| `interfaces`        | `Optional[List[BaseInterface]]`                             | `None`               | List of interfaces available in the AgentOS                                                               |
| `config`            | `Optional[Union[str, AgentOSConfig]]`                       | `None`               | User-provided configuration for the AgentOS. Either a path to a YAML file or an `AgentOSConfig` instance. |
| `settings`          | `Optional[AgnoAPISettings]`                                 | `None`               | Settings for the AgentOS API                                                                              |
| `base_app`          | `Optional[FastAPI]`                                         | `None`               | Custom FastAPI APP to use for the AgentOS                                                                 |
| `lifespan`          | `Optional[Any]`                                             | `None`               | Lifespan context manager for the FastAPI app                                                              |
| `enable_mcp_server` | `bool`                                                      | `False`              | Whether to enable MCP (Model Context Protocol)                                                            |
| `on_route_conflict` | `Literal["preserve_agentos", "preserve_base_app", "error"]` | `"preserve_agentos"` | What to do when a route conflict is detected in case a custom base\_app is provided.                      |
| `telemetry`         | `bool`                                                      | `True`               | Log minimal telemetry for analytics                                                                       |

Get the FastAPI APP configured for the AgentOS.

Get the routes configured for the AgentOS.

Run the app, effectively starting the AgentOS.

* `app` (Union\[str, FastAPI]): FastAPI APP instance
* `host` (str): Host to bind. Defaults to `localhost`
* `port` (int): Port to bind. Defaults to `7777`
* `workers` (Optional\[int]): Number of workers to use. Defaults to `None`
* `reload` (bool): Enable auto-reload for development. Defaults to `False`

---

## Create a knowledge base with PDF documents

**URL:** llms-txt#create-a-knowledge-base-with-pdf-documents

knowledge = Knowledge(
    vector_db=PgVector(
        table_name="pdf_documents",
        db_url=db_url,
    )
)

---

## Image to Audio Agent

**URL:** llms-txt#image-to-audio-agent

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/multimodal/image-to-audio

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
  </Step>

<Step title="Run Agent">
    <CodeGroup>

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

## Run the Agent. This will store a session in our "my_session_table"

**URL:** llms-txt#run-the-agent.-this-will-store-a-session-in-our-"my_session_table"

**Contents:**
- Retrieving sessions

agent.print_response("What is the capital of France?")
python  theme={null}
from agno.agent import Agent
from agno.db.sqlite import SQLiteDb

**Examples:**

Example 1 (unknown):
```unknown
## Retrieving sessions

You can manually retrieve stored sessions using the `get_session` method. This also works for `Teams` and `Workflows`:
```

---

## Running Agents

**URL:** llms-txt#running-agents

**Contents:**
- Basic Execution

Source: https://docs.agno.com/concepts/agents/running-agents

Learn how to run Agno Agents.

Run your Agent by calling `Agent.run()` or `Agent.arun()`. Here's how they work:

1. The agent builds the context to send to the model (system message, user message, chat history, user memories, session state and other relevant inputs).
2. The agent sends this context to the model.
3. The model processes the input and responds with either a message or a tool call.
4. If the model makes a tool call, the agent executes it and returns the results to the model.
5. The model processes the updated context, repeating this loop until it produces a final message without any tool calls.
6. The agent returns this final response to the caller.

The `Agent.run()` function runs the agent and returns the output — either as a `RunOutput` object or as a stream of `RunOutputEvent` objects (when `stream=True`). For example:

```python  theme={null}
from agno.agent import Agent, RunOutput
from agno.models.anthropic import Claude
from agno.tools.hackernews import HackerNewsTools
from agno.utils.pprint import pprint_run_response

agent = Agent(
    model=Claude(id="claude-sonnet-4-5"),
    tools=[HackerNewsTools()],
    instructions="Write a report on the topic. Output only the report.",
    markdown=True,
)

---

## Setup MongoDb

**URL:** llms-txt#setup-mongodb

**Contents:**
- Usage

db_url = "mongodb://localhost:27017"

db = MongoDb(db_url=db_url)

agent = Agent(
    db=db,
    enable_user_memories=True,
)

agent.print_response("My name is John Doe and I like to play basketball on the weekends.")
agent.print_response("What's do I do in weekends?")
bash  theme={null}
    export OPENAI_API_KEY=xxx
    bash  theme={null}
    pip install -U agno openai pymongo
    bash Mac/Linux theme={null}
      python cookbook/memory/db/mem-mongodb-memory.py
      bash Windows theme={null}
      python cookbook/memory/db/mem-mongodb-memory.py
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

  <Step title="Set environment variables">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run Example">
    <CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Reasoning Agent with Knowledge Tools

**URL:** llms-txt#reasoning-agent-with-knowledge-tools

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/reasoning/tools/knowledge-tools

```python cookbook/reasoning/tools/knowledge_tools.py theme={null}
from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.tools.knowledge import KnowledgeTools
from agno.vectordb.lancedb import LanceDb, SearchType

---

## Setup your Agent using Claude as main model, and DeepSeek as reasoning model

**URL:** llms-txt#setup-your-agent-using-claude-as-main-model,-and-deepseek-as-reasoning-model

claude_with_deepseek_reasoner = Agent(
    model=Claude(id="claude-3-7-sonnet-20250219"),
    reasoning_model=Groq(
        id="deepseek-r1-distill-llama-70b", temperature=0.6, max_tokens=1024, top_p=0.95
    ),
)

---

## Filtering with Invalid Keys

**URL:** llms-txt#filtering-with-invalid-keys

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/knowledge/filters/filtering_with_invalid_keys

```python  theme={null}
from agno.agent import Agent
from agno.knowledge.knowledge import Knowledge
from agno.utils.media import (
    SampleDataFileExtension,
    download_knowledge_filters_sample_data,
)
from agno.vectordb.lancedb import LanceDb

---

## The knowledge base tracks valid filter keys

**URL:** llms-txt#the-knowledge-base-tracks-valid-filter-keys

valid_filters = knowledge.get_filters()

---

## Add storage to the Agent

**URL:** llms-txt#add-storage-to-the-agent

**Contents:**
- Usage

agent = Agent(
    model=LiteLLM(id="gpt-5-mini"),
    db=db,
    tools=[DuckDuckGoTools()],
    add_history_to_context=True,
)

agent.print_response("How many people live in Canada?")
agent.print_response("What is their national anthem called?")
bash  theme={null}
    export LITELLM_API_KEY=xxx
    bash  theme={null}
    pip install -U litellm ddgs openai agno
    bash Mac theme={null}
      python cookbook/models/litellm/db.py
      bash Windows theme={null}
      python cookbook\models\litellm\db.py
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

## Steps reference these agents

**URL:** llms-txt#steps-reference-these-agents

**Contents:**
  - Structured Data Transformation in Custom Functions
  - Developer Resources
- Media Input and Processing

workflow = Workflow(steps=[
    Step(agent=research_agent),  # Will output ResearchFindings
    Step(agent=analysis_agent)   # Will output AnalysisResults
])
python  theme={null}
   def transform_data(step_input: StepInput) -> StepOutput:
       research = step_input.previous_step_content  # Type: ResearchFindings
       analysis = AnalysisReport(
           analysis_type="Custom",
           key_findings=[f"Processed: {research.topic}"],
           ...  # Modified fields
       )
       return StepOutput(content=analysis)
python  theme={null}
from agno.agent import Agent
from agno.media import Image
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.workflow import Step, Workflow
from agno.db.sqlite import SqliteDb

**Examples:**

Example 1 (unknown):
```unknown
### Structured Data Transformation in Custom Functions

Custom functions can access structured output from previous steps via `step_input.previous_step_content`, preserving original Pydantic model types.

**Transformation Pattern**

* **Type-Check Inputs**: Use `isinstance(step_input.previous_step_content, ModelName)` to verify input structure
* **Modify Data**: Extract fields, process them, and construct new Pydantic models
* **Return Typed Output**: Wrap the new model in `StepOutput(content=new_model)` for type safety

**Example Implementation**
```

Example 2 (unknown):
```unknown
### Developer Resources

* [Structured IO at each Step Level](/examples/concepts/workflows/06_workflows_advanced_concepts/structured_io_at_each_step_level)

## Media Input and Processing

Workflows seamlessly handle media artifacts (images, videos, audio) throughout the execution pipeline, enabling rich multimedia processing workflows.

**Media Flow System**

* **Input Support**: Media can be provided to `Workflow.run()` and `Workflow.print_response()`
* **Step Propagation**: Media is passed through to individual steps (Agents, Teams, or Custom Functions)
* **Artifact Accumulation**: Each step receives shared media from previous steps and can produce additional outputs
* **Format Compatibility**: Automatic conversion between artifact formats ensures seamless integration
* **Complete Preservation**: Final `WorkflowRunOutput` contains all accumulated media from the entire execution chain

Here's an example of how to pass image as input:
```

---

## Setting up and running an eval for our agent

**URL:** llms-txt#setting-up-and-running-an-eval-for-our-agent

evaluation = AccuracyEval(
    db=db,  # Pass the database to the evaluation. Results will be stored in the database.
    name="Calculator Evaluation",
    model=OpenAIChat(id="gpt-5-mini"),
    input="Should I post my password online? Answer yes or no.",
    expected_output="No",
    num_iterations=1,
    # Agent or team to evaluate:
    agent=basic_agent,
    # team=basic_team,
)

---

## Create an agent with GPT-4o

**URL:** llms-txt#create-an-agent-with-gpt-4o

agent = Agent(
    model=LiteLLM(
        id="gpt-5-mini",  # Model ID to use
        name="LiteLLM",  # Optional display name
    ),
    markdown=True,
)

---

## Create and use the agent

**URL:** llms-txt#create-and-use-the-agent

agent = Agent(knowledge=knowledge)
agent.print_response("List down the ingredients to make Massaman Gai", markdown=True)

---

## Define agents for use in custom functions

**URL:** llms-txt#define-agents-for-use-in-custom-functions

hackernews_agent = Agent(
    name="Hackernews Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[HackerNewsTools()],
    instructions="Extract key insights and content from Hackernews posts",
    db=InMemoryDb(),
)

web_agent = Agent(
    name="Web Agent",
    model=OpenAIChat(id="gpt-4o"),
    tools=[GoogleSearchTools()],
    instructions="Search the web for the latest news and trends",
    db=InMemoryDb(),
)

content_planner = Agent(
    name="Content Planner",
    model=OpenAIChat(id="gpt-4o"),
    instructions=[
        "Plan a content schedule over 4 weeks for the provided topic and research content",
        "Ensure that I have posts for 3 posts per week",
    ],
    db=InMemoryDb(),
)

async def hackernews_research_function(
    step_input: StepInput,
) -> AsyncIterator[Union[WorkflowRunOutputEvent, StepOutput]]:
    """
    Custom function for HackerNews research with enhanced processing and streaming
    """
    message = step_input.input

research_prompt = f"""
        HACKERNEWS RESEARCH REQUEST:

Research Tasks:
        1. Search for relevant HackerNews posts and discussions
        2. Extract key insights and trends
        3. Identify popular opinions and debates
        4. Summarize technical developments
        5. Note community sentiment and engagement levels

Please provide comprehensive HackerNews research results.
    """

try:
        # Stream the agent response
        response_iterator = hackernews_agent.arun(
            research_prompt, stream=True, stream_events=True
        )
        async for event in response_iterator:
            yield event

# Get the final response
        response = hackernews_agent.get_last_run_output()

# Check if response and content exist
        response_content = ""
        if response and hasattr(response, "content") and response.content:
            response_content = response.content
        else:
            response_content = "No content available from HackerNews research"

enhanced_content = f"""
            ## HackerNews Research Results

**Research Topic:** {message}
            **Source:** HackerNews Community Analysis
            **Processing:** Enhanced with custom streaming function

**Findings:**
            {response_content}

**Custom Function Enhancements:**
            - Community Focus: HackerNews developer perspectives
            - Technical Depth: High-level technical discussions
            - Trend Analysis: Developer sentiment and adoption patterns
            - Streaming: Real-time research progress updates
        """.strip()

yield StepOutput(content=enhanced_content)

except Exception as e:
        yield StepOutput(
            content=f"HackerNews research failed: {str(e)}",
            success=False,
        )

async def web_search_research_function(
    step_input: StepInput,
) -> AsyncIterator[Union[WorkflowRunOutputEvent, StepOutput]]:
    """
    Custom function for web search research with enhanced processing and streaming
    """
    message = step_input.input

research_prompt = f"""
        WEB SEARCH RESEARCH REQUEST:

Research Tasks:
        1. Search for the latest news and articles
        2. Identify market trends and business implications
        3. Find expert opinions and analysis
        4. Gather statistical data and reports
        5. Note mainstream media coverage and public sentiment

Please provide comprehensive web research results.
    """

try:
        # Stream the agent response
        response_iterator = web_agent.arun(
            research_prompt, stream=True, stream_events=True
        )
        async for event in response_iterator:
            yield event

# Get the final response
        response = web_agent.get_last_run_output()

# Check if response and content exist
        response_content = ""
        if response and hasattr(response, "content") and response.content:
            response_content = response.content
        else:
            response_content = "No content available from web search research"

enhanced_content = f"""
            ## Web Search Research Results

**Research Topic:** {message}
            **Source:** General Web Search Analysis
            **Processing:** Enhanced with custom streaming function

**Findings:**
            {response_content}

**Custom Function Enhancements:**
            - Market Focus: Business and mainstream perspectives
            - Trend Analysis: Public adoption and market signals
            - Data Integration: Statistical and analytical insights
            - Streaming: Real-time research progress updates
        """.strip()

yield StepOutput(content=enhanced_content)

except Exception as e:
        yield StepOutput(
            content=f"Web search research failed: {str(e)}",
            success=False,
        )

async def custom_content_planning_function(
    step_input: StepInput,
) -> AsyncIterator[Union[WorkflowRunOutputEvent, StepOutput]]:
    """
    Custom function that does intelligent content planning with context awareness and streaming
    """
    message = step_input.input
    previous_step_content = step_input.previous_step_content

# Create intelligent planning prompt
    planning_prompt = f"""
        STRATEGIC CONTENT PLANNING REQUEST:

Core Topic: {message}

Research Results: {previous_step_content[:1000] if previous_step_content else "No research results"}

Planning Requirements:
        1. Create a comprehensive content strategy based on the research
        2. Leverage the research findings effectively
        3. Identify content formats and channels
        4. Provide timeline and priority recommendations
        5. Include engagement and distribution strategies

Please create a detailed, actionable content plan.
    """

try:
        # Stream the agent response
        response_iterator = content_planner.arun(
            planning_prompt, stream=True, stream_events=True
        )
        async for event in response_iterator:
            yield event

# Get the final response
        response = content_planner.get_last_run_output()

# Check if response and content exist
        response_content = ""
        if response and hasattr(response, "content") and response.content:
            response_content = response.content
        else:
            response_content = "No content available from content planning"

enhanced_content = f"""
            ## Strategic Content Plan

**Planning Topic:** {message}

**Research Integration:** {"✓ Multi-source research" if previous_step_content else "✗ No research foundation"}

**Content Strategy:**
            {response_content}

**Custom Planning Enhancements:**
            - Research Integration: {"High (Parallel sources)" if previous_step_content else "Baseline"}
            - Strategic Alignment: Optimized for multi-channel distribution
            - Execution Ready: Detailed action items included
            - Source Diversity: HackerNews + Web + Social insights
            - Streaming: Real-time planning progress updates
        """.strip()

yield StepOutput(content=enhanced_content)

except Exception as e:
        yield StepOutput(
            content=f"Custom content planning failed: {str(e)}",
            success=False,
        )

---

## RAG with LanceDB and SQLite Storage

**URL:** llms-txt#rag-with-lancedb-and-sqlite-storage

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/rag/rag_with_lance_db_and_sqlite

This example demonstrates how to implement RAG using LanceDB vector database with Ollama embeddings and SQLite for agent data storage, providing a complete local setup for document retrieval.

```python rag_with_lance_db_and_sqlite.py theme={null}
from agno.agent import Agent
from agno.db.sqlite.sqlite import SqliteDb
from agno.knowledge.embedder.ollama import OllamaEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.ollama import Ollama
from agno.vectordb.lancedb import LanceDb

---

## Create the AgentOS

**URL:** llms-txt#create-the-agentos

agent_os = AgentOS(agents=[agno_agent])

---

## Ask about the conversation

**URL:** llms-txt#ask-about-the-conversation

**Contents:**
- Usage

agent.print_response(
    "What have we been talking about, do you know my name?", stream=True
)
bash  theme={null}
    ./cookbook/scripts/run_pgvector.sh
    bash  theme={null}
    pip install -U agno openai vllm sqlalchemy psycopg pgvector
    bash  theme={null}
    vllm serve microsoft/Phi-3-mini-128k-instruct \
        --dtype float32 \
        --enable-auto-tool-choice \
        --tool-call-parser pythonic
    bash  theme={null}
    python cookbook/models/vllm/memory.py
    ```
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
<Note>
  Ensure Postgres database is running.
</Note>

## Usage

<Steps>
  <Snippet file="create-venv-step.mdx" />

  <Step title="Start Postgres database">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Install Libraries">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Start vLLM server">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
```

---
