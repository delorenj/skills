# Agno - Examples

**Pages:** 188

---

## Workflow with Input Schema Validation

**URL:** llms-txt#workflow-with-input-schema-validation

**Contents:**
- Key Features:

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/workflow_with_input_schema

This example demonstrates **Workflows** support for input schema validation using Pydantic models to ensure type safety and data integrity at the workflow entry point.

This example shows how to use input schema validation in workflows to enforce type safety and data structure validation. By defining an `input_schema` with a Pydantic model, you can ensure that your workflow receives properly structured and validated data before execution begins.

* **Type Safety**: Automatic validation of input data against Pydantic models
* **Structure Validation**: Ensure all required fields are present and correctly typed
* **Clear Contracts**: Define exactly what data your workflow expects
* **Error Prevention**: Catch invalid inputs before workflow execution begins
* **Multiple Input Formats**: Support for Pydantic models and matching dictionaries

```python workflow_with_input_schema.py theme={null}
from typing import List

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow
from pydantic import BaseModel, Field

class DifferentModel(BaseModel):
    name: str

class ResearchTopic(BaseModel):
    """Structured research topic with specific requirements"""

topic: str
    focus_areas: List[str] = Field(description="Specific areas to focus on")
    target_audience: str = Field(description="Who this research is for")
    sources_required: int = Field(description="Number of sources needed", default=5)

---

## Audio Sentiment Analysis Team

**URL:** llms-txt#audio-sentiment-analysis-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/multimodal/audio_sentiment_analysis

This example demonstrates how a team can collaborate to perform sentiment analysis on audio conversations using transcription and sentiment analysis agents working together.

```python cookbook/examples/teams/multimodal/audio_sentiment_analysis.py theme={null}
import requests
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.media import Audio
from agno.models.google import Gemini
from agno.team import Team

transcription_agent = Agent(
    name="Audio Transcriber",
    role="Transcribe audio conversations accurately",
    model=Gemini(id="gemini-2.0-flash-exp"),
    instructions=[
        "Transcribe audio with speaker identification",
        "Maintain conversation structure and flow",
    ],
)

sentiment_analyst = Agent(
    name="Sentiment Analyst",
    role="Analyze emotional tone and sentiment in conversations",
    model=Gemini(id="gemini-2.0-flash-exp"),
    instructions=[
        "Analyze sentiment for each speaker separately",
        "Identify emotional patterns and conversation dynamics",
        "Provide detailed sentiment insights",
    ],
)

---

## Example 1: Adding items (demonstrates role-based delegation)

**URL:** llms-txt#example-1:-adding-items-(demonstrates-role-based-delegation)

print("Example 1: Adding Items to Shopping List")
print("-" * 50)
shopping_team.print_response(
    "Add milk, eggs, and bread to the shopping list", stream=True
)
print(f"Session state: {shopping_team.get_session_state()}")
print()

---

## Team with Exponential Backoff

**URL:** llms-txt#team-with-exponential-backoff

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/other/team_exponential_backoff

This example demonstrates how to configure a team with exponential backoff retry logic. When agents encounter errors or rate limits, the team will automatically retry with increasing delays between attempts.

```python cookbook/examples/teams/basic/team_exponential_backoff.py theme={null}
from agno.agent import Agent
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools

---

## DEMONSTRATION

**URL:** llms-txt#demonstration

---

## Async Events Streaming

**URL:** llms-txt#async-events-streaming

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/workflows/01-basic-workflows/async_events_streaming

This example demonstrates how to stream events from a workflow.

```python async_events_streaming.py theme={null}
import asyncio
from textwrap import dedent
from typing import AsyncIterator

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.run.workflow import WorkflowRunOutputEvent, WorkflowRunEvent
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.types import StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## Enable History for Specific Steps

**URL:** llms-txt#enable-history-for-specific-steps

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/workflow_history/03_enable_history_for_step

This example demonstrates a workflow with history enabled for a specific step.

This example shows how to use the `add_workflow_history` flag to add workflow history to a specific step in the workflow.
In this case we have a workflow with three steps.

* The first step is a research specialist that gathers information on topics.
* The second step is a content creator that writes engaging content.
* The third step is a content publisher that prepares the content for publication.

---

## Demo Phi4

**URL:** llms-txt#demo-phi4

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/ollama/demo_phi4

```python cookbook/models/ollama/demo_phi4.py theme={null}
from agno.agent import Agent, RunOutput  # noqa
from agno.models.ollama import Ollama

agent = Agent(model=Ollama(id="phi4"), markdown=True)

---

## Collaborative Image Generation Team

**URL:** llms-txt#collaborative-image-generation-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/multimodal/generate_image_with_team

This example demonstrates how a team can collaborate to generate high-quality images using a prompt engineer to optimize prompts and an image creator to generate images with DALL-E.

```python cookbook/examples/teams/multimodal/generate_image_with_team.py theme={null}
from typing import Iterator

from agno.agent import Agent, RunOutputEvent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.dalle import DalleTools
from agno.utils.common import dataclass_to_dict
from rich.pretty import pprint

image_generator = Agent(
    name="Image Creator",
    role="Generate images using DALL-E",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[DalleTools()],
    instructions=[
        "Use the DALL-E tool to create high-quality images",
        "Return image URLs in markdown format: `![description](URL)`",
    ],
)

prompt_engineer = Agent(
    name="Prompt Engineer",
    role="Optimize and enhance image generation prompts",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "Enhance user prompts for better image generation results",
        "Consider artistic style, composition, and technical details",
    ],
)

---

## Get sample videos from https://www.pexels.com/search/videos/sample/

**URL:** llms-txt#get-sample-videos-from-https://www.pexels.com/search/videos/sample/

**Contents:**
- Usage

video_path = Path(__file__).parent.joinpath("sample_video.mp4")

agent.print_response("Tell me about this video?", videos=[Video(filepath=video_path)])
bash  theme={null}
    export GOOGLE_API_KEY=xxx
    bash  theme={null}
    pip install -U google-genai agno
    bash Mac theme={null}
      python cookbook/models/google/gemini/video_input_local_file_upload.py
      bash Windows theme={null}
      python cookbook/models/google/gemini/video_input_local_file_upload.py
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

## Router with Loop Steps Workflow

**URL:** llms-txt#router-with-loop-steps-workflow

Source: https://docs.agno.com/examples/concepts/workflows/05_workflows_conditional_branching/router_with_loop_steps

This example demonstrates **Workflows 2.0** advanced pattern combining Router-based intelligent path selection with Loop execution for iterative quality improvement.

This example shows how to create adaptive workflows that select optimal research strategies and execution patterns based on topic complexity.

**When to use**: When different topic types require fundamentally different research
methodologies - some needing simple single-pass research, others requiring iterative
deep-dive analysis. Ideal for content-adaptive workflows where processing complexity
should match content complexity.

```python router_with_loop_steps.py theme={null}
from typing import List

from agno.agent.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.loop import Loop
from agno.workflow.router import Router
from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## Step with function

**URL:** llms-txt#step-with-function

Source: https://docs.agno.com/examples/concepts/workflows/01-basic-workflows/step_with_function

This example demonstrates how to use named steps with custom function executors.

This example demonstrates **Workflows** using named Step objects with custom function
executors. This pattern combines the benefits of named steps with the flexibility of
custom functions, allowing for sophisticated data processing within structured workflow steps.

**When to use**: When you need named step organization but want custom logic that goes
beyond what agents/teams provide. Ideal for complex data processing, multi-step operations,
or when you need to orchestrate multiple agents within a single step.

```python step_with_function.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## Async Team Streaming

**URL:** llms-txt#async-team-streaming

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/streaming/async_team_streaming

This example demonstrates asynchronous streaming responses from a team using specialized agents with financial tools to provide real-time stock information with async streaming output.

```python cookbook/examples/teams/streaming/04_async_team_streaming.py theme={null}
"""
This example demonstrates asynchronous streaming responses from a team.

The team uses specialized agents with financial tools to provide real-time
stock information with async streaming output.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.exa import ExaTools
from agno.utils.pprint import apprint_run_response

---

## Session State In Instructions

**URL:** llms-txt#session-state-in-instructions

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/state/session_state_in_instructions

This example demonstrates how to use session state variables directly in agent instructions. It shows how to initialize session state and reference those variables in the instruction templates.

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

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/state" target="_blank">
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

## Video to Shorts Generation

**URL:** llms-txt#video-to-shorts-generation

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/multimodal/video_to_shorts

This example demonstrates how to analyze a video and automatically generate short-form content segments optimized for platforms like YouTube Shorts and Instagram Reels.

```python video_to_shorts.py theme={null}
"""
1. Install dependencies using: `pip install opencv-python google-geneai sqlalchemy`
2. Install ffmpeg `brew install ffmpeg`
2. Run the script using: `python cookbook/agent_concepts/video_to_shorts.py`
"""

import subprocess
from pathlib import Path

from agno.agent import Agent
from agno.media import Video
from agno.models.google import Gemini
from agno.utils.log import logger

video_path = Path(__file__).parent.joinpath("sample_video.mp4")
output_dir = Path("tmp/shorts")

agent = Agent(
    name="Video2Shorts",
    description="Process videos and generate engaging shorts.",
    model=Gemini(id="gemini-2.0-flash-exp"),
    markdown=True,
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

## AI Image Transformation Team

**URL:** llms-txt#ai-image-transformation-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/multimodal/image_to_image_transformation

This example demonstrates how a team can collaborate to transform images using a style advisor to recommend transformations and an image transformer to apply AI-powered changes.

```python cookbook/examples/teams/multimodal/image_to_image_transformation.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.fal import FalTools

style_advisor = Agent(
    name="Style Advisor",
    role="Analyze and recommend artistic styles and transformations",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "Analyze the input image and transformation request",
        "Provide style recommendations and enhancement suggestions",
        "Consider artistic elements like composition, lighting, and mood",
    ],
)

image_transformer = Agent(
    name="Image Transformer",
    role="Transform images using AI tools",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[FalTools()],
    instructions=[
        "Use the `image_to_image` tool to generate transformed images",
        "Apply the recommended styles and transformations",
        "Return the image URL as provided without markdown conversion",
    ],
)

---

## Define and use examples

**URL:** llms-txt#define-and-use-examples

if __name__ == "__main__":
    content_creation_workflow = Workflow(
        name="Content Creation Workflow",
        description="Automated content creation with custom execution options",
        db=SqliteDb(
            session_table="workflow_session",
            db_file="tmp/workflow.db",
        ),
        steps=[research_step, content_planning_step],
    )

# Run workflow with additional_data
    content_creation_workflow.print_response(
        input="AI trends in 2024",
        additional_data={
            "user_email": "kaustubh@agno.com",
            "priority": "high",
            "client_type": "enterprise",
        },
        markdown=True,
        stream=True,
        stream_events=True,
    )

print("\n" + "=" * 60 + "\n")
```

To checkout async version, see the cookbook-

* [Step with Function using Additional Data (async)](https://github.com/agno-agi/agno/blob/main/cookbook/workflows/_01_basic_workflows/_02_step_with_function/async/step_with_function_additional_data.py)

---

## Clone the repo and navigate to the demo folder

**URL:** llms-txt#clone-the-repo-and-navigate-to-the-demo-folder

git clone https://github.com/agno-agi/agno.git
cd agno/cookbook/tools/mcp/mcp_toolbox_demo

---

## Basic Team Coordination

**URL:** llms-txt#basic-team-coordination

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/teams/basic/basic_coordination

This example demonstrates a coordinated team of AI agents working together to research topics across different platforms.

The team consists of three specialized agents:

1. **HackerNews Researcher** - Uses HackerNews API to find and analyze relevant HackerNews posts
2. **Article Reader** - Reads articles from URLs

The team leader coordinates the agents by:

* Giving each agent a specific task
* Providing clear instructions for each agent
* Collecting and summarizing the results from each agent

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

## Async Coordinated Team

**URL:** llms-txt#async-coordinated-team

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/async/async_coordination_team

This example demonstrates a coordinated team of AI agents working together asynchronously to research topics across different platforms.

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

## Persistent Session with History Limit

**URL:** llms-txt#persistent-session-with-history-limit

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/session/02_persistent_session_history

This example demonstrates how to use session history with a configurable number of previous runs added to context, allowing control over how much conversation history is included.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Setup PostgreSQL">
    
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

## Audio Sentiment Analysis

**URL:** llms-txt#audio-sentiment-analysis

Source: https://docs.agno.com/examples/concepts/agent/multimodal/audio_sentiment_analysis

This example demonstrates how to perform sentiment analysis on audio conversations using Agno agents with multimodal capabilities.

```python audio_sentiment_analysis.py theme={null}
import requests
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.media import Audio
from agno.models.google import Gemini

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_history_to_context=True,
    markdown=True,
    db=SqliteDb(
        session_table="audio_sentiment_analysis_sessions",
        db_file="tmp/audio_sentiment_analysis.db",
    ),
)

url = "https://agno-public.s3.amazonaws.com/demo_data/sample_conversation.wav"

response = requests.get(url)
audio_content = response.content

---

## Distributed Search with Infinity Reranker

**URL:** llms-txt#distributed-search-with-infinity-reranker

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/search_coordination/distributed_infinity_search

This example demonstrates how multiple agents coordinate to perform distributed search using Infinity reranker for high-performance ranking across team members.

```python cookbook/examples/teams/search_coordination/03_distributed_infinity_search.py theme={null}
"""
This example demonstrates how multiple agents coordinate to perform distributed
search using Infinity reranker for high-performance ranking across team members.

Team Composition:
- Primary Searcher: Performs initial broad search with infinity reranking
- Secondary Searcher: Performs targeted search on specific topics
- Cross-Reference Validator: Validates information across different sources
- Result Synthesizer: Combines and ranks all results for final response

Setup:
1. Install dependencies: `pip install agno anthropic infinity-client lancedb`
2. Set up Infinity Server:
   \`\`\`bash
   pip install "infinity-emb[all]"
   infinity_emb v2 --model-id BAAI/bge-reranker-base --port 7997
   \`\`\`
3. Export ANTHROPIC_API_KEY
4. Run this script
"""

from agno.agent import Agent
from agno.knowledge.embedder.cohere import CohereEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reranker.infinity import InfinityReranker
from agno.models.anthropic import Claude
from agno.team.team import Team
from agno.vectordb.lancedb import LanceDb, SearchType

---

## Image Input for Tools

**URL:** llms-txt#image-input-for-tools

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/image_input_for_tool

This example demonstrates how tools can receive and process images automatically through Agno's joint media access functionality. It shows initial image upload and analysis, DALL-E image generation within the same run, and cross-run media persistence.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Export your OpenAI API key">
    <CodeGroup>

</CodeGroup>
  </Step>

<Step title="Set up PostgreSQL">
    
  </Step>

<Step title="Install libraries">
    
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

  <Step title="Export your OpenAI API key">
    <CodeGroup>
```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeGroup>
  </Step>

  <Step title="Set up PostgreSQL">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Install libraries">
```

---

## Execute sample queries.

**URL:** llms-txt#execute-sample-queries.

agent1.print_response("How many people live in Canada?")
agent1.print_response("What is their national anthem called?")

---

## Example 5: Recipe suggestions (demonstrates culinary expertise role)

**URL:** llms-txt#example-5:-recipe-suggestions-(demonstrates-culinary-expertise-role)

print("Example 5: Recipe Suggestions from Culinary Team")
print("-" * 50)
shopping_team.print_response("What can I make with these ingredients?", stream=True)
print(f"Session state: {shopping_team.get_session_state()}")
print()

---

## Change Session State on Run

**URL:** llms-txt#change-session-state-on-run

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/state/change_state_on_run

This example demonstrates how to set and manage session state for different users and sessions. It shows how session state can be passed during runs and persists across multiple interactions within the same session.

```python cookbook/examples/teams/state/change_state_on_run.py theme={null}
from agno.db.in_memory import InMemoryDb
from agno.models.openai import OpenAIChat
from agno.team import Team

team = Team(
    db=InMemoryDb(),
    model=OpenAIChat(id="gpt-5-mini"),
    members=[],
    instructions="Users name is {user_name} and age is {age}",
)

---

## Confirmation Required with Streaming

**URL:** llms-txt#confirmation-required-with-streaming

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/confirmation_required_stream

This example demonstrates human-in-the-loop functionality with streaming responses. It shows how to handle user confirmation during tool execution while maintaining real-time streaming capabilities.

```python confirmation_required_stream.py theme={null}
"""🤝 Human-in-the-Loop: Adding User Confirmation to Tool Calls

This example shows how to implement human-in-the-loop functionality in your Agno tools.
It shows how to:
- Handle user confirmation during tool execution
- Gracefully cancel operations based on user choice

Some practical applications:
- Confirming sensitive operations before execution
- Reviewing API calls before they're made
- Validating data transformations
- Approving automated actions in critical systems

Run `pip install openai httpx rich agno` to install dependencies.
"""

import httpx
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.utils import pprint
from rich.console import Console
from rich.prompt import Prompt

@tool(requires_confirmation=True)
def get_top_hackernews_stories(num_stories: int) -> str:
    """Fetch top stories from Hacker News.

Args:
        num_stories (int): Number of stories to retrieve

Returns:
        str: JSON string containing story details
    """
    # Fetch top story IDs
    response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    story_ids = response.json()

# Yield story details
    all_stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        )
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        all_stories.append(story)
    return json.dumps(all_stories)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    db=SqliteDb(
        db_file="tmp/example.db",
    ),
    tools=[get_top_hackernews_stories],
    markdown=True,
)

for run_event in agent.run("Fetch the top 2 hackernews stories", stream=True):
    if run_event.is_paused:
        for tool in run_event.tools_requiring_confirmation:  # type: ignore
            # Ask for confirmation
            console.print(
                f"Tool name [bold blue]{tool.tool_name}({tool.tool_args})[/] requires confirmation."
            )
            message = (
                Prompt.ask("Do you want to continue?", choices=["y", "n"], default="y")
                .strip()
                .lower()
            )

if message == "n":
                tool.confirmed = False
            else:
                # We update the tools in place
                tool.confirmed = True
        run_response = agent.continue_run(
            run_id=run_event.run_id, updated_tools=run_event.tools, stream=True
        )  # type: ignore
        pprint.pprint_run_response(run_response)

---

## Capture Reasoning Content

**URL:** llms-txt#capture-reasoning-content

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/reasoning/agents/capture-reasoning-content-cot

This example demonstrates how to access and print the `reasoning_content` when using a Reasoning Agent (with `reasoning=True`) or setting a specific `reasoning_model`.

```python cookbook/reasoning/agents/capture_reasoning_content_default_COT.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat

print("\n=== Example 1: Using reasoning=True (default COT) ===\n")

---

## Google Maps Tools

**URL:** llms-txt#google-maps-tools

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/tools/others/google_maps

```python cookbook/tools/google_maps_tools.py theme={null}
from agno.agent import Agent
from agno.tools.google_maps import GoogleMapTools
from agno.tools.crawl4ai import Crawl4aiTools  # Optional: for enriching place data

agent = Agent(
    name="Maps API Demo Agent",
    tools=[
        GoogleMapTools(),
        Crawl4aiTools(max_length=5000),  # Optional: for scraping business websites
    ],
    description="Location and business information specialist for mapping and location-based queries.",
    markdown=True,
    )

---

## Advanced Session State Management

**URL:** llms-txt#advanced-session-state-management

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/state/session_state_advanced

This example demonstrates advanced session state management with multiple tools for managing a shopping list, including add, remove, and list operations.

```python session_state_advanced.py theme={null}
from textwrap import dedent

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

---

## Interactive CLI Writing Team

**URL:** llms-txt#interactive-cli-writing-team

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/other/run_as_cli

This example demonstrates how to create an interactive CLI application with a collaborative writing team. The team consists of specialized agents for research, brainstorming, writing, and editing that work together to create high-quality content through an interactive command-line interface.

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

## User Input Required All Fields

**URL:** llms-txt#user-input-required-all-fields

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/user_input_required_all_fields

This example demonstrates how to use the `requires_user_input` parameter to collect input for all fields in a tool. It shows how to handle user input schema and collect values for each required field.

```python user_input_required_all_fields.py theme={null}
"""🤝 Human-in-the-Loop: Allowing users to provide input externally

This example shows how to use the `requires_user_input` parameter to allow users to provide input externally.
"""

from typing import List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.tools.function import UserInputField
from agno.utils import pprint

@tool(requires_user_input=True)
def send_email(subject: str, body: str, to_address: str) -> str:
    """
    Send an email.

Args:
        subject (str): The subject of the email.
        body (str): The body of the email.
        to_address (str): The address to send the email to.
    """
    return f"Sent email to {to_address} with subject {subject} and body {body}"

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[send_email],
    markdown=True,
)

run_response = agent.run("Send an email please")
if run_response.is_paused:  # Or agent.run_response.is_paused
    for tool in run_response.tools_requiring_user_input:  # type: ignore
        input_schema: List[UserInputField] = tool.user_input_schema  # type: ignore

for field in input_schema:
            # Get user input for each field in the schema
            field_type = field.field_type
            field_description = field.description

# Display field information to the user
            print(f"\nField: {field.name}")
            print(f"Description: {field_description}")
            print(f"Type: {field_type}")

# Get user input
            if field.value is None:
                user_value = input(f"Please enter a value for {field.name}: ")

# Update the field value
            field.value = user_value

run_response = agent.continue_run(run_response=run_response)
    pprint.pprint_run_response(run_response)

---

## Download all sample CVs and get their paths

**URL:** llms-txt#download-all-sample-cvs-and-get-their-paths

downloaded_cv_paths = download_knowledge_filters_sample_data(
    num_files=5, file_extension=SampleDataFileExtension.PDF
)

---

## Download all sample sales files and get their paths

**URL:** llms-txt#download-all-sample-sales-files-and-get-their-paths

downloaded_csv_paths = download_knowledge_filters_sample_data(
    num_files=4, file_extension=SampleDataFileExtension.CSV
)

---

## Async Tool Confirmation Required

**URL:** llms-txt#async-tool-confirmation-required

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/confirmation_required_async

This example demonstrates how to implement human-in-the-loop functionality with async agents, requiring user confirmation before executing tool operations.

```python confirmation_required_async.py theme={null}
"""🤝 Human-in-the-Loop: Adding User Confirmation to Tool Calls

This example shows how to implement human-in-the-loop functionality in your Agno tools.
It shows how to:
- Handle user confirmation during tool execution
- Gracefully cancel operations based on user choice

Some practical applications:
- Confirming sensitive operations before execution
- Reviewing API calls before they're made
- Validating data transformations
- Approving automated actions in critical systems

Run `pip install openai httpx rich agno` to install dependencies.
"""

import asyncio
import json

import httpx
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.utils import pprint
from rich.console import Console
from rich.prompt import Prompt

@tool(requires_confirmation=True)
def get_top_hackernews_stories(num_stories: int) -> str:
    """Fetch top stories from Hacker News.

Args:
        num_stories (int): Number of stories to retrieve

Returns:
        str: JSON string containing story details
    """
    # Fetch top story IDs
    response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    story_ids = response.json()

# Yield story details
    all_stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        )
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        all_stories.append(story)
    return json.dumps(all_stories)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[get_top_hackernews_stories],
    markdown=True,
)

run_response = asyncio.run(agent.arun("Fetch the top 2 hackernews stories"))
if run_response.is_paused:
    for tool in run_response.tools_requiring_confirmation:
        # Ask for confirmation
        console.print(
            f"Tool name [bold blue]{tool.tool_name}({tool.tool_args})[/] requires confirmation."
        )
        message = (
            Prompt.ask("Do you want to continue?", choices=["y", "n"], default="y")
            .strip()
            .lower()
        )

if message == "n":
            tool.confirmed = False
        else:
            # We update the tools in place
            tool.confirmed = True

run_response = asyncio.run(agent.acontinue_run(run_response=run_response))

---

## Sequence of steps

**URL:** llms-txt#sequence-of-steps

**Contents:**
- Pattern: Sequential Named Steps

Source: https://docs.agno.com/examples/concepts/workflows/01-basic-workflows/sequence_of_steps

This example demonstrates how to use named steps in a workflow.

This example demonstrates **Workflows** using named Step objects for better tracking
and organization. This pattern provides clear step identification and enhanced logging
while maintaining simple sequential execution.

## Pattern: Sequential Named Steps

**When to use**: Linear processes where you want clear step identification, better logging,
and future platform support. Ideal when you have distinct phases that benefit from naming.

```python sequence_of_steps.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow

---

## Function instead of steps

**URL:** llms-txt#function-instead-of-steps

Source: https://docs.agno.com/examples/concepts/workflows/01-basic-workflows/function_instead_of_steps

This example demonstrates how to use just a single function instead of steps in a workflow.

This example demonstrates **Workflows** using a single custom execution function instead of
discrete steps. This pattern gives you complete control over the orchestration logic while still
benefiting from workflow features like storage, streaming, and session management.

**When to use**: When you need maximum flexibility and control over the execution flow, similar
to Workflows 1.0 approach but with a better structured approach.

```python function_instead_of_steps.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.types import WorkflowExecutionInput
from agno.workflow.workflow import Workflow

---

## Coordinated Reasoning RAG Team

**URL:** llms-txt#coordinated-reasoning-rag-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/search_coordination/coordinated_reasoning_rag

This example demonstrates how multiple specialized agents coordinate to provide comprehensive RAG responses with distributed reasoning capabilities. Each agent has specific reasoning responsibilities to ensure thorough analysis.

```python cookbook/examples/teams/search_coordination/02_coordinated_reasoning_rag.py theme={null}
"""
This example demonstrates how multiple specialized agents coordinate to provide
comprehensive RAG responses with distributed reasoning capabilities. Each agent
has specific reasoning responsibilities to ensure thorough analysis.

Team Composition:
- Information Gatherer: Searches knowledge base and gathers raw information
- Reasoning Analyst: Applies logical reasoning to analyze gathered information
- Evidence Evaluator: Evaluates evidence quality and identifies gaps
- Response Coordinator: Synthesizes everything into a final reasoned response

Setup:
1. Run: `pip install agno anthropic cohere lancedb tantivy sqlalchemy`
2. Export your ANTHROPIC_API_KEY and CO_API_KEY
3. Run this script to see coordinated reasoning RAG in action
"""

from agno.agent import Agent
from agno.knowledge.embedder.cohere import CohereEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reranker.cohere import CohereReranker
from agno.models.anthropic import Claude
from agno.team.team import Team
from agno.tools.reasoning import ReasoningTools
from agno.vectordb.lancedb import LanceDb, SearchType

---

## Async Team with Tools

**URL:** llms-txt#async-team-with-tools

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/tools/async_team_with_tools

This example demonstrates how to create an async team with various tools for information gathering using multiple agents with different tools (Wikipedia, DuckDuckGo, AgentQL) to gather comprehensive information asynchronously.

```python cookbook/examples/teams/tools/03_async_team_with_tools.py theme={null}
"""
This example demonstrates how to create an async team with various tools for information gathering.

The team uses multiple agents with different tools (Wikipedia, DuckDuckGo, AgentQL) to
gather comprehensive information about a company asynchronously.
"""

import asyncio
from uuid import uuid4

from agno.agent.agent import Agent
from agno.models.anthropic import Claude
from agno.models.mistral import MistralChat
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.agentql import AgentQLTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.wikipedia import WikipediaTools

---

## Generate Video Using ModelsLab

**URL:** llms-txt#generate-video-using-modelslab

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/multimodal/generate_video_using_models_lab

This example demonstrates how to create an AI agent that generates videos using the ModelsLab API.

```python generate_video_using_models_lab.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.models_labs import ModelsLabTools

video_agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[ModelsLabTools()],
    description="You are an AI agent that can generate videos using the ModelsLabs API.",
    instructions=[
        "When the user asks you to create a video, use the `generate_media` tool to create the video.",
        "The video will be displayed in the UI automatically below your response, so you don't need to show the video URL in your response.",
        "Politely and courteously let the user know that the video has been generated and will be displayed below as soon as its ready.",
    ],
    markdown=True,
)

video_agent.print_response("Generate a video of a cat playing with a ball")

---

## Access Dependencies in Team Tool

**URL:** llms-txt#access-dependencies-in-team-tool

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/dependencies/access_dependencies_in_tool

How to access dependencies passed to a team in a tool

This example demonstrates how team tools can access dependencies passed to the team, allowing tools to utilize dynamic context like team metrics and current time information while team members collaborate with shared data sources.

```python cookbook/examples/teams/dependencies/access_dependencies_in_tool.py theme={null}
from typing import Dict, Any, Optional
from datetime import datetime

from agno.agent import Agent
from agno.team import Team
from agno.models.openai import OpenAIChat

def get_current_context() -> dict:
    """Get current contextual information like time, weather, etc."""
    return {
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "PST",
        "day_of_week": datetime.now().strftime("%A"),
    }

def analyze_team_performance(team_id: str, dependencies: Optional[Dict[str, Any]] = None) -> str:
    """
    Analyze team performance using available data sources.
    
    This tool analyzes team metrics and provides insights.
    Call this tool with the team_id you want to analyze.
    
    Args:
        team_id: The team ID to analyze (e.g., 'engineering_team', 'sales_team')
        dependencies: Available data sources (automatically provided)
    
    Returns:
        Detailed team performance analysis and insights
    """
    if not dependencies:
        return "No data sources available for analysis."
    
    print(f"--> Team tool received data sources: {list(dependencies.keys())}")
    
    results = [f"=== TEAM PERFORMANCE ANALYSIS FOR {team_id.upper()} ==="]
    
    # Use team metrics data if available
    if "team_metrics" in dependencies:
        metrics_data = dependencies["team_metrics"]
        results.append(f"Team Metrics: {metrics_data}")
        
        # Add analysis based on the metrics
        if metrics_data.get("productivity_score"):
            score = metrics_data["productivity_score"]
            if score >= 8:
                results.append(f"Performance Analysis: Excellent performance with {score}/10 productivity score")
            elif score >= 6:
                results.append(f"Performance Analysis: Good performance with {score}/10 productivity score")
            else:
                results.append(f"Performance Analysis: Needs improvement with {score}/10 productivity score")
    
    # Use current context data if available
    if "current_context" in dependencies:
        context_data = dependencies["current_context"]
        results.append(f"Current Context: {context_data}")
        results.append(f"Time-based Analysis: Team analysis performed on {context_data['day_of_week']} at {context_data['current_time']}")

print(f"--> Team tool returned results: {results}")
    
    return "\n\n".join(results)

---

## Async Collaborative Team

**URL:** llms-txt#async-collaborative-team

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/async/async_delegate_to_all_members

This example demonstrates a collaborative team of AI agents working together asynchronously to research topics across different platforms.

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

## Audio to Text Transcription

**URL:** llms-txt#audio-to-text-transcription

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/multimodal/audio_to_text

This example demonstrates how to create an agent that can transcribe audio conversations, identifying different speakers and providing accurate transcriptions.

```python audio_to_text.py theme={null}
import requests
from agno.agent import Agent
from agno.media import Audio
from agno.models.google import Gemini

agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    markdown=True,
)

url = "https://agno-public.s3.us-east-1.amazonaws.com/demo_data/QA-01.mp3"

response = requests.get(url)
audio_content = response.content

---

## Dynamic Instructions via Function

**URL:** llms-txt#dynamic-instructions-via-function

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/context_management/instructions_via_function

This example demonstrates how to provide instructions to an agent via a function that can access the agent's properties, enabling dynamic and personalized instruction generation.

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

## Audio Multi Turn

**URL:** llms-txt#audio-multi-turn

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/audio_multi_turn

This example demonstrates how to create an agent that can handle multi-turn audio conversations, maintaining context between audio interactions while generating both text and audio responses.

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

## Adding Dependencies to Team Run

**URL:** llms-txt#adding-dependencies-to-team-run

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/dependencies/add_dependencies_run

This example demonstrates how to add dependencies to a specific team run. Dependencies are functions that provide contextual information (like user profiles and current context) that get passed to the team during execution for personalized responses.

```python cookbook/examples/teams/dependencies/add_dependencies_on_run.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team

def get_user_profile(user_id: str = "john_doe") -> dict:
    """Get user profile information that can be referenced in responses."""
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

profile_agent = Agent(
    name="ProfileAnalyst",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You analyze user profiles and provide personalized recommendations.",
)

context_agent = Agent(
    name="ContextAnalyst",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You analyze current context and timing to provide relevant insights.",
)

team = Team(
    name="PersonalizationTeam",
    model=OpenAIChat(id="gpt-5-mini"),
    members=[profile_agent, context_agent],
    markdown=True,
)

response = team.run(
    "Please provide me with a personalized summary of today's priorities based on my profile and interests.",
    dependencies={
        "user_profile": get_user_profile,
        "current_context": get_current_context,
    },
    add_dependencies_to_context=True,
)

print(response.content)

---

## Example 1: Transcription

**URL:** llms-txt#example-1:-transcription

**Contents:**
- Using Multimodal Models

url = "https://agno-public.s3.amazonaws.com/demo_data/sample_conversation.wav"

local_audio_path = Path("tmp/sample_conversation.wav")
print(f"Downloading file to local path: {local_audio_path}")
download_file(url, local_audio_path)

transcription_agent = Agent(
    tools=[OpenAITools(transcription_model="gpt-4o-transcribe")],
    markdown=True,
)
transcription_agent.print_response(
    f"Transcribe the audio file for this file: {local_audio_path}"
)
python cookbook/agents/multimodal/audio_to_text.py theme={null}
import requests
from agno.agent import Agent
from agno.media import Audio
from agno.models.google import Gemini

agent = Agent(
    model=Gemini(id="gemini-2.0-flash-exp"),
    markdown=True,
)

url = "https://agno-public.s3.us-east-1.amazonaws.com/demo_data/QA-01.mp3"

response = requests.get(url)
audio_content = response.content

**Examples:**

Example 1 (unknown):
```unknown
**Best for**: High accuracy, cloud processing

## Using Multimodal Models

Multimodal models like Gemini can transcribe audio directly without additional tools.
```

---

## Team Streaming Responses

**URL:** llms-txt#team-streaming-responses

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/streaming/team_streaming

This example demonstrates streaming responses from a team using specialized agents with financial tools to provide real-time stock information with streaming output.

```python cookbook/examples/teams/streaming/01_team_streaming.py theme={null}
"""
This example demonstrates streaming responses from a team.

The team uses specialized agents with financial tools to provide real-time
stock information with streaming output.
"""

from typing import Iterator  # noqa
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.exa import ExaTools

---

## Adding Dependencies to Team Context

**URL:** llms-txt#adding-dependencies-to-team-context

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/dependencies/add_dependencies_to_context

This example demonstrates how to add dependencies directly to the team context. Unlike adding dependencies per run, this approach makes the dependency functions available to all team runs by default, providing consistent access to contextual information across all interactions.

```python cookbook/examples/teams/dependencies/add_dependencies_to_context.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team

def get_user_profile(user_id: str = "john_doe") -> dict:
    """Get user profile information that can be referenced in responses."""
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

profile_agent = Agent(
    name="ProfileAnalyst",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You analyze user profiles and provide personalized recommendations.",
)

context_agent = Agent(
    name="ContextAnalyst",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="You analyze current context and timing to provide relevant insights.",
)

team = Team(
    name="PersonalizationTeam",
    model=OpenAIChat(id="gpt-5-mini"),
    members=[profile_agent, context_agent],
    dependencies={
        "user_profile": get_user_profile,
        "current_context": get_current_context,
    },
    add_dependencies_to_context=True,
    debug_mode=True,
    markdown=True,
)

response = team.run(
    "Please provide me with a personalized summary of today's priorities based on my profile and interests.",
)

print(response.content)

---

## Prompt Injection Guardrail

**URL:** llms-txt#prompt-injection-guardrail

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/guardrails/prompt_injection

This example demonstrates how to use Agno's built-in prompt injection guardrail with an Team.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run example">
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

  <Step title="Run example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Router Team with Direct Response

**URL:** llms-txt#router-team-with-direct-response

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/teams/basic/respond_directly_router_team

This example demonstrates a team of AI agents working together to answer questions in different languages.

The team consists of six specialized agents:

1. **English Agent** - Can only answer in English
2. **Japanese Agent** - Can only answer in Japanese
3. **Chinese Agent** - Can only answer in Chinese
4. **Spanish Agent** - Can only answer in Spanish
5. **French Agent** - Can only answer in French
6. **German Agent** - Can only answer in German

The team leader routes the user's question to the appropriate language agent. With `respond_directly=True`, the selected agent responds directly without the team leader processing the response.

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

## Route Mode Team Events

**URL:** llms-txt#route-mode-team-events

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/streaming/route_mode_events

This example demonstrates event handling in route mode teams, showing how to capture team and member events separately with detailed tool call information.

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

## Usage examples

**URL:** llms-txt#usage-examples

if __name__ == "__main__":
    # Create the media generation workflow
    media_workflow = Workflow(
        name="AI Media Generation Workflow",
        description="Generate and analyze images or videos using AI agents",
        steps=[
            Router(
                name="Media Type Router",
                description="Routes to appropriate media generation pipeline based on content type",
                selector=media_sequence_selector,
                choices=[image_sequence, video_sequence],
            )
        ],
    )

print("=== Example 1: Image Generation (using message_data) ===")
    image_request = MediaRequest(
        topic="Create an image of magical forest for a movie scene",
        content_type="image",
        prompt="A mystical forest with glowing mushrooms",
        style="fantasy art",
        resolution="1920x1080",
    )

media_workflow.print_response(
        input="Create an image of magical forest for a movie scene",
        markdown=True,
    )

# print("\n=== Example 2: Video Generation (using message_data) ===")
    # video_request = MediaRequest(
    #     topic="Create a cinematic video city timelapse",
    #     content_type="video",
    #     prompt="A time-lapse of a city skyline from day to night",
    #     style="cinematic",
    #     duration=30,
    #     resolution="4K"
    # )

# media_workflow.print_response(
    #     input="Create a cinematic video city timelapse",
    #     markdown=True,
    # )
```

---

## Pydantic Models as Team Output

**URL:** llms-txt#pydantic-models-as-team-output

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/structured_input_output/pydantic_model_output

This example demonstrates how to use Pydantic models as output from teams, showing how structured data can be returned as responses for more precise and validated output handling.

```python cookbook/examples/teams/structured_input_output/00_pydantic_model_output.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.utils.pprint import pprint_run_response
from pydantic import BaseModel

class StockAnalysis(BaseModel):
    symbol: str
    company_name: str
    analysis: str

class CompanyAnalysis(BaseModel):
    company_name: str
    analysis: str

stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat("gpt-5-mini"),
    output_schema=StockAnalysis,
    role="Searches for information on stocks and provides price analysis.",
    tools=[DuckDuckGoTools()],
)

company_info_agent = Agent(
    name="Company Info Searcher",
    model=OpenAIChat("gpt-5-mini"),
    role="Searches for information about companies and recent news.",
    output_schema=CompanyAnalysis,
    tools=[DuckDuckGoTools()],
)

class StockReport(BaseModel):
    symbol: str
    company_name: str
    analysis: str

team = Team(
    name="Stock Research Team",
    model=OpenAIChat("gpt-5-mini"),
    members=[stock_searcher, company_info_agent],
    output_schema=StockReport,
    markdown=True,
)

---

## Team Input Schema Validation

**URL:** llms-txt#team-input-schema-validation

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/structured_input_output/input_schema_on_team

This example demonstrates how to use input\_schema with teams for automatic input validation and structured data handling, allowing automatic validation and conversion of dictionary inputs into Pydantic models.

```python cookbook/examples/teams/structured_input_output/06_input_schema_on_team.py theme={null}
"""
This example demonstrates how to use input_schema with teams for automatic
input validation and structured data handling.

The input_schema feature allows teams to automatically validate and convert
dictionary inputs into Pydantic models, ensuring type safety and data validation.
"""

from typing import List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from pydantic import BaseModel, Field

class ResearchProject(BaseModel):
    """Structured research project with validation requirements."""

project_name: str = Field(description="Name of the research project")
    research_topics: List[str] = Field(
        description="List of topics to research", min_items=1
    )
    target_audience: str = Field(description="Intended audience for the research")
    depth_level: str = Field(
        description="Research depth level", pattern="^(basic|intermediate|advanced)$"
    )
    max_sources: int = Field(
        description="Maximum number of sources to use", ge=3, le=20, default=10
    )
    include_recent_only: bool = Field(
        description="Whether to focus only on recent sources", default=True
    )

---

## More examples to try:

**URL:** llms-txt#more-examples-to-try:

"""
Sample prompts to explore:
1. "What's the historical significance of this location?"
2. "How has this place changed over time?"
3. "What cultural events happen here?"
4. "What's the architectural style and influence?"
5. "What recent developments affect this area?"

Sample image URLs to analyze:
1. Eiffel Tower: "https://upload.wikimedia.org/wikipedia/commons/8/85/Tour_Eiffel_Wikimedia_Commons_%28cropped%29.jpg"
2. Taj Mahal: "https://upload.wikimedia.org/wikipedia/commons/b/bd/Taj_Mahal%2C_Agra%2C_India_edit3.jpg"
3. Golden Gate Bridge: "https://upload.wikimedia.org/wikipedia/commons/0/0c/GoldenGateBridge-001.jpg"
"""

---

## Disable Storing Tool Messages

**URL:** llms-txt#disable-storing-tool-messages

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/session/10_disable_storing_tool_messages

This example demonstrates how to disable storing tool messages in a session.

This example shows how to disable storing tool messages in a session.

---

## Last N Session Messages

**URL:** llms-txt#last-n-session-messages

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/state/last_n_session_messages

This example demonstrates how to configure agents to search through previous sessions and limit the number of historical sessions included in context. This helps manage context length while maintaining relevant conversation history.

```python last_n_session_messages.py theme={null}
import os

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

---

## Pydantic Models as Team Input

**URL:** llms-txt#pydantic-models-as-team-input

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/structured_input_output/pydantic_model_as_input

This example demonstrates how to use Pydantic models as input to teams, showing how structured data can be passed as messages for more precise and validated input handling.

```python cookbook/examples/teams/structured_input_output/01_pydantic_model_as_input.py theme={null}
"""
This example demonstrates how to use Pydantic models as input to teams.

Shows how structured data can be passed as messages to teams for more
precise and validated input handling.
"""

from typing import List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.hackernews import HackerNewsTools
from pydantic import BaseModel, Field

class ResearchTopic(BaseModel):
    """Structured research topic with specific requirements."""

topic: str = Field(description="The main research topic")
    focus_areas: List[str] = Field(description="Specific areas to focus on")
    target_audience: str = Field(description="Who this research is for")
    sources_required: int = Field(description="Number of sources needed", default=5)

---

## RAG with Sentence Transformer Reranker

**URL:** llms-txt#rag-with-sentence-transformer-reranker

**Contents:**
- Code
- Setup Instructions:
  - 1. Install Dependencies
  - 2. Start the Postgres Server with pgvector
  - 3. Run the example
- Usage

Source: https://docs.agno.com/examples/concepts/agent/rag/rag_sentence_transformer

This example demonstrates Agentic RAG using Sentence Transformer Reranker with multilingual data for improved search relevance.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Start Postgres with pgvector">
    
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

  <Step title="Start Postgres with pgvector">
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

## Access Session State in Router Selector Function

**URL:** llms-txt#access-session-state-in-router-selector-function

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/access_session_state_in_router_selector_function

This example demonstrates how to access session state in the selector function of a router step

1. Using `session_state` in a Router selector function
2. Making routing decisions based on session state data
3. Accessing user preferences and history from session\_state
4. Dynamically selecting different agents based on user context

```python access_session_state_in_router_selector_function.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.workflow.router import Router
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

def route_based_on_user_preference(step_input: StepInput, session_state: dict) -> Step:
    """
    Router selector that chooses an agent based on user preferences in session_state.

Args:
        step_input: The input for this step (contains user query)
        session_state: The shared session state dictionary

Returns:
        Step: The step to execute based on user preference
    """
    print("\n=== Routing Decision ===")
    print(f"User ID: {session_state.get('current_user_id')}")
    print(f"Session ID: {session_state.get('current_session_id')}")

# Get user preference from session state
    user_preference = session_state.get("agent_preference", "general")
    interaction_count = session_state.get("interaction_count", 0)

print(f"User Preference: {user_preference}")
    print(f"Interaction Count: {interaction_count}")

# Update interaction count
    session_state["interaction_count"] = interaction_count + 1

# Route based on preference
    if user_preference == "technical":
        print("→ Routing to Technical Expert")
        return technical_step
    elif user_preference == "friendly":
        print("→ Routing to Friendly Assistant")
        return friendly_step
    else:
        # For first interaction, route to onboarding
        if interaction_count == 0:
            print("→ Routing to Onboarding (first interaction)")
            return onboarding_step
        else:
            print("→ Routing to General Assistant")
            return general_step

def set_user_preference(step_input: StepInput, session_state: dict) -> StepOutput:
    """Custom function that sets user preference based on onboarding."""
    print("\n=== Setting User Preference ===")

# In a real scenario, this would analyze the user's response
    # For demo purposes, we'll set it based on interaction count
    interaction_count = session_state.get("interaction_count", 0)

if interaction_count % 3 == 1:
        session_state["agent_preference"] = "technical"
        preference = "technical"
    elif interaction_count % 3 == 2:
        session_state["agent_preference"] = "friendly"
        preference = "friendly"
    else:
        session_state["agent_preference"] = "general"
        preference = "general"

print(f"Set preference to: {preference}")
    return StepOutput(content=f"Preference set to: {preference}")

---

## Using Reference Dependencies in Team Instructions

**URL:** llms-txt#using-reference-dependencies-in-team-instructions

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/dependencies/reference_dependencies

This example demonstrates how to use reference dependencies by defining them in the team constructor and referencing them directly in team instructions. This approach allows dependencies to be automatically injected into the team's context and referenced using template variables in instructions.

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

## Demo Deepseek R1

**URL:** llms-txt#demo-deepseek-r1

**Contents:**
- Code

Source: https://docs.agno.com/examples/models/ollama/demo_deepseek_r1

```python cookbook/models/ollama/demo_deepseek_r1.py theme={null}
from agno.agent import Agent, RunOutput  # noqa
from agno.models.ollama import Ollama

agent = Agent(model=Ollama(id="deepseek-r1:14b"), markdown=True)

---

## Image to Fiction Story Team

**URL:** llms-txt#image-to-fiction-story-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/multimodal/image_to_text

This example demonstrates how a team can collaborate to analyze images and create engaging fiction stories using an image analyst and creative writer.

```python cookbook/examples/teams/multimodal/image_to_text.py theme={null}
from pathlib import Path

from agno.agent import Agent
from agno.media import Image
from agno.models.openai import OpenAIChat
from agno.team import Team

image_analyzer = Agent(
    name="Image Analyst",
    role="Analyze and describe images in detail",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "Analyze images carefully and provide detailed descriptions",
        "Focus on visual elements, composition, and key details",
    ],
)

creative_writer = Agent(
    name="Creative Writer",
    role="Create engaging stories and narratives",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "Transform image descriptions into compelling fiction stories",
        "Use vivid language and creative storytelling techniques",
    ],
)

---

## Demo Qwen

**URL:** llms-txt#demo-qwen

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/ollama/demo_qwen

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install Ollama">
    Follow the [Ollama installation guide](https://github.com/ollama/ollama?tab=readme-ov-file#macos) and run:

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

## Team Metrics Analysis

**URL:** llms-txt#team-metrics-analysis

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/metrics/team_metrics

This example demonstrates how to access and analyze comprehensive team metrics including message-level metrics, session metrics, and member-specific performance data.

```python cookbook/examples/teams/metrics/01_team_metrics.py theme={null}
"""
This example demonstrates how to access and analyze team metrics.

Shows how to retrieve detailed metrics for team execution, including
message-level metrics, session metrics, and member-specific metrics.

Prerequisites:
1. Run: cookbook/run_pgvector.sh (to start PostgreSQL)
2. Ensure PostgreSQL is running on localhost:5532
"""

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.exa import ExaTools
from agno.utils.pprint import pprint_run_response
from rich.pretty import pprint

---

## Selector for Image Video Generation Pipelines

**URL:** llms-txt#selector-for-image-video-generation-pipelines

**Contents:**
- Key Features:
- Key Features:

Source: https://docs.agno.com/examples/concepts/workflows/05_workflows_conditional_branching/selector_for_image_video_generation_pipelines

This example demonstrates **Workflows 2.0** router pattern for dynamically selecting between image and video generation pipelines.

This example demonstrates **Workflows 2.0** router pattern for dynamically selecting between image and video generation pipelines. It uses `Steps` to encapsulate each media type's workflow and a `Router` to intelligently choose the pipeline based on input analysis.

* **Dynamic Routing**: Selects pipelines (`Steps`) based on input keywords (e.g., "image" or "video").
* **Modular Pipelines**: Encapsulates image/video workflows as reusable `Steps` objects.
* **Structured Inputs**: Uses Pydantic models for type-safe configuration (e.g., resolution, style).

* **Nested Logic**: Embeds `Condition` and `Parallel` within a `Steps` sequence.
* **Topic-Specialized Research**: Uses `Condition` to trigger parallel tech/news research for tech topics.
* **Modular Design**: Encapsulates the entire workflow as a reusable `Steps` object.

```python selector_for_image_video_generation_pipelines.py theme={null}
from typing import List, Optional

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.models.gemini import GeminiTools
from agno.tools.openai import OpenAITools
from agno.workflow.router import Router
from agno.workflow.step import Step
from agno.workflow.steps import Steps
from agno.workflow.types import StepInput
from agno.workflow.workflow import Workflow
from pydantic import BaseModel

---

## External Tool Execution Async

**URL:** llms-txt#external-tool-execution-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/external_tool_execution_async

This example demonstrates how to execute tools outside of the agent using external tool execution in an asynchronous environment. This pattern allows you to control tool execution externally while maintaining agent functionality with async operations.

```python external_tool_execution_async.py theme={null}
"""🤝 Human-in-the-Loop: Execute a tool call outside of the agent

This example shows how to implement human-in-the-loop functionality in your Agno tools.
It shows how to:
- Use external tool execution to execute a tool call outside of the agent

Run `pip install openai agno` to install dependencies.
"""

import asyncio
import subprocess

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.utils import pprint

---

## Video Generation Tools

**URL:** llms-txt#video-generation-tools

**Contents:**
- Developer Resources

Source: https://docs.agno.com/concepts/multimodal/video/video_generation

Learn how to use video generation tools with Agno agents.

The following example demonstrates how to generate a video using `FalTools` with an agent. See [FAL](https://fal.ai/video) for more details.

## Developer Resources

* View a [Replicate](/examples/concepts/multimodal/generate-video-replicate) example.
* View a [Fal](/examples/concepts/tools/others/fal) example.
* View a [ModelsLabs](/examples/concepts/multimodal/generate-video-models-lab) example.

---

## Image to Structured Output

**URL:** llms-txt#image-to-structured-output

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/image_to_structured_output

This example demonstrates how to analyze images and generate structured output using Pydantic models, creating movie scripts based on image content.

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

## DEMO FUNCTIONS USING CLI

**URL:** llms-txt#demo-functions-using-cli

---

## Blog Post Generator

**URL:** llms-txt#blog-post-generator

Source: https://docs.agno.com/examples/use-cases/workflows/blog-post-generator

This example demonstrates how to migrate from the similar workflows 1.0 example to workflows 2.0 structure.

This advanced example demonstrates how to build a sophisticated blog post generator that combines
web research capabilities with professional writing expertise. The workflow uses a multi-stage
approach:

1. Intelligent web research and source gathering
2. Content extraction and processing
3. Professional blog post writing with proper citations

* Advanced web research and source evaluation
* Content scraping and processing
* Professional writing with SEO optimization
* Automatic content caching for efficiency
* Source attribution and fact verification

Example blog topics to try:

* "The Rise of Artificial General Intelligence: Latest Breakthroughs"
* "How Quantum Computing is Revolutionizing Cybersecurity"
* "Sustainable Living in 2024: Practical Tips for Reducing Carbon Footprint"
* "The Future of Work: AI and Human Collaboration"
* "Space Tourism: From Science Fiction to Reality"
* "Mindfulness and Mental Health in the Digital Age"
* "The Evolution of Electric Vehicles: Current State and Future Trends"

Run `pip install openai ddgs newspaper4k lxml_html_clean sqlalchemy agno` to install dependencies.

```python blog_post_generator.py theme={null}
"""🎨 Blog Post Generator v2.0 - Your AI Content Creation Studio!

This advanced example demonstrates how to build a sophisticated blog post generator using
the new workflow v2.0 architecture. The workflow combines web research capabilities with
professional writing expertise using a multi-stage approach:

1. Intelligent web research and source gathering
2. Content extraction and processing
3. Professional blog post writing with proper citations

Key capabilities:
- Advanced web research and source evaluation
- Content scraping and processing
- Professional writing with SEO optimization
- Automatic content caching for efficiency
- Source attribution and fact verification
"""

import asyncio
import json
from textwrap import dedent
from typing import Dict, Optional

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.workflow.workflow import Workflow
from pydantic import BaseModel, Field

---

## PII Detection Guardrail

**URL:** llms-txt#pii-detection-guardrail

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/guardrails/pii_detection

This example demonstrates how to use Agno's built-in PII detection guardrail with an Team.

This example shows how to:

1. Detect and block personally identifiable information (PII) in input
2. Protect sensitive data like SSNs, credit cards, emails, and phone numbers
3. Handle different types of PII violations with appropriate error messages

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run example">
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

  <Step title="Run example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Tool Call Limit

**URL:** llms-txt#tool-call-limit

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/other/tool_call_limit

This example demonstrates how to use tool call limits to control the number of tool calls an agent can make. This is useful for preventing excessive API usage or limiting agent behavior in specific scenarios.

```python tool_call_limit.py theme={null}
"""
This cookbook shows how to use tool call limit to control the number of tool calls an agent can make.
"""

from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.duckduckgo import DuckDuckGoTools

agent = Agent(
    model=Claude(id="claude-3-5-haiku-20241022"),
    tools=[DuckDuckGoTools(company_news=True, cache_results=True)],
    tool_call_limit=1,
)

---

## Async Team Events Monitoring

**URL:** llms-txt#async-team-events-monitoring

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/streaming/async_team_events

This example demonstrates how to handle and monitor team events asynchronously, capturing various events during async team execution including tool calls, run states, and content generation.

```python cookbook/examples/teams/streaming/05_async_team_events.py theme={null}
"""
This example demonstrates how to handle and monitor team events asynchronously.

Shows how to capture and respond to various events during async team execution,
including tool calls, run states, and content generation events.
"""

import asyncio
from uuid import uuid4

from agno.agent import RunEvent
from agno.agent.agent import Agent
from agno.models.anthropic.claude import Claude
from agno.models.openai import OpenAIChat
from agno.team.team import Team, TeamRunEvent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

---

## Structured Output Streaming

**URL:** llms-txt#structured-output-streaming

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/structured_input_output/structured_output_streaming

This example demonstrates streaming structured output from a team, using Pydantic models to ensure validated data structures while providing real-time streaming responses.

```python cookbook/examples/teams/structured_input_output/04_structured_output_streaming.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.exa import ExaTools
from pydantic import BaseModel

class StockAnalysis(BaseModel):
    symbol: str
    company_name: str
    analysis: str

stock_searcher = Agent(
    name="Stock Searcher",
    model=OpenAIChat("gpt-5-mini"),
    output_schema=StockAnalysis,
    role="Searches the web for information on a stock.",
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            highlights=False,
            show_results=True,
        )
    ],
)

class CompanyAnalysis(BaseModel):
    company_name: str
    analysis: str

company_info_agent = Agent(
    name="Company Info Searcher",
    model=OpenAIChat("gpt-5-mini"),
    role="Searches the web for information on a stock.",
    output_schema=CompanyAnalysis,
    tools=[
        ExaTools(
            include_domains=["cnbc.com", "reuters.com", "bloomberg.com", "wsj.com"],
            text=False,
            highlights=False,
            show_results=True,
        )
    ],
)

class StockReport(BaseModel):
    symbol: str
    company_name: str
    analysis: str

team = Team(
    name="Stock Research Team",
    model=OpenAIChat("gpt-5-mini"),
    members=[stock_searcher, company_info_agent],
    output_schema=StockReport,
    markdown=True,
    show_members_responses=True,
)

---

## Async Multi-Language Team

**URL:** llms-txt#async-multi-language-team

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/async/async_respond_directly

This example demonstrates an asynchronous route team of AI agents working together to answer questions in different languages. The team consists of six specialized language agents (English, Japanese, Chinese, Spanish, French, and German) with a team leader that routes user questions to the appropriate language agent based on the input language.

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

## External Tool Execution Stream

**URL:** llms-txt#external-tool-execution-stream

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/external_tool_execution_stream

This example demonstrates how to execute tools outside of the agent using external tool execution with streaming responses. It shows how to handle external tool execution while maintaining real-time streaming capabilities.

```python external_tool_execution_stream.py theme={null}
"""🤝 Human-in-the-Loop: Execute a tool call outside of the agent

This example shows how to implement human-in-the-loop functionality in your Agno tools.
It shows how to:
- Use external tool execution to execute a tool call outside of the agent

Run `pip install openai agno` to install dependencies.
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.utils import pprint

---

## Dynamic Session State

**URL:** llms-txt#dynamic-session-state

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/state/dynamic_session_state

This example demonstrates how to use tool hooks to dynamically manage session state. It shows how to create a customer management system that updates session state through tool interactions rather than direct modification.

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

<Link href="https://github.com/agno-agi/agno/tree/main/cookbook/agents/state" target="_blank">
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

## Condition steps workflow

**URL:** llms-txt#condition-steps-workflow

Source: https://docs.agno.com/examples/concepts/workflows/02-workflows-conditional-execution/condition_steps_workflow_stream

This example demonstrates how to use conditional steps in a workflow.

This example demonstrates **Workflows 2.0** conditional execution pattern. Shows how to conditionally execute steps based on content analysis,
providing intelligent selection of steps based on the actual data being processed.

**When to use**: When you need intelligent selection of steps based on content analysis rather than
simple input parameters or some other business logic. Ideal for quality gates, content-specific processing, or
adaptive workflows that respond to intermediate results.

```python condition_steps_workflow_stream.py theme={null}
from agno.agent.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.workflow.condition import Condition
from agno.workflow.step import Step
from agno.workflow.types import StepInput
from agno.workflow.workflow import Workflow

---

## Study Partner

**URL:** llms-txt#study-partner

**Contents:**
- Description
- Code
- Usage

Source: https://docs.agno.com/examples/use-cases/agents/study-partner

This Study Partner agent demonstrates how to create an AI-powered study partner that combines multiple information sources and tools to provide comprehensive learning support. The agent showcases several key capabilities:

**Multi-tool Integration**: Combines Exa search tools for web research and YouTube tools for video content discovery, enabling the agent to access diverse learning resources.

**Personalized Learning Support**: Creates customized study plans based on user constraints (time available, current knowledge level, daily study hours) and learning preferences.

**Resource Curation**: Searches and recommends high-quality learning materials including documentation, tutorials, research papers, and community discussions from reliable sources.

**Interactive Learning**: Provides step-by-step explanations, practical examples, and hands-on project suggestions to reinforce understanding.

**Progress Tracking**: Designs structured study plans with clear milestones and deadlines to help users stay on track with their learning goals.

**Learning Strategy**: Offers tips on effective study techniques, time management, and motivation maintenance for sustained learning success.

This example is particularly useful for developers, students, or anyone looking to build AI agents that can assist with educational content discovery, personalized learning path creation, and comprehensive study support across various subjects and skill levels.

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

## Session State In Context

**URL:** llms-txt#session-state-in-context

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/state/session_state_in_context

This example demonstrates how to use session state with PostgreSQL database and manage user context across different sessions. It shows how session state persists and can be retrieved for different users and sessions.

```python session_state_in_context.py theme={null}
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

db = PostgresDb(db_url=db_url, session_table="sessions")

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    instructions="Users name is {user_name} and age is {age}",
    db=db,
)

---

## Tool Confirmation Required

**URL:** llms-txt#tool-confirmation-required

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/confirmation_required

This example demonstrates how to implement human-in-the-loop functionality by requiring user confirmation before executing sensitive tool operations, such as API calls or data modifications.

```python confirmation_required.py theme={null}
"""🤝 Human-in-the-Loop: Adding User Confirmation to Tool Calls

This example shows how to implement human-in-the-loop functionality in your Agno tools.
It shows how to:
- Handle user confirmation during tool execution
- Gracefully cancel operations based on user choice

Some practical applications:
- Confirming sensitive operations before execution
- Reviewing API calls before they're made
- Validating data transformations
- Approving automated actions in critical systems

Run `pip install openai httpx rich agno` to install dependencies.
"""

import httpx
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.utils import pprint
from rich.console import Console
from rich.prompt import Prompt

@tool(requires_confirmation=True)
def get_top_hackernews_stories(num_stories: int) -> str:
    """Fetch top stories from Hacker News.

Args:
        num_stories (int): Number of stories to retrieve

Returns:
        str: JSON string containing story details
    """
    # Fetch top story IDs
    response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    story_ids = response.json()

# Yield story details
    all_stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        )
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        all_stories.append(story)
    return json.dumps(all_stories)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[get_top_hackernews_stories],
    markdown=True,
    db=SqliteDb(session_table="test_session", db_file="tmp/example.db"),
)

run_response = agent.run("Fetch the top 2 hackernews stories.")
if run_response.is_paused:
    for tool in run_response.tools_requiring_confirmation:
        # Ask for confirmation
        console.print(
            f"Tool name [bold blue]{tool.tool_name}({tool.tool_args})[/] requires confirmation."
        )
        message = (
            Prompt.ask("Do you want to continue?", choices=["y", "n"], default="y")
            .strip()
            .lower()
        )

if message == "n":
            tool.confirmed = False
        else:
            # We update the tools in place
            tool.confirmed = True

run_response = agent.continue_run(run_response=run_response)

---

## Capturing Team Responses as Variables

**URL:** llms-txt#capturing-team-responses-as-variables

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/other/response_as_variable

This example demonstrates how to capture team responses as variables and validate them using Pydantic models. It shows a routing team that analyzes stocks and company news, with structured responses for different types of queries.

```python cookbook/examples/teams/basic/response_as_variable.py theme={null}
"""
This example demonstrates how to capture team responses as variables.

Shows how to get structured responses from teams and validate them using
Pydantic models for different types of queries.
"""

from typing import Iterator  # noqa
from pydantic import BaseModel
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.utils.pprint import pprint_run_response
from agno.tools.exa import ExaTools

class StockAnalysis(BaseModel):
    """Stock analysis data structure."""

symbol: str
    company_name: str
    analysis: str

class CompanyAnalysis(BaseModel):
    """Company analysis data structure."""

company_name: str
    analysis: str

---

## Image to Audio Story Generation

**URL:** llms-txt#image-to-audio-story-generation

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/image_to_audio

This example demonstrates how to analyze an image to create a story and then convert that story to audio narration.

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

## Access Session State in Condition Evaluator Function

**URL:** llms-txt#access-session-state-in-condition-evaluator-function

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/access_session_state_in_condition_evaluator_function

This example demonstrates how to access session state in the evaluator function of a condition step

1. How to use `session_state` in a Condition evaluator function
2. Reading and modifying `session_state` based on condition logic
3. Accessing `user_id` and `session_id` from `session_state`
4. Making conditional decisions based on `session_state`

```python access_session_state_in_condition_evaluator_function.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.workflow.condition import Condition
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

def check_user_has_context(step_input: StepInput, session_state: dict) -> bool:
    """
    Condition evaluator that checks if user has been greeted before.

Args:
        step_input: The input for this step (contains workflow context)
        session_state: The shared session state dictionary

Returns:
        bool: True if user has context, False otherwise
    """
    print("\n=== Evaluating Condition ===")
    print(f"User ID: {session_state.get('current_user_id')}")
    print(f"Session ID: {session_state.get('current_session_id')}")
    print(f"Has been greeted: {session_state.get('has_been_greeted', False)}")

# Check if user has been greeted before
    return session_state.get("has_been_greeted", False)

def mark_user_as_greeted(step_input: StepInput, session_state: dict) -> StepOutput:
    """Custom function that marks user as greeted in session state."""
    print("\n=== Marking User as Greeted ===")
    session_state["has_been_greeted"] = True
    session_state["greeting_count"] = session_state.get("greeting_count", 0) + 1

return StepOutput(
        content=f"User has been greeted. Total greetings: {session_state['greeting_count']}"
    )

---

## Structured Input with Pydantic Models

**URL:** llms-txt#structured-input-with-pydantic-models

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/structured_input

This example demonstrates how to use structured Pydantic models as input to agents, enabling type-safe and validated input parameters for complex research tasks.

```python structured_input.py theme={null}
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

## Workflow with History Enabled for Steps

**URL:** llms-txt#workflow-with-history-enabled-for-steps

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/workflow_history/02_workflow_with_history_enabled_for_steps

This example demonstrates a workflow with history enabled for specific steps.

This example shows how to use the `add_workflow_history_to_steps` flag to add workflow history to multiple steps in the workflow.
In this case we have a workflow with three steps.

* The first step is a meal suggester that suggests meal categories and cuisines.
* The second step is a preference analysis step that analyzes the conversation history to understand user food preferences.
* The third step is a recipe specialist that provides recipe recommendations based on the user's preferences.

```python 02_workflow_with_history_enabled_for_steps.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## Workflow using steps

**URL:** llms-txt#workflow-using-steps

Source: https://docs.agno.com/examples/concepts/workflows/01-basic-workflows/workflow_using_steps

This example demonstrates how to use the Steps object to organize multiple individual steps into logical sequences.

This example demonstrates **Workflows** using the Steps object to organize multiple
individual steps into logical sequences. This pattern allows you to define reusable step
sequences and choose which sequences to execute in your workflow.

**When to use**: When you have logical groupings of steps that you want to organize, reuse,
or selectively execute. Ideal for creating modular workflow components that can be mixed
and matched based on different scenarios.

```python workflow_using_steps.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.workflow.step import Step
from agno.workflow.steps import Steps
from agno.workflow.workflow import Workflow

---

## Arize Phoenix via OpenInference

**URL:** llms-txt#arize-phoenix-via-openinference

**Contents:**
- Overview
- Code

Source: https://docs.agno.com/examples/concepts/integrations/observability/arize-phoenix-via-openinference

This example demonstrates how to instrument your Agno agent with OpenInference and send traces to Arize Phoenix.

```python  theme={null}
import asyncio
import os

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from phoenix.otel import register

---

## External Tool Execution Toolkit

**URL:** llms-txt#external-tool-execution-toolkit

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/external_tool_execution_toolkit

This example demonstrates how to execute toolkit-based tools outside of the agent using external tool execution. It shows how to create a custom toolkit with tools that require external execution.

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

## Confirmation Required with Async Streaming

**URL:** llms-txt#confirmation-required-with-async-streaming

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/confirmation_required_stream_async

This example demonstrates human-in-the-loop functionality with asynchronous streaming responses. It shows how to handle user confirmation during tool execution in an async environment while maintaining real-time streaming.

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

## Distributed RAG with Advanced Reranking

**URL:** llms-txt#distributed-rag-with-advanced-reranking

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/distributed_rag/distributed_rag_with_reranking

This example demonstrates how multiple specialized agents coordinate to provide comprehensive RAG responses using advanced reranking strategies for optimal information retrieval and synthesis. The team includes initial retrieval, reranking optimization, context analysis, and final synthesis.

```python cookbook/examples/teams/distributed_rag/03_distributed_rag_with_reranking.py theme={null}
"""
This example demonstrates how multiple specialized agents coordinate to provide
comprehensive RAG responses using advanced reranking strategies for optimal
information retrieval and synthesis.

Team Composition:
- Initial Retriever: Performs broad initial retrieval from knowledge base
- Reranking Specialist: Applies advanced reranking for result optimization
- Context Analyzer: Analyzes context and relevance of reranked results
- Final Synthesizer: Synthesizes reranked results into optimal responses

Setup:
1. Run: `pip install openai lancedb tantivy pypdf sqlalchemy agno`
2. Run this script to see advanced reranking RAG in action
"""

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reranker import CohereReranker
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.utils.print_response.team import aprint_response, print_response
from agno.vectordb.lancedb import LanceDb, SearchType

---

## Access Dependencies in Tool

**URL:** llms-txt#access-dependencies-in-tool

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/dependencies/access_dependencies_in_tool

How to access dependencies passed to an agent in a tool

This example demonstrates how tools can access dependencies passed to the agent,
allowing tools to utilize dynamic context like user profiles and current time information for enhanced functionality.

```python access_dependencies_in_tool.py theme={null}
from typing import Dict, Any, Optional
from datetime import datetime

from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_current_context() -> dict:
    """Get current contextual information like time, weather, etc."""
    return {
        "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "PST",
        "day_of_week": datetime.now().strftime("%A"),
    }

def analyze_user(user_id: str, dependencies: Optional[Dict[str, Any]] = None) -> str:
    """
    Analyze a specific user's profile and provide insights.
    
    This tool analyzes user behavior and preferences using available data sources.
    Call this tool with the user_id you want to analyze.
    
    Args:
        user_id: The user ID to analyze (e.g., 'john_doe', 'jane_smith')
        dependencies: Available data sources (automatically provided)
    
    Returns:
        Detailed analysis and insights about the user
    """
    if not dependencies:
        return "No data sources available for analysis."
    
    print(f"--> Tool received data sources: {list(dependencies.keys())}")
    
    results = [f"=== USER ANALYSIS FOR {user_id.upper()} ==="]
    
    # Use user profile data if available
    if "user_profile" in dependencies:
        profile_data = dependencies["user_profile"]
        results.append(f"Profile Data: {profile_data}")
        
        # Add analysis based on the profile
        if profile_data.get("role"):
            results.append(f"Professional Analysis: {profile_data['role']} with expertise in {', '.join(profile_data.get('preferences', []))}")
    
    # Use current context data if available
    if "current_context" in dependencies:
        context_data = dependencies["current_context"]
        results.append(f"Current Context: {context_data}")
        results.append(f"Time-based Analysis: Analysis performed on {context_data['day_of_week']} at {context_data['current_time']}")

print(f"--> Tool returned results: {results}")
    
    return "\n\n".join(results)

---

## Audio Generation Tools

**URL:** llms-txt#audio-generation-tools

**Contents:**
- Developer Resources

Source: https://docs.agno.com/concepts/multimodal/audio/audio_generation

Learn how to use audio generation tools with Agno agents.

The following example demonstrates how to generate an audio using the ElevenLabs tool with an agent. See [Eleven Labs](https://elevenlabs.io/) for more details.

## Developer Resources

* See the [Music Generation](/examples/concepts/multimodal/generate-music-agent) example.

---

## Persistent Session Storage

**URL:** llms-txt#persistent-session-storage

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/session/01_persistent_session

This example demonstrates how to create an agent with persistent session storage using PostgreSQL, enabling conversation history to be maintained across different runs.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Setup PostgreSQL">
    
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

## Generate Image with Intermediate Steps

**URL:** llms-txt#generate-image-with-intermediate-steps

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/generate_image_with_intermediate_steps

This example demonstrates how to create an agent that generates images using DALL-E while streaming during the image creation process.

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

## Demo Gemma

**URL:** llms-txt#demo-gemma

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/models/ollama/demo_gemma

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install Ollama">
    Follow the [Ollama installation guide](https://github.com/ollama/ollama?tab=readme-ov-file#macos) and run:

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

## Class-based Executor

**URL:** llms-txt#class-based-executor

Source: https://docs.agno.com/examples/concepts/workflows/01-basic-workflows/class_based_executor

This example demonstrates how to use a class-based executor in a workflow.

This example demonstrates how to use a class-based executor in a workflow.

```python class_based_executor.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## Setup the Agno API App

**URL:** llms-txt#setup-the-agno-api-app

agent_os = AgentOS(
    description="Example app for basic agent with eval capabilities",
    id="eval-demo",
    agents=[basic_agent],
)
app = agent_os.get_app()

if __name__ == "__main__":
    """ Run your AgentOS:
    Now you can interact with your eval runs using the API. Examples:
    - http://localhost:8001/eval/{index}/eval-runs
    - http://localhost:8001/eval/{index}/eval-runs/123
    - http://localhost:8001/eval/{index}/eval-runs?agent_id=123
    - http://localhost:8001/eval/{index}/eval-runs?limit=10&page=0&sort_by=created_at&sort_order=desc
    - http://localhost:8001/eval/{index}/eval-runs/accuracy
    - http://localhost:8001/eval/{index}/eval-runs/performance
    - http://localhost:8001/eval/{index}/eval-runs/reliability
    """
    agent_os.serve(app="evals_demo:app", reload=True)

bash Mac theme={null}
      python evals_demo.py
      ```
    </CodeGroup>
  </Step>

<Step title="View the Evals Demo">
    Head over to <a href="https://os.agno.com/evaluation">[https://os.agno.com/evaluation](https://os.agno.com/evaluation)</a> to view the evals.
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
<Steps>
  <Step title="Run the Evals Demo">
    <CodeGroup>
```

---

## Workflow using Steps with Nested Pattern

**URL:** llms-txt#workflow-using-steps-with-nested-pattern

Source: https://docs.agno.com/examples/concepts/workflows/01-basic-workflows/workflow_using_steps_nested

This example demonstrates **Workflows 2.0** nested patterns using `Steps` to encapsulate a complex workflow with conditional parallel execution.

This example demonstrates **Workflows** nested patterns using `Steps` to encapsulate
a complex workflow with conditional parallel execution. It combines `Condition`, `Parallel`,
and `Steps` for modular and adaptive content creation.

```python workflow_using_steps_nested.py theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.condition import Condition
from agno.workflow.parallel import Parallel
from agno.workflow.step import Step
from agno.workflow.steps import Steps
from agno.workflow.workflow import Workflow

---

## Input Validation Pre-Hook

**URL:** llms-txt#input-validation-pre-hook

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/hooks/input_validation_pre_hook

This example demonstrates how to use a pre-hook to validate the input of an Team, before it is presented to the LLM.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run example">
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

  <Step title="Run example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Confirmation Required with Toolkit

**URL:** llms-txt#confirmation-required-with-toolkit

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/confirmation_required_toolkit

This example demonstrates human-in-the-loop functionality using toolkit-based tools that require confirmation. It shows how to handle user confirmation when working with pre-built tool collections like YFinanceTools.

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

## Multi Purpose CLI App with Workflow History

**URL:** llms-txt#multi-purpose-cli-app-with-workflow-history

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/workflow_history/05_multi_purpose_cli

This example demonstrates how to use workflow history in a multi purpose CLI.

This example shows how to use the `add_workflow_history_to_steps` flag to add workflow history to the steps.
In this case we have a multi-step workflow with a single agent.

We show different scenarios of a continuous execution of the workflow.
We have 5 different demos:

* Customer Support
* Medical Consultation
* Tutoring

```python 05_multi_purpose_cli.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow

---

## Multi-Purpose Reasoning Team

**URL:** llms-txt#multi-purpose-reasoning-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/reasoning/reasoning_multi_purpose_team

This example demonstrates a comprehensive team of specialist agents that uses reasoning tools to analyze questions and intelligently delegate tasks to appropriate members including web search, finance, writing, medical research, and code execution agents.

```python cookbook/examples/teams/reasoning/01_reasoning_multi_purpose_team.py theme={null}
"""
This example demonstrates a team of agents that can answer a variety of questions.

The team uses reasoning tools to reason about the questions and delegate to the appropriate agent.

The team consists of:
- A web agent that can search the web for information
- A finance agent that can get financial data
- A writer agent that can write content
- A calculator agent that can calculate
- A FastAPI assistant that can explain how to write FastAPI code
- A code execution agent that can execute code in a secure E2B sandbox
"""

import asyncio
from pathlib import Path
from textwrap import dedent

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.file import FileTools
from agno.tools.github import GithubTools
from agno.tools.knowledge import KnowledgeTools
from agno.tools.pubmed import PubmedTools
from agno.tools.python import PythonTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.exa import ExaTools
from agno.vectordb.lancedb import LanceDb
from agno.vectordb.search import SearchType

cwd = Path(__file__).parent.resolve()

---

## Input Transformation Pre-Hook

**URL:** llms-txt#input-transformation-pre-hook

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/hooks/input_transformation_pre_hook

This example demonstrates how to use a pre-hook to transform the input of an Team, before it is presented to the LLM.

```python  theme={null}
from typing import Optional

from agno.team import Team
from agno.models.openai import OpenAIChat
from agno.run.team import RunInput
from agno.session.team import TeamSession
from agno.utils.log import log_debug

def transform_input(
    run_input: RunInput,
    session: TeamSession,
    user_id: Optional[str] = None,
    debug_mode: Optional[bool] = None,
) -> None:
    """
    Pre-hook: Rewrite the input to be more relevant to the team's purpose.

This hook rewrites the input to be more relevant to the team's purpose.
    """
    log_debug(
        f"Transforming input: {run_input.input_content} for user {user_id} and session {session.session_id}"
    )

# Input transformation team
    transformer_team = Team(
        name="Input Transformer",
        model=OpenAIChat(id="gpt-5-mini"),
        instructions=[
            "You are an input transformation specialist.",
            "Rewrite the user request to be more relevant to the team's purpose.",
            "Use known context engineering standards to rewrite the input.",
            "Keep the input as concise as possible.",
            "The team's purpose is to provide investment guidance and financial planning advice.",
        ],
        debug_mode=debug_mode,
    )

transformation_result = transformer_team.run(
        input=f"Transform this user request: '{run_input.input_content}'"
    )

# Overwrite the input with the transformed input
    run_input.input_content = transformation_result.content
    log_debug(f"Transformed input: {run_input.input_content}")

print("🚀 Input Transformation Pre-Hook Example")
print("=" * 60)

---

## Confirmation Required with History

**URL:** llms-txt#confirmation-required-with-history

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/confirmation_required_with_history

This example demonstrates human-in-the-loop functionality while maintaining conversation history. It shows how user confirmation works when the agent has access to previous conversation context.

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

## User Input Required Stream Async

**URL:** llms-txt#user-input-required-stream-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/user_input_required_stream_async

This example demonstrates how to use the `requires_user_input` parameter with async streaming responses. It shows how to collect specific user input fields in an asynchronous environment while maintaining real-time streaming.

```python user_input_required_stream_async.py theme={null}
"""🤝 Human-in-the-Loop: Allowing users to provide input externally

This example shows how to use the `requires_user_input` parameter to allow users to provide input externally.
"""

import asyncio
from typing import List

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.tools.function import UserInputField

---

## Condition with list of steps

**URL:** llms-txt#condition-with-list-of-steps

Source: https://docs.agno.com/examples/concepts/workflows/02-workflows-conditional-execution/condition_with_list_of_steps

This example demonstrates how to use conditional step to execute multiple steps in parallel.

This example demonstrates **Workflows 2.0** advanced conditional execution where conditions
can trigger multiple steps and run in parallel. Shows how to create sophisticated branching
logic with complex multi-step sequences based on content analysis.

**When to use**: When different topics or content types require completely different
processing pipelines. Ideal for adaptive workflows where the research methodology
should change based on the subject matter or complexity requirements.

```python condition_with_list_of_steps.py theme={null}
from agno.agent.agent import Agent
from agno.tools.exa import ExaTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.condition import Condition
from agno.workflow.parallel import Parallel
from agno.workflow.step import Step
from agno.workflow.types import StepInput
from agno.workflow.workflow import Workflow

---

## Investment Report Generator

**URL:** llms-txt#investment-report-generator

Source: https://docs.agno.com/examples/use-cases/workflows/investment-report-generator

This example demonstrates how to build a sophisticated investment analysis system that combines market research, financial analysis, and portfolio management.

This advanced example demonstrates how to build a sophisticated investment analysis system that combines
market research, financial analysis, and portfolio management. The workflow uses a three-stage
approach:

1. Comprehensive stock analysis and market research
2. Investment potential evaluation and ranking
3. Strategic portfolio allocation recommendations

* Real-time market data analysis
* Professional financial research
* Investment risk assessment
* Portfolio allocation strategy
* Detailed investment rationale

Example companies to analyze:

* "AAPL, MSFT, GOOGL" (Tech Giants)
* "NVDA, AMD, INTC" (Semiconductor Leaders)
* "TSLA, F, GM" (Automotive Innovation)
* "JPM, BAC, GS" (Banking Sector)
* "AMZN, WMT, TGT" (Retail Competition)
* "PFE, JNJ, MRNA" (Healthcare Focus)
* "XOM, CVX, BP" (Energy Sector)

Run `pip install openai ddgs agno` to install dependencies.

```python investment_report_generator.py theme={null}
"""💰 Investment Report Generator - Your AI Financial Analysis Studio!

This advanced example demonstrates how to build a sophisticated investment analysis system that combines
market research, financial analysis, and portfolio management. The workflow uses a three-stage
approach:
1. Comprehensive stock analysis and market research
2. Investment potential evaluation and ranking
3. Strategic portfolio allocation recommendations

Key capabilities:
- Real-time market data analysis
- Professional financial research
- Investment risk assessment
- Portfolio allocation strategy
- Detailed investment rationale

Example companies to analyze:
- "AAPL, MSFT, GOOGL" (Tech Giants)
- "NVDA, AMD, INTC" (Semiconductor Leaders)
- "TSLA, F, GM" (Automotive Innovation)
- "JPM, BAC, GS" (Banking Sector)
- "AMZN, WMT, TGT" (Retail Competition)
- "PFE, JNJ, MRNA" (Healthcare Focus)
- "XOM, CVX, BP" (Energy Sector)

Run `pip install openai ddgs agno` to install dependencies.
"""

import asyncio
import random
from pathlib import Path
from shutil import rmtree
from textwrap import dedent

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.utils.pprint import pprint_run_response
from agno.workflow.types import WorkflowExecutionInput
from agno.workflow.workflow import Workflow
from pydantic import BaseModel

---

## Example: Create a dataframe with sample data and get the first 5 rows

**URL:** llms-txt#example:-create-a-dataframe-with-sample-data-and-get-the-first-5-rows

**Contents:**
- Toolkit Params
- Toolkit Functions
- Developer Resources

agent.print_response("""
Please perform these tasks:
1. Create a pandas dataframe named 'sales_data' using DataFrame() with this sample data:
   {'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04', '2023-01-05'],
    'product': ['Widget A', 'Widget B', 'Widget A', 'Widget C', 'Widget B'],
    'quantity': [10, 15, 8, 12, 20],
    'price': [9.99, 15.99, 9.99, 12.99, 15.99]}
2. Show me the first 5 rows of the sales_data dataframe
""")
```

| Parameter                        | Type   | Default | Description                                        |
| -------------------------------- | ------ | ------- | -------------------------------------------------- |
| `enable_create_pandas_dataframe` | `bool` | `True`  | Enables functionality to create pandas DataFrames. |
| `enable_run_dataframe_operation` | `bool` | `True`  | Enables functionality to run DataFrame operations. |
| `all`                            | `bool` | `False` | Enables all functionality when set to True.        |

| Function                  | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                           |
| ------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `create_pandas_dataframe` | Creates a Pandas DataFrame named `dataframe_name` by using the specified function `create_using_function` with parameters `function_parameters`. Parameters include 'dataframe\_name' for the name of the DataFrame, 'create\_using\_function' for the function to create it (e.g., 'read\_csv'), and 'function\_parameters' for the arguments required by the function. Returns the name of the created DataFrame if successful, otherwise returns an error message. |
| `run_dataframe_operation` | Runs a specified operation `operation` on a DataFrame `dataframe_name` with the parameters `operation_parameters`. Parameters include 'dataframe\_name' for the DataFrame to operate on, 'operation' for the operation to perform (e.g., 'head', 'tail'), and 'operation\_parameters' for the arguments required by the operation. Returns the result of the operation if successful, otherwise returns an error message.                                             |

## Developer Resources

* View [Tools](https://github.com/agno-agi/agno/blob/main/libs/agno/agno/tools/pandas.py)
* View [Cookbook](https://github.com/agno-agi/agno/tree/main/cookbook/tools/pandas_tools.py)

---

## Direct Response with Team History

**URL:** llms-txt#direct-response-with-team-history

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/teams/basic/respond_directly_with_history

This example demonstrates a team where the team leader routes requests to the appropriate member, and the members respond directly to the user.

In addition, the team has access to the conversation history through `add_history_to_context=True`.

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

## Run: `wget https://storage.googleapis.com/generativeai-downloads/images/GreatRedSpot.mp4` to download a sample video

**URL:** llms-txt#run:-`wget-https://storage.googleapis.com/generativeai-downloads/images/greatredspot.mp4`-to-download-a-sample-video

video_path = Path(__file__).parent.joinpath("samplevideo.mp4")
video_file = None
remote_file_name = f"files/{video_path.stem.lower().replace('_', '')}"
try:
    video_file = model.get_client().files.get(name=remote_file_name)
except Exception as e:
    logger.info(f"Error getting file {video_path.stem}: {e}")
    pass

---

## External Tool Execution

**URL:** llms-txt#external-tool-execution

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/external_tool_execution

This example demonstrates how to execute tools outside of the agent using external tool execution. This pattern allows you to control tool execution externally while maintaining agent functionality.

```python external_tool_execution.py theme={null}
"""🤝 Human-in-the-Loop: Execute a tool call outside of the agent

This example shows how to implement human-in-the-loop functionality in your Agno tools.
It shows how to:
- Use external tool execution to execute a tool call outside of the agent

Run `pip install openai agno` to install dependencies.
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.utils import pprint

---

## Session Summary with References

**URL:** llms-txt#session-summary-with-references

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/session/04_session_summary_references

This example demonstrates how to use session summaries with context references, enabling the agent to maintain conversation context and reference previous session summaries.

```python 04_session_summary_references.py theme={null}
"""
This example shows how to use the `add_session_summary_to_context` parameter in the Agent config to
add session summaries to the Agent context.

Start the postgres db locally on Docker by running: cookbook/scripts/run_pgvector.sh
"""

from agno.agent.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

db = PostgresDb(db_url=db_url, session_table="sessions")

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    db=db,
    session_id="session_summary",
    enable_session_summaries=True,
)

---

## Async Structured Output Streaming

**URL:** llms-txt#async-structured-output-streaming

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/structured_input_output/async_structured_output_streaming

This example demonstrates async structured output streaming from a team using Pydantic models to ensure structured responses while streaming, providing both real-time output and validated data structures asynchronously.

```python cookbook/examples/teams/structured_input_output/05_async_structured_output_streaming.py theme={null}
"""
This example demonstrates async structured output streaming from a team.

The team uses Pydantic models to ensure structured responses while streaming,
providing both real-time output and validated data structures asynchronously.
"""

import asyncio
from typing import Iterator  # noqa

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.exa import ExaTools
from agno.utils.pprint import apprint_run_response
from pydantic import BaseModel

class StockAnalysis(BaseModel):
    """Stock analysis data structure."""

symbol: str
    company_name: str
    analysis: str

class CompanyAnalysis(BaseModel):
    """Company analysis data structure."""

company_name: str
    analysis: str

class StockReport(BaseModel):
    """Final stock report data structure."""

symbol: str
    company_name: str
    analysis: str

---

## Store Events and Events to Skip in a Workflow

**URL:** llms-txt#store-events-and-events-to-skip-in-a-workflow

**Contents:**
- Key Features:

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/store_events_and_events_to_skip_in_a_workflow

This example demonstrates **Workflows 2.0** event storage capabilities

This example demonstrates **Workflows 2.0** event storage capabilities, showing how to:

1. **Store execution events** for debugging/auditing (`store_events=True`)
2. **Filter noisy events** (`events_to_skip`) to focus on critical workflow milestones
3. **Access stored events** post-execution via `workflow.run_response.events`

* **Selective Storage**: Skip verbose events (e.g., `step_started`) while retaining key milestones.
* **Debugging/Audit**: Capture execution flow for analysis without manual logging.
* **Performance Optimization**: Reduce storage overhead by filtering non-essential events.

```python store_events_and_events_to_skip_in_a_workflow.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.run.agent import (
    RunContentEvent,
    ToolCallCompletedEvent,
    ToolCallStartedEvent,
)
from agno.run.workflow import WorkflowRunEvent, WorkflowRunOutput
from agno.tools.hackernews import HackerNewsTools
from agno.run.agent import RunEvent
from agno.workflow.parallel import Parallel
from agno.workflow.step import Step
from agno.workflow.workflow import Workflow

---

## Async Multi-Purpose Reasoning Team

**URL:** llms-txt#async-multi-purpose-reasoning-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/reasoning/async_multi_purpose_reasoning_team

This example demonstrates an asynchronous multi-purpose reasoning team that uses reasoning tools to analyze questions and delegate to appropriate specialist agents asynchronously, showcasing coordination and intelligent task routing.

```python cookbook/examples/teams/reasoning/02_async_multi_purpose_reasoning_team.py theme={null}
"""
This example demonstrates an async multi-purpose reasoning team.

The team uses reasoning tools to analyze questions and delegate to appropriate
specialist agents asynchronously, showcasing coordination and intelligent task routing.
"""

import asyncio
from pathlib import Path

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.calculator import CalculatorTools
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.e2b import E2BTools
from agno.tools.knowledge import KnowledgeTools
from agno.tools.pubmed import PubmedTools
from agno.tools.reasoning import ReasoningTools
from agno.tools.exa import ExaTools
from agno.vectordb.lancedb.lance_db import LanceDb
from agno.vectordb.search import SearchType

cwd = Path(__file__).parent.resolve()

---

## Generate Video Using Replicate

**URL:** llms-txt#generate-video-using-replicate

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/generate_video_using_replicate

This example demonstrates how to create an AI agent that generates videos using the Replicate API with the HunyuanVideo model.

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

## Step with Function using Additional Data

**URL:** llms-txt#step-with-function-using-additional-data

**Contents:**
- Key Features:

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/step_with_function_additional_data

This example demonstrates **Workflows 2.0** support for passing metadata and contextual information to steps via `additional_data`.

This example shows how to pass metadata and contextual information to steps via `additional_data`. This allows separation of workflow logic from configuration, enabling dynamic behavior based on external context.

* **Context-Aware Steps**: Access `step_input.additional_data` in custom functions
* **Flexible Metadata**: Pass user info, priorities, settings, etc.
* **Clean Separation**: Keep workflow logic focused while enriching steps with context

```python step_with_function_additional_data.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## Research Workflow

**URL:** llms-txt#research-workflow

**Contents:**
- Code

Source: https://docs.agno.com/examples/getting-started/19-blog-generator-workflow

This advanced example demonstrates how to build a sophisticated blog post generator using
the new workflow v2.0 architecture. The workflow combines web research capabilities with
professional writing expertise using a multi-stage approach:

1. Intelligent web research and source gathering
2. Content extraction and processing
3. Professional blog post writing with proper citations

* Advanced web research and source evaluation
* Content scraping and processing
* Professional writing with SEO optimization
* Automatic content caching for efficiency
* Source attribution and fact verification

```python blog-generator-workflow.py theme={null}
import asyncio
import json
from textwrap import dedent
from typing import Dict, Optional

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.newspaper4k import Newspaper4kTools
from agno.utils.log import logger
from agno.utils.pprint import pprint_run_response
from agno.workflow.workflow import Workflow
from pydantic import BaseModel, Field

---

## Access Multiple Previous Steps Output

**URL:** llms-txt#access-multiple-previous-steps-output

**Contents:**
- Key Features:

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/access_multiple_previous_steps_output

This example demonstrates **Workflows 2.0** advanced data flow capabilities

This example demonstrates **Workflows 2.0** shows how to:

1. Access outputs from **specific named steps** (`get_step_content()`)
2. Aggregate **all previous outputs** (`get_all_previous_content()`)
3. Create comprehensive reports by combining multiple research sources

* **Step Output Access**: Retrieve data from any previous step by name or collectively.
* **Custom Reporting**: Combine and analyze outputs from parallel or sequential steps.
* **Streaming Support**: Real-time updates during execution.

```python access_multiple_previous_steps_output.py theme={null}
from agno.agent.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step
from agno.workflow.types import StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## File Input for Tools

**URL:** llms-txt#file-input-for-tools

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/file_input_for_tool

This example demonstrates how tools can access and process files (PDFs, documents, etc.) passed to the agent. It shows uploading a PDF file, processing it with a custom tool, and having the LLM respond based on the extracted content.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Set your API key">
    
  </Step>

<Step title="Install libraries">
    
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

  <Step title="Create a Python file">
    Create a Python file and add the above code.
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run Agent">
    <CodeGroup>
```

---

## Run Response Events

**URL:** llms-txt#run-response-events

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/other/run_response_events

This example demonstrates how to handle different types of events during agent run streaming. It shows how to capture and process content events, tool call started events, and tool call completed events.

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

## Basic Session State Management

**URL:** llms-txt#basic-session-state-management

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/state/session_state_basic

This example demonstrates how to create an agent with basic session state management, maintaining a shopping list across interactions using SQLite storage.

```python session_state_basic.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

def add_item(session_state, item: str) -> str:
    """Add an item to the shopping list."""
    session_state["shopping_list"].append(item)  # type: ignore
    return f"The shopping list is now {session_state['shopping_list']}"  # type: ignore

---

## Confirmation Required with Mixed Tools

**URL:** llms-txt#confirmation-required-with-mixed-tools

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/confirmation_required_mixed_tools

This example demonstrates human-in-the-loop functionality where only some tools require user confirmation. The agent executes tools that don't require confirmation automatically and pauses only for tools that need approval.

```python confirmation_required_mixed_tools.py theme={null}
"""🤝 Human-in-the-Loop: Adding User Confirmation to Tool Calls

This example shows how to implement human-in-the-loop functionality in your Agno tools.

In this case we have multiple tools and only one of them requires confirmation.

The agent should execute the tool that doesn't require confirmation and then pause for user confirmation.

The user can then either approve or reject the tool call and the agent should continue from where it left off.
"""

import httpx
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.utils import pprint
from rich.console import Console
from rich.prompt import Prompt

def get_top_hackernews_stories(num_stories: int) -> str:
    """Fetch top stories from Hacker News.

Args:
        num_stories (int): Number of stories to retrieve

Returns:
        str: JSON string containing story details
    """
    # Fetch top story IDs
    response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    story_ids = response.json()

# Yield story details
    all_stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        )
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        all_stories.append(story)
    return json.dumps(all_stories)

@tool(requires_confirmation=True)
def send_email(to: str, subject: str, body: str) -> str:
    """Send an email.

Args:
        to (str): Email address to send to
        subject (str): Subject of the email
        body (str): Body of the email
    """
    return f"Email sent to {to} with subject {subject} and body {body}"

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[get_top_hackernews_stories, send_email],
    markdown=True,
)

run_response = agent.run(
    "Fetch the top 2 hackernews stories and email them to john@doe.com."
)
if run_response.is_paused:
    for tool in run_response.tools:  # type: ignore
        if tool.requires_confirmation:
            # Ask for confirmation
            console.print(
                f"Tool name [bold blue]{tool.tool_name}({tool.tool_args})[/] requires confirmation."
            )
            message = (
                Prompt.ask("Do you want to continue?", choices=["y", "n"], default="y")
                .strip()
                .lower()
            )

if message == "n":
                tool.confirmed = False
            else:
                # We update the tools in place
                tool.confirmed = True
        else:
            console.print(
                f"Tool name [bold blue]{tool.tool_name}({tool.tool_args})[/] was completed in [bold green]{tool.metrics.duration:.2f}[/] seconds."  # type: ignore
            )

run_response = agent.continue_run(run_response=run_response)
    pprint.pprint_run_response(run_response)

---

## More examples:

**URL:** llms-txt#more-examples:

---

## Confirmation Required with Multiple Tools

**URL:** llms-txt#confirmation-required-with-multiple-tools

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/confirmation_required_multiple_tools

This example demonstrates human-in-the-loop functionality with multiple tools that require confirmation. It shows how to handle user confirmation during tool execution and gracefully cancel operations based on user choice.

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

## Output Transformation Post-Hook

**URL:** llms-txt#output-transformation-post-hook

**Contents:**
- Code
  - Key Takeaways
  - Important Disclaimer
  - Questions to Consider Next
- Usage

Source: https://docs.agno.com/examples/concepts/teams/hooks/output_transformation_post_hook

This example demonstrates how to use a post-hook to transform the output of an Team, before it is returned to the user.

This example shows how to:

1. Transform team responses by updating RunOutput.content
2. Add formatting, structure, and additional information
3. Enhance the user experience through content modification

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run example">
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

  <Step title="Run example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Debug Level

**URL:** llms-txt#debug-level

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/other/debug_level

This example demonstrates how to set different debug levels for an agent. The debug level controls the amount of debug information displayed, helping you troubleshoot and understand agent behavior at different levels of detail.

```python debug_level.py theme={null}
"""
This example shows how to set the debug level of an agent.

The debug level is a number between 1 and 2.

1: Basic debug information
2: Detailed debug information

The default debug level is 1.
"""

from agno.agent.agent import Agent
from agno.models.anthropic.claude import Claude
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Team Input as Image List

**URL:** llms-txt#team-input-as-image-list

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/other/input_as_list

This example demonstrates how to pass input to a team as a list containing both text and images. The team processes multimodal input including text descriptions and image URLs for analysis.

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

## Multi-user, Multi-session Chat

**URL:** llms-txt#multi-user,-multi-session-chat

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/memory/05-multi-user-multi-session-chat

This example demonstrates how to run a multi-user, multi-session chat.

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

## Distributed RAG with PgVector

**URL:** llms-txt#distributed-rag-with-pgvector

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/distributed_rag/distributed_rag_pgvector

This example demonstrates how multiple specialized agents coordinate to provide comprehensive RAG responses using distributed PostgreSQL vector databases with pgvector for scalable, production-ready retrieval. The team includes vector retrieval, hybrid search, data validation, and response composition specialists.

```python cookbook/examples/teams/distributed_rag/01_distributed_rag_pgvector.py theme={null}
"""
This example demonstrates how multiple specialized agents coordinate to provide
comprehensive RAG responses using distributed PostgreSQL vector databases with
pgvector for scalable, production-ready retrieval.

Team Composition:
- Vector Retriever: Specialized in vector similarity search using pgvector
- Hybrid Searcher: Combines vector and text search for comprehensive results
- Data Validator: Validates retrieved data quality and relevance
- Response Composer: Composes final responses with proper source attribution

Setup:
1. Run: `./cookbook/run_pgvector.sh` to start a postgres container with pgvector
2. Run: `pip install openai sqlalchemy 'psycopg[binary]' pgvector agno`
3. Run this script to see distributed PgVector RAG in action
"""

import asyncio  # noqa: F401

from agno.agent import Agent
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.knowledge.knowledge import Knowledge
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.vectordb.pgvector import PgVector, SearchType

---

## Session State in Instructions

**URL:** llms-txt#session-state-in-instructions

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/state/session_state_in_instructions

This example demonstrates how to use session state variables directly in team instructions using template syntax. The session state values are automatically injected into the instructions, making them available to the team during execution.

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

## User Input Required Stream

**URL:** llms-txt#user-input-required-stream

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/user_input_required_stream

This example demonstrates how to use the `requires_user_input` parameter with streaming responses. It shows how to collect specific user input fields while maintaining real-time streaming capabilities.

```python user_input_required_stream.py theme={null}
"""🤝 Human-in-the-Loop: Allowing users to provide input externally

This example shows how to use the `requires_user_input` parameter to allow users to provide input externally.
"""

from typing import List

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.tools.function import UserInputField
from agno.utils import pprint

---

## Few-shot examples showing good support patterns

**URL:** llms-txt#few-shot-examples-showing-good-support-patterns

**Contents:**
- Usage

support_examples = [
    # Example 1: Simple issue resolution
    Message(role="user", content="I forgot my password and can't log in"),
    Message(
        role="assistant",
        content="""
    I'll help you reset your password right away.
    
    **Transferring to Support Specialist**: Please assist this customer with password reset:
    - Guide them through the password reset process
    - Verify their identity if needed  
    - Ensure they can successfully log in
    - Provide tips for creating a secure password
    
    Expected outcome: Customer successfully logs in with new password.
    """.strip(),
    ),
    # Example 2: Escalation pattern
    Message(
        role="user",
        content="I've been charged twice for the same order and your chat bot couldn't help!",
    ),
    Message(
        role="assistant",
        content="""
        I sincerely apologize for the billing issue and the frustration with our chat system.

**Transferring to Escalation Manager**: Priority billing issue requiring immediate attention:
        - Customer charged twice for same order
        - Previous automated support was unsuccessful
        - Customer is understandably frustrated
        - Needs immediate resolution and possible compensation

Expected outcome: Billing corrected, customer satisfaction restored, and follow-up to prevent recurrence.
        """.strip(),
    ),
    # Example 3: Proactive support
    Message(role="user", content="Your app keeps crashing when I try to upload photos"),
    Message(
        role="assistant",
        content="""
    I'm sorry you're experiencing crashes with photo uploads. Let me get this resolved for you.

**Transferring to Support Specialist**: Technical issue with photo upload feature:
    - App crashes during photo upload process
    - Need to troubleshoot device compatibility and app version
    - Provide workaround solutions if available
    - Escalate to technical team if it's a known bug

Expected outcome: Upload feature working properly or clear timeline for fix provided.
        """.strip(),
    ),
]

if __name__ == "__main__":
    # Support Agent
    support_agent = Agent(
        name="Support Specialist",
        role="Handle customer inquiries",
        model=OpenAIChat(id="gpt-5-mini"),
        instructions=[
            "You are a helpful customer support specialist.",
            "Always be polite, professional, and solution-oriented.",
        ],
    )

# Escalation Agent
    escalation_agent = Agent(
        name="Escalation Manager",
        role="Handle complex issues",
        model=OpenAIChat(id="gpt-5-mini"),
        instructions=[
            "You handle escalated customer issues that require management attention.",
            "Focus on customer satisfaction and finding solutions.",
        ],
    )

# Create team with few-shot learning
    team = Team(
        name="Customer Support Team",
        members=[support_agent, escalation_agent],
        model=OpenAIChat(id="gpt-5-mini"),
        add_name_to_context=True,
        additional_input=support_examples,  # 🆕 Teaching examples
        instructions=[
            "You coordinate customer support with excellence and empathy.",
            "Follow established patterns for proper issue resolution.",
            "Always prioritize customer satisfaction and clear communication.",
        ],
        debug_mode=True,
        markdown=True,
    )

scenarios = [
        "I can't find my order confirmation email",
        "The product I received is damaged",
        "I want to cancel my subscription but the website won't let me",
    ]

for i, scenario in enumerate(scenarios, 1):
        print(f"📞 Scenario {i}: {scenario}")
        print("-" * 50)
        team.print_response(scenario)
bash  theme={null}
    pip install agno openai
    bash  theme={null}
    export OPENAI_API_KEY=****
    bash  theme={null}
    python cookbook/examples/teams/basic/few_shot_learning.py
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

## JWT Middleware with Authorization Headers

**URL:** llms-txt#jwt-middleware-with-authorization-headers

**Contents:**
- Code

Source: https://docs.agno.com/examples/agent-os/middleware/jwt-middleware

AgentOS with JWT middleware for authentication and parameter injection using Authorization headers

This example demonstrates how to use JWT middleware with AgentOS for authentication and automatic parameter injection using Authorization headers.

```python jwt_middleware.py theme={null}
from datetime import UTC, datetime, timedelta

import jwt
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.os.middleware import JWTMiddleware

---

## Audio Streaming

**URL:** llms-txt#audio-streaming

Source: https://docs.agno.com/examples/concepts/agent/multimodal/audio_streaming

This example demonstrates how to use Agno agents to generate streaming audio responses using OpenAI's GPT-4o audio preview model.

```python  theme={null}
import base64
import wave
from typing import Iterator

from agno.agent import Agent, RunOutputEvent
from agno.models.openai import OpenAIChat

---

## Chat History Retrieval

**URL:** llms-txt#chat-history-retrieval

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/session/chat_history

This example demonstrates how to retrieve and display chat history from team sessions for conversation tracking and analysis.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install required libraries">
    
  </Step>

<Step title="Set environment variables">
    
  </Step>

<Step title="Start PostgreSQL database">
    
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

  <Step title="Start PostgreSQL database">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run the agent">
```

---

## Download all sample sales documents and get their paths

**URL:** llms-txt#download-all-sample-sales-documents-and-get-their-paths

downloaded_csv_paths = download_knowledge_filters_sample_data(
    num_files=4, file_extension=SampleDataFileExtension.CSV
)

---

## Delete operations examples

**URL:** llms-txt#delete-operations-examples

vector_db = knowledge.vector_db
vector_db.delete_by_name("Recipes")

---

## Share Member Interactions

**URL:** llms-txt#share-member-interactions

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/state/share_member_interactions

This example demonstrates how to enable sharing of member interactions within a team. When `share_member_interactions` is set to True, team members can see and build upon each other's responses, creating a collaborative workflow.

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

## Single Step Continuous Execution Workflow

**URL:** llms-txt#single-step-continuous-execution-workflow

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/workflow_history/01_single_step_continuous_execution_workflow

This example demonstrates a workflow with a single step that is executed continuously with access to workflow history.

This example shows how to use the `add_workflow_history_to_steps` flag to add workflow history to all the steps in the workflow.

In this case we have a single step workflow with a single agent.

The agent has access to the workflow history and uses it to provide personalized educational support.

---

## External Tool Execution Async Responses

**URL:** llms-txt#external-tool-execution-async-responses

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/external_tool_execution_async_responses

This example demonstrates external tool execution using OpenAI Responses API with gpt-4.1-mini model. It shows how to handle tool-call IDs and execute multiple external tools in a loop until completion.

```python external_tool_execution_async_responses.py theme={null}
"""🤝 Human-in-the-Loop with OpenAI Responses API (gpt-4.1-mini)

This example mirrors the external tool execution async example but uses
OpenAIResponses with gpt-4.1-mini to validate tool-call id handling.

Run `pip install openai agno` to install dependencies.
"""

import asyncio
import subprocess

from agno.agent import Agent
from agno.models.openai import OpenAIResponses
from agno.tools import tool
from agno.utils import pprint

---

## Custom Middleware

**URL:** llms-txt#custom-middleware

**Contents:**
- Code

Source: https://docs.agno.com/examples/agent-os/middleware/custom-middleware

AgentOS with custom middleware for rate limiting, logging, and monitoring

This example demonstrates how to create and add custom middleware to your AgentOS application. We implement two common middleware types: rate limiting and request/response logging.

```python custom_middleware.py theme={null}
import time
from collections import defaultdict, deque
from typing import Dict

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.tools.duckduckgo import DuckDuckGoTools
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

---

## Team with Tool Hooks

**URL:** llms-txt#team-with-tool-hooks

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/tools/team_with_tool_hooks

This example demonstrates how to use tool hooks with teams and agents for intercepting and monitoring tool function calls, providing logging, timing, and other observability features.

```python cookbook/examples/teams/tools/02_team_with_tool_hooks.py theme={null}
"""
This example demonstrates how to use tool hooks with teams and agents.

Tool hooks allow you to intercept and monitor tool function calls, providing
logging, timing, and other observability features.
"""

import time
from typing import Any, Callable, Dict
from uuid import uuid4

from agno.agent.agent import Agent
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.reddit import RedditTools
from agno.utils.log import logger

def logger_hook(function_name: str, function_call: Callable, arguments: Dict[str, Any]):
    """
    Tool hook that logs function calls and measures execution time.

Args:
        function_name: Name of the function being called
        function_call: The actual function to call
        arguments: Arguments passed to the function

Returns:
        The result of the function call
    """
    if function_name == "delegate_task_to_member":
        member_id = arguments.get("member_id")
        logger.info(f"Delegating task to member {member_id}")

# Start timer
    start_time = time.time()
    result = function_call(**arguments)
    # End timer
    end_time = time.time()
    duration = end_time - start_time
    logger.info(f"Function {function_name} took {duration:.2f} seconds to execute")
    return result

---

## Loop Steps Workflow

**URL:** llms-txt#loop-steps-workflow

Source: https://docs.agno.com/examples/concepts/workflows/03_workflows_loop_execution/loop_steps_workflow

This example demonstrates **Workflows 2.0** loop execution for quality-driven iterative processes.

This example demonstrates **Workflows 2.0** to repeatedly execute steps until specific conditions are met,
ensuring adequate research depth before proceeding to content creation.

**When to use**: When you need iterative refinement, quality assurance, or when the
required output quality can't be guaranteed in a single execution. Ideal for research
gathering, data collection, or any process where "good enough" is determined by content
analysis rather than a fixed number of iterations.

```python loop_steps_workflow.py theme={null}
from typing import List

from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow import Loop, Step, Workflow
from agno.workflow.types import StepOutput

---

## User Input Required for Tool Execution

**URL:** llms-txt#user-input-required-for-tool-execution

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/user_input_required

This example demonstrates how to create tools that require user input before execution, allowing for dynamic data collection during agent runs.

```python user_input_required.py theme={null}
"""🤝 Human-in-the-Loop: Allowing users to provide input externally

This example shows how to use the `requires_user_input` parameter to allow users to provide input externally.
"""

from typing import List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.tools.function import UserInputField
from agno.utils import pprint

---

## Early Stop a Workflow

**URL:** llms-txt#early-stop-a-workflow

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/early_stop_workflow

This example demonstrates **Workflows 2.0** early termination of a running workflow.

This example shows how to create workflows that can terminate
gracefully when quality conditions aren't met, preventing downstream processing of
invalid or unsafe data.

**When to use**: When you need safety mechanisms, quality gates, or validation checkpoints
that should prevent downstream processing if conditions aren't met. Ideal for data
validation pipelines, security checks, quality assurance workflows, or any process where
continuing with invalid inputs could cause problems.

```python early_stop_workflow_with_agents.py theme={null}
from agno.agent import Agent
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.workflow import Workflow
from agno.workflow.types import StepInput, StepOutput

---

## Video Caption Generation Team

**URL:** llms-txt#video-caption-generation-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/multimodal/video_caption_generation

This example demonstrates how a team can collaborate to process videos and generate captions by extracting audio, transcribing it, and embedding captions back into the video.

```python cookbook/examples/teams/multimodal/video_caption_generation.py theme={null}
"""Please install dependencies using:
pip install openai moviepy ffmpeg
"""

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.moviepy_video import MoviePyVideoTools
from agno.tools.openai import OpenAITools

video_processor = Agent(
    name="Video Processor",
    role="Handle video processing and audio extraction",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[MoviePyVideoTools(process_video=True, generate_captions=True)],
    instructions=[
        "Extract audio from videos for processing",
        "Handle video file operations efficiently",
    ],
)

caption_generator = Agent(
    name="Caption Generator",
    role="Generate and embed captions in videos",
    model=OpenAIChat(id="gpt-5-mini"),
    tools=[MoviePyVideoTools(embed_captions=True), OpenAITools()],
    instructions=[
        "Transcribe audio to create accurate captions",
        "Generate SRT format captions with proper timing",
        "Embed captions seamlessly into videos",
    ],
)

---

## Session State for Multiple Users

**URL:** llms-txt#session-state-for-multiple-users

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/state/session_state_multiple_users

This example demonstrates how to maintain separate session state for multiple users in a multi-user environment, with each user having their own shopping lists and sessions.

```python session_state_multiple_users.py theme={null}
"""
This example demonstrates how to maintain state for each user in a multi-user environment.

The shopping list is stored in a dictionary, organized by user ID and session ID.

Agno automatically creates the "current_user_id" and "current_session_id" variables in the session state.

You can access these variables in your functions using the `agent.get_session_state()` dictionary.
"""

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat

---

## Condition and Parallel Steps Workflow

**URL:** llms-txt#condition-and-parallel-steps-workflow

Source: https://docs.agno.com/examples/concepts/workflows/02-workflows-conditional-execution/condition_and_parallel_steps_stream

This example demonstrates **Workflows 2.0** advanced pattern combining conditional execution with parallel processing.

This example shows how to create sophisticated workflows where multiple
conditions evaluate simultaneously, each potentially triggering different research strategies
based on comprehensive content analysis.

**When to use**: When you need comprehensive, multi-dimensional content analysis where
different aspects of the input may trigger different specialized research pipelines
simultaneously. Ideal for adaptive research workflows that can leverage multiple sources
based on various content characteristics.

```python condition_and_parallel_steps_stream.py theme={null}
from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.exa import ExaTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.condition import Condition
from agno.workflow.parallel import Parallel
from agno.workflow.step import Step
from agno.workflow.types import StepInput
from agno.workflow.workflow import Workflow

---

## Context Management with DateTime Instructions

**URL:** llms-txt#context-management-with-datetime-instructions

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/context_management/datetime_instructions

This example demonstrates how to add current date and time context to agent instructions, enabling the agent to provide time-aware responses.

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

## External Tool Execution Stream Async

**URL:** llms-txt#external-tool-execution-stream-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/external_tool_execution_stream_async

This example demonstrates how to execute tools outside of the agent using external tool execution with async streaming responses. It shows how to handle external tool execution in an asynchronous environment while maintaining real-time streaming.

```python external_tool_execution_stream_async.py theme={null}
"""🤝 Human-in-the-Loop: Execute a tool call outside of the agent

This example shows how to implement human-in-the-loop functionality in your Agno tools.
It shows how to:
- Use external tool execution to execute a tool call outside of the agent

Run `pip install openai agno` to install dependencies.
"""

import asyncio
import subprocess

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools import tool

---

## Team History for Members

**URL:** llms-txt#team-history-for-members

**Contents:**
- How it Works
- Code

Source: https://docs.agno.com/examples/concepts/teams/basic/team_history

This example demonstrates a team where the team leader routes requests to the appropriate member, and the members respond directly to the user.

Using `add_team_history_to_members=True`, each team member has access to the shared history of the team, allowing them to use context from previous interactions with other members.

When `add_team_history_to_members=True`, team history is appended to tasks sent to members:

This allows the Spanish agent to recall the name "John" that was originally shared with the German agent.

```python team_history.py theme={null}
from uuid import uuid4

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team.team import Team

german_agent = Agent(
    name="German Agent",
    role="You answer German questions.",
    model=OpenAIChat(id="o3-mini"),
)

spanish_agent = Agent(
    name="Spanish Agent",
    role="You answer Spanish questions.",
    model=OpenAIChat(id="o3-mini"),
)

multi_lingual_q_and_a_team = Team(
    name="Multi Lingual Q and A Team",
    model=OpenAIChat("o3-mini"),
    members=[german_agent, spanish_agent],
    instructions=[
        "You are a multi lingual Q and A team that can answer questions in English and Spanish. You MUST delegate the task to the appropriate member based on the language of the question.",
        "If the question is in German, delegate to the German agent. If the question is in Spanish, delegate to the Spanish agent.",
        "Always translate the response from the appropriate language to English and show both the original and translated responses.",
    ],
    db=SqliteDb(
        db_file="tmp/multi_lingual_q_and_a_team.db"
    ),  # Add a database to store the conversation history. This is a requirement for history to work correctly.
    determine_input_for_members=False,  # Send the input directly to the member agents without the team leader synthesizing its own input.
    respond_directly=True,
    add_team_history_to_members=True,  # Send all interactions between the user and the team to the member agents.
)

session_id = f"conversation_{uuid4()}"

**Examples:**

Example 1 (unknown):
```unknown
<team_history_context>
input: Hallo, wie heißt du? Meine Name ist John.
response: Ich heiße ChatGPT.
</team_history_context>
```

---

## Managing Tool Calls

**URL:** llms-txt#managing-tool-calls

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/context_management/filter_tool_calls_from_history

This example demonstrates how to use `max_tool_calls_from_history` to limit tool calls in team context across multiple research queries.

```python filter_tool_calls_from_history.py theme={null}
from textwrap import dedent

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools

---

## Output Validation Post-Hook

**URL:** llms-txt#output-validation-post-hook

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/hooks/output_validation_post_hook

This example demonstrates how to use a post-hook to validate the output of an Team, before it is returned to the user.

This example shows how to:

1. Validate team responses for quality and safety
2. Ensure outputs meet minimum standards before being returned
3. Raise OutputCheckError when validation fails

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run example">
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

  <Step title="Run example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Chat History Management

**URL:** llms-txt#chat-history-management

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/session/05_chat_history

This example demonstrates how to manage and retrieve chat history in agent conversations, enabling access to previous conversation messages and context.

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Setup PostgreSQL">
    
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

## Image to Structured Movie Script Team

**URL:** llms-txt#image-to-structured-movie-script-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/multimodal/image_to_structured_output

This example demonstrates how a team can collaborate to analyze images and create structured movie scripts using Pydantic models for consistent output format.

```python cookbook/examples/teams/multimodal/image_to_structured_output.py theme={null}
from typing import List

from agno.agent import Agent
from agno.media import Image
from agno.models.openai import OpenAIChat
from agno.team import Team
from pydantic import BaseModel, Field
from rich.pretty import pprint

class MovieScript(BaseModel):
    name: str = Field(..., description="Give a name to this movie")
    setting: str = Field(
        ..., description="Provide a nice setting for a blockbuster movie."
    )
    characters: List[str] = Field(..., description="Name of characters for this movie.")
    storyline: str = Field(
        ..., description="3 sentence storyline for the movie. Make it exciting!"
    )

image_analyst = Agent(
    name="Image Analyst",
    role="Analyze visual content and extract key elements",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "Analyze images for visual elements, setting, and characters",
        "Focus on details that can inspire creative content",
    ],
)

script_writer = Agent(
    name="Script Writer",
    role="Create structured movie scripts from visual inspiration",
    model=OpenAIChat(id="gpt-5-mini"),
    instructions=[
        "Transform visual analysis into compelling movie concepts",
        "Follow the structured output format precisely",
    ],
)

---

## OpenAI Moderation Guardrail

**URL:** llms-txt#openai-moderation-guardrail

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/guardrails/openai_moderation

This example demonstrates how to use Agno's built-in OpenAI moderation guardrail with an Team.

This example shows how to:

1. Detect and block content that violates OpenAI's content policy
2. Handle both text and image content moderation
3. Configure moderation for specific categories
4. Use both sync and async moderation checks
5. Customize moderation models and sensitivity settings

<Steps>
  <Snippet file="create-venv-step.mdx" />

<Step title="Install libraries">
    
  </Step>

<Step title="Run example">
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

  <Step title="Run example">
    <CodeGroup>
```

Example 3 (unknown):
```unknown

```

---

## Team Events Monitoring

**URL:** llms-txt#team-events-monitoring

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/streaming/events

This example demonstrates how to monitor and handle different types of events during team execution, including tool calls, run states, and content generation events.

```python cookbook/examples/teams/streaming/02_events.py theme={null}
import asyncio
from uuid import uuid4

from agno.agent import RunEvent
from agno.agent.agent import Agent
from agno.models.anthropic.claude import Claude

---

## Session Name Management

**URL:** llms-txt#session-name-management

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/session/rename_session

This example demonstrates how to set custom session names or automatically generate meaningful names for better session organization and identification.

```python cookbook/examples/teams/session/06_rename_session.py theme={null}
from agno.agent.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.team import Team

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

db = PostgresDb(db_url=db_url)

agent = Agent(
    model=OpenAIChat(id="gpt-5-mini"),
)

team = Team(
    model=OpenAIChat(id="gpt-5-mini"),
    members=[agent],
    db=db,
)

team.print_response("Tell me a new interesting fact about space")
team.set_session_name(session_name="Interesting Space Facts")
print(team.get_session_name())

---

## Parser Model for Structured Output

**URL:** llms-txt#parser-model-for-structured-output

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/input_and_output/parser_model

This example demonstrates how to use a different parser model for structured output generation, combining Claude for content generation with OpenAI for parsing into structured formats.

```python parser_model.py theme={null}
import random
from typing import List

from agno.agent import Agent, RunOutput  # noqa
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
    model=Claude(id="claude-sonnet-4-20250514"),
    description="You help people plan amazing national park adventures and provide detailed park guides.",
    output_schema=NationalParkAdventure,
    parser_model=OpenAIChat(id="gpt-5-mini"),
)

---

## Parallel Steps Workflow

**URL:** llms-txt#parallel-steps-workflow

Source: https://docs.agno.com/examples/concepts/workflows/04-workflows-parallel-execution/parallel_steps_workflow

This example demonstrates **Workflows 2.0** parallel execution for independent tasks that can run simultaneously. Shows how to optimize workflow performance by executing non-dependent steps in parallel, significantly reducing total execution time.

This example demonstrates **Workflows 2.0** parallel execution for independent tasks that
can run simultaneously. Shows how to optimize workflow performance by executing
non-dependent steps in parallel, significantly reducing total execution time.

**When to use**: When you have independent tasks that don't depend on each other's output
but can contribute to the same final goal. Ideal for research from multiple sources,
parallel data processing, or any scenario where tasks can run simultaneously.

```python parallel_steps_workflow.py theme={null}
from agno.agent import Agent
from agno.tools.googlesearch import GoogleSearchTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow import Step, Workflow
from agno.workflow.parallel import Parallel

---

## Team with Parser Model

**URL:** llms-txt#team-with-parser-model

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/structured_input_output/team_with_parser_model

This example demonstrates using a parser model with teams to generate structured output, creating detailed national park adventure guides with validated Pydantic schemas.

```python cookbook/examples/teams/structured_input_output/02_team_with_parser_model.py theme={null}
import random
from typing import Iterator, List  # noqa

from agno.agent import Agent, RunOutput, RunOutputEvent  # noqa
from agno.models.anthropic import Claude
from agno.models.openai import OpenAIChat
from agno.team import Team
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

itinerary_planner = Agent(
    name="Itinerary Planner",
    model=Claude(id="claude-sonnet-4-20250514"),
    description="You help people plan amazing national park adventures and provide detailed park guides.",
)

weather_expert = Agent(
    name="Weather Expert",
    model=Claude(id="claude-sonnet-4-20250514"),
    description="You are a weather expert and can provide detailed weather information for a given location.",
)

national_park_expert = Team(
    model=OpenAIChat(id="gpt-5-mini"),
    members=[itinerary_planner, weather_expert],
    output_schema=NationalParkAdventure,
    parser_model=OpenAIChat(id="gpt-5-mini"),
)

---

## Workflow Cancellation

**URL:** llms-txt#workflow-cancellation

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/workflow_cancellation

This example demonstrates **Workflows 2.0** support for cancelling running workflow executions, including thread-based cancellation and handling cancelled responses.

This example shows how to cancel a running workflow execution in real-time. It demonstrates:

1. **Thread-based Execution**: Running workflows in separate threads for non-blocking operation
2. **Dynamic Cancellation**: Cancelling workflows while they're actively running
3. **Cancellation Events**: Handling and responding to cancellation events
4. **Status Tracking**: Monitoring workflow status throughout execution and cancellation

---

## JWT Middleware with Cookies

**URL:** llms-txt#jwt-middleware-with-cookies

**Contents:**
- Code

Source: https://docs.agno.com/examples/agent-os/middleware/jwt-cookies

AgentOS with JWT middleware using HTTP-only cookies for secure web authentication

This example demonstrates how to use JWT middleware with AgentOS using HTTP-only cookies instead of Authorization headers.
This approach is more secure for web applications as it prevents XSS attacks.

```python jwt_cookies.py theme={null}
from datetime import UTC, datetime, timedelta

import jwt
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.os.middleware import JWTMiddleware
from agno.os.middleware.jwt import TokenSource
from fastapi import FastAPI, Response

---

## Few-Shot Learning with Customer Support Team

**URL:** llms-txt#few-shot-learning-with-customer-support-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/other/few_shot_learning

This example demonstrates few-shot learning by providing example conversations to teach a customer support team proper response patterns. The team learns from provided examples to handle different types of customer issues with appropriate escalation and communication patterns.

```python cookbook/examples/teams/basic/few_shot_learning.py theme={null}
"""
This example shows a straightforward use case of additional_input
to teach a customer support team proper response patterns.
"""

from agno.agent import Agent
from agno.models.message import Message
from agno.models.openai import OpenAIChat
from agno.team import Team

---

## Image to Text Analysis

**URL:** llms-txt#image-to-text-analysis

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/image_to_text

This example demonstrates how to create an agent that can analyze images and generate creative text content based on the visual content.

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

## Disable Storing History Messages

**URL:** llms-txt#disable-storing-history-messages

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/session/09_disable_storing_history_messages

This example demonstrates how to disable storing history messages in a session.

This example shows how to disable storing history messages in a session.

---

## Startup Idea Validator

**URL:** llms-txt#startup-idea-validator

Source: https://docs.agno.com/examples/use-cases/workflows/startup-idea-validator

This example demonstrates how to migrate from the similar workflows 1.0 example to workflows 2.0 structure.

This workflow helps entrepreneurs validate their startup ideas by:

1. Clarifying and refining the core business concept
2. Evaluating originality compared to existing solutions
3. Defining clear mission and objectives
4. Conducting comprehensive market research and analysis

**Why is this helpful:**

* Get objective feedback on your startup idea before investing resources
* Understand your total addressable market and target segments
* Validate assumptions about market opportunity and competition
* Define clear mission and objectives to guide execution

**Example use cases:**

* New product/service validation
* Market opportunity assessment
* Competitive analysis
* Business model validation
* Target customer segmentation
* Mission/vision refinement

Run `pip install openai agno googlesearch-python` to install dependencies.

The workflow will guide you through validating your startup idea with AI-powered
analysis and research. Use the insights to refine your concept and business plan!

```python startup_idea_validator.py theme={null}
"""
🚀 Startup Idea Validator - Your Personal Business Validation Assistant!

This workflow helps entrepreneurs validate their startup ideas by:
1. Clarifying and refining the core business concept
2. Evaluating originality compared to existing solutions
3. Defining clear mission and objectives
4. Conducting comprehensive market research and analysis

Why is this helpful?
--------------------------------------------------------------------------------
• Get objective feedback on your startup idea before investing resources
• Understand your total addressable market and target segments
• Validate assumptions about market opportunity and competition
• Define clear mission and objectives to guide execution

Who should use this?
--------------------------------------------------------------------------------
• Entrepreneurs and Startup Founders
• Product Managers and Business Strategists
• Innovation Teams
• Angel Investors and VCs doing initial screening

Example use cases:
--------------------------------------------------------------------------------
• New product/service validation
• Market opportunity assessment
• Competitive analysis
• Business model validation
• Target customer segmentation
• Mission/vision refinement

Quick Start:
--------------------------------------------------------------------------------
1. Install dependencies:
   pip install openai agno

2. Set environment variables:
   - OPENAI_API_KEY

3. Run:
   python startup_idea_validator.py

The workflow will guide you through validating your startup idea with AI-powered
analysis and research. Use the insights to refine your concept and business plan!
"""

import asyncio
from typing import Any

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.tools.googlesearch import GoogleSearchTools
from agno.utils.pprint import pprint_run_response
from agno.workflow.types import WorkflowExecutionInput
from agno.workflow.workflow import Workflow
from pydantic import BaseModel, Field

---

## Confirmation Required with Run ID

**URL:** llms-txt#confirmation-required-with-run-id

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/confirmation_required_with_run_id

This example demonstrates human-in-the-loop functionality using specific run IDs for session management. It shows how to continue agent execution with updated tools using run identifiers.

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

## Arize Phoenix via OpenInference (Local Collector)

**URL:** llms-txt#arize-phoenix-via-openinference-(local-collector)

**Contents:**
- Overview
- Code

Source: https://docs.agno.com/examples/concepts/integrations/observability/arize-phoenix-via-openinference-local

This example demonstrates how to instrument your Agno agent with OpenInference and send traces to a local Arize Phoenix collector.

```python  theme={null}
import os

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.duckduckgo import DuckDuckGoTools
from phoenix.otel import register

---

## Loop with Parallel Steps Workflow

**URL:** llms-txt#loop-with-parallel-steps-workflow

Source: https://docs.agno.com/examples/concepts/workflows/03_workflows_loop_execution/loop_with_parallel_steps_stream

This example demonstrates **Workflows 2.0** most sophisticated pattern combining loop execution with parallel processing and real-time streaming.

This example shows how to create iterative
workflows that execute multiple independent tasks simultaneously within each iteration,
optimizing both quality and performance.

**When to use**: When you need iterative quality improvement with parallel task execution
in each iteration. Ideal for comprehensive research workflows where multiple independent
tasks contribute to overall quality, and you need to repeat until quality thresholds are met.

```python loop_with_parallel_steps_stream.py theme={null}
from typing import List

from agno.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow import Loop, Parallel, Step, Workflow
from agno.workflow.types import StepOutput

---

## Conditional Branching Workflow

**URL:** llms-txt#conditional-branching-workflow

Source: https://docs.agno.com/examples/concepts/workflows/05_workflows_conditional_branching/router_steps_workflow

This example demonstrates **Workflows 2.0** router pattern for intelligent, content-based workflow routing.

This example demonstrates **Workflows 2.0** to dynamically select the best execution path based on input
analysis, enabling adaptive workflows that choose optimal strategies per topic.

**When to use**: When you need mutually exclusive execution paths based on business logic.
Ideal for topic-specific workflows, expertise routing, or when different subjects require
completely different processing strategies. Unlike Conditions which can trigger multiple
parallel paths, Router selects exactly one path.

```python router_steps_workflow.py theme={null}
from typing import List

from agno.agent.agent import Agent
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.router import Router
from agno.workflow.step import Step
from agno.workflow.types import StepInput
from agno.workflow.workflow import Workflow

---

## Member-Level History

**URL:** llms-txt#member-level-history

**Contents:**
- Ask question in German
- Follow up in German
- Ask question in Spanish
- Follow up in Spanish
- Usage

Source: https://docs.agno.com/examples/concepts/teams/basic/history_of_members

This example demonstrates a team where each member has access to its own history through `add_history_to_context=True` set on individual agents.

Unlike team-level history, each member only has access to its own conversation history, not the history of other members or the team.

Use member-level history when:

* Each member handles distinct, independent tasks
* You don't need cross-member context sharing
* Members should maintain isolated conversation threads
* You want to minimize context size for each member

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

## Intent Routing with Workflow History

**URL:** llms-txt#intent-routing-with-workflow-history

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/workflow_history/06_intent_routing_with_history

This example demonstrates how to use workflow history in intent routing.

This example demonstrates:

1. A simple Router that routes to different specialist agents
2. All agents share the same conversation history for context continuity
3. The power of shared context across different agents

The router uses basic intent detection, but the real value is in the shared history.

```python 06_intent_routing_with_history.py theme={null}
from typing import List

from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.workflow.router import Router
from agno.workflow.step import Step
from agno.workflow.types import StepInput
from agno.workflow.workflow import Workflow

---

## User Input Required Async

**URL:** llms-txt#user-input-required-async

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/human_in_the_loop/user_input_required_async

This example demonstrates how to use the `requires_user_input` parameter with asynchronous operations. It shows how to collect specific user input fields in an async environment.

```python user_input_required_async.py theme={null}
"""🤝 Human-in-the-Loop: Allowing users to provide input externally"""

import asyncio
from typing import List

from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools import tool
from agno.tools.function import UserInputField
from agno.utils import pprint

---

## Delegate to All Members (Cooperation)

**URL:** llms-txt#delegate-to-all-members-(cooperation)

**Contents:**
- Usage

Source: https://docs.agno.com/examples/concepts/teams/basic/delegate_to_all_members_cooperation

This example demonstrates a collaborative team of AI agents working together to research topics across different platforms.

The team consists of two specialized agents:

1. **Reddit Researcher** - Uses DuckDuckGo to find and analyze relevant Reddit posts
2. **HackerNews Researcher** - Uses HackerNews API to find and analyze relevant HackerNews posts

The agents work in "collaborate" mode by using `delegate_task_to_all_members=True`, meaning they:

* Both are given the same task at the same time
* Work towards reaching consensus through discussion
* Are coordinated by a team leader that guides the discussion

The team leader moderates the discussion and determines when consensus is reached.

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

## Audio to Text Transcription Team

**URL:** llms-txt#audio-to-text-transcription-team

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/multimodal/audio_to_text

This example demonstrates how a team can collaborate to transcribe audio content and analyze the transcribed text for insights and themes.

```python cookbook/examples/teams/multimodal/audio_to_text.py theme={null}
import requests
from agno.agent import Agent
from agno.media import Audio
from agno.models.google import Gemini
from agno.team import Team

transcription_specialist = Agent(
    name="Transcription Specialist",
    role="Convert audio to accurate text transcriptions",
    model=Gemini(id="gemini-2.0-flash-exp"),
    instructions=[
        "Transcribe audio with high accuracy",
        "Identify speakers clearly as Speaker A, Speaker B, etc.",
        "Maintain conversation flow and context",
    ],
)

content_analyzer = Agent(
    name="Content Analyzer",
    role="Analyze transcribed content for insights",
    model=Gemini(id="gemini-2.0-flash-exp"),
    instructions=[
        "Analyze transcription for key themes and insights",
        "Provide summaries and extract important information",
    ],
)

---

## Access Session State in Custom Python Function Step

**URL:** llms-txt#access-session-state-in-custom-python-function-step

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/access_session_state_in_custom_python_function_step

This example demonstrates how to access session state in a custom python function step

```python access_session_state_in_custom_python_function_step.py theme={null}
from agno.agent import Agent
from agno.db.sqlite import SqliteDb
from agno.models.openai import OpenAIChat
from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools
from agno.workflow.step import Step, StepInput, StepOutput
from agno.workflow.workflow import Workflow

---

## High Fidelity Image Input

**URL:** llms-txt#high-fidelity-image-input

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/multimodal/image_input_high_fidelity

This example demonstrates how to use high fidelity image analysis with an AI agent by setting the detail parameter.

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

## Few-Shot Learning with Additional Input

**URL:** llms-txt#few-shot-learning-with-additional-input

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/agent/context_management/few_shot_learning

This example demonstrates how to use additional\_input with an Agent to teach proper response patterns through few-shot learning, specifically for customer support scenarios.

```python few_shot_learning.py theme={null}
"""
This example demonstrates how to use additional_input with an Agent
to teach proper response patterns through few-shot learning.
"""

from agno.agent import Agent
from agno.models.message import Message
from agno.models.openai import OpenAIChat

---

## Team Input as Messages List

**URL:** llms-txt#team-input-as-messages-list

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/teams/other/input_as_messages_list

This example demonstrates how to provide input to a team as a list of Message objects, creating a conversation context with multiple user and assistant messages for more complex interactions.

```python cookbook/examples/teams/basic/input_as_messages_list.py theme={null}
from agno.agent import Agent
from agno.models.message import Message
from agno.team import Team

---

## Dynamic Instructions Based on Session State

**URL:** llms-txt#dynamic-instructions-based-on-session-state

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/agent/context_management/dynamic_instructions

This example demonstrates how to create dynamic instructions that change based on session state, allowing personalized agent behavior for different users.

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

## Team Run Cancellation

**URL:** llms-txt#team-run-cancellation

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/other/team_cancel_a_run

This example demonstrates how to cancel a running team execution by starting a team run in a separate thread and cancelling it from another thread. It shows proper handling of cancelled responses and thread management.

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

## Get History in Function

**URL:** llms-txt#get-history-in-function

Source: https://docs.agno.com/examples/concepts/workflows/06_workflows_advanced_concepts/workflow_history/04_get_history_in_function

This example demonstrates how to get workflow history in a custom function.

This example shows how to get workflow history in a custom function.

* Using `step_input.get_workflow_history(num_runs=5)` we can get the history as a list of tuples.
* We can also use `step_input.get_workflow_history_context(num_runs=5)` to get the history as a string.

---
