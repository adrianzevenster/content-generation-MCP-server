#!/bin/bash
# Initialize Docker secrets from local files
# Run this once before docker compose up

set -e

SECRETS_DIR="./secrets"

echo "==================================="
echo "Docker Secrets Initialization"
echo "==================================="
echo ""

# Check if running with Docker Swarm (required for native docker secret)
if docker info 2>/dev/null | grep -q "Swarm: active"; then
    echo "✓ Docker Swarm detected - using native secrets"
    USE_SWARM=true
else
    echo "ℹ Docker Swarm is not active. Using file-based secrets (recommended for docker-compose)."
    echo "  For production with Docker Swarm, run: docker swarm init"
    echo ""
    USE_SWARM=false
fi

# Create secrets directory
mkdir -p "${SECRETS_DIR}"
chmod 700 "${SECRETS_DIR}"

# Initialize GCP service account key
echo "1. Configuring GCP service account key..."
if [ -f "./adk-agent-key.json" ]; then
    if [ "$USE_SWARM" = true ]; then
        # Use Docker native secrets
        if docker secret inspect gcp_sa_key >/dev/null 2>&1; then
            echo "   ⚠ Secret 'gcp_sa_key' already exists (skipping)"
        else
            docker secret create gcp_sa_key ./adk-agent-key.json
            echo "   ✓ Created Docker secret: gcp_sa_key"
        fi
    else
        # Use file-based secrets for docker-compose
        cp ./adk-agent-key.json "${SECRETS_DIR}/gcp-sa.json"
        chmod 600 "${SECRETS_DIR}/gcp-sa.json"
        echo "   ✓ Copied to ${SECRETS_DIR}/gcp-sa.json"
    fi
else
    echo "   ✗ ERROR: ./adk-agent-key.json not found"
    echo "   Please place your GCP service account key JSON file at: ./adk-agent-key.json"
    exit 1
fi

# Initialize API key
echo ""
echo "2. Configuring API key..."
if [ -f "${SECRETS_DIR}/api-key.txt" ]; then
    API_KEY=$(cat "${SECRETS_DIR}/api-key.txt")
    echo "   ℹ API key already exists"

    if [ "$USE_SWARM" = true ] && ! docker secret inspect api_key >/dev/null 2>&1; then
        echo "$API_KEY" | docker secret create api_key -
        echo "   ✓ Created Docker secret: api_key"
    fi
else
    # Generate new API key
    API_KEY=$(openssl rand -hex 32)
    echo "${API_KEY}" > "${SECRETS_DIR}/api-key.txt"
    chmod 600 "${SECRETS_DIR}/api-key.txt"

    if [ "$USE_SWARM" = true ]; then
        echo "$API_KEY" | docker secret create api_key -
        echo "   ✓ Created Docker secret: api_key"
    else
        echo "   ✓ Generated new API key at ${SECRETS_DIR}/api-key.txt"
    fi

    echo ""
    echo "   ┌────────────────────────────────────────────────────────────────┐"
    echo "   │ IMPORTANT: Save this API key for authentication!              │"
    echo "   │                                                                │"
    echo "   │ API Key: ${API_KEY} │"
    echo "   │                                                                │"
    echo "   │ Use this in API requests via X-API-Key header                 │"
    echo "   └────────────────────────────────────────────────────────────────┘"
fi

echo ""
echo "==================================="
echo "Secrets initialization complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "  1. Ensure your .env file is configured (see .env.example)"
echo "  2. Run: docker compose build"
echo "  3. Run: docker compose up -d"
echo "  4. Verify: docker compose ps"
echo ""

if [ "$USE_SWARM" = false ]; then
    echo "Note: Secrets are stored in ${SECRETS_DIR}/"
    echo "      Make sure this directory is in .gitignore"
    echo ""
fi

# Display current API key location
echo "To view your API key later:"
echo "  cat ${SECRETS_DIR}/api-key.txt"
echo ""
