
A simple MCP server that exposes a website fetching tool.

## Usage

Start the server using either stdio (default) or SSE transport:

```bash
# Using stdio transport (default)
uv run mcp-simple-tool

# Using SSE transport on custom port
uv run mcp-simple-tool --transport sse --port 8000
```

The server exposes a tool named "fetch" that accepts one required argument:

- `url`: The URL of the website to fetch

## Inspect the server

- Run inspector

```bash
npx @modelcontextprotocol/inspector
```

- Open inspector with token pre-filled: `http://localhost:6274/?MCP_PROXY_AUTH_TOKEN=<SessionToken>`


- Connect to the server URL `http://127.0.0.1:8000/sse` with transport type `SSE`


## Example

Using the MCP client, you can use the tool like this using the STDIO transport: `uv run client.py`

- Client code:

```python
import asyncio
from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def main():
    async with stdio_client(
        StdioServerParameters(command="uv", args=["run", "mcp-simple-tool"])
    ) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # List available tools
            tools = await session.list_tools()
            print(tools)

            # Call the fetch tool
            result = await session.call_tool("fetch", {"url": "https://example.com"})
            print(result)


asyncio.run(main())

```
