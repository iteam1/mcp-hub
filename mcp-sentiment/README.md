# MCP Sentiment

## Setup

```bash
uv init mcp-sentiment -p 3.10
cp mcp-sentiment
uv venv -p 3.10
source .venv/bin/activate
uv add "gradio[mcp]" textblob
```

##  Creating the Server

*Hugging face spaces needs an app.py file to build the space. So the name of the python file has to be app.py*

- Create a new file called [app.py](app.py)

- Start the server by running: `python app.py`

You should see output indicating that both the web interface and MCP server are running. The web interface will be available at http://localhost:7860, and the MCP server at http://localhost:7860/gradio_api/mcp/sse.

Visit http://localhost:7860/gradio_api/mcp/schema to see the MCP schema.

## Troubleshooting

Troubleshooting Tips

- Type Hints and Docstrings:
    - Always provide type hints for your function parameters and return values
    - Include a docstring with an “Args:” block for each parameter
    - This helps Gradio generate accurate MCP tool schemas

- String Inputs:
    - When in doubt, accept input arguments as str
    - Convert them to the desired type inside the function
    - This provides better compatibility with MCP clients

- SSE Support:
    - Some MCP clients don’t support SSE-based MCP Servers
    - In those cases, use mcp-remote:
```json
        {
          "mcpServers": {
            "gradio": {
              "command": "npx",
              "args": [
                "mcp-remote",
                "http://localhost:7860/gradio_api/mcp/sse"
              ]
            }
          }
        }
```

- Connection Issues:
    - If you encounter connection problems, try restarting both the client and server
    - Check that the server is running and accessible
    - Verify that the MCP schema is available at the expected URL

## Deploy on Hugging Face Spaces

To make your server available to others, you can deploy it to Hugging Face Spaces:

- Create a new Space on Hugging Face:
    - Go to huggingface.co/spaces
    - Click “Create new Space”
    - Choose “Gradio” as the SDK
    - Name your space (e.g., “mcp-sentiment”)

- Create a requirements.txt file:
```txt
gradio[mcp]
textblob
```

- Push your code to the Space:
```bash
git init
git add app.py requirements.txt
git commit -m "Initial commit"
git remote add origin https://huggingface.co/spaces/YOUR_USERNAME/mcp-sentiment
git push -u origin main
```

Your MCP server will now be available at: https://YOUR_USERNAME-mcp-sentiment.hf.space/gradio_api/mcp/sse



