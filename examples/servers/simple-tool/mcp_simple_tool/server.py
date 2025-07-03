# Import necessary libraries.
# click is used to create a command-line interface.
# mcp.types provides the data structures for the Model Context Protocol.
# mcp.server.lowlevel.Server is the core class for creating an MCP server.
# mcp.shared._httpx_utils provides a utility to create an HTTP client.
import click
import httpx
import mcp.types as types
from mcp.server.lowlevel import Server
from mcp.shared._httpx_utils import create_mcp_http_client

# Core function to fetch website content.
async def fetch_website(
    url: str,
    ) -> list[types.ContentBlock]:
    """
    Fetches the content of a website for a given URL.

    Args:
        url: The URL of the website to fetch.

    Returns:
        A list containing a single TextContent block with the website's text content.
    """
    # Set a User-Agent header to identify the client making the request.
    headers = {
        "User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)"
    }
    # Create an MCP HTTP client with the specified headers.
    async with create_mcp_http_client(headers=headers) as client:
        # Make an asynchronous GET request to the URL.
        response = await client.get(url)
        # Raise an exception if the request returned an HTTP error status.
        response.raise_for_status()
        # Return the response text wrapped in a TextContent block.
        return [types.TextContent(type="text", text=response.text)]


# Core function to fetch website content using a secure SSL connection.
async def fetch_website_via_ssl(
    url: str,
    ) -> list[types.ContentBlock]:
    """
    Fetches the content of a website for a given URL using a secure SSL connection.

    Args:
        url: The URL of the website to fetch.

    Returns:
        A list containing a single TextContent block with the website's text content.
    """
    # Set a User-Agent header to identify the client making the request.
    headers = {
        "User-Agent": "MCP Test Server (github.com/modelcontextprotocol/python-sdk)"
    }
    # Create an MCP HTTP client with the specified headers.
    async with httpx.AsyncClient(headers=headers) as client:
        # Make an asynchronous GET request to the URL.
        response = await client.get(url)
        # Raise an exception if the request returned an HTTP error status.
        response.raise_for_status()
        # Return the response text wrapped in a TextContent block.
        return [types.TextContent(type="text", text=response.text)]


# Defines a command-line interface for the server using click.
@click.command()
# Adds a '--port' option to specify the listening port for SSE transport.
@click.option("--port", default=8000, help="Port to listen on for SSE")
# Adds a '--transport' option to choose between 'stdio' and 'sse'.
@click.option("--transport",
    type=click.Choice(["stdio", "sse"]),
    default="stdio",
    help="Transport type",
)

def main(port: int, transport: str) -> int:
    """
    Main function to set up and run the MCP server.

    Args:
        port: The port number for the SSE server.
        transport: The communication transport to use ('stdio' or 'sse').
    """
    # Initialize the MCP Server with a unique name for identification.
    app = Server("mcp-website-fetcher")

    # Registers a function to handle tool calls from a client.
    @app.call_tool()
    async def handle_tool_call(name: str, arguments: dict) -> list[types.ContentBlock]:
        """
        Handles the tool call from the client.

        Args:
            name: The name of the tool being called.
            arguments: A dictionary of arguments for the tool.

        Returns:
            The content fetched from the website.
        
        Raises:
            ValueError: If the tool name is unknown or arguments are missing.
        """
        # Ensure the correct tool is being called.
        if name not in ["fetch", "fetch_web_content_via_ssl"]:
            raise ValueError(f"Unknown tool: {name}")
        
        # Validate that the required 'url' argument is provided.
        if "url" not in arguments:
            raise ValueError("Missing required argument 'url'")
        
        # Use the helper function to perform the website fetch.
        if name == "fetch":
            return await fetch_website(arguments["url"])
        elif name == "fetch_web_content_via_ssl":
            return await fetch_website_via_ssl(arguments["url"])

    # Registers a function to list the tools available on this server.
    @app.list_tools()
    async def list_tools() -> list[types.Tool]:
        """Returns the list of tools that this server provides."""
        return [
            types.Tool(
                name="fetch",
                title="Website Fetcher",
                description="Fetches a website and returns its content",
                # Defines the expected input schema for the 'fetch' tool.
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
            ),
            types.Tool(
                name="fetch_web_content_via_ssl",
                title="Website Fetcher via SSL",
                description="Fetches a website and returns its content using a secure SSL connection",
                # Defines the expected input schema for the 'fetch_web_content_via_ssl' tool.
                inputSchema={
                    "type": "object",
                    "required": ["url"],
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "URL to fetch over SSL",
                        }
                    },
                },
            )
        ]

    # Depending on the chosen transport, configure and run the server.
    if transport == "sse":
        # Import uvicorn to run the ASGI application.
        import uvicorn
        # SSE (Server-Sent Events) is used for communication over HTTP, suitable for web clients.
        from mcp.server.sse import SseServerTransport
        from starlette.applications import Starlette
        from starlette.responses import Response
        from starlette.routing import Mount, Route

        # Initialize the SSE transport with a message endpoint path.
        sse = SseServerTransport("/messages/")

        # This function is an asynchronous request handler
        # that gets triggered when a client tries to establish an SSE connection.
        async def handle_sse(request):
            """Handles an incoming SSE connection request."""
            # Establish an SSE connection and run the MCP application.
            async with sse.connect_sse(
                request.scope, request.receive, request._send
            ) as streams:
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
            return Response()

        # Create a Starlette web application to handle HTTP requests.
        # When a client sends a GET request to /sse, the 
        # handle_sse function is called to open the SSE connection.
        starlette_app = Starlette(
            debug=True,
            routes=[
                # Route for establishing the SSE connection.
                Route("/sse", endpoint=handle_sse, methods=["GET"]),
                # Mount point for handling incoming POST messages from the client.
                Mount("/messages/", app=sse.handle_post_message),
            ],
        )

        # Run the Starlette app using uvicorn.
        uvicorn.run(starlette_app, host="127.0.0.1", port=port)
    else:
        # Import anyio to run the server.
        import anyio
        # 'stdio' (standard input/output) is used for direct command-line interaction.
        # The stdio_server doesn't open a network port.
        # Instead, it captures the process's standard input (what you type in the terminal)
        # and standard output (what gets printed to the terminal) and treats them as a pair of communication streams.
        from mcp.server.stdio import stdio_server

        async def arun():
            """Runs the server using standard I/O."""
            # Create a stdio server to handle input and output streams.
            async with stdio_server() as streams:
                # Run the MCP application with the stdio streams.
                await app.run(
                    streams[0], streams[1], app.create_initialization_options()
                )
        
        # Start the asynchronous event loop for the stdio server.
        anyio.run(arun)

    return 0
