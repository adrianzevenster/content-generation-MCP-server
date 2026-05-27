# Production Deployment Guide

This guide covers deploying the production-hardened agent-content-creation application using Docker Compose.

## Table of Contents
- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Deployment](#deployment)
- [Authentication](#authentication)
- [Monitoring](#monitoring)
- [Maintenance](#maintenance)
- [Troubleshooting](#troubleshooting)
- [Security Checklist](#security-checklist)

---

## Prerequisites

### Required Software
- **Docker**: Version 20.10 or higher
- **Docker Compose**: Version 2.0 or higher
- **Git**: For cloning the repository

### Required Access
- **GCP Project**: With Vertex AI and BigQuery enabled
- **GCP Service Account**: JSON key file with appropriate permissions
  - Vertex AI User
  - BigQuery Data Editor
  - Cloud Storage Object Viewer

### Verify Installation
```bash
docker --version
docker compose version
```

---

## Initial Setup

### 1. Clone Repository
```bash
git clone <repository-url>
cd agent-content-creation
```

### 2. Configure Environment

Copy the example environment file and configure it:
```bash
cp .env.example .env
```

Edit `.env` with your actual values:
```bash
nano .env
```

**Key Configuration Variables:**
```bash
# Google Cloud Project
GOOGLE_CLOUD_PROJECT=your-project-id
GOOGLE_CLOUD_LOCATION=europe-west1

# BigQuery
MONC_BQ_PROJECT_ID=your-project-id
MONC_BQ_DATASET_ID=monc_content
MONC_BQ_TABLE_ID=generated_ads

# RAG Configuration (if using RAG)
RAG_GCS_BUCKET=gs://your-bucket-name
RAG_INDEX_RESOURCE_NAME=projects/PROJECT_NUMBER/locations/LOCATION/indexes/INDEX_ID
RAG_INDEX_ENDPOINT_RESOURCE_NAME=projects/PROJECT_NUMBER/locations/LOCATION/indexEndpoints/ENDPOINT_ID

# Logging
LOG_LEVEL=INFO  # Options: DEBUG, INFO, WARNING, ERROR
```

### 3. Place GCP Service Account Key

Place your GCP service account JSON key file in the project root:
```bash
# File should be named: adk-agent-key.json
cp /path/to/your-service-account-key.json ./adk-agent-key.json
chmod 600 ./adk-agent-key.json
```

### 4. Initialize Secrets

Run the secrets initialization script:
```bash
bash scripts/init-secrets.sh
```

**This script will:**
- Copy GCP credentials to `secrets/gcp-sa.json`
- Generate a secure API key at `secrets/api-key.txt`
- Display your API key (save it securely!)

**IMPORTANT: Save the API key displayed by the script.** You'll need it for all API requests.

---

## Deployment

### Build and Start Services

```bash
# Build Docker images
docker compose build

# Start all services in detached mode
docker compose up -d

# View logs
docker compose logs -f
```

### Verify Deployment

```bash
# Check service status (all should show "healthy")
docker compose ps

# Expected output:
# NAME                STATUS              PORTS
# compliance          Up (healthy)
# api                 Up (healthy)
# ui                  Up (healthy)        0.0.0.0:8501->8501/tcp
```

### Access the Application

- **Web UI**: http://localhost:8501
- **API Documentation**: Not exposed (internal only)
- **Metrics**: Internal only (see Monitoring section)

---

## Authentication

All API endpoints (except `/health`) require authentication using an API key.

### API Key Usage

Include the API key in the `X-API-Key` header:

```bash
# Example: Generate an ad
curl -X POST http://localhost:8501 \
  -H "X-API-Key: YOUR_API_KEY_HERE" \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a business account ad for Nigerian SMEs",
    "channel": "META",
    "brand": "Moniepoint",
    "country": "NG"
  }'
```

### Retrieve Your API Key

```bash
cat secrets/api-key.txt
```

### Rotate API Key

To generate a new API key:

```bash
# Generate new key
openssl rand -hex 32 > secrets/api-key.txt

# Restart services to load new key
docker compose restart
```

---

## Monitoring

### Service Logs

**View all logs:**
```bash
docker compose logs -f
```

**View specific service:**
```bash
docker compose logs -f api
docker compose logs -f compliance
docker compose logs -f ui
```

**Structured JSON Logs:**
All services output JSON-formatted logs for easy parsing:
```bash
docker compose logs api | jq .
```

### Health Checks

**Check health status:**
```bash
# From inside Docker network
docker compose exec api curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "rag_enabled": true,
  "dependencies": {
    "gcp": {"status": "healthy"},
    "compliance": {"status": "healthy"}
  }
}
```

### Resource Usage

**Monitor resource consumption:**
```bash
docker stats
```

### Metrics (Future)

Prometheus metrics endpoints are available internally:
- API service: `http://api:8000/metrics`
- Compliance service: `http://compliance:8001/metrics`

To expose metrics for external monitoring, add port mappings in `docker-compose.yml`.

---

## Maintenance

### Update Application

```bash
# Pull latest changes
git pull

# Rebuild and restart
docker compose build
docker compose up -d

# Verify deployment
docker compose ps
```

### Backup Secrets

```bash
# Create encrypted backup of secrets
tar -czf secrets-backup-$(date +%Y%m%d).tar.gz secrets/
gpg -c secrets-backup-$(date +%Y%m%d).tar.gz
rm secrets-backup-$(date +%Y%m%d).tar.gz
```

### Scaling Services

To run multiple instances of a service:

```bash
# Scale API service to 3 replicas
docker compose up -d --scale api=3
```

### Stop Services

```bash
# Stop all services
docker compose stop

# Stop and remove containers
docker compose down

# Stop and remove containers + volumes
docker compose down -v
```

---

## Troubleshooting

### Services Not Starting

**Check logs:**
```bash
docker compose logs <service-name>
```

**Common issues:**

1. **Missing secrets:**
   ```bash
   # Verify secrets exist
   ls -la secrets/

   # Re-run initialization
   bash scripts/init-secrets.sh
   ```

2. **Port conflicts:**
   ```bash
   # Check if port 8501 is in use
   lsof -i :8501

   # Kill conflicting process or change port in docker-compose.yml
   ```

3. **GCP authentication failure:**
   ```bash
   # Verify service account key
   docker compose exec api cat /run/secrets/gcp_sa_key | jq .

   # Check permissions
   ls -l adk-agent-key.json
   ```

### Authentication Errors

**401 Unauthorized:**
- Verify API key is correct: `cat secrets/api-key.txt`
- Ensure `X-API-Key` header is included in request
- Check UI has access to secret: `docker compose exec ui cat /run/secrets/api_key`

### Health Check Failures

**Services show unhealthy:**
```bash
# Check health check output
docker compose exec api python3 -c "import requests; print(requests.get('http://localhost:8000/health').text)"

# Increase start_period in docker-compose.yml if services need more time
```

### Network Connectivity Issues

**UI cannot reach API:**
```bash
# Test internal DNS
docker compose exec ui nslookup api

# Test connectivity
docker compose exec ui curl http://api:8000/health
```

**API cannot reach Compliance:**
```bash
docker compose exec api curl http://compliance:8001/health
```

### Performance Issues

**High memory usage:**
```bash
# Check current limits
docker compose config | grep -A 5 "resources"

# Adjust limits in docker-compose.yml under deploy.resources
```

**Slow responses:**
- Check GCP quota limits
- Review structured logs for slow operations
- Monitor BigQuery write performance

---

## Security Checklist

Before deploying to production, verify:

- [ ] `.env` file removed from git history
- [ ] `secrets/` directory in `.gitignore`
- [ ] GCP service account has minimal required permissions
- [ ] API key stored securely in `secrets/api-key.txt`
- [ ] Only UI port (8501) exposed externally
- [ ] All containers running as non-root user
- [ ] Resource limits configured for all services
- [ ] Health checks enabled for all services
- [ ] Structured logging configured (JSON format)
- [ ] Backup of secrets created and encrypted
- [ ] Monitoring alerts configured (future)
- [ ] Regular dependency updates scheduled

---

## Architecture Overview

### Network Topology

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ :8501
┌──────▼──────────────────────────┐
│  External Network (bridge)      │
└──────┬──────────────────────────┘
       │
┌──────▼──────┐
│  UI Service │
└──────┬──────┘
       │
┌──────▼──────────────────────────┐
│  Internal Network (isolated)    │
│                                  │
│  ┌──────────┐   ┌────────────┐  │
│  │ API      │───│ Compliance │  │
│  └──────────┘   └────────────┘  │
│                                  │
│  (No external access)            │
└──────────────────────────────────┘
       │
       ▼
┌──────────────┐
│ GCP Services │
│ - Vertex AI  │
│ - BigQuery   │
│ - GCS        │
└──────────────┘
```

### Service Communication

- **Browser → UI**: External HTTP on port 8501
- **UI → API**: Internal HTTP via Docker network
- **API → Compliance**: Internal HTTP via Docker network
- **API → GCP**: External HTTPS (Vertex AI, BigQuery, GCS)
- **All services**: Authenticated with API key via `X-API-Key` header

### Data Flow

1. User submits prompt via UI
2. UI sends authenticated request to API
3. API retrieves context from RAG (optional)
4. API calls LLM via Vertex AI
5. API sends generated ad to Compliance service
6. Compliance service validates and suggests rewrites
7. API writes result to BigQuery
8. API returns final ad copy to UI
9. UI displays result to user

---

## Support

For issues or questions:
1. Check this deployment guide
2. Review structured logs: `docker compose logs -f`
3. Check health endpoints
4. Verify configuration in `.env`
5. Open an issue in the project repository

---

## Additional Resources

- **Docker Compose Documentation**: https://docs.docker.com/compose/
- **GCP Vertex AI**: https://cloud.google.com/vertex-ai/docs
- **BigQuery**: https://cloud.google.com/bigquery/docs
- **Structured Logging**: https://www.structlog.org/
