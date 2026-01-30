# Griot Agent

LangGraph-based RAG agent for the Griot & Grits collection. The Griot is an AI oral historian that helps users explore African American history, oral histories, and cultural artifacts.

## Features

- **LangGraph agent** with tool calling for retrieval
- **FastMCP client** for connecting to retrieval-mcp server
- **Llama-4-Scout-17B** via MaaS for generation with tool calling
- **Rich CLI** for interactive chat sessions
- **Citation support** for grounding responses in source documents

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      Griot Agent                            │
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   CLI Chat   │    │  LangGraph   │    │   FastMCP    │  │
│  │   Interface  │───▶│    Agent     │───▶│   Client     │  │
│  └──────────────┘    └──────────────┘    └──────────────┘  │
│                             │                    │          │
│                             ▼                    ▼          │
│                    ┌──────────────┐    ┌──────────────────┐│
│                    │Llama-4-Scout │    │  retrieval-mcp   ││
│                    │   (MaaS)     │    │    (OpenShift)   ││
│                    └──────────────┘    └──────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

## Installation

### Local Development

```bash
cd infra/rag/griot-agent

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -e .

# Or just install requirements
pip install -r requirements.txt
```

### Configuration

Create or update `.env.local` in the project root:

```bash
# LLM (Llama-4-Scout-17B via MaaS)
LLAMA_API_KEY=your-api-key-here
LLAMA_API_URL=https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1
LLAMA_MODEL=llama-4-scout-17b-16e-w4a16

# Retrieval MCP (update with your namespace)
RETRIEVAL_MCP_URL=https://retrieval-mcp-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com/mcp/
```

## Usage

### Interactive Chat

```bash
# Start interactive chat session
python -m src.cli chat

# Or if installed as package
griot chat
```

### CLI Commands

```bash
# Search the collection directly
python -m src.cli search "Great Migration"

# List available MCP tools
python -m src.cli list-tools

# Show configuration
python -m src.cli config
```

### In-Chat Commands

While in the interactive chat:

- `quit` or `exit` - End the session
- `clear` - Clear conversation history
- `sources` - List sources in the collection
- `tools` - List available MCP tools

## The Griot Persona

The Griot (pronounced GREE-oh) is modeled after the West African tradition of the griot - a storyteller, historian, and keeper of oral tradition. The agent:

- Speaks with warmth and reverence for the stories in the collection
- Connects individual narratives to broader historical contexts
- Always cites sources when referencing collection content
- Admits when information isn't available rather than fabricating

## Example Session

```
┌─────────────────────────────────────────────────────────────┐
│                    Welcome to the Griot                     │
├─────────────────────────────────────────────────────────────┤
│ I am the Griot, an AI oral historian for the Griot & Grits │
│ collection.                                                 │
│                                                             │
│ Ask me about:                                               │
│ - Historical events like the Great Migration                │
│ - Stories from oral history interviews                      │
│ - Cultural traditions and community history                 │
└─────────────────────────────────────────────────────────────┘

You: Tell me about the Great Migration

┌─────────────────────────────────────────────────────────────┐
│                          Griot                              │
├─────────────────────────────────────────────────────────────┤
│ The Great Migration holds a central place in our           │
│ collection. Based on oral history interviews, many         │
│ families made the journey north seeking opportunity...     │
│                                                             │
│ [Source: Mary Johnson oral history, 1985]                  │
│                                                             │
│ Would you like to explore specific family stories or       │
│ learn about the communities that formed in northern cities?│
└─────────────────────────────────────────────────────────────┘
```

## Development

### Running Tests

```bash
pytest tests/
```

### Testing MCP Connection

```bash
# Test the MCP client directly
python -m src.mcp_client
```

### Testing Agent

```bash
# Test the agent with a sample query
python -m src.agent
```

## Dependencies

- **LangGraph/LangChain**: Agent orchestration and LLM integration
- **FastMCP**: MCP client for retrieval-mcp server
- **langchain-openai**: OpenAI-compatible LLM client (works with Llama-4-Scout)
- **Rich**: Beautiful terminal output
- **Typer**: CLI framework

## Related Components

- [retrieval-mcp](../retrieval-mcp/) - MCP server for RAG search
- [ingestion-mcp](../ingestion-mcp/) - MCP server for document ingestion
- [vector-gateway](../vector-gateway/) - REST API for vector operations
