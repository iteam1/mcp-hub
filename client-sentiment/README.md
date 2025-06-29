# MCP Client Sentiment

## Setup

```bash
uv init client-sentiment -p 3.10
cp client-sentiment
uv venv -p 3.10
source .venv/bin/activate
uv add "smolagents[mcp]" "gradio[mcp]" mcp fastmcp
```

## Running the Client

```bash
python app.py
```

You should see a Gradio interface at http://127.0.0.1:7861