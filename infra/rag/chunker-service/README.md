# Chunker Service

Go-based sliding window text chunker exposed as an HTTP service. Provides fast, configurable text chunking for RAG pipelines.

Part of the Griot & Grits RAG infrastructure.

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/healthz` | GET | Health check - returns `{"status": "ok"}` |
| `/chunk` | POST | Chunk text using sliding window algorithm |

### Chunk Request

```json
{
  "text": "Your text to chunk...",
  "plan": {
    "window_size": 200,
    "overlap": 40,
    "mode": "tokens",
    "break_on_headings": false,
    "max_chunks": 0
  },
  "meta": {
    "file_name": "doc.txt",
    "file_path": "/path/doc.txt",
    "mime_type": "text/plain"
  }
}
```

### Chunk Response

Returns JSON array of chunks with metadata.

## Local Development

```bash
cd infra/rag/chunker-service

# Run server directly
go run ./cmd/chunker-server

# Or build and run
go build -o chunker-server ./cmd/chunker-server
./chunker-server
```

Server listens on port 8080 by default.

### Running Tests

```bash
cd infra/rag/chunker-service
go test ./...
```

## Container Build

Build from within the `chunker-service` directory:

```bash
cd infra/rag/chunker-service

# Local build (for testing)
podman build -t chunker-service:local -f Containerfile .

# Build for OpenShift (x86_64) - from Mac, use remote build:
rsync -avz --exclude='.git' . ec2-dev:~/builds/chunker-service/
ssh ec2-dev 'cd ~/builds/chunker-service && podman build -t chunker-service:latest -f Containerfile .'
```

## OpenShift Deployment

### Prerequisites

- OpenShift cluster access
- Container image pushed to accessible registry

### Push to OpenShift Registry

```bash
# Get registry route and token
REGISTRY=$(oc get route default-route -n openshift-image-registry -o jsonpath='{.spec.host}')
OC_TOKEN=$(oc whoami -t)
NAMESPACE=$(cat .openshift-config | grep NAMESPACE | cut -d= -f2)

# Login from build machine
podman login -u unused -p ${OC_TOKEN} ${REGISTRY} --tls-verify=false

# Tag and push
podman tag chunker-service:latest ${REGISTRY}/${NAMESPACE}/chunker-service:latest
podman push --tls-verify=false ${REGISTRY}/${NAMESPACE}/chunker-service:latest
```

### Deploy

```bash
NAMESPACE=$(cat .openshift-config | grep NAMESPACE | cut -d= -f2)

# Create ImageStream (first time only)
oc create imagestream chunker-service -n ${NAMESPACE} 2>/dev/null || true

# Apply deployment manifests (replace ${NAMESPACE} placeholder)
sed "s/\${NAMESPACE}/${NAMESPACE}/g" infra/rag/chunker-service/openshift/deployment.yaml | oc apply -f - -n ${NAMESPACE}

# Wait for deployment
oc wait --for=condition=Available deployment/chunker-service -n ${NAMESPACE} --timeout=120s

# Get route URL
oc get route chunker-service -n ${NAMESPACE} -o jsonpath='{.spec.host}'
```

### Verify

```bash
NAMESPACE=$(cat .openshift-config | grep NAMESPACE | cut -d= -f2)
CHUNKER_URL=$(oc get route chunker-service -n ${NAMESPACE} -o jsonpath='{.spec.host}')

# Health check
curl -s "https://${CHUNKER_URL}/healthz" | jq .

# Test chunking
curl -X POST "https://${CHUNKER_URL}/chunk" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "This is a test document. It contains multiple sentences. Each sentence should be chunked appropriately based on the plan settings.",
    "plan": {"window_size": 50, "overlap": 10, "mode": "tokens"},
    "meta": {"file_name": "test.txt"}
  }'
```

## Configuration

The chunker service is stateless and requires no environment variables. All chunking behavior is controlled through the request payload.

### Chunking Plan Options

| Field | Type | Description |
|-------|------|-------------|
| `window_size` | int | Chunk size (required, > 0) |
| `overlap` | int | Overlap between chunks |
| `mode` | string | "tokens", "chars", or "lines" |
| `break_on_headings` | bool | Split on markdown headings (lines mode only) |
| `include_headings` | bool | Prepend heading text to each chunk |
| `max_chunks` | int | Limit chunks (0 = unlimited) |

## Wiring into Backend

Set environment variable to use the service:

```bash
export CHUNKER_SERVICE_URL=http://chunker-service.${NAMESPACE}.svc.cluster.local:8080
```

## Internal Service URL

```
http://chunker-service.<namespace>.svc.cluster.local:8080
```
