# MCP Python SDK Guide

## Overview

The Model Context Protocol (MCP) Python SDK is a comprehensive implementation of the [Model Context Protocol](https://modelcontextprotocol.io), designed to facilitate communication between applications and Large Language Models (LLMs). The SDK enables developers to:

- Build MCP clients that can connect to any MCP server
- Create MCP servers that expose resources, prompts, and tools
- Use standard transports like stdio, SSE, and Streamable HTTP
- Handle all MCP protocol messages and lifecycle events

This guide focuses on the low-level components of the MCP SDK, providing detailed information about their functionality and usage.

## Installation

### Adding MCP to your Python project

Using [uv](https://docs.astral.sh/uv/) (recommended):

```bash
# Create a new project
uv init mcp-server-demo
cd mcp-server-demo

# Add MCP to your project dependencies
uv add "mcp[cli]"
```

Using pip:

```bash
pip install "mcp[cli]"
```

### Running the standalone MCP development tools

```bash
uv run mcp
```

## Core Components

### Low-Level Server Implementation

#### `Server` Class

The `Server` class from `mcp.server.lowlevel` is the foundation of the MCP SDK. It provides the core functionality for creating MCP servers and handling protocol messages.

```python
from mcp.server.lowlevel import Server

# Create a server instance with a name
app = Server("mcp-website-fetcher")
```

The `Server` class provides methods for registering handlers for various MCP protocol operations:

- `@app.call_tool()`: Register a handler for tool calls
- `@app.list_tools()`: Register a handler for listing available tools
- `@app.list_resources()`: Register a handler for listing available resources
- `@app.read_resource()`: Register a handler for reading resources
- `@app.list_prompts()`: Register a handler for listing available prompts
- `@app.get_prompt()`: Register a handler for retrieving prompt templates

Example usage:

```python
@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.ContentBlock]:
    if name != "fetch":
        raise ValueError(f"Unknown tool: {name}")
    if "url" not in arguments:
        raise ValueError("Missing required argument 'url'")
    return await fetch_website(arguments["url"])

@app.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="fetch",
            title="Website Fetcher",
            description="Fetches a website and returns its content",
            inputSchema={
                "type": "object",
                "required": ["url"],
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "URL to fetch",
                    }
                },
            },
        )
    ]
```

The `Server` class also provides a `run` method for starting the server with a specific transport:

```python
await app.run(
    read_stream,  # Input stream for receiving messages
    write_stream,  # Output stream for sending messages
    app.create_initialization_options()  # Server initialization options
)
```

#### FastMCP Server

The `FastMCP` class provides a higher-level API built on top of the low-level `Server` class:

```python
from mcp.server.fastmcp import FastMCP

# Create a named server
mcp = FastMCP("My App")

# Specify dependencies for deployment and development
mcp = FastMCP("My App", dependencies=["pandas", "numpy"])
```

#### Server Lifecycle Management

The SDK supports lifecycle management through the lifespan API:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator
from dataclasses import dataclass

from mcp.server.fastmcp import FastMCP

@dataclass
class AppContext:
    db: Database

@asynccontextmanager
async def app_lifespan(server: FastMCP) -> AsyncIterator[AppContext]:
    """Manage application lifecycle with type-safe context"""
    # Initialize on startup
    db = await Database.connect()
    try:
        yield AppContext(db=db)
    finally:
        # Cleanup on shutdown
        await db.disconnect()

# Pass lifespan to server
mcp = FastMCP("My App", lifespan=app_lifespan)

# Access type-safe lifespan context in tools
@mcp.tool()
def query_db() -> str:
    """Tool that uses initialized resources"""
    ctx = mcp.get_context()
    db = ctx.request_context.lifespan_context["db"]
    return db.query()
```

### HTTP Utilities

#### `create_mcp_http_client` Function

The `create_mcp_http_client` function from `mcp.shared._httpx_utils` provides a standardized way to create HTTP clients for MCP applications. It sets up an `httpx.AsyncClient` with common defaults used throughout the MCP codebase.

```python
from mcp.shared._httpx_utils import create_mcp_http_client

# Basic usage with MCP defaults
async with create_mcp_http_client() as client:
    response = await client.get("https://api.example.com")

# With custom headers
headers = {"User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)"}
async with create_mcp_http_client(headers=headers) as client:
    response = await client.get(url)
    response.raise_for_status()
    return [types.TextContent(type="text", text=response.text)]
```

Key features of `create_mcp_http_client`:

- Sets `follow_redirects=True` by default
- Provides a default timeout of 30 seconds
- Allows customization of headers, timeout, and authentication
- Returns an `httpx.AsyncClient` that must be used as a context manager

Implementation details:

```python
def create_mcp_http_client(
    headers: dict[str, str] | None = None,
    timeout: httpx.Timeout | None = None,
    auth: httpx.Auth | None = None,
) -> httpx.AsyncClient:
    # Set MCP defaults
    kwargs: dict[str, Any] = {
        "follow_redirects": True,
    }

    # Handle timeout
    if timeout is None:
        kwargs["timeout"] = httpx.Timeout(30.0)
    else:
        kwargs["timeout"] = timeout

    # Handle headers
    if headers is not None:
        kwargs["headers"] = headers

    # Handle authentication
    if auth is not None:
        kwargs["auth"] = auth

    return httpx.AsyncClient(**kwargs)
```

### Resources

Resources are how you expose data to LLMs. They're similar to GET endpoints in a REST API - they provide data but shouldn't perform significant computation or have side effects.

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My App")

@mcp.resource("config://app", title="Application Configuration")
def get_config() -> str:
    """Static configuration data"""
    return "App configuration here"

@mcp.resource("users://{user_id}/profile", title="User Profile")
def get_user_profile(user_id: str) -> str:
    """Dynamic user data"""
    return f"Profile data for user {user_id}"
```

### Tools

Tools let LLMs take actions through your server. Unlike resources, tools are expected to perform computation and have side effects.

```python
import httpx
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My App")

@mcp.tool(title="BMI Calculator")
def calculate_bmi(weight_kg: float, height_m: float) -> float:
    """Calculate BMI given weight in kg and height in meters"""
    return weight_kg / (height_m**2)

@mcp.tool(title="Weather Fetcher")
async def fetch_weather(city: str) -> str:
    """Fetch current weather for a city"""
    async with httpx.AsyncClient() as client:
        response = await client.get(f"https://api.weather.com/{city}")
        return response.text
```

### Prompts

Prompts are reusable templates that help LLMs interact with your server effectively.

```python
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base

mcp = FastMCP("My App")

@mcp.prompt(title="Code Review")
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"

@mcp.prompt(title="Debug Assistant")
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]
```

### Images

FastMCP provides an `Image` class that automatically handles image data.

```python
from mcp.server.fastmcp import FastMCP, Image
from PIL import Image as PILImage

mcp = FastMCP("My App")

@mcp.tool()
def create_thumbnail(image_path: str) -> Image:
    """Create a thumbnail from an image"""
    img = PILImage.open(image_path)
    img.thumbnail((100, 100))
    return Image(data=img.tobytes(), format="png")
```

### Context

The Context object gives your tools and resources access to MCP capabilities.

```python
from mcp.server.fastmcp import FastMCP, Context

mcp = FastMCP("My App")

@mcp.tool()
async def long_task(files: list[str], ctx: Context) -> str:
    """Process multiple files with progress tracking"""
    for i, file in enumerate(files):
        ctx.info(f"Processing {file}")
        await ctx.report_progress(i, len(files))
        data, mime_type = await ctx.read_resource(f"file://{file}")
    return "Processing complete"
```

### Completions

MCP supports providing completion suggestions for prompt arguments and resource template parameters.

```python
from mcp.server import Server
from mcp.types import (
    Completion,
    CompletionArgument,
    CompletionContext,
    PromptReference,
    ResourceTemplateReference,
)

server = Server("example-server")

@server.completion()
async def handle_completion(
    ref: PromptReference | ResourceTemplateReference,
    argument: CompletionArgument,
    context: CompletionContext | None,
) -> Completion | None:
    if isinstance(ref, ResourceTemplateReference):
        if ref.uri == "github://repos/{owner}/{repo}" and argument.name == "repo":
            # Use context to provide owner-specific repos
            if context and context.arguments:
                owner = context.arguments.get("owner")
                if owner == "modelcontextprotocol":
                    repos = ["python-sdk", "typescript-sdk", "specification"]
                    # Filter based on partial input
                    filtered = [r for r in repos if r.startswith(argument.value)]
                    return Completion(values=filtered)
    return None
```

### Elicitation

Request additional information from users during tool execution.

```python
from mcp.server.fastmcp import FastMCP, Context
from mcp.server.elicitation import (
    AcceptedElicitation,
    DeclinedElicitation,
    CancelledElicitation,
)
from pydantic import BaseModel, Field

mcp = FastMCP("Booking System")

@mcp.tool()
async def book_table(date: str, party_size: int, ctx: Context) -> str:
    """Book a table with confirmation"""

    # Schema must only contain primitive types (str, int, float, bool)
    class ConfirmBooking(BaseModel):
        confirm: bool = Field(description="Confirm booking?")
        notes: str = Field(default="", description="Special requests")

    result = await ctx.elicit(
        message=f"Confirm booking for {party_size} on {date}?", schema=ConfirmBooking
    )

    match result:
        case AcceptedElicitation(data=data):
            if data.confirm:
                return f"Booked! Notes: {data.notes or 'None'}"
            return "Booking cancelled"
        case DeclinedElicitation():
            return "Booking declined"
        case CancelledElicitation():
            return "Booking cancelled"
```

### Authentication

Authentication can be used by servers that want to expose tools accessing protected resources.

```python
from mcp import FastMCP
from mcp.server.auth.provider import TokenVerifier, TokenInfo
from mcp.server.auth.settings import AuthSettings


class MyTokenVerifier(TokenVerifier):
    # Implement token validation logic (typically via token introspection)
    async def verify_token(self, token: str) -> TokenInfo:
        # Verify with your authorization server
        ...


mcp = FastMCP(
    "My App",
    token_verifier=MyTokenVerifier(),
    auth=AuthSettings(
        issuer_url="https://auth.example.com",
        resource_server_url="http://localhost:3001",
        required_scopes=["mcp:read", "mcp:write"],
    ),
)
```

## Running Your Server

### Development Mode

The fastest way to test and debug your server is with the MCP Inspector:

```bash
mcp dev server.py

# Add dependencies
mcp dev server.py --with pandas --with numpy

# Mount local code
mcp dev server.py --with-editable .
```

### Claude Desktop Integration

Once your server is ready, install it in Claude Desktop:

```bash
mcp install server.py

# Custom name
mcp install server.py --name "My Analytics Server"

# Environment variables
mcp install server.py -v API_KEY=abc123 -v DB_URL=postgres://...
mcp install server.py -f .env
```

### Direct Execution

For advanced scenarios like custom deployments:

```python
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("My App")

if __name__ == "__main__":
    mcp.run()
```

Run it with:
```bash
python server.py
# or
mcp run server.py
```

### Mounting to an Existing ASGI Server

You can mount the MCP server to an existing ASGI server:

```python
from starlette.applications import Starlette
from starlette.routing import Mount
from mcp.server.fastmcp import FastMCP

# Create multiple MCP servers
github_mcp = FastMCP("GitHub API")
browser_mcp = FastMCP("Browser")

# Configure mount paths via settings
github_mcp.settings.mount_path = "/github"
browser_mcp.settings.mount_path = "/browser"

# Create Starlette app with multiple mounted servers
app = Starlette(
    routes=[
        Mount("/github", app=github_mcp.sse_app()),
        Mount("/browser", app=browser_mcp.sse_app()),
    ]
)
```

## Transport Implementations

### SSE Transport

#### `SseServerTransport` Class

The `SseServerTransport` class from `mcp.server.sse` implements a Server-Sent Events (SSE) transport layer for MCP servers. It provides two ASGI applications for handling SSE connections:

1. `connect_sse()`: Handles incoming GET requests and sets up a new SSE stream to send server messages to the client
2. `handle_post_message()`: Handles incoming POST requests containing client messages linked to a previously-established SSE session

```python
from mcp.server.sse import SseServerTransport
from starlette.applications import Starlette
from starlette.responses import Response
from starlette.routing import Mount, Route

# Initialize the SSE transport with a message endpoint path
sse = SseServerTransport("/messages/")

# Define an asynchronous request handler for SSE connections
async def handle_sse(request):
    async with sse.connect_sse(
        request.scope, request.receive, request._send
    ) as streams:
        await app.run(
            streams[0], streams[1], app.create_initialization_options()
        )
    # Return empty response to avoid NoneType error
    return Response()

# Create Starlette routes for SSE and message handling
starlette_app = Starlette(
    debug=True,
    routes=[
        Route("/sse", endpoint=handle_sse, methods=["GET"]),
        Mount("/messages/", app=sse.handle_post_message),
    ],
)
```

Key features of `SseServerTransport`:

- Manages bidirectional communication over HTTP using SSE for server-to-client messages and POST requests for client-to-server messages
- Provides DNS rebinding protection through the `TransportSecurityMiddleware`
- Handles session management with unique session IDs
- Supports sending events with different types (e.g., "endpoint", "message")

### Streamable HTTP Transport

#### `StreamableHTTPSessionManager` Class

The `StreamableHTTPSessionManager` class from `mcp.server.streamable_http_manager` implements the Streamable HTTP transport protocol for MCP servers. This transport is superseding SSE for production deployments.

```python
from mcp.server.lowlevel import Server
from mcp.server.streamable_http_manager import StreamableHTTPSessionManager
from starlette.applications import Starlette
from starlette.routing import Mount
from starlette.types import Receive, Scope, Send

# Create the server
app = Server("mcp-streamable-http-demo")

# Create event store for resumability
event_store = InMemoryEventStore()

# Create the session manager with our app and event store
session_manager = StreamableHTTPSessionManager(
    app=app,
    event_store=event_store,  # Enable resumability
    json_response=json_response,  # Toggle between JSON and SSE response formats
)

# ASGI handler for streamable HTTP connections
async def handle_streamable_http(
    scope: Scope, receive: Receive, send: Send
) -> None:
    await session_manager.handle_request(scope, receive, send)

# Create an ASGI application using the transport
starlette_app = Starlette(
    debug=True,
    routes=[
        Mount("/mcp", app=handle_streamable_http),
    ],
    lifespan=lifespan,  # Manages session manager lifecycle
)
```

Key features of `StreamableHTTPSessionManager`:

- Supports both stateful and stateless operation modes
- Provides resumability with event stores
- Supports both JSON and SSE response formats
- Offers better scalability for multi-node deployments
- Handles session management and message routing

The `lifespan` context manager is used to manage the session manager lifecycle:

```python
@contextlib.asynccontextmanager
async def lifespan(app: Starlette) -> AsyncIterator[None]:
    """Context manager for managing session manager lifecycle."""
    async with session_manager.run():
        logger.info("Application started with StreamableHTTP session manager!")
        try:
            yield
        finally:
            logger.info("Application shutting down...")
```

## Advanced Usage

### Low-Level Server

For more control, you can use the low-level server implementation directly:

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncIterator

from mcp.server import Server

@asynccontextmanager
async def server_lifespan(server: Server) -> AsyncIterator[dict]:
    """Manage server startup and shutdown lifecycle."""
    # Initialize resources on startup
    db = await Database.connect()
    try:
        yield {"db": db}
    finally:
        # Clean up on shutdown
        await db.disconnect()

# Pass lifespan to server
server = Server("example-server", lifespan=server_lifespan)

# Access lifespan context in handlers
@server.call_tool()
async def query_db(name: str, arguments: dict) -> list:
    ctx = server.request_context
    db = ctx.lifespan_context["db"]
    return await db.query(arguments["query"])
```

### Writing MCP Clients

The SDK provides a high-level client interface for connecting to MCP servers:

```python
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["example_server.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)

async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the connection
            await session.initialize()

            # List available prompts
            prompts = await session.list_prompts()

            # Get a prompt
            prompt = await session.get_prompt(
                "example-prompt", arguments={"arg1": "value"}
            )

            # List available resources
            resources = await session.list_resources()

            # List available tools
            tools = await session.list_tools()

            # Read a resource
            content, mime_type = await session.read_resource("file://some/path")

            # Call a tool
            result = await session.call_tool("tool-name", arguments={"arg1": "value"})
```

## MCP Primitives

The MCP protocol defines three core primitives that servers can implement:

| Primitive | Control               | Description                                         | Example Use                  |
|-----------|-----------------------|-----------------------------------------------------|------------------------------|
| Prompts   | User-controlled       | Interactive templates invoked by user choice        | Slash commands, menu options |
| Resources | Application-controlled| Contextual data managed by the client application   | File contents, API responses |
| Tools     | Model-controlled      | Functions exposed to the LLM to take actions        | API calls, data updates      |

## Server Capabilities

MCP servers declare capabilities during initialization:

| Capability  | Feature Flag                 | Description                        |
|-------------|------------------------------|------------------------------------|
| `prompts`   | `listChanged`                | Prompt template management         |
| `resources` | `subscribe`<br/>`listChanged`| Resource exposure and updates      |
| `tools`     | `listChanged`                | Tool discovery and execution       |
| `logging`   | -                            | Server logging configuration       |
| `completion`| -                            | Argument completion suggestions    |
