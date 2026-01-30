# Ask the Griot - Implementation Backlog

This backlog tracks implementation tasks for the "Ask the Griot" RAG feature ([Issue #14](https://github.com/griot-and-grits/rh-hackathon/issues/14)).

## Status Legend

- [ ] Not started
- [x] Complete
- [~] In progress
- [!] Blocked

## Phase 1: Vector Infrastructure

### Milvus Deployment

- [x] Copy `advanced-rag/databases/milvus/openshift/` to `infra/rag/milvus/`
- [~] Request SCC grants from cluster admin (`anyuid` for default and milvus-minio service accounts)
- [!] Deploy Milvus via Helm chart (blocked on SCC)
- [!] Verify Milvus health endpoint (blocked on SCC)
- [!] Test basic collection creation (blocked on SCC)

### Vector Gateway

- [x] Copy `advanced-rag/services/vector_gateway/` to `infra/rag/vector-gateway/`
- [x] Update configuration to use Nomic embedding endpoint (MaaS)
- [x] Build and push container image
- [x] Deploy to OpenShift
- [x] Verify `/healthz` endpoint
- [!] Test `/upsert` with sample document (blocked on Milvus)
- [!] Test `/search` query (blocked on Milvus)

## Phase 2: Ingestion Pipeline

### Chunker Service

- [x] Copy `advanced-rag/services/chunker_service/` to `infra/rag/chunker-service/`
- [x] Build and push container image
- [x] Deploy to OpenShift
- [x] Test chunking with sample text

### Docling

- [x] Copy `advanced-rag/docling-serve/` to `infra/rag/docling-serve/`
- [x] Deploy Docling (CPU overlay for dev)
- [ ] Configure ingestion-mcp to use Docling endpoint
- [ ] Test PDF to Markdown conversion

### Ingestion MCP Server

- [x] Copy `advanced-rag/ingestion-mcp/` to `infra/rag/ingestion-mcp/`
- [x] Update configuration for this project's services
- [x] Build and push container image
- [x] Deploy to OpenShift
- [!] Test `ingest_text` with sample content (blocked on Milvus)
- [!] Test `ingest_document` with sample PDF (blocked on Milvus)
- [!] Verify documents appear in Milvus collection (blocked on Milvus)

### MinIO Staging Bucket

- [x] Create `rag-staging` bucket in existing MinIO
- [x] Create subdirectories: `pending/`, `processing/`, `completed/`
- [x] Test file upload to staging area

## Phase 3: Retrieval & Agent

### Retrieval MCP Server

- [x] Copy `advanced-rag/retrieval-mcp/` to `infra/rag/retrieval-mcp/`
- [x] Update configuration for this project's services
- [x] Build and push container image
- [x] Deploy to OpenShift
- [!] Test `rag_search` against ingested documents (blocked on Milvus)
- [!] Test `rag_list_collections` (blocked on Milvus)
- [!] Test `rag_list_sources` (blocked on Milvus)

### Griot Agent

- [x] Design agent implementation approach: **LangGraph with tool calling**
- [x] Implement FastMCP client for retrieval-mcp (`src/mcp_client.py`)
- [x] Implement LLM client for Llama-4-Scout MaaS endpoint
- [x] Implement LangGraph agent with tool calling (`src/agent.py`)
- [x] Create Griot system prompt (`src/prompts.py`)
- [x] Create CLI chat tool (`src/cli.py`)
- [!] Test agent with sample queries (blocked on Milvus)

### Backend Integration

- [ ] Add `/chat` endpoint to backend
- [ ] Implement request/response models
- [ ] Wire up Griot Agent
- [ ] Add conversation history support
- [ ] Implement citation extraction
- [ ] Add error handling and logging

## Phase 4: Frontend & Polish

### Chat UI

- [ ] Design chat interface mockup
- [ ] Implement chat component in frontend
- [ ] Add message history display
- [ ] Add citation/source links
- [ ] Add loading states
- [ ] Add error handling

### Guardrails

- [ ] Implement topic filtering (stay on-collection)
- [ ] Implement hallucination prevention (require citations)
- [ ] Add content moderation if needed
- [ ] Test edge cases

### Testing & Documentation

- [ ] Create sample test documents
- [ ] Ingest sample collection
- [ ] End-to-end testing
- [ ] Update user documentation
- [ ] Create demo script

## Phase 5: Production Readiness (Future)

- [ ] Performance optimization
- [ ] Backfill existing artifacts
- [ ] Add monitoring/metrics
- [ ] Add rate limiting
- [ ] Security review

## Blocked Items

| Item | Blocker | Notes |
| ---- | ------- | ----- |
| Milvus deployment | SCC grants needed | Requires cluster-admin to grant `anyuid` SCC |

## Dependencies

```text
Phase 1 (Infrastructure)
    │
    ├── Milvus ─────────────────────────────┐
    │                                        │
    └── Vector Gateway ──────────────────────┤
                                             │
Phase 2 (Ingestion)                          │
    │                                        │
    ├── Chunker Service ─────────────────────┤
    │                                        │
    ├── Docling ─────────────────────────────┤
    │                                        │
    └── ingestion-mcp ───────────────────────┤
                                             │
Phase 3 (Retrieval & Agent)                  │
    │                                        │
    ├── retrieval-mcp ◄──────────────────────┘
    │       │
    ├── Griot Agent ◄── retrieval-mcp
    │       │
    └── Backend /chat ◄── Griot Agent

Phase 4 (Frontend)
    │
    └── Chat UI ◄── Backend /chat
```

## Deployed Services

| Service | URL | Status |
| ------- | --- | ------ |
| Chunker Service | https://chunker-service-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com | Running |
| Vector Gateway | https://vector-gateway-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com | Running (needs Milvus) |
| Retrieval MCP | https://retrieval-mcp-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com/mcp/ | Running (needs Milvus) |
| Ingestion MCP | https://ingestion-mcp-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com/mcp/ | Running (needs Milvus) |
| Docling | https://docling-serve-gng-user50.apps.ocp.tvbt2.sandbox3429.opentlc.com | Running |

## Local Tools

| Tool | Location | Description |
| ---- | -------- | ----------- |
| Griot Agent CLI | `infra/rag/griot-agent/` | LangGraph agent with interactive chat |

## Notes

- All AI models are accessed via MaaS - no local GPU deployment needed
- Code is copied from `advanced-rag/` (not moved) to keep reference intact
- Vector dimension is 768 (Nomic Embed Text v1.5)
- Single "griot" collection to start
