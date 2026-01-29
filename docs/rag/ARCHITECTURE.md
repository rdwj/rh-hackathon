# "Ask the Griot" RAG Architecture

This document describes the architecture for implementing [Issue #14: "Ask the Griot" feature](https://github.com/griot-and-grits/rh-hackathon/issues/14) - a RAG-based chat interface where users can ask questions and receive answers grounded in the collection data.

## Current State

The Griot & Grits platform currently has **no vector database or RAG components**:

```text
┌─────────────────────────────────────────────────────────────────┐
│                     Current Architecture                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   Frontend (Next.js) ──────► Backend (FastAPI)                   │
│        :3000                      :8000                          │
│                                     │                            │
│                         ┌───────────┼───────────┐                │
│                         ▼           ▼           ▼                │
│                     MongoDB      MinIO      Whisper              │
│                      :27017      :9000      (optional)           │
│                    [Metadata]  [Artifacts] [Transcription]       │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**What exists today:**

- **MongoDB**: Document metadata (PREMIS preservation records)
- **MinIO**: Object storage for artifact files (audio, images, documents)
- **Whisper**: Optional speech-to-text transcription
- No semantic search, no embeddings, no RAG pipeline

## Proposed Architecture

### High-Level Overview

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                        "Ask the Griot" RAG Architecture                       │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────┐      ┌──────────────┐      ┌────────────────┐                   │
│  │ Frontend│─────►│   Backend    │─────►│  Griot Agent   │                   │
│  │ Chat UI │      │   FastAPI    │      │  (MCP Client)  │                   │
│  └─────────┘      └──────────────┘      └───────┬────────┘                   │
│                                                 │                            │
│                          ┌──────────────────────┼──────────────────┐         │
│                          │                      │                  │         │
│                          ▼                      ▼                  ▼         │
│                   ┌────────────┐        ┌────────────┐     ┌────────────┐    │
│                   │retrieval-  │        │ingestion-  │     │   LLM      │    │
│                   │mcp         │        │mcp         │     │  (MaaS)    │    │
│                   └─────┬──────┘        └─────┬──────┘     └────────────┘    │
│                         │                     │                              │
│                         ▼                     ▼                              │
│                   ┌──────────────┐      ┌──────────────┐                     │
│                   │vector-gateway│      │   Docling    │                     │
│                   │  (FastAPI)   │      │   Chunker    │                     │
│                   └──────┬───────┘      └──────────────┘                     │
│                          │                                                   │
│            ┌─────────────┼─────────────┐                                     │
│            ▼             ▼             ▼                                     │
│     ┌──────────┐  ┌──────────────┐  ┌──────────────┐                         │
│     │  Milvus  │  │  Embeddings  │  │   Reranker   │                         │
│     │ [Vectors]│  │   (MaaS)     │  │   (future)   │                         │
│     └──────────┘  └──────────────┘  └──────────────┘                         │
│                                                                               │
│  ┌─────────┐      ┌──────────────┐      ┌──────────────┐                     │
│  │ MongoDB │      │    MinIO     │      │   Whisper    │                     │
│  │[Metadata]│     │ [Artifacts]  │      │[Transcripts] │                     │
│  └─────────┘      │ [Staging]    │      └──────────────┘                     │
│                   └──────────────┘                                           │
│                                                                               │
│  ════════════════════════════════════════════════════════════════════════    │
│                     External Services (MaaS - No Local Deployment)           │
│  ════════════════════════════════════════════════════════════════════════    │
│                                                                               │
│     ┌────────────────┐  ┌────────────────┐  ┌────────────────┐               │
│     │ Llama-4-Scout  │  │  Nomic Embed   │  │ Granite Vision │               │
│     │    17B (LLM)   │  │  Text v1.5     │  │   3.2 2B       │               │
│     └────────────────┘  └────────────────┘  └────────────────┘               │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

### Key Decisions

| Decision | Choice | Rationale |
| -------- | ------ | --------- |
| Vector Database | Standalone Milvus (Helm) | No admin access for LlamaStack; Helm is simpler |
| LLM for Generation | MaaS endpoint (no local deployment) | Shared resources, no GPU needed locally |
| Embedding Model | MaaS endpoint (no local deployment) | Simplifies deployment, no model management |
| Collection Strategy | Single "griot" collection | Start simple, expand later if needed |
| Agent Architecture | MCP-based agent | Agent decides when to retrieve, chat, etc. |
| Namespace | Same as existing services | Single namespace for simplicity |
| Code Strategy | Copy from advanced-rag (not move) | Keep advanced-rag intact as reference |

## AI Models (Models-as-a-Service)

**This project does not deploy any AI models locally.** All AI capabilities are accessed via MaaS (Model-as-a-Service) endpoints. Developers must either:

1. Use the provided MaaS endpoints (if available in your environment)
2. Deploy compatible models to OpenShift AI and configure endpoints
3. Use alternative hosted model APIs (OpenAI, etc.)

### Required Models

| Purpose | Model | API Compatibility | Notes |
| ------- | ----- | ----------------- | ----- |
| **LLM (Generation)** | Llama-4-Scout-17B | OpenAI Chat Completions | Tool calling supported |
| **Embeddings** | Nomic Embed Text v1.5 | OpenAI Embeddings | 768-dim vectors |
| **Vision (optional)** | Granite Vision 3.2 2B | OpenAI Vision | Image analysis |
| **Speech-to-Text** | Whisper ASR | Custom REST API | Transcription + timestamps |

### Current MaaS Configuration

Configured in `.env.local` (API keys stored separately):

```bash
# LLM - Chat/Agent generation with tool calling
LLAMA_API_URL=https://llama-4-scout-17b-16e-w4a16-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443
LLAMA_MODEL=llama-4-scout-17b-16e-w4a16

# Embeddings - Document and query vectorization
NOMIC_API_URL=https://nomic-embed-text-v1-5-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443
NOMIC_MODEL=/mnt/models

# Vision (optional) - Image understanding for artifacts
GRANITE_VISION_API_URL=https://granite-vision-3-2-2b-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443
GRANITE_VISION_MODEL=granite-vision-3-2

# Speech-to-Text - Audio transcription (no API key required)
WHISPER_ASR_API_URL=https://whisper-api-griot-grits.apps.ocp-test.nerc.mghpcc.org
```

### Model Capabilities

**Llama-4-Scout-17B:**

- OpenAI-compatible chat completions API (`/v1/chat/completions`)
- Tool calling support (verified working)
- Suitable for agent-based workflows

**Nomic Embed Text v1.5:**

- OpenAI-compatible embeddings API (`/v1/embeddings`)
- 768-dimensional vectors
- Good multilingual support
- Efficient for document search

**Granite Vision 3.2 2B (optional):**

- Vision-language model for image understanding
- Can describe artifact images, extract text from photos
- Useful for enriching image-based artifacts with searchable descriptions

**Whisper ASR:**

- Speech-to-text transcription for audio/video artifacts
- Word-level timestamps with confidence scores
- Speaker diarization support (identify different speakers)
- 99 language support with auto-detection
- Output formats: plain text, JSON (with timestamps), SRT, VTT subtitles

### Alternative Model Options

If the MaaS endpoints are unavailable, you can:

1. **Deploy to OpenShift AI:**
   - Use vLLM ServingRuntime for LLM
   - Use vLLM with `--task embed` for embeddings
   - Reference: `/Users/wjackson/Developer/advanced-rag/models/`

2. **Use Caikit (CPU-only):**
   - Granite-278m-multilingual for embeddings
   - MS-MARCO MiniLM L12 for reranking
   - Reference: `/Users/wjackson/Developer/advanced-rag/models/caikit-embeddings/`

3. **Use external APIs:**
   - OpenAI API (text-embedding-3-small, gpt-4o)
   - Cohere API
   - Other OpenAI-compatible endpoints

## Components to Deploy

Since models are accessed via MaaS, local deployment focuses on infrastructure and services:

### From `advanced-rag/databases/milvus/`

Standalone Milvus deployment using Helm chart.

**Resource requirements:**

- CPU: 1 core request / 4 cores limit
- Memory: 4Gi request / 8Gi limit
- Storage: 10Gi etcd + 20Gi MinIO PVCs

**Note:** Requires SCC grants before deployment:

```bash
oc adm policy add-scc-to-user anyuid -z default -n $NAMESPACE
oc adm policy add-scc-to-user anyuid -z milvus-minio -n $NAMESPACE
```

### From `advanced-rag/services/`

| Service | Purpose | API |
| ------- | ------- | --- |
| `vector_gateway/` | Abstraction over Milvus with hybrid search | REST `/upsert`, `/search`, `/collections` |
| `chunker_service/` | Text segmentation with configurable presets | REST `/chunk` |

**Note:** vector-gateway needs configuration to use the MaaS embedding endpoint instead of local models.

### From `advanced-rag/ingestion-mcp/` and `retrieval-mcp/`

MCP servers that provide agent-friendly interfaces:

**ingestion-mcp tools:**

- `ingest_document` - File ingestion (PDF, DOCX, TXT, MD, HTML)
- `ingest_text` - Raw text ingestion (for transcripts)
- `ingest_from_url` - URL fetching
- `get_collections` - Collection listing

**retrieval-mcp tools:**

- `rag_search` - Hybrid search with reranking
- `rag_list_collections` - Collection discovery
- `rag_list_sources` - Document listing
- `rag_rewrite_query` - Query optimization

## Agent Architecture

The "Ask the Griot" feature uses an **agent-based architecture** where an AI agent decides when and how to use retrieval tools.

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Griot Agent Architecture                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  User: "Tell me about the migration stories from Mississippi"                │
│              │                                                               │
│              ▼                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                         Griot Agent                                   │   │
│  │  ┌────────────────────────────────────────────────────────────────┐  │   │
│  │  │ System Prompt: "You are The Griot, an AI oral historian..."    │  │   │
│  │  │ "Use rag_search to find relevant stories before answering."    │  │   │
│  │  │ "Always cite your sources. Never make up information."         │  │   │
│  │  └────────────────────────────────────────────────────────────────┘  │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  Agent thinks: "I should search for Mississippi migration stories"   │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  Tool call: rag_search(query="migration Mississippi", top_k=5)       │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  [Results returned with sources and citations]                        │   │
│  │                              │                                        │   │
│  │                              ▼                                        │   │
│  │  Agent generates response with citations                              │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│              │                                                               │
│              ▼                                                               │
│  Response: "The Great Migration brought many families from Mississippi..."   │
│  Sources: [Interview with Mary Johnson, 1985], [Oral History #42]           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Why MCP-based agent?**

- Agent decides when retrieval is needed (not every question needs search)
- Agent can reformulate queries if initial search yields poor results
- Agent can combine information from multiple searches
- Agent maintains conversation context across turns
- Future extensibility: agent can use other tools (ingest new content, etc.)

## Integration Architecture

### MinIO as Staging Area

MinIO serves dual purposes:

1. **Artifact storage** (existing): Final storage for uploaded artifacts
2. **Ingestion staging** (new): Temporary holding area for documents awaiting vector ingestion

### Ingestion Flow

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Ingestion Flow                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. Artifact uploaded to MinIO (artifacts/ bucket)                           │
│              │                                                               │
│              ▼                                                               │
│  2. Copy to rag-staging/pending/ for ingestion                               │
│              │                                                               │
│              ▼                                                               │
│  3. If audio/video → Whisper transcription → save transcript                 │
│              │                                                               │
│              ▼                                                               │
│  4. ingestion-mcp receives document/transcript                               │
│              │                                                               │
│              ▼                                                               │
│  5. Pipeline: Docling → Chunker → Vector Gateway → Milvus                    │
│     - Nomic embeddings generated (768-dim) via MaaS                          │
│     - Chunks stored with metadata (source, page, section)                    │
│              │                                                               │
│              ▼                                                               │
│  6. Move to rag-staging/completed/ or delete                                 │
│                                                                              │
│  7. Metadata in MongoDB links artifact_id ↔ Milvus chunks                    │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Retrieval Flow (Ask the Griot)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Retrieval Flow                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. User asks question in Chat UI                                            │
│              │                                                               │
│              ▼                                                               │
│  2. Backend invokes Griot Agent with user message                            │
│              │                                                               │
│              ▼                                                               │
│  3. Agent (via MaaS LLM) decides to use rag_search tool                      │
│              │                                                               │
│              ▼                                                               │
│  4. retrieval-mcp → Vector Gateway → Milvus                                  │
│     a. Query embedded via Nomic (768-dim) via MaaS                           │
│     b. Hybrid search: dense vectors + BM25 sparse                            │
│     c. Context window expanded (surrounding chunks)                          │
│              │                                                               │
│              ▼                                                               │
│  5. Agent receives ranked chunks with sources                                │
│              │                                                               │
│              ▼                                                               │
│  6. Agent generates response grounded in retrieved context                   │
│              │                                                               │
│              ▼                                                               │
│  7. Response returned with citations linking to MongoDB/MinIO artifacts      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Infrastructure Requirements

### OpenShift Resources (Local Deployment Only)

| Component | CPU | Memory | Storage | Notes |
| --------- | --- | ------ | ------- | ----- |
| Milvus | 1-4 cores | 4-8Gi | 30Gi PVC | Standalone mode |
| Docling | 1 core | 2Gi | - | Document parsing |
| Chunker | 0.5 core | 512Mi | - | Text segmentation |
| Vector Gateway | 1 core | 1Gi | - | Milvus abstraction |
| ingestion-mcp | 0.5 core | 512Mi | - | MCP server |
| retrieval-mcp | 0.5 core | 512Mi | - | MCP server |

**Total estimates:**

- CPU: ~5-8 cores
- Memory: ~10-15Gi
- GPU: None (models accessed via MaaS)
- Storage: 30Gi+ for Milvus

### Environment Variables

```bash
# MaaS Model Endpoints
LLAMA_API_URL=<llm-endpoint>
LLAMA_MODEL=<model-name>
LLAMA_API_KEY=<api-key>

NOMIC_API_URL=<embedding-endpoint>
NOMIC_MODEL=<model-name>
NOMIC_API_KEY=<api-key>

# Optional: Vision model for image artifacts
GRANITE_VISION_API_URL=<vision-endpoint>
GRANITE_VISION_MODEL=<model-name>
GRANITE_VISION_API_KEY=<api-key>

# Vector Gateway
VECTOR_GATEWAY_URL=http://vector-gateway:8000

# MCP servers (for agent)
RETRIEVAL_MCP_URL=http://retrieval-mcp:8080/mcp/
INGESTION_MCP_URL=http://ingestion-mcp:8080/mcp/

# Collection name
GRIOT_COLLECTION=griot

# MinIO staging
RAG_STAGING_BUCKET=rag-staging
```

## The Griot Persona

System prompt for the Griot Agent:

```text
You are The Griot, an AI oral historian dedicated to preserving and sharing
the stories of minority communities. You have access to a collection of
oral histories, interviews, documents, and cultural artifacts.

Guidelines:
- ALWAYS use the rag_search tool before answering questions about the collection
- Ground your responses ONLY in the retrieved context - never make up information
- Cite your sources by referencing the specific artifacts (e.g., "According to
  the interview with Mary Johnson recorded in 1985...")
- If no relevant information is found, say so honestly
- Speak with warmth and respect for the communities whose stories you carry
- When appropriate, acknowledge the complexity and diversity of experiences
- Preserve the voices of the original storytellers - quote them when possible

You may:
- Search the collection multiple times if needed
- Reformulate queries if initial searches don't find relevant content
- Combine information from multiple sources
- Provide context about historical events when relevant to understanding stories

You must NOT:
- Invent stories, quotes, or facts not in the collection
- Speak for communities you don't have data about
- Make assumptions about experiences not documented in the sources
```

## Directory Structure (Proposed)

```text
infra/rag/
├── milvus/
│   └── openshift/
│       └── values-openshift.yaml
├── vector-gateway/
│   ├── src/
│   └── openshift/
│       └── deployment.yaml
├── chunker-service/
│   ├── src/
│   └── openshift/
│       └── deployment.yaml
├── ingestion-mcp/
│   ├── src/
│   └── openshift/
│       └── deployment.yaml
└── retrieval-mcp/
    ├── src/
    └── openshift/
        └── deployment.yaml
```

## References

- [Milvus Helm Chart](https://github.com/zilliztech/milvus-helm)
- [Nomic Embed Text v1.5](https://huggingface.co/nomic-ai/nomic-embed-text-v1.5)
- [Red Hat OpenShift AI - Working with Llama Stack](https://docs.redhat.com/en/documentation/red_hat_openshift_ai_self-managed/3.0/html-single/working_with_llama_stack/index)
