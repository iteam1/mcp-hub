# MCP Cheatsheet

## Components

- **Proxy server (MCPP)**: Your web browser, for security reasons, cannot directly start or communicate with a local program on your computer, like your Python server using stdio. Browsers are built to communicate over web protocols like HTTP. The proxy server bridges this gap. The Inspector UI (in your browser) sends requests to the Proxy Server (listening on `127.0.0.1:6277`). The Proxy Server then takes those requests and forwards them to your MCP Server using the correct transport method (like stdio, SSE, streamable HTTP).

- **Inspector (MCPI)**: The Inspector UI on `127.0.0.1:6274` sends requests to the Proxy Server.

- **MCP server**: The MCP server is the program that handles the requests from the Proxy Server and performs the necessary actions based on the requests.

## Transports

### Abstraction

Use `npx @modelcontextprotocol/inspector` to start the inspector.

- STDIO: The inspector will start the MCP server by command `uv` with the arguments `run mcp_simple_tool` and connect to it. For example, `uv run mcp_simple_tool` or `run --with mcp --with Pillow --with pyautogui mcp run examples/fastmcp/screenshot.py`.

- SSE: We have to start the MCP server by command `uv run mcp_simple_tool --port 8000 --transport sse` before starting the inspector. The inspector will connect to the MCP server at `http://localhost:8000/sse`.

When run command `uv run`, `uv` will detect `pyproject.toml` and `uv.lock` to create the virtual environment and install dependencies before starting the MCP server. Without a token, any other application or even a malicious script in your browser could potentially connect to the inspector and interact with your MCP server. The session token ensures that only you (by using the special link provided) can communicate with the inspector's proxy. Any request made without the correct token will be rejected.

The session token is a security feature for the MCP Inspector.

### Details of STDIO Transport

The `stdio` (Standard Input/Output) transport is a simpler, non-web alternative to SSE, designed for direct interaction from the command line. It captures the process's standard input (keyboard) and standard output (terminal screen) and treats them as the communication streams for the MCP application. This allows the core application logic to remain identical regardless of the transport mechanism.



### Details of SSE Transport

The Server-Sent Events (SSE) transport allows an MCP server to communicate with clients over HTTP, making it ideal for web-based applications. It creates an abstraction layer where the core application logic doesn't need to know about the underlying HTTP transport.

The data flow is as follows:

1.  **Connection (`Route`)**: A client initiates a connection by sending a `GET` request to the `/sse` endpoint. A `Route` handler establishes a persistent connection and creates a pair of communication `streams`. The main `app.run()` logic then begins listening on these streams.

2.  **Communication (`Mount`)**: The client sends subsequent tool calls as `POST` requests to the `/messages/` endpoint. A `Mount` directive catches these requests and passes them to a dedicated `handle_post_message` application. This handler extracts the message from the HTTP request and forwards it to the `app.run()` loop via the input stream established in step 1.

This is implemented using a lightweight ASGI framework (`Starlette`) and a server (`uvicorn`).

Here is a comparison between the two transports:

| Feature      | `stdio` Transport                               | `sse` (Web) Transport                              |
|--------------|-------------------------------------------------|----------------------------------------------------|
| **Purpose**  | Direct command-line interaction, local testing. | Communication with web browsers or remote clients. |
| **Endpoint** | The terminal's standard input/output.           | A network port (e.g., `127.0.0.1:8000`).           |
| **Stack**    | `anyio`, `mcp.server.stdio`                     | `uvicorn`, `starlette`, `mcp.server.sse`           |
| **Core Logic** | Both use the **identical** `app.run()` call.    | Both use the **identical** `app.run()` call.       |

#### Key Components:

-   **`SseServerTransport("/messages/")`**: Initializes the core transport handler from the MCP library. It's configured to expect messages at the `/messages/` endpoint.

-   **`Route("/sse", ...)`**: This defines the entry point for the connection. A client starts the process by sending a `GET` request to the `/sse` URL. This triggers a handler function that establishes the persistent SSE connection and starts the main `app.run()` loop on the resulting communication streams.

-   **`Mount("/messages/", ...)`**: This delegates handling of a URL path to a sub-application. Here, it directs all `POST` requests under `/messages/` to `sse.handle_post_message`. This built-in handler is responsible for receiving tool call messages from the client and forwarding them to the main application logic running on its stream.

-   **`uvicorn.run(...)`**: This command starts the web server, making the `Route` and `Mount` endpoints available over the network.

In summary, a `Route` establishes the channel, and a `Mount` handles the messages sent through that channel.

## Resources

Read-only data sources that provide context without significant computation.

- Static resource

```python
@mcp.resource("echo://static")
def echo_resource() -> str:
    return "Echo!"
```

- Template resource

```python
@mcp.resource("echo://{text}")
def echo_template(text: str) -> str:
    """Echo the input text"""
    return f"Echo: {text}"
```

- Add description

```python
@mcp.tool(description="🌟 A tool that uses various Unicode characters in its description: " "á é í ó ú ñ 漢字 🎉")
def hello_unicode(name: str = "世界", greeting: str = "¡Hola") -> str:
    """
    A simple tool that demonstrates Unicode handling in:
    - Tool description (emojis, accents, CJK characters)
    - Parameter defaults (CJK characters)
    - Return values (Spanish punctuation, emojis)
    """
    return f"{greeting}, {name}! 👋"
```

- List directory

```python
@mcp.resource("dir://desktop")
def desktop() -> list[str]:
    """List the files in the user's desktop"""
    desktop = Path.home() / "Desktop"
    return [str(f) for f in desktop.iterdir()]
```

- Use `Annotated` for validation

```python
class ShrimpTank(BaseModel):
    class Shrimp(BaseModel):
        name: Annotated[str, Field(max_length=10)]

    shrimp: list[Shrimp]


@mcp.tool()
def name_shrimp(
    tank: ShrimpTank,
    # You can use pydantic Field in function signatures for validation.
    extra_names: Annotated[list[str], Field(max_length=10)],
) -> list[str]:
    """List all shrimp names in the tank"""
    return [shrimp.name for shrimp in tank.shrimp] + extra_names
```

- Use `Field` for parameter descriptions

```python
@mcp.tool()
def greet_user(
    name: str = Field(description="The name of the person to greet"),
    title: str = Field(description="Optional title like Mr/Ms/Dr", default=""),
    times: int = Field(description="Number of times to repeat the greeting", default=1),
) -> str:
    """Greet a user with optional title and repetition"""
    greeting = f"Hello {title + ' ' if title else ''}{name}!"
    return "\n".join([greeting] * times)
```

- Use dependencies

```python
import io
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.utilities.types import Image

# Create server
mcp = FastMCP("Screenshot Demo", dependencies=["pyautogui", "Pillow"])

@mcp.tool()
def take_screenshot() -> Image:
    """
    Take a screenshot of the user's screen and return it as an image. Use
    this tool anytime the user wants you to look at something they're doing.
    """
    import pyautogui

    buffer = io.BytesIO()

    # if the file exceeds ~1MB, it will be rejected by Claude
    screenshot = pyautogui.screenshot()
    screenshot.convert("RGB").save(buffer, format="JPEG", quality=60, optimize=True)
    return Image(data=buffer.getvalue(), format="jpeg")
```


## Tools

Executable functions that the AI model can invoke to perform actions or retrieve computed data. Typically relating to the use case of the application.

- Simple tool

```python
@mcp.tool()
def echo_tool(text: str) -> str:
    """Echo the input text"""
    return text
```

## Prompts

Pre-defined templates or workflows that guide interactions between users, AI models, and the available capabilities.

- Simple prompt

```python

@mcp.prompt("echo")
def echo_prompt(text: str) -> str:
    return text
```


## Sampling

Server-initiated requests for the Client/Host to perform LLM interactions, enabling recursive actions where the LLM can review generated content and make further decisions.