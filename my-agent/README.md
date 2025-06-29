# my-agent

## Setup

Let’s install npx with npm. If you don’t have npm installed, check out the [npm documentation](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

```bash
# install npx
npm install -g npx
```

Then, we need to install the mcp-remote package. `npm i mcp-remote`

For JavaScript, we need to install the tiny-agents package. `npm install @huggingface/tiny-agents`

For Python, you need to install the latest version of huggingface_hub with the mcp extra to get all the necessary components. `pip install "huggingface_hub[mcp]>=0.32.0"`

## Tiny Agents MCP Client in the Command Line

Let’s setup a project with a basic Tiny Agent.

```bash
mkdir my-agent
touch my-agent/agent.json
```

The JSON file will look like [this](agent.json).


We can then run the agent with the following command:

```bash
npx @huggingface/tiny-agents run ./my-agent
```

For Python, you can run the agent with the following command:

```bash
tiny-agents run agent.json
```

## Using the Gradio Server with Tiny Agents

```python
import os

from huggingface_hub import Agent

agent = Agent(
    model="Qwen/Qwen2.5-72B-Instruct",
    provider="nebius",
    servers=[
        {
            "command": "npx",
            "args": [
                "mcp-remote",
                "http://localhost:7860/gradio_api/mcp/sse"  # Your Gradio MCP server
            ]
        }
    ],
)
```


[Tiny Agents: an MCP-powered agent in 50 lines of code ](https://huggingface.co/blog/tiny-agents)