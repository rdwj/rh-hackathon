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

### Deployed to OpenShift (`infra/rag/`)

| Component | Location | Purpose |
| --------- | -------- | ------- |
| Milvus | `infra/rag/milvus/` | Vector database (Helm) |
| Vector Gateway | `infra/rag/vector-gateway/` | Milvus abstraction layer |
| Chunker Service | `infra/rag/chunker-service/` | Go-based text segmentation |
| Docling | `infra/rag/docling-serve/` | PDF/document conversion |
| ingestion-mcp | `infra/rag/ingestion-mcp/` | Document ingestion MCP server |
| retrieval-mcp | `infra/rag/retrieval-mcp/` | RAG search MCP server |

### Local Tools

| Component | Location | Purpose |
| --------- | -------- | ------- |
| Griot Agent | `infra/rag/griot-agent/` | LangGraph agent with CLI chat interface |

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
   # Services are already built and deployed to gng-user50
   ```

3. **Configure environment:**
   ```bash
   # Edit .env.local with your MaaS endpoints
   LLAMA_API_KEY=your-key
   LLAMA_API_URL=https://...
   NOMIC_API_KEY=your-key
   ```

4. **Test the Griot Agent CLI:**
   ```bash
   cd infra/rag/griot-agent
   python -m venv .venv && source .venv/bin/activate
   pip install -r requirements.txt
   python -m src.cli chat
   ```

5. **Test the pipeline:**
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
