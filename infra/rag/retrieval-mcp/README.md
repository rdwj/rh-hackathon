# Griot Retrieval MCP Server

A FastMCP server that exposes RAG (Retrieval-Augmented Generation) capabilities via the Model Context Protocol for the Griot project - AI-powered preservation of minority history.

## Features

- **Hybrid Search**: Dense vector + BM25 sparse search with reranking
- **Context Expansion**: Automatically include surrounding chunks for better context
- **Query Rewriting**: LLM-powered query optimization for improved retrieval
- **Collection Discovery**: Tools to explore available collections and documents
- **Flexible Filtering**: Filter by file name, glob pattern, or MIME type
- **Multiple Output Formats**: Concise citations or detailed JSON responses
- **Default Collection**: Pre-configured for the "griot" collection

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   AI Agent      │────▶│  retrieval-mcp  │────▶│ vector-gateway  │
│   (Claude,      │ MCP │  (FastMCP)      │HTTP │ (FastAPI)       │
│   LibreChat)    │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └────────┬────────┘
                                                         │
                                                         ▼
                                                ┌─────────────────┐
                                                │  Milvus/PGVector│
                                                │  (Vector Store) │
                                                └─────────────────┘
```

## MCP Tools

### `rag_search`

Primary retrieval tool. Performs hybrid search with reranking and context expansion.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Natural language search query |
| `collection` | string | "griot" | Collection to search |
| `top_k` | int | 5 | Number of results (1-20) |
| `context_window` | int | 2 | Surrounding chunks to include (0-5) |
| `file_name` | string | null | Filter by exact file name |
| `file_pattern` | string | null | Filter by glob pattern (e.g., `interview-*`) |
| `mime_type` | string | null | Filter by MIME type |
| `min_score` | float | 0.0 | Minimum relevance threshold (0.0-1.0) |
| `response_format` | string | "concise" | `concise` or `detailed` |

### `rag_list_collections`

Discover available document collections in the vector store.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `response_format` | string | "concise" | `concise` (names) or `detailed` (with stats) |

### `rag_list_sources`

List documents within a specific collection.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `collection` | string | "griot" | Collection name |
| `response_format` | string | "concise" | `concise` or `detailed` |
| `limit` | int | 50 | Maximum sources to return (1-500) |

### `rag_rewrite_query`

Optimize a query for better retrieval using LLM sampling.

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `query` | string | required | Original query to rewrite |
| `domain_context` | string | null | Domain hints (e.g., "oral history interviews") |
| `rewrite_style` | string | "expand" | `expand`, `simplify`, or `technical` |

## Deployment to OpenShift

### Prerequisites

- OpenShift CLI (`oc`) installed and logged in
- `vector-gateway` service deployed in the same namespace

### Deploy

```bash
# Deploy to current namespace
./deploy.sh

# Or specify namespace
./deploy.sh griot-dev
```

### Manual Deployment

```bash
NAMESPACE=griot-dev

# Create build resources
oc apply -f openshift/buildconfig.yaml -n $NAMESPACE

# Build the image
oc start-build retrieval-mcp --from-dir=. --follow -n $NAMESPACE

# Deploy (substitute namespace in deployment.yaml)
sed "s/\${NAMESPACE}/$NAMESPACE/g" openshift/deployment.yaml | oc apply -f - -n $NAMESPACE
oc apply -f openshift/service.yaml -n $NAMESPACE
oc apply -f openshift/route.yaml -n $NAMESPACE
```

### Verify Deployment

```bash
# Check pods
oc get pods -n $NAMESPACE -l app=retrieval-mcp

# View logs
oc logs -f deployment/retrieval-mcp -n $NAMESPACE

# Get route URL
oc get route retrieval-mcp -n $NAMESPACE -o jsonpath='{.spec.host}'
```

## Local Development

### Setup

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Run Locally (STDIO mode)

```bash
python -m src.main
```

### Run with HTTP Transport

```bash
export MCP_TRANSPORT=http
export MCP_HTTP_PORT=8080
export VECTOR_GATEWAY_URL=http://localhost:8000
python -m src.main
```

### Test with MCP Inspector

```bash
# After deployment
npx @modelcontextprotocol/inspector https://<route-url>/mcp/
```

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VECTOR_GATEWAY_URL` | `http://vector-gateway:8000` | Vector gateway service URL |
| `DEFAULT_COLLECTION` | `griot` | Default collection for searches |
| `MCP_TRANSPORT` | `stdio` | Transport: `stdio` (local) or `http` (OpenShift) |
| `MCP_HTTP_PORT` | `8080` | HTTP server port (when using http transport) |
| `MCP_HTTP_PATH` | `/mcp/` | HTTP endpoint path |
| `MCP_SERVER_NAME` | `griot-retrieval-mcp` | Server name for identification |

## Integration Examples

### LibreChat Agent

Configure the MCP server in your agent's system prompt:

```
You have access to a document retrieval system via MCP tools.
The default collection is "griot" containing oral history interviews and narratives.

Available tools:
- rag_search: Search for relevant content
- rag_list_sources: See available documents
- rag_rewrite_query: Optimize queries for oral history content
```

### Claude Code

Add to your MCP server configuration:

```json
{
  "mcpServers": {
    "griot-retrieval": {
      "command": "python",
      "args": ["-m", "src.main"],
      "cwd": "/path/to/retrieval-mcp",
      "env": {
        "VECTOR_GATEWAY_URL": "https://vector-gateway-griot.apps.your-cluster.com"
      }
    }
  }
}
```

## Related Components

- [vector-gateway](../vector-gateway/) - Vector store abstraction service
- [ingestion-mcp](../ingestion-mcp/) - Document ingestion MCP server
- [chunker-service](../chunker-service/) - Document chunking service
