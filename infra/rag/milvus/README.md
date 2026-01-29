# Milvus Vector Database for Griot & Grits

Milvus is an open-source vector database optimized for similarity search and AI applications. This deployment provides vector storage for RAG (Retrieval-Augmented Generation) capabilities in the Griot & Grits platform.

## Features

- Native hybrid search (dense vectors + BM25 sparse)
- High-performance similarity search with HNSW and IVF indexes
- Scalable architecture with standalone and distributed deployment options
- Built-in MinIO integration for object storage

## Use Case in Griot & Grits

Milvus stores vector embeddings for:
- Oral history transcriptions and narratives
- Historical document chunks processed by Docling
- Semantic search across the historical archive

## Directory Structure

```
milvus/
├── README.md                          # This file
├── openshift/
│   ├── values-openshift.yaml          # Helm values for OpenShift deployment
│   └── OPENSHIFT_DEPLOYMENT.md        # Detailed OpenShift deployment guide
└── local/
    ├── podman_milvus.sh               # Podman-based local development (recommended)
    ├── standalone_embed.sh            # Docker-based standalone (alternative)
    ├── embedEtcd.yaml                 # Embedded etcd configuration
    └── user.yaml                      # Milvus configuration overrides
```

## Local Development

### Quick Start with Podman (Recommended)

```bash
cd local
./podman_milvus.sh start
curl -s http://localhost:9091/healthz   # expect OK
```

### Exposed Ports

| Service | Port | Description |
|---------|------|-------------|
| Milvus gRPC | 19530 | Primary API endpoint |
| Milvus Metrics | 9091 | Health checks and metrics |
| MinIO API | 9000 | Object storage API |
| MinIO Console | 9090 | Web UI (admin/minioadmin) |

### Common Commands

```bash
./podman_milvus.sh start    # Start or ensure pod is running
./podman_milvus.sh stop     # Stop all containers
./podman_milvus.sh status   # Show status summary
./podman_milvus.sh logs     # View Milvus logs
./podman_milvus.sh health   # Health check only
./podman_milvus.sh destroy  # Tear down (data preserved in ./data)
```

## OpenShift Deployment

See [openshift/OPENSHIFT_DEPLOYMENT.md](openshift/OPENSHIFT_DEPLOYMENT.md) for detailed instructions.

### Quick Deploy

```bash
# Set your namespace (typically gng-<username> for hackathon)
NAMESPACE=gng-myuser

# Grant SCCs before deploying (requires cluster-admin)
oc adm policy add-scc-to-user anyuid -z default -n $NAMESPACE
oc adm policy add-scc-to-user anyuid -z milvus-minio -n $NAMESPACE

# Add Helm repo and install
helm repo add milvus https://zilliztech.github.io/milvus-helm/
helm repo update milvus

helm install milvus milvus/milvus \
  -f openshift/values-openshift.yaml \
  -n $NAMESPACE

# Wait for pods
oc wait --for=condition=Ready pods -l app.kubernetes.io/instance=milvus -n $NAMESPACE --timeout=600s
```

### Service Endpoints (OpenShift)

| Service | Internal URL | Port |
|---------|-------------|------|
| Milvus gRPC | `milvus.<namespace>.svc.cluster.local` | 19530 |
| Milvus Metrics | `milvus.<namespace>.svc.cluster.local` | 9091 |

## Connecting from Backend

### Environment Variables

For OpenShift deployment, add these to the backend configuration:

```bash
# Same-namespace access
MILVUS_HOST=milvus
MILVUS_PORT=19530
MILVUS_URI=http://milvus:19530

# Cross-namespace access (replace <namespace>)
MILVUS_HOST=milvus.<namespace>.svc.cluster.local
MILVUS_URI=http://milvus.<namespace>.svc.cluster.local:19530
```

### Python Usage (pymilvus)

```python
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType

# Connect to Milvus
connections.connect(
    host=os.getenv("MILVUS_HOST", "localhost"),
    port=os.getenv("MILVUS_PORT", "19530")
)

# Define schema for historical document chunks
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="chunk_id", dtype=DataType.VARCHAR, max_length=255),
    FieldSchema(name="document_id", dtype=DataType.VARCHAR, max_length=255),
    FieldSchema(name="text", dtype=DataType.VARCHAR, max_length=65535),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=1536),  # OpenAI ada-002 dimension
]
schema = CollectionSchema(fields, description="Griot historical document chunks")

# Create collection
collection = Collection("griot_documents", schema)

# Create HNSW index for fast similarity search
collection.create_index(
    field_name="embedding",
    index_params={
        "index_type": "HNSW",
        "metric_type": "COSINE",
        "params": {"M": 16, "efConstruction": 256}
    }
)

# Search example
results = collection.search(
    data=[query_embedding],
    anns_field="embedding",
    param={"metric_type": "COSINE", "params": {"ef": 64}},
    limit=10,
    output_fields=["chunk_id", "document_id", "text"]
)
```

## Resource Requirements

The default OpenShift values configure:
- **Milvus standalone**: 1 CPU request, 4Gi memory request (limits: 4 CPU, 8Gi)
- **etcd**: 1 replica with 10Gi persistent storage
- **MinIO**: Standalone mode with 20Gi persistent storage

For hackathon use, these defaults should be sufficient. For production workloads, adjust `openshift/values-openshift.yaml` accordingly.

## Cleanup

```bash
# Uninstall Milvus (keeps PVCs by default)
helm uninstall milvus -n $NAMESPACE

# Delete PVCs if you want to remove all data
oc delete pvc -l app.kubernetes.io/instance=milvus -n $NAMESPACE
```

## Version Information

Tested with:
- Milvus 2.6.6
- Milvus Helm Chart 5.0.8
- OpenShift 4.14+

## Notes

- Data persists in PVCs on OpenShift, in `./data/` directories locally
- For production, configure authentication in `openshift/values-openshift.yaml`
- Milvus v2.4+ required for hybrid search with BM25 sparse vectors
