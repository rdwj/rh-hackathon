# Ask the Griot - RAG Implementation

This directory contains documentation for the "Ask the Griot" RAG (Retrieval-Augmented Generation) feature - an AI-powered chat interface that allows users to ask questions and receive answers grounded in the collection's oral histories, documents, and artifacts.

## Overview

The Griot is an AI oral historian that:

- Searches the collection using semantic search
- Answers questions based only on retrieved content
- Cites sources for every claim
- Never makes up information

## Documents

| Document | Description |
| -------- | ----------- |
| [ARCHITECTURE.md](ARCHITECTURE.md) | Technical architecture, component design, and integration details |
| [BACKLOG.md](BACKLOG.md) | Implementation backlog and task breakdown |

## API Examples

Tested examples showing how to use each endpoint:

| Example | Description |
| ------- | ----------- |
| [examples/llm-chat-completions.md](examples/llm-chat-completions.md) | Llama-4-Scout-17B chat API with tool calling |
| [examples/embeddings-api.md](examples/embeddings-api.md) | Nomic Embed Text v1.5 for vector embeddings |
| [examples/vision-api.md](examples/vision-api.md) | Granite Vision 3.2 2B for image analysis |
| [examples/whisper-asr-api.md](examples/whisper-asr-api.md) | Whisper ASR for audio transcription |

## AI Models

**This project uses Models-as-a-Service (MaaS) - no local model deployment required.**

| Purpose | Model | Notes |
| ------- | ----- | ----- |
| LLM (Generation) | Llama-4-Scout-17B | Chat completions with tool calling |
| Embeddings | Nomic Embed Text v1.5 | 768-dimensional vectors |
| Vision (optional) | Granite Vision 3.2 2B | Image understanding for artifacts |
| Speech-to-Text | Whisper ASR | Audio transcription with timestamps |

### For Other Developers

If the MaaS endpoints are not available in your environment, you must either:

1. **Deploy models to OpenShift AI** - See `advanced-rag/models/` for vLLM deployment examples
2. **Use Caikit (CPU-only)** - See `advanced-rag/models/caikit-embeddings/` for CPU-based inference
3. **Use external APIs** - OpenAI, Cohere, or other OpenAI-compatible endpoints

Configure your model endpoints in `.env.local`:

```bash
# LLM
LLAMA_API_URL=<your-llm-endpoint>
LLAMA_MODEL=<model-name>
LLAMA_API_KEY=<api-key>

# Embeddings
NOMIC_API_URL=<your-embedding-endpoint>
NOMIC_MODEL=<model-name>
NOMIC_API_KEY=<api-key>
```

## Components

### To Deploy (Local Infrastructure)

| Component | Source | Purpose |
| --------- | ------ | ------- |
| Milvus | `advanced-rag/databases/milvus/` | Vector database |
| Vector Gateway | `advanced-rag/services/vector_gateway/` | Milvus abstraction layer |
| Chunker Service | `advanced-rag/services/chunker_service/` | Text segmentation |
| ingestion-mcp | `advanced-rag/ingestion-mcp/` | Document ingestion MCP server |
| retrieval-mcp | `advanced-rag/retrieval-mcp/` | RAG search MCP server |

### External (MaaS)

- LLM endpoint (Llama-4-Scout-17B or compatible)
- Embedding endpoint (Nomic Embed Text v1.5 or compatible)
- Optional: Vision endpoint (Granite Vision 3.2 2B)

## Quick Start

1. **Prerequisites:**
   - OpenShift cluster access
   - MaaS endpoints configured (or deploy your own models)
   - SCC grants for Milvus (requires cluster-admin)

2. **Deploy infrastructure:**
   ```bash
   # See BACKLOG.md for detailed steps
   ```

3. **Configure environment:**
   ```bash
   cp .env.local.example .env.local
   # Edit with your MaaS endpoints
   ```

4. **Test the pipeline:**
   ```bash
   # Ingest a sample document
   # Query via retrieval-mcp
   # See BACKLOG.md for testing steps
   ```

## Related Issues

- [Issue #14: "Ask the Griot" feature](https://github.com/griot-and-grits/rh-hackathon/issues/14)

## Reference Implementation

Code is being adapted from:

- `/Users/wjackson/Developer/advanced-rag/` - RAG infrastructure and MCP servers

This is a **copy** (not move) to keep the reference implementation intact.
