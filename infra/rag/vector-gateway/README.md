# Vector Gateway

FastAPI microservice providing a REST API for vector operations backed by Milvus. Exposes `/search` and `/upsert` endpoints with embedding generation using the Nomic embed-text-v1.5 model (768-dimensional vectors).

Part of the **Griot & Grits** hackathon project.

## Key Features

- **Nomic Embeddings**: Uses Nomic embed-text-v1.5 model via OpenAI-compatible MaaS endpoint
- **768-Dimensional Vectors**: Optimized for Nomic's embedding dimensions
- **Hybrid Search**: Dense vector + BM25 keyword search with RRF fusion
- **Default Collection**: "griot" - pre-configured for the project

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check - returns `{status, backend, count}` |
| `/upsert` | POST | Insert/update documents with embeddings |
| `/search` | POST | Semantic + keyword hybrid search |
| `/collections` | GET | List all Milvus collections |
| `/collections/{name}/stats` | GET | Get collection statistics |

### Upsert Request

```json
{
  "documents": [
    {"doc_id": "id1", "text": "hello world", "metadata": {"source": "test"}}
  ],
  "collection": "griot"
}
```

### Search Request

```json
{
  "query": "hello",
  "top_k": 5,
  "collection": "griot",
  "context_window": 2,
  "filters": {
    "file_pattern": "interview-*.txt"
  }
}
```

## Local Development

```bash
cd infra/rag/vector-gateway
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# Set required environment variables
export NOMIC_API_KEY="your-api-key"
export NOMIC_API_URL="https://nomic-embed-text-v1-5-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1"
export NOMIC_MODEL="/mnt/models"

# For Milvus backend (default)
export MILVUS_HOST="localhost"
export MILVUS_PORT="19530"
export MILVUS_COLLECTION="griot"
export MILVUS_DIM="768"

# Or use memory backend for testing
export GATEWAY_BACKEND="memory"

uvicorn src.app:app --host 0.0.0.0 --port 8005 --reload
```

## Container Build

```bash
cd infra/rag/vector-gateway

# Local build (for testing)
podman build -t vector-gateway:local -f Containerfile .

# Build for OpenShift (x86_64) - from Mac, use remote build
podman build --platform linux/amd64 -t vector-gateway:latest -f Containerfile .
```

## OpenShift Deployment

### Prerequisites

- Milvus deployed in the namespace
- Nomic API key for MaaS endpoint
- Container image pushed to accessible registry

### Deploy

```bash
NAMESPACE="gng-<username>"  # Your namespace

# Set your Nomic API key in the secret
oc create secret generic vector-gateway-secrets \
  -n $NAMESPACE \
  --from-literal=NOMIC_API_KEY="your-actual-api-key" \
  --dry-run=client -o yaml | oc apply -f -

# Update ConfigMap for your namespace (update MILVUS_HOST)
# Edit openshift/deployment.yaml if needed

# Apply deployment manifests
oc apply -f openshift/deployment.yaml -n $NAMESPACE

# Wait for deployment
oc wait --for=condition=Available deployment/vector-gateway -n $NAMESPACE --timeout=120s

# Get route URL
oc get route vector-gateway -n $NAMESPACE -o jsonpath='{.spec.host}'
```

### Verify

```bash
GATEWAY_URL=$(oc get route vector-gateway -n $NAMESPACE -o jsonpath='{.spec.host}')

# Health check
curl -s "https://${GATEWAY_URL}/healthz" | jq .

# Upsert a test document
curl -X POST "https://${GATEWAY_URL}/upsert" \
  -H "Content-Type: application/json" \
  -d '{
    "documents": [
      {"doc_id": "test-1", "text": "This is a test document about minority history preservation.", "metadata": {"source": "test"}}
    ],
    "collection": "griot"
  }'

# Search
curl -X POST "https://${GATEWAY_URL}/search" \
  -H "Content-Type: application/json" \
  -d '{"query": "history preservation", "top_k": 3, "collection": "griot"}'
```

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `GATEWAY_BACKEND` | `milvus` | Backend type: `milvus` or `memory` |
| `GATEWAY_REQUIRE_BACKEND` | `0` | Fail if backend unavailable (`1` = yes) |
| `GATEWAY_MAX_DOCS` | `10000` | Max documents for memory backend |
| `MILVUS_HOST` | - | Milvus host address |
| `MILVUS_PORT` | `19530` | Milvus gRPC port |
| `MILVUS_COLLECTION` | `griot` | Default collection name |
| `MILVUS_DIM` | `768` | Vector dimension (Nomic = 768) |
| `NOMIC_API_KEY` | - | API key for Nomic MaaS endpoint |
| `NOMIC_API_URL` | - | Nomic embedding API URL |
| `NOMIC_MODEL` | `/mnt/models` | Model path on MaaS |
| `RERANK_SERVICE_URL` | - | Optional: rerank service URL |
| `AUTH_TOKEN` | - | Optional: require auth token |

### Authentication

If `AUTH_TOKEN` is set, requests must include:
- `Authorization: Bearer <token>` header, or
- `X-API-Key: <token>` header

## Embedding Configuration

This service uses the **Nomic embed-text-v1.5** model served via Red Hat's Model as a Service (MaaS) platform. The API is OpenAI-compatible.

**Endpoint Details:**
- URL: `https://nomic-embed-text-v1-5-maas-apicast-production.apps.prod.rhoai.rh-aiservices-bu.com:443/v1`
- Model: `/mnt/models`
- Dimensions: 768

**Key Differences from OpenAI:**
- 768-dimensional vectors (vs 1536 for text-embedding-3-small)
- Model path is `/mnt/models` (not a model name like `text-embedding-3-small`)
- API key is for the MaaS platform, not OpenAI

## Architecture Notes

This service is adapted from the advanced-rag vector_gateway but simplified to be self-contained without depending on the external `rag_core` library. The embedding logic is built directly into the service using the OpenAI Python client with the Nomic MaaS endpoint.
