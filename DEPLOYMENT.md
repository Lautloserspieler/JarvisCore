# 🚀 JarvisCore v1.1.0 - Deployment Guide

## 📋 Overview

JarvisCore v1.1.0 features a microservices architecture with:
- **Frontend**: Vue.js + TypeScript + Shadcn/UI
- **Backend**: Python (FastAPI) + llama.cpp
- **Go Services**: Auth, Security, Memory, Database
- **Database**: PostgreSQL 16

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend (Vue.js)                    │
│                    Port: 5173                           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Backend (Python + llama.cpp)               │
│                    Port: 5050                           │
└──┬────────┬────────┬────────┬────────┬──────────────────┘
   │        │        │        │        │
   ▼        ▼        ▼        ▼        ▼
┌─────┐ ┌──────┐ ┌──────┐ ┌──────┐ ┌──────────┐
│Auth │ │Security│Memory│ │Database│PostgreSQL│
│8080 │ │  8081  │ 8082 │ │  8083  │   5432   │
└─────┘ └──────┘ └──────┘ └──────┘ └──────────┘
```

---

## ⚙️ Prerequisites

### Required
- **Docker** 24.0+ & **Docker Compose** 2.20+
- **NVIDIA GPU** with CUDA 12.0+ (for llama.cpp)
- **16GB+ RAM** (8GB minimum)
- **20GB+ Disk Space** (for models)

### Optional
- **Go 1.21+** (for local Go service development)
- **Node.js 18+** (for local frontend development)
- **Python 3.11+** (for local backend development)

---

## 🐳 Docker Deployment (Recommended)

### 1. Clone Repository

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore
```

### 2. Create Environment Variables

Create `.env` file:

```bash
cat > .env << EOF
# Database
DATABASE_URL=postgres://jarvis:jarvis@postgres:5432/jarviscore?sslmode=disable
POSTGRES_USER=jarvis
POSTGRES_PASSWORD=jarvis
POSTGRES_DB=jarviscore

# Auth
SECRET_KEY=your-secret-key-change-in-production

# Frontend
VITE_BACKEND_URL=http://localhost:5050
VITE_WS_URL=ws://localhost:5050

# Services
AUTH_SERVICE_URL=http://auth-service:8080
SECURITY_SERVICE_URL=http://security-service:8081
MEMORY_SERVICE_URL=http://memory-service:8082
DATABASE_SERVICE_URL=http://database-service:8083
EOF
```

### 3. Build All Services

```bash
docker-compose build
```

### 4. Start All Services

```bash
docker-compose up -d
```

### 5. Check Service Health

```bash
# Check all services
docker-compose ps

# Check logs
docker-compose logs -f

# Health endpoints
curl http://localhost:8080/health  # Auth
curl http://localhost:8081/health  # Security
curl http://localhost:8082/health  # Memory
curl http://localhost:8083/health  # Database
curl http://localhost:5050/health  # Backend
```

### 6. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5050
- **API Docs**: http://localhost:5050/docs

---

## 🔧 Local Development Setup

### Backend (Python)

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run server
uvicorn main:app --reload --host 0.0.0.0 --port 5050
```

### Frontend (Vue.js)

```bash
cd frontend

# Install dependencies
npm install

# Run dev server
npm run dev
```

### Go Services

#### Auth Service
```bash
cd go-services/auth
go mod download
go run main.go
# Listens on :8080
```

#### Security Service
```bash
cd go-services/security
go mod download
go run main.go
# Listens on :8081
```

#### Memory Service
```bash
cd go-services/memory
go mod download
go run main.go
# Listens on :8082
```

#### Database Service
```bash
cd go-services/database

# Start PostgreSQL first
docker run -d \
  --name postgres \
  -e POSTGRES_USER=jarvis \
  -e POSTGRES_PASSWORD=jarvis \
  -e POSTGRES_DB=jarviscore \
  -p 5432:5432 \
  postgres:16-alpine

# Run service
go mod download
go run main.go
# Listens on :8083
```

---

## 🔑 API Key Management

### Create API Key

```bash
curl -X POST http://localhost:8080/api/auth/keys/create \
  -H "Content-Type: application/json" \
  -d '{
    "key": "your-api-key-123",
    "rate_limit": 100,
    "burst": 20
  }'
```

### Generate JWT Token

```bash
curl -X POST http://localhost:8080/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-api-key-123"}'
```

### Use API Key

```bash
curl http://localhost:5050/api/models \
  -H "X-API-Key: your-api-key-123"
```

---

## 📦 Model Management

### Download Models

Models are managed through the Frontend UI:
1. Navigate to **Models** tab
2. Click **Download** on desired model
3. Select quantization (Q4_K_M, Q5_K_M, Q6_K, Q8_0)
4. Wait for download to complete

### Manual Model Installation

```bash
# Create models directory
mkdir -p models/llm

# Download model (example)
wget https://huggingface.co/TheBloke/Llama-2-7B-GGUF/resolve/main/llama-2-7b.Q4_K_M.gguf \
  -O models/llm/llama-2-7b-q4.gguf

# Verify
ls -lh models/llm/
```

---

## 🔒 Security Configuration

### Prompt Injection Protection

The security service automatically validates all prompts:

```python
# Test validation
import requests

response = requests.post('http://localhost:8081/api/security/validate', json={
    'input': 'Your prompt here',
    'strict': False  # Set to True for stricter validation
})

print(response.json())
# {
#   "is_safe": true,
#   "cleaned_input": "...",
#   "warnings": [],
#   "severity": "low",
#   "rejected": false
# }
```

### Rate Limiting

Default rate limits:
- **Demo Key**: 60 requests/minute, burst 10
- **Admin Key**: 300 requests/minute, burst 50

Customize in `go-services/auth/main.go`.

---

## 🗄️ Database Management

### Backup Database

```bash
docker exec jarvis-postgres pg_dump -U jarvis jarviscore > backup.sql
```

### Restore Database

```bash
docker exec -i jarvis-postgres psql -U jarvis jarviscore < backup.sql
```

### Connect to Database

```bash
docker exec -it jarvis-postgres psql -U jarvis -d jarviscore
```

---

## 🧪 Testing

### Run All Tests

```bash
# Backend tests
cd backend
pytest tests/ -v

# Frontend tests
cd frontend
npm run test

# Go service tests
cd go-services/auth
go test -v ./...
```

### Test Endpoints

```bash
# Health checks
for port in 8080 8081 8082 8083 5050; do
  echo "Testing port $port:"
  curl -s http://localhost:$port/health | jq
done

# Load model
curl -X POST http://localhost:5050/api/models/llama-2-7b-q4/load

# Generate text
curl -X POST http://localhost:5050/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hallo JARVIS!"}'
```

---

## 📊 Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend

# Last 100 lines
docker-compose logs --tail=100 backend
```

### Service Metrics

```bash
# Memory service stats
curl http://localhost:8082/api/memory/stats

# Database stats
curl http://localhost:8083/api/stats

# Multi-model stats
curl http://localhost:5050/api/models/stats
```

---

## 🔄 Updates

### Pull Latest Changes

```bash
git pull origin main

# Rebuild services
docker-compose build

# Restart
docker-compose down
docker-compose up -d
```

### Database Migrations

```bash
# Run migrations (handled automatically by database service)
docker-compose restart database-service
```

---

## 🐛 Troubleshooting

### Service Won't Start

```bash
# Check logs
docker-compose logs service-name

# Restart service
docker-compose restart service-name

# Rebuild and restart
docker-compose up -d --build service-name
```

### CUDA/GPU Issues

```bash
# Verify NVIDIA Docker runtime
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# Check GPU availability
nvidia-smi

# Rebuild backend with CUDA
cd backend
docker build --build-arg CUDA_VERSION=12.0 -t jarvis-backend .
```

### Database Connection Issues

```bash
# Check PostgreSQL status
docker-compose ps postgres

# Reset database
docker-compose down -v  # WARNING: Deletes all data!
docker-compose up -d postgres
```

### Port Conflicts

If ports are already in use, edit `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "3000:5173"  # Use port 3000 instead of 5173
```

---

## 🚀 Production Deployment

### Security Checklist

- [ ] Change default passwords in `.env`
- [ ] Generate strong `SECRET_KEY`
- [ ] Enable HTTPS (use nginx reverse proxy)
- [ ] Configure firewall rules
- [ ] Enable rate limiting on all services
- [ ] Set up monitoring (Prometheus + Grafana)
- [ ] Configure automated backups
- [ ] Enable Docker health checks
- [ ] Use secrets management (HashiCorp Vault)

### Reverse Proxy (Nginx)

```nginx
upstream jarvis_backend {
    server localhost:5050;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/cert.pem;
    ssl_certificate_key /etc/ssl/private/key.pem;

    location / {
        proxy_pass http://localhost:5173;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
    }

    location /api {
        proxy_pass http://jarvis_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### Scaling

For high-traffic deployments:

```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Use load balancer (nginx/HAProxy)
# Add Redis for session management
# Use managed PostgreSQL (AWS RDS, Google Cloud SQL)
```

---

## 📞 Support

- **Issues**: https://github.com/Lautloserspieler/JarvisCore/issues
- **Discussions**: https://github.com/Lautloserspieler/JarvisCore/discussions
- **Documentation**: https://github.com/Lautloserspieler/JarvisCore/wiki

---

## 📝 License

MIT License - See [LICENSE](LICENSE) file for details.
