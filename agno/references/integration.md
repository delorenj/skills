# Agno - Integration

**Pages:** 42

---

## Database Tables

**URL:** llms-txt#database-tables

**Contents:**
- Table Definition
- Create a database revision
- Migrate dev database
  - Optional: Add test user
- Migrate production database
  - Update the `workspace/prd_resources.py` file

Source: https://docs.agno.com/templates/infra-management/database-tables

Agno templates come pre-configured with [SqlAlchemy](https://www.sqlalchemy.org/) and [Alembic](https://alembic.sqlalchemy.org/en/latest/) to manage databases. You can use these tables to store data for your Agents, Teams and Workflows. The general way to add a table is:

1. Add table definition to the `db/tables` directory.
2. Import the table class in the `db/tables/__init__.py` file.
3. Create a database migration.
4. Run database migration.

Let's create a `UsersTable`, copy the following code to `db/tables/user.py`

Update the `db/tables/__init__.py` file:

## Create a database revision

Run the alembic command to create a database migration in the dev container:

## Migrate dev database

Run the alembic command to migrate the dev database:

### Optional: Add test user

Now lets's add a test user. Copy the following code to `db/tables/test_add_user.py`

Run the script to add a test adding a user:

## Migrate production database

We recommended migrating the production database by setting the environment variable `MIGRATE_DB = True` and restarting the production service. This runs `alembic -c db/alembic.ini upgrade head` from the entrypoint script at container startup.

### Update the `workspace/prd_resources.py` file

```python workspace/prd_resources.py theme={null}
...

**Examples:**

Example 1 (unknown):
```unknown
Update the `db/tables/__init__.py` file:
```

Example 2 (unknown):
```unknown
## Create a database revision

Run the alembic command to create a database migration in the dev container:
```

Example 3 (unknown):
```unknown
## Migrate dev database

Run the alembic command to migrate the dev database:
```

Example 4 (unknown):
```unknown
### Optional: Add test user

Now lets's add a test user. Copy the following code to `db/tables/test_add_user.py`
```

---

## Setup the SQLite database

**URL:** llms-txt#setup-the-sqlite-database

db = SqliteDb(db_file="tmp/data.db")

---

## Setup database

**URL:** llms-txt#setup-database

db = PostgresDb(db_url="postgresql+psycopg://ai:ai@localhost:5532/ai")

---

## Initialize LanceDB vector database

**URL:** llms-txt#initialize-lancedb-vector-database

---

## Define the database URL where the vector database will be stored

**URL:** llms-txt#define-the-database-url-where-the-vector-database-will-be-stored

db_url = "/tmp/lancedb"

---

## 1. Configure vector database with embedder

**URL:** llms-txt#1.-configure-vector-database-with-embedder

vector_db = PgVector(
    table_name="company_knowledge",
    db_url="postgresql+psycopg://user:pass@localhost:5432/db",
    embedder=OpenAIEmbedder(id="text-embedding-3-small")  # Optional: defaults to OpenAIEmbedder
)

---

## Airbnb Mcp

**URL:** llms-txt#airbnb-mcp

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/use-cases/agents/airbnb_mcp

🏠 MCP Airbnb Agent - Search for Airbnb listings!

This example shows how to create an agent that uses MCP and Llama 4 to search for Airbnb listings.

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

## SSE Transport

**URL:** llms-txt#sse-transport

Source: https://docs.agno.com/concepts/tools/mcp/transports/sse

Agno's MCP integration supports the [SSE transport](https://modelcontextprotocol.io/docs/concepts/transports#server-sent-events-sse). This transport enables server-to-client streaming, and can prove more useful than [stdio](https://modelcontextprotocol.io/docs/concepts/transports#standard-input%2Foutput-stdio) when working with restricted networks.

<Note>
  This transport is not recommended anymore by the MCP protocol. Use the [Streamable HTTP transport](/concepts/tools/mcp/transports/streamable_http) instead.
</Note>

To use it, initialize the `MCPTools` passing the URL of the MCP server and setting the transport to `sse`:

```python  theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

server_url = "http://localhost:8000/sse"

---

## Set up vector database - stores embeddings

**URL:** llms-txt#set-up-vector-database---stores-embeddings

vector_db = PgVector(
    table_name="vectors",
    db_url="postgresql+psycopg://user:pass@localhost:5432/db"
)

---

## Setup your Database

**URL:** llms-txt#setup-your-database

db = SingleStoreDb(db_url=db_url)

---

## Get your Neon database URL

**URL:** llms-txt#get-your-neon-database-url

NEON_DB_URL = getenv("NEON_DB_URL")

---

## Setup the DynamoDB database

**URL:** llms-txt#setup-the-dynamodb-database

**Contents:**
- Params
- Developer Resources

class Article(BaseModel):
    title: str
    summary: str
    reference_links: List[str]

hn_researcher = Agent(
    name="HackerNews Researcher",
    model=OpenAIChat("gpt-5-mini"),
    role="Gets top stories from hackernews.",
    tools=[HackerNewsTools()],
)

web_searcher = Agent(
    name="Web Searcher",
    model=OpenAIChat("gpt-5-mini"),
    role="Searches the web for information on a topic",
    tools=[DuckDuckGoTools()],
    add_datetime_to_context=True,
)

hn_team = Team(
    name="HackerNews Team",
    model=OpenAIChat("gpt-5-mini"),
    members=[hn_researcher, web_searcher],
    db=db,
    instructions=[
        "First, search hackernews for what the user is asking about.",
        "Then, ask the web searcher to search for each story to get more information.",
        "Finally, provide a thoughtful and engaging summary.",
    ],
    output_schema=Article,
    markdown=True,
    show_members_responses=True,
)

hn_team.print_response("Write an article about the top 2 stories on hackernews")
```

<Snippet file="db-dynamodb-params.mdx" />

## Developer Resources

* View [Cookbook](https://github.com/agno-agi/agno/blob/main/cookbook/db/dynamodb/dynamo_for_team.py)

---

## Embed sentence in database

**URL:** llms-txt#embed-sentence-in-database

embeddings = GeminiEmbedder().get_embedding("The quick brown fox jumps over the lazy dog.")

---

## -*- Secrets for production database

**URL:** llms-txt#-*--secrets-for-production-database

prd_db_secret = SecretsManager(
    ...
    # Create secret from workspace/secrets/prd_db_secrets.yml
    secret_files=[infra_settings.infra_root.joinpath("infra/secrets/prd_db_secrets.yml")],
)
python FastApi theme={null}
  prd_fastapi = FastApi(
      ...
      aws_secrets=[prd_secret],
      ...
  )
  python RDS theme={null}
  prd_db = DbInstance(
      ...
      aws_secret=prd_db_secret,
      ...
  )
  ```
</CodeGroup>

Production resources can also read secrets using yaml files but we highly recommend using [AWS Secrets](https://docs.aws.amazon.com/secretsmanager/latest/userguide/intro.html).

**Examples:**

Example 1 (unknown):
```unknown
Read the secret in production apps using:

<CodeGroup>
```

Example 2 (unknown):
```unknown

```

---

## JSON Files as Database

**URL:** llms-txt#json-files-as-database

**Contents:**
- Usage

Source: https://docs.agno.com/concepts/db/json

Agno supports using local JSON files as a "database" with the `JsonDb` class.
This is a simple way to store your Agent's session data without having to setup a database.

<Warning>
  Using JSON files as a database is not recommended for production applications.
  Use it for demos, testing and any other use case where you don't want to setup a database.
</Warning>

```python json_for_agent.py theme={null}
from agno.agent import Agent
from agno.db.json import JsonDb

---

## Setup the Neon database

**URL:** llms-txt#setup-the-neon-database

db = PostgresDb(db_url=NEON_DB_URL)

---

## Create MCPTools instance

**URL:** llms-txt#create-mcptools-instance

mcp_tools = MCPTools(
    transport="streamable-http", 
    url="https://docs.agno.com/mcp"
)

---

## Performance with Database Logging

**URL:** llms-txt#performance-with-database-logging

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/evals/performance/performance_db_logging

Learn how to store performance evaluation results in the database.

This example shows how to store evaluation results in the database.

```python  theme={null}
"""Example showing how to store evaluation results in the database."""

from agno.agent import Agent
from agno.db.postgres.postgres import PostgresDb
from agno.eval.performance import PerformanceEval
from agno.models.openai import OpenAIChat

---

## Database URL

**URL:** llms-txt#database-url

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

---

## Database connection

**URL:** llms-txt#database-connection

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
db = PostgresDb(db_url=db_url)

@tool(requires_confirmation=True)
def delete_records(table_name: str, count: int) -> str:
    """Delete records from a database table.

Args:
        table_name: Name of the table
        count: Number of records to delete

Returns:
        str: Confirmation message
    """
    return f"Deleted {count} records from {table_name}"

@tool(requires_confirmation=True)
def send_notification(recipient: str, message: str) -> str:
    """Send a notification to a user.

Args:
        recipient: Email or username of the recipient
        message: Notification message

Returns:
        str: Confirmation message
    """
    return f"Sent notification to {recipient}: {message}"

---

## Setup the Firestore database

**URL:** llms-txt#setup-the-firestore-database

db = FirestoreDb(project_id=PROJECT_ID)

---

## Accuracy with Database Logging

**URL:** llms-txt#accuracy-with-database-logging

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/evals/accuracy/accuracy_db_logging

Learn how to store evaluation results in the database for tracking and analysis.

This example shows how to store evaluation results in the database.

```python  theme={null}
"""Example showing how to store evaluation results in the database."""

from typing import Optional

from agno.agent import Agent
from agno.db.postgres.postgres import PostgresDb
from agno.eval.accuracy import AccuracyEval, AccuracyResult
from agno.models.openai import OpenAIChat
from agno.tools.calculator import CalculatorTools

---

## Setup the JSON database

**URL:** llms-txt#setup-the-json-database

db = JsonDb(db_path="tmp/json_db")

---

## Get the vector database

**URL:** llms-txt#get-the-vector-database

db = Chroma(embedding_function=OpenAIEmbeddings(), persist_directory=str(chroma_db_dir))

---

## Database configuration for metrics storage

**URL:** llms-txt#database-configuration-for-metrics-storage

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
db = PostgresDb(db_url=db_url, session_table="team_metrics_sessions")

---

## Setup your database

**URL:** llms-txt#setup-your-database

db = SqliteDb(db_file="agno.db")

---

## Allow the memories to sync with Zep database

**URL:** llms-txt#allow-the-memories-to-sync-with-zep-database

---

## Setup the Supabase database

**URL:** llms-txt#setup-the-supabase-database

db = PostgresDb(db_url=SUPABASE_DB_URL)

---

## Initialize vector database connection

**URL:** llms-txt#initialize-vector-database-connection

vector_db = Qdrant(
    collection="thai-recipes", url="http://localhost:6333", embedder=embedder
)

---

## Add embedding to database

**URL:** llms-txt#add-embedding-to-database

embeddings = CohereEmbedder(id="embed-english-v3.0").get_embedding("The quick brown fox jumps over the lazy dog.")

---

## - External IDs for cloud integrations

**URL:** llms-txt#--external-ids-for-cloud-integrations

**Contents:**
  - Content Retrieval and Management

**Examples:**

Example 1 (unknown):
```unknown
### Content Retrieval and Management
```

---

## JSON files as database, on Google Cloud Storage (GCS)

**URL:** llms-txt#json-files-as-database,-on-google-cloud-storage-(gcs)

**Contents:**
- Usage

Source: https://docs.agno.com/concepts/db/gcs

Agno supports using [Google Cloud Storage (GCS)](https://cloud.google.com/storage) as a database with the `GcsJsonDb` class.
Session data will be stored as JSON blobs in a GCS bucket.

You can get started with GCS following their [Get Started guide](https://cloud.google.com/docs/get-started).

```python gcs_for_agent.py theme={null}
import uuid
import google.auth
from agno.agent import Agent
from agno.db.gcs_json import GcsJsonDb

---

## Database connection URL

**URL:** llms-txt#database-connection-url

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"

---

## MongoDB Database

**URL:** llms-txt#mongodb-database

**Contents:**
- Usage

Source: https://docs.agno.com/concepts/db/mongodb

Learn to use MongoDB as a database for your Agents

Agno supports using [MongoDB](https://www.mongodb.com/) as a database with the `MongoDb` class.

<Tip>
  **v2 Migration Support**: If you're upgrading from Agno v1, MongoDB is fully supported in the v2 migration script. See the [migration guide](/how-to/v2-migration) for details.
</Tip>

```python mongodb_for_agent.py theme={null}
from agno.agent import Agent
from agno.db.mongo import MongoDb

---

## Setup the database

**URL:** llms-txt#setup-the-database

**Contents:**
- Usage

db_url = "postgresql+psycopg://ai:ai@localhost:5532/ai"
db = PostgresDb(db_url=db_url)

agent = Agent(
    model=VLLM(id="Qwen/Qwen2.5-7B-Instruct"),
    db=db,
    tools=[DuckDuckGoTools()],
    add_history_to_context=True,
)

agent.print_response("How many people live in Canada?")
agent.print_response("What is their national anthem called?")
bash  theme={null}
    pip install -U agno openai vllm sqlalchemy psycopg ddgs
    bash  theme={null}
    ./cookbook/scripts/run_pgvector.sh
    bash  theme={null}
    vllm serve Qwen/Qwen2.5-7B-Instruct \
        --enable-auto-tool-choice \
        --tool-call-parser hermes \
        --dtype float16 \
        --max-model-len 8192 \
        --gpu-memory-utilization 0.9
    bash  theme={null}
    python cookbook/models/vllm/db.py
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

  <Step title="Install Libraries">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Start Postgres database">
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

## Stdio Transport

**URL:** llms-txt#stdio-transport

Source: https://docs.agno.com/concepts/tools/mcp/transports/stdio

The stdio (standard input/output) transport is the default one in Agno's integration. It works best for local integrations.

To use it, simply initialize the `MCPTools` class with the `command` argument.
The command you want to pass is the one used to run the MCP server the agent will have access to.

For example `uvx mcp-server-git`, which runs a [git MCP server](https://github.com/modelcontextprotocol/servers/tree/main/src/git):

```python  theme={null}
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.mcp import MCPTools

---

## Write Your Own Tool

**URL:** llms-txt#write-your-own-tool

**Contents:**
- Code

Source: https://docs.agno.com/examples/getting-started/04-write-your-own-tool

This example shows how to create and use your own custom tool with Agno.
You can replace the Hacker News functionality with any API or service you want!

Some ideas for your own tools:

* Weather data fetcher
* Stock price analyzer
* Personal calendar integration
* Custom database queries
* Local file operations

```python custom_tools.py theme={null}
import json
from textwrap import dedent

import httpx
from agno.agent import Agent
from agno.models.openai import OpenAIChat

def get_top_hackernews_stories(num_stories: int = 10) -> str:
    """Use this function to get top stories from Hacker News.

Args:
        num_stories (int): Number of stories to return. Defaults to 10.

Returns:
        str: JSON string of top stories.
    """

# Fetch top story IDs
    response = httpx.get("https://hacker-news.firebaseio.com/v0/topstories.json")
    story_ids = response.json()

# Fetch story details
    stories = []
    for story_id in story_ids[:num_stories]:
        story_response = httpx.get(
            f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        )
        story = story_response.json()
        if "text" in story:
            story.pop("text", None)
        stories.append(story)
    return json.dumps(stories)

---

## Persistent Session with Database

**URL:** llms-txt#persistent-session-with-database

**Contents:**
- Code
- Usage

Source: https://docs.agno.com/examples/concepts/teams/session/persistent_session

This example demonstrates how to use persistent session storage with a PostgreSQL database to maintain team conversations across multiple runs.

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

## Model Context Protocol (MCP)

**URL:** llms-txt#model-context-protocol-(mcp)

Source: https://docs.agno.com/concepts/tools/mcp/mcp

Learn how to use MCP with Agno to enable your agents to interact with external systems through a standardized interface.

The [Model Context Protocol (MCP)](https://modelcontextprotocol.io) enables Agents to interact with external systems through a standardized interface.
You can connect your Agents to any MCP server, using Agno's MCP integration.

This simple example shows how to connect an Agent to the Agno MCP server:

```python agno_agent.py lines theme={null}
from agno.agent import Agent
from agno.models.anthropic import Claude
from agno.tools.mcp import MCPTools

---

## Load all documents into the vector database

**URL:** llms-txt#load-all-documents-into-the-vector-database

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

## Define the directory where the Chroma database is located

**URL:** llms-txt#define-the-directory-where-the-chroma-database-is-located

chroma_db_dir = pathlib.Path("./chroma_db")

---

## Reliability with Database Logging

**URL:** llms-txt#reliability-with-database-logging

**Contents:**
- Code

Source: https://docs.agno.com/examples/concepts/evals/reliability/reliability_db_logging

Learn how to store reliability evaluation results in the database.

This example shows how to store evaluation results in the database.

```python  theme={null}
"""Example showing how to store evaluation results in the database."""

from typing import Optional

from agno.agent import Agent
from agno.db.postgres.postgres import PostgresDb
from agno.eval.reliability import ReliabilityEval, ReliabilityResult
from agno.models.openai import OpenAIChat
from agno.run.agent import RunOutput
from agno.tools.calculator import CalculatorTools

---
