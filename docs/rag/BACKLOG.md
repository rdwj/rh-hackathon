# Ask the Griot - Implementation Backlog

This backlog tracks implementation tasks for the "Ask the Griot" RAG feature ([Issue #14](https://github.com/griot-and-grits/rh-hackathon/issues/14)).

## Status Legend

- [ ] Not started
- [x] Complete
- [~] In progress
- [!] Blocked

## Phase 1: Vector Infrastructure

### Milvus Deployment

- [ ] Copy `advanced-rag/databases/milvus/openshift/` to `infra/rag/milvus/`
- [ ] Request SCC grants from cluster admin (`anyuid` for default and milvus-minio service accounts)
- [ ] Deploy Milvus via Helm chart
- [ ] Verify Milvus health endpoint
- [ ] Test basic collection creation

### Vector Gateway

- [ ] Copy `advanced-rag/services/vector_gateway/` to `infra/rag/vector-gateway/`
- [ ] Update configuration to use Nomic embedding endpoint (MaaS)
- [ ] Build and push container image
- [ ] Deploy to OpenShift
- [ ] Verify `/healthz` endpoint
- [ ] Test `/upsert` with sample document
- [ ] Test `/search` query

## Phase 2: Ingestion Pipeline

### Chunker Service

- [ ] Copy `advanced-rag/services/chunker_service/` to `infra/rag/chunker-service/`
- [ ] Build and push container image
- [ ] Deploy to OpenShift
- [ ] Test chunking with sample text

### Docling

- [ ] Determine deployment approach:
  - [ ] Option A: Use Red Hat hosted Docling service
  - [ ] Option B: Deploy local Docling instance
  - [ ] Option C: Use existing deployment if available
- [ ] Configure ingestion-mcp to use Docling endpoint

### Ingestion MCP Server

- [ ] Copy `advanced-rag/ingestion-mcp/` to `infra/rag/ingestion-mcp/`
- [ ] Update configuration for this project's services
- [ ] Build and push container image
- [ ] Deploy to OpenShift
- [ ] Test `ingest_text` with sample content
- [ ] Test `ingest_document` with sample PDF
- [ ] Verify documents appear in Milvus collection

### MinIO Staging Bucket

- [ ] Create `rag-staging` bucket in existing MinIO
- [ ] Create subdirectories: `pending/`, `processing/`, `completed/`
- [ ] Test file upload to staging area

## Phase 3: Retrieval & Agent

### Retrieval MCP Server

- [ ] Copy `advanced-rag/retrieval-mcp/` to `infra/rag/retrieval-mcp/`
- [ ] Update configuration for this project's services
- [ ] Build and push container image
- [ ] Deploy to OpenShift
- [ ] Test `rag_search` against ingested documents
- [ ] Test `rag_list_collections`
- [ ] Test `rag_list_sources`

### Griot Agent

- [ ] Design agent implementation approach:
  - [ ] Option A: LangChain/LangGraph agent
  - [ ] Option B: Custom agent loop with tool calling
  - [ ] Option C: Use existing agent framework
- [ ] Implement MCP client for retrieval-mcp
- [ ] Implement LLM client for MaaS endpoint
- [ ] Implement agent loop with tool calling
- [ ] Create Griot system prompt
- [ ] Test agent with sample queries

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

## Notes

- All AI models are accessed via MaaS - no local GPU deployment needed
- Code is copied from `advanced-rag/` (not moved) to keep reference intact
- Vector dimension is 768 (Nomic Embed Text v1.5)
- Single "griot" collection to start
