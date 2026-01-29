#!/bin/bash
# Deployment script for retrieval-mcp
#
# This script builds and deploys the retrieval-mcp service to OpenShift.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
NAMESPACE=${1:-$(oc project -q 2>/dev/null || echo "griot")}

echo "========================================="
echo "Retrieval MCP Deployment"
echo "========================================="
echo "Namespace: $NAMESPACE"
echo ""

# Check if logged in to OpenShift
if ! oc whoami &>/dev/null; then
    echo "Error: Not logged in to OpenShift. Please run 'oc login' first."
    exit 1
fi

# Check namespace exists
if ! oc get namespace "$NAMESPACE" &>/dev/null; then
    echo "Creating namespace: $NAMESPACE"
    oc new-project "$NAMESPACE"
fi

# Apply BuildConfig and ImageStream
echo "Creating build resources..."
oc apply -f "$SCRIPT_DIR/openshift/buildconfig.yaml" -n "$NAMESPACE"

# Start the build
echo "Starting build..."
oc start-build retrieval-mcp --from-dir="$SCRIPT_DIR" --follow -n "$NAMESPACE"

# Apply deployment manifests (substituting namespace)
echo "Deploying application..."
sed "s/\${NAMESPACE}/$NAMESPACE/g" "$SCRIPT_DIR/openshift/deployment.yaml" | oc apply -f - -n "$NAMESPACE"
oc apply -f "$SCRIPT_DIR/openshift/service.yaml" -n "$NAMESPACE"
oc apply -f "$SCRIPT_DIR/openshift/route.yaml" -n "$NAMESPACE"

# Wait for rollout
echo "Waiting for deployment..."
oc rollout status deployment/retrieval-mcp -n "$NAMESPACE" --timeout=120s

# Get route
ROUTE=$(oc get route retrieval-mcp -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "")

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
if [ -n "$ROUTE" ]; then
    echo "MCP Server URL: https://$ROUTE/mcp/"
    echo ""
    echo "Test with MCP Inspector:"
    echo "  npx @modelcontextprotocol/inspector https://$ROUTE/mcp/"
else
    echo "Warning: Could not retrieve route URL"
fi
echo ""
echo "Environment Variables:"
echo "  DEFAULT_COLLECTION: griot"
echo "  VECTOR_GATEWAY_URL: http://vector-gateway:8000"
echo "========================================="
