# Agno - Agentos

**Pages:** 22

---

## Multiple MCP Servers

**URL:** llms-txt#multiple-mcp-servers

**Contents:**
- Using multiple `MCPTools` instances

Source: https://docs.agno.com/concepts/tools/mcp/multiple-servers

Understanding how to connect to multiple MCP servers with Agno

Agno's MCP integration also supports handling connections to multiple servers, specifying server parameters and using your own MCP servers

There are two approaches to this:

1. Using multiple `MCPTools` instances
2. Using a single `MultiMCPTools` instance

## Using multiple `MCPTools` instances

```python multiple_mcp_servers.py theme={null}
import asyncio
import os

from agno.agent import Agent
from agno.tools.mcp import MCPTools

async def run_agent(message: str) -> None:
    """Run the Airbnb and Google Maps agent with the given message."""

env = {
        **os.environ,
        "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY"),
    }

# Initialize and connect to multiple MCP servers
    airbnb_tools = MCPTools(command="npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt")
    google_maps_tools = MCPTools(command="npx -y @modelcontextprotocol/server-google-maps", env=env)
    await airbnb_tools.connect()
    await google_maps_tools.connect()

try:
        agent = Agent(
            tools=[airbnb_tools, google_maps_tools],
            markdown=True,
        )

await agent.aprint_response(message, stream=True)
    finally:
        await airbnb_tools.close()
        await google_maps_tools.close()

---

## Bring Your Own FastAPI App

**URL:** llms-txt#bring-your-own-fastapi-app

**Contents:**
- Quick Start

Source: https://docs.agno.com/agent-os/customize/custom-fastapi

Learn how to use your own FastAPI app in your AgentOS

AgentOS is built on FastAPI, which means you can easily integrate your existing FastAPI applications or add custom routes and routers to extend your agent's capabilities.

The simplest way to bring your own FastAPI app is to pass it to the AgentOS constructor:

```python  theme={null}
from fastapi import FastAPI
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS

---

## This is the URL of the MCP server we want to use.

**URL:** llms-txt#this-is-the-url-of-the-mcp-server-we-want-to-use.

server_url = "http://localhost:7777/mcp"

async def run_agent(message: str) -> None:
    async with MCPTools(transport="streamable-http", url=server_url) as mcp_tools:
        agent = Agent(
            model=Claude(id="claude-sonnet-4-0"),
            tools=[mcp_tools],
            markdown=True,
        )
        await agent.aprint_response(input=message, stream=True, markdown=True)

---

## Custom FastAPI app

**URL:** llms-txt#custom-fastapi-app

app: FastAPI = FastAPI(
    title="Custom FastAPI App",
    version="1.0.0",
)

---

## Understanding Server Parameters

**URL:** llms-txt#understanding-server-parameters

Source: https://docs.agno.com/concepts/tools/mcp/server-params

Understanding how to configure the server parameters for the MCPTools and MultiMCPTools classes

The recommended way to configure `MCPTools` is to use the `command` or `url` parameters.

Alternatively, you can use the `server_params` parameter with `MCPTools` to configure the connection to the MCP server in more detail.

When using the **stdio** transport, the `server_params` parameter should be an instance of `StdioServerParameters`. It contains the following keys:

* `command`: The command to run the MCP server.
  * Use `npx` for mcp servers that can be installed via npm (or `node` if running on Windows).
  * Use `uvx` for mcp servers that can be installed via uvx.
  * Use custom binary executables (e.g., `./my-server`, `../usr/local/bin/my-server`, or binaries in your PATH).
* `args`: The arguments to pass to the MCP server.
* `env`: Optional environment variables to pass to the MCP server. Remember to include all current environment variables in the `env` dictionary. If `env` is not provided, the current environment variables will be used.
  e.g.

When using the **SSE** transport, the `server_params` parameter should be an instance of `SSEClientParams`. It contains the following fields:

* `url`: The URL of the MCP server.
* `headers`: Headers to pass to the MCP server (optional).
* `timeout`: Timeout for the connection to the MCP server (optional).
* `sse_read_timeout`: Timeout for the SSE connection itself (optional).

When using the **Streamable HTTP** transport, the `server_params` parameter should be an instance of `StreamableHTTPClientParams`. It contains the following fields:

* `url`: The URL of the MCP server.
* `headers`: Headers to pass to the MCP server (optional).
* `timeout`: Timeout for the connection to the MCP server (optional).
* `sse_read_timeout`: how long (in seconds) the client will wait for a new event before disconnecting. All other HTTP operations are controlled by `timeout` (optional).
* `terminate_on_close`: Whether to terminate the connection when the client is closed (optional).

---

## Add Agno JWT middleware to your custom FastAPI app

**URL:** llms-txt#add-agno-jwt-middleware-to-your-custom-fastapi-app

app.add_middleware(
    JWTMiddleware,
    secret_key=JWT_SECRET,
    excluded_route_paths=[
        "/auth/login"
    ],  # We don't want to validate the token for the login endpoint
    validate=True,  # Set validate to False to skip token validation
)

---

## Get all routes

**URL:** llms-txt#get-all-routes

**Contents:**
- Developer Resources

routes = agent_os.get_routes()

for route in routes:
    print(f"Route: {route.path}")
    if hasattr(route, 'methods'):
        print(f"Methods: {route.methods}")
```

## Developer Resources

* [AgentOS Reference](/reference/agent-os/agent-os)
* [Full Example](/examples/agent-os/custom-fastapi)
* [FastAPI Documentation](https://fastapi.tiangolo.com/)

---

## Initialize and connect to the MCP server

**URL:** llms-txt#initialize-and-connect-to-the-mcp-server

---

## -*- FastAPI running on ECS

**URL:** llms-txt#-*--fastapi-running-on-ecs

prd_fastapi = FastApi(
    ...
    # To enable HTTPS, create an ACM certificate and add the ARN below:
    load_balancer_enable_https=True,
    load_balancer_certificate_arn="arn:aws:acm:us-east-1:497891874516:certificate/6598c24a-d4fc-4f17-8ee0-0d3906eb705f",
    ...
)
bash terminal theme={null}
  ag infra up --env prd --infra aws --name listener
  bash shorthand theme={null}
  ag infra up -e prd -i aws -n listener
  bash terminal theme={null}
  ag infra patch --env prd --infra aws --name listener
  bash shorthand theme={null}
  ag infra patch -e prd -i aws -n listener
  ```
</CodeGroup>

After this, all HTTP requests should redirect to HTTPS automatically.

**Examples:**

Example 1 (unknown):
```unknown
4. Create new Loadbalancer Listeners

Create new listeners for the loadbalancer to pickup the HTTPs configuration.

<CodeGroup>
```

Example 2 (unknown):
```unknown

```

Example 3 (unknown):
```unknown
</CodeGroup>

<Note>The certificate should be `Issued` before applying it.</Note>

After this, `https` should be working on your custom domain.

5. Update existing listeners to redirect HTTP to HTTPS

<CodeGroup>
```

Example 4 (unknown):
```unknown

```

---

## Can also use custom binaries: command="./my-mcp-server"

**URL:** llms-txt#can-also-use-custom-binaries:-command="./my-mcp-server"

mcp_tools = MCPTools(command="uvx mcp-server-git")
await mcp_tools.connect()

try:
    agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
    await agent.aprint_response("What is the license for this project?", stream=True)
finally:
    # Always close the connection when done
    await mcp_tools.close()
python  theme={null}
import asyncio
import os

from agno.agent import Agent
from agno.tools.mcp import MultiMCPTools

async def run_agent(message: str) -> None:
    """Run the Airbnb and Google Maps agent with the given message."""

env = {
        **os.environ,
        "GOOGLE_MAPS_API_KEY": os.getenv("GOOGLE_MAPS_API_KEY"),
    }

# Initialize and connect to multiple MCP servers
    mcp_tools = MultiMCPTools(
        commands=[
            "npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt",
            "npx -y @modelcontextprotocol/server-google-maps",
        ],
        env=env,
    )
    await mcp_tools.connect()

try:
        agent = Agent(
            tools=[mcp_tools],
            markdown=True,
        )

await agent.aprint_response(message, stream=True)
    finally:
        # Always close the connection when done
        await mcp_tools.close()

**Examples:**

Example 1 (unknown):
```unknown
You can also use multiple MCP servers at once, with the `MultiMCPTools` class. For example:
```

---

## app.router.routes.append(route)

**URL:** llms-txt#app.router.routes.append(route)

**Contents:**
- Middleware and Dependencies

app = agent_os.get_app()

if __name__ == "__main__":
    """Run our AgentOS.

You can see the docs at:
    http://localhost:7777/docs

"""
    agent_os.serve(app="custom_fastapi_app:app", reload=True)
python  theme={null}
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer

**Examples:**

Example 1 (unknown):
```unknown
## Middleware and Dependencies

You can add middleware and dependencies to your custom FastAPI app:
```

---

## Initialize and connect to the SSE MCP server

**URL:** llms-txt#initialize-and-connect-to-the-sse-mcp-server

mcp_tools = MCPTools(url=server_url, transport="sse")
await mcp_tools.connect()

try:
    agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
    await agent.aprint_response("What is the license for this project?", stream=True)
finally:
    # Always close the connection when done
    await mcp_tools.close()
python  theme={null}
from agno.tools.mcp import MCPTools, SSEClientParams

server_params = SSEClientParams(
    url=...,
    headers=...,
    timeout=...,
    sse_read_timeout=...,
)

**Examples:**

Example 1 (unknown):
```unknown
You can also use the `server_params` argument to define the MCP connection. This way you can specify the headers to send to the MCP server with every request, and the timeout values:
```

---

## Create custom FastAPI app

**URL:** llms-txt#create-custom-fastapi-app

app = FastAPI(
    title="Example Custom App",
    version="1.0.0",
)

---

## Run infinity server with reranking model

**URL:** llms-txt#run-infinity-server-with-reranking-model

infinity_emb v2 --model-id BAAI/bge-reranker-base --port 7997

Wait for the engine to start.

For better performance, you can use larger models:

---

## Example: Run a web server

**URL:** llms-txt#example:-run-a-web-server

agent.print_response(
    "Create a simple FastAPI web server that displays 'Hello from E2B Sandbox!' and run it to get a public URL"
)

---

## Create your custom FastAPI app

**URL:** llms-txt#create-your-custom-fastapi-app

app = FastAPI(title="My Custom App")

---

## Agno Telemetry

**URL:** llms-txt#agno-telemetry

**Contents:**
- Disabling Telemetry

Source: https://docs.agno.com/concepts/telemetry

Understanding what Agno logs

Agno automatically logs anonymised data about agents, teams and workflows, as well as AgentOS configurations.
This helps us improve the Agno platform and provide better support.

<Note>
  No sensitive data is sent to the Agno servers. Telemetry is only used to improve the Agno platform.
</Note>

Agno logs the following:

* Agent runs
* Team runs
* Workflow runs
* AgentOS Launches

Below is an example of the payload sent to the Agno servers for an agent run:

## Disabling Telemetry

You can disable this by setting `AGNO_TELEMETRY=false` in your environment or by setting `telemetry=False` on the agent, team, workflow or AgentOS.

See the [Agent class reference](/reference/agents/agent) for more details.

**Examples:**

Example 1 (unknown):
```unknown
## Disabling Telemetry

You can disable this by setting `AGNO_TELEMETRY=false` in your environment or by setting `telemetry=False` on the agent, team, workflow or AgentOS.
```

Example 2 (unknown):
```unknown
or:
```

---

## Start the database and MCP Toolbox servers

**URL:** llms-txt#start-the-database-and-mcp-toolbox-servers

---

## Initialize and connect to the Streamable HTTP MCP server

**URL:** llms-txt#initialize-and-connect-to-the-streamable-http-mcp-server

mcp_tools = MCPTools(url="https://docs.agno.com/mcp", transport="streamable-http")
await mcp_tools.connect()

try:
    agent = Agent(model=OpenAIChat(id="gpt-5-mini"), tools=[mcp_tools])
    await agent.aprint_response("What can you tell me about MCP support in Agno?", stream=True)
finally:
    # Always close the connection when done
    await mcp_tools.close()
python  theme={null}
from agno.tools.mcp import MCPTools, StreamableHTTPClientParams

server_params = StreamableHTTPClientParams(
    url=...,
    headers=...,
    timeout=...,
    sse_read_timeout=...,
    terminate_on_close=...,
)

**Examples:**

Example 1 (unknown):
```unknown
You can also use the `server_params` argument to define the MCP connection. This way you can specify the headers to send to the MCP server with every request, and the timeout values:
```

---

## Lifespan

**URL:** llms-txt#lifespan

Source: https://docs.agno.com/agent-os/customize/os/lifespan

Complete AgentOS setup with custom lifespan

You can customize the lifespan context manager of the AgentOS.
This allows you to run code before and after the AgentOS is started and stopped.

For example, you can use this to:

* Connect to a database
* Log information
* Setup a monitoring system

<Tip>
  See [FastAPI documentation](https://fastapi.tiangolo.com/advanced/events/#lifespan-events) for more information about the lifespan context manager.
</Tip>

```python custom_lifespan.py theme={null}

from contextlib import asynccontextmanager

from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.anthropic import Claude
from agno.os import AgentOS
from agno.utils.log import log_info

---

## Custom FastAPI App with JWT Middleware

**URL:** llms-txt#custom-fastapi-app-with-jwt-middleware

**Contents:**
- Code

Source: https://docs.agno.com/examples/agent-os/middleware/custom-fastapi-jwt

Custom FastAPI application with JWT middleware for authentication and AgentOS integration

This example demonstrates how to integrate JWT middleware with your custom FastAPI application and then add AgentOS functionality on top.

```python custom_fastapi_jwt.py theme={null}
from datetime import datetime, timedelta, UTC

import jwt
from agno.agent import Agent
from agno.db.postgres import PostgresDb
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from agno.os.middleware import JWTMiddleware
from agno.tools.duckduckgo import DuckDuckGoTools
from fastapi import FastAPI, Form, HTTPException

---

## Initialize and connect using server parameters

**URL:** llms-txt#initialize-and-connect-using-server-parameters

**Contents:**
- Complete example

mcp_tools = MCPTools(server_params=server_params, transport="streamable-http")
await mcp_tools.connect()

try:
    # Use mcp_tools with your agent
    pass
finally:
    await mcp_tools.close()
python streamable_http_server.py theme={null}
    from mcp.server.fastmcp import FastMCP

mcp = FastMCP("calendar_assistant")

@mcp.tool()
    def get_events(day: str) -> str:
        return f"There are no events scheduled for {day}."

@mcp.tool()
    def get_birthdays_this_week() -> str:
        return "It is your mom's birthday tomorrow"

if __name__ == "__main__":
        mcp.run(transport="streamable-http")
    python streamable_http_client.py theme={null}
    import asyncio

from agno.agent import Agent
    from agno.models.openai import OpenAIChat
    from agno.tools.mcp import MCPTools, MultiMCPTools

# This is the URL of the MCP server we want to use.
    server_url = "http://localhost:8000/mcp"

async def run_agent(message: str) -> None:
        # Initialize and connect to the Streamable HTTP MCP server
        mcp_tools = MCPTools(transport="streamable-http", url=server_url)
        await mcp_tools.connect()

try:
            agent = Agent(
                model=OpenAIChat(id="gpt-5-mini"),
                tools=[mcp_tools],
                markdown=True,
            )
            await agent.aprint_response(message=message, stream=True, markdown=True)
        finally:
            await mcp_tools.close()

# Using MultiMCPTools, we can connect to multiple MCP servers at once, even if they use different transports.
    # In this example we connect to both our example server (Streamable HTTP transport), and a different server (stdio transport).
    async def run_agent_with_multimcp(message: str) -> None:
        # Initialize and connect to multiple MCP servers with different transports
        mcp_tools = MultiMCPTools(
            commands=["npx -y @openbnb/mcp-server-airbnb --ignore-robots-txt"],
            urls=[server_url],
            urls_transports=["streamable-http"],
        )
        await mcp_tools.connect()

try:
            agent = Agent(
                model=OpenAIChat(id="gpt-5-mini"),
                tools=[mcp_tools],
                markdown=True,
            )
            await agent.aprint_response(message=message, stream=True, markdown=True)
        finally:
            await mcp_tools.close()

if __name__ == "__main__":
        asyncio.run(run_agent("Do I have any birthdays this week?"))
        asyncio.run(
            run_agent_with_multimcp(
                "Can you check when is my mom's birthday, and if there are any AirBnb listings in SF for two people for that day?"
            )
        )
    bash  theme={null}
    python streamable_http_server.py
    bash  theme={null}
    python streamable_http_client.py
    ```
  </Step>
</Steps>

**Examples:**

Example 1 (unknown):
```unknown
## Complete example

Let's set up a simple local server and connect to it using the Streamable HTTP transport:

<Steps>
  <Step title="Setup the server">
```

Example 2 (unknown):
```unknown
</Step>

  <Step title="Setup the client">
```

Example 3 (unknown):
```unknown
</Step>

  <Step title="Run the server">
```

Example 4 (unknown):
```unknown
</Step>

  <Step title="Run the client">
```

---
