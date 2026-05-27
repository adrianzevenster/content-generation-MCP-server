#!/bin/bash
# Temporary fix for secrets initialization with permission issues

set -e

SECRETS_DIR="./secrets"
API_KEY="79bf0743f4d915eab884dee9e14087b95ddbd4d2b4048738d30f4ad502664596"

echo "==================================="
echo "Fixing Secrets Configuration"
echo "==================================="
echo ""

# Try to create secrets directory (may already exist)
mkdir -p "${SECRETS_DIR}" 2>/dev/null || true

# If we can't write to secrets/, we need sudo or docker
if [ ! -w "${SECRETS_DIR}" ]; then
    echo "⚠ Secrets directory is not writable by current user"
    echo "  The directory is owned by root. Using Docker to create files..."

    # Use Docker to create the files with proper ownership
    docker run --rm -v "$(pwd)/secrets:/secrets" -v "$(pwd)/adk-agent-key.json:/key.json:ro" alpine sh -c "
        cp /key.json /secrets/gcp-sa.json
        echo '$API_KEY' > /secrets/api-key.txt
        chmod 600 /secrets/gcp-sa.json /secrets/api-key.txt
        chown $(id -u):$(id -g) /secrets/gcp-sa.json /secrets/api-key.txt
    "

    if [ $? -eq 0 ]; then
        echo "✓ Secrets created successfully via Docker"
    else
        echo "✗ Failed to create secrets via Docker"
        echo ""
        echo "Manual steps required:"
        echo "  sudo chown -R $(whoami):$(whoami) ${SECRETS_DIR}"
        echo "  bash scripts/init-secrets.sh"
        exit 1
    fi
else
    # Normal path - we have write permissions
    if [ -f "./adk-agent-key.json" ]; then
        cp ./adk-agent-key.json "${SECRETS_DIR}/gcp-sa.json"
        chmod 600 "${SECRETS_DIR}/gcp-sa.json"
        echo "✓ Copied GCP key to ${SECRETS_DIR}/gcp-sa.json"
    else
        echo "✗ ERROR: ./adk-agent-key.json not found"
        exit 1
    fi

    echo "${API_KEY}" > "${SECRETS_DIR}/api-key.txt"
    chmod 600 "${SECRETS_DIR}/api-key.txt"
    echo "✓ Generated API key at ${SECRETS_DIR}/api-key.txt"
fi

echo ""
echo "┌────────────────────────────────────────────────────────────────┐"
echo "│ IMPORTANT: Save this API key for authentication!              │"
echo "│                                                                │"
echo "│ API Key: ${API_KEY} │"
echo "│                                                                │"
echo "│ Use this in API requests via X-API-Key header                 │"
echo "└────────────────────────────────────────────────────────────────┘"
echo ""
echo "Secrets initialization complete!"
echo "You can now run: docker compose up -d"
echo ""
