#!/bin/bash
# Deployment script for Ingestion MCP server to OpenShift
# Usage: ./deploy.sh [namespace]

set -e

NAMESPACE=${1:-$(oc project -q 2>/dev/null || echo "gng-demo")}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "========================================="
echo "Ingestion MCP Server Deployment"
echo "========================================="
echo "Namespace: $NAMESPACE"
echo ""

# Check if logged in to OpenShift
if ! oc whoami &>/dev/null; then
    echo "Error: Not logged in to OpenShift. Please run 'oc login' first."
    exit 1
fi

# Apply OpenShift resources
echo "-> Applying OpenShift resources..."
sed "s|image: ingestion-mcp:latest|image: image-registry.openshift-image-registry.svc:5000/$NAMESPACE/ingestion-mcp:latest|g" \
    "$SCRIPT_DIR/openshift/deployment.yaml" | oc apply -f - -n "$NAMESPACE"

# Start build
echo "-> Building container image..."
echo "  Creating filtered build context..."

# Create a temporary directory for the build context
BUILD_DIR=$(mktemp -d)
trap "rm -rf $BUILD_DIR" EXIT

# Copy only necessary files (exclude __pycache__ and .pyc files)
cp "$SCRIPT_DIR/Containerfile" "$SCRIPT_DIR/requirements.txt" "$SCRIPT_DIR/pyproject.toml" "$BUILD_DIR/"

# Use rsync to copy src/ while excluding cache files
rsync -a --exclude='__pycache__' --exclude='*.pyc' --exclude='*.pyo' --exclude='.mypy_cache' \
    "$SCRIPT_DIR/src/" "$BUILD_DIR/src/"

echo "  Starting binary build with filtered context..."
oc start-build ingestion-mcp --from-dir="$BUILD_DIR" --follow -n "$NAMESPACE"

# Wait for rollout
echo "-> Deploying application..."
oc rollout restart deployment/ingestion-mcp -n "$NAMESPACE" 2>/dev/null || true
oc rollout status deployment/ingestion-mcp -n "$NAMESPACE" --timeout=300s

# Get route (host and path)
ROUTE_HOST=$(oc get route ingestion-mcp -n "$NAMESPACE" -o jsonpath='{.spec.host}' 2>/dev/null || echo "")
ROUTE_PATH=$(oc get route ingestion-mcp -n "$NAMESPACE" -o jsonpath='{.spec.path}' 2>/dev/null || echo "/mcp/")

echo ""
echo "========================================="
echo "Deployment Complete!"
echo "========================================="
if [ -n "$ROUTE_HOST" ]; then
    echo "MCP Server URL: https://${ROUTE_HOST}${ROUTE_PATH}"
    echo ""
    echo "Test with MCP Inspector:"
    echo "  npx @modelcontextprotocol/inspector https://${ROUTE_HOST}${ROUTE_PATH}"
    echo ""
    echo "Add to LibreChat agent config:"
    echo '  {"mcpServers": {"ingestion": {"url": "https://'"${ROUTE_HOST}${ROUTE_PATH}"'"}}}'
else
    echo "Warning: Could not retrieve route URL"
fi
echo "========================================="
