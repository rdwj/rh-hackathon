# Ingestion MCP Server

MCP server for document ingestion into the Griot & Grits RAG pipeline. Provides tools for AI agents to ingest documents, URLs, and raw text into the vector database.

## Tools

| Tool | Description |
|------|-------------|
| `ingest_document` | Ingest a local file (PDF, DOCX, TXT, MD, HTML) |
| `ingest_from_url` | Fetch and ingest content from a URL |
| `ingest_text` | Ingest raw text directly |
| `get_collections` | List collections or get stats for a specific collection |

## Prerequisites

This MCP server requires the following services deployed in the same namespace:

- **Docling service** (`docling-serve:8080`) - Document parsing (PDF, DOCX)
- **Chunker service** (`chunker-service:8080`) - Text chunking
- **Vector gateway** (`vector-gateway:8080`) - Embedding and storage (Milvus)

## Deployment

### Deploy to OpenShift

```bash
# Deploy to your namespace (auto-detects current project)
./deploy.sh

# Or specify a namespace
./deploy.sh gng-demo

# Verify deployment
oc get pods -l app=ingestion-mcp
```

### Environment Variables

These are pre-configured in the deployment manifest for same-namespace services:

| Variable | Default | Description |
|----------|---------|-------------|
| `DOCLING_SERVICE_URL` | `http://docling-serve:8080` | URL to docling-serve |
| `CHUNKER_SERVICE_URL` | `http://chunker-service:8080` | URL to chunker service |
| `VECTOR_GATEWAY_URL` | `http://vector-gateway:8080` | URL to vector gateway |
| `DEFAULT_COLLECTION` | `griot` | Default Milvus collection |
| `AUTH_TOKEN` | (empty) | Bearer token for service authentication |

To override for cross-namespace or external services, edit `openshift/deployment.yaml`.

## Agent Integration

Add to your LibreChat agent's MCP configuration:

```json
{
  "mcpServers": {
    "ingestion": {
      "url": "https://ingestion-mcp-<namespace>.apps.<cluster>/mcp/"
    }
  }
}
```

## Local Development

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables (point to local or port-forwarded services)
export DOCLING_SERVICE_URL="http://localhost:8081"
export CHUNKER_SERVICE_URL="http://localhost:8082"
export VECTOR_GATEWAY_URL="http://localhost:8083"
export DEFAULT_COLLECTION="griot"

# Run locally
python -m src.main

# Test with cmcp
cmcp ".venv/bin/python -m src.main" tools/list
```

## Usage Examples

### Ingest a document

```
Use ingest_document to ingest /data/oral-history.pdf into the griot collection
```

### Ingest from URL

```
Ingest the PDF at https://example.com/historical-document.pdf with tags ["oral-history", "1960s"]
```

### Ingest raw text

```
Ingest this interview transcript into the griot collection: [text content]
```

### List collections

```
What collections are available and how many documents are in each?
```

## Chunking Strategies

| Strategy | Token Window | Overlap | Use Case |
|----------|--------------|---------|----------|
| `default` | 200 | 40 | General documents |
| `dense` | 100 | 30 | Short documents, high precision |
| `sparse` | 400 | 60 | Long documents, efficiency |

## Supported File Types

- PDF (`.pdf`)
- Word (`.docx`, `.doc`)
- Text (`.txt`)
- Markdown (`.md`)
- HTML (`.html`, `.htm`)

## Architecture

```
                    +------------------+
                    | Ingestion MCP    |
                    |    :8080/mcp/    |
                    +--------+---------+
                             |
         +-------------------+-------------------+
         |                   |                   |
         v                   v                   v
+--------+--------+ +--------+--------+ +--------+--------+
| Docling Serve   | | Chunker Service | | Vector Gateway  |
|     :8080       | |     :8080       | |     :8080       |
+-----------------+ +-----------------+ +--------+--------+
                                                 |
                                                 v
                                        +--------+--------+
                                        |     Milvus      |
                                        +-----------------+
```
