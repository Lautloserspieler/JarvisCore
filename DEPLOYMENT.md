# 🚀 JarvisCore v1.1.0 - Deployment-Anleitung

## 📋 Übersicht

JarvisCore v1.1.0 verfügt über eine Microservices-Architektur mit:
- **Frontend**: Vue.js + TypeScript + Shadcn/UI
- **Backend**: Python (FastAPI) + llama.cpp
- **Go Services**: Auth, Security, Memory, Database
- **Datenbank**: PostgreSQL 16

---

## 🏗️ Architektur

```
┌─────────────────────────────────────────────────────────┐
│                   Frontend (Vue.js)                     │
│                    Port: 5173                           │
└────────────────────────┬────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────┐
│            Backend (Python + llama.cpp)                │
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

## ⚙️ Voraussetzungen

### Erforderlich
- **Docker** 24.0+ & **Docker Compose** 2.20+
- **NVIDIA GPU** mit CUDA 12.0+ (für llama.cpp)
- **16GB+ RAM** (8GB minimum)
- **20GB+ Speicherplatz** (für Modelle)

### Optional
- **Go 1.21+** (für lokale Go Service-Entwicklung)
- **Node.js 18+** (für lokale Frontend-Entwicklung)
- **Python 3.11+** (für lokale Backend-Entwicklung)

---

## 🐳 Docker-Deployment (Empfohlen)

### 1. Repository klonen

```bash
git clone https://github.com/Lautloserspieler/JarvisCore.git
cd JarvisCore
```

### 2. Umgebungsvariablen erstellen

Erstelle `.env` Datei:

```bash
cat > .env << EOF
# Datenbank
DATABASE_URL=postgres://jarvis:jarvis@postgres:5432/jarviscore?sslmode=disable
POSTGRES_USER=jarvis
POSTGRES_PASSWORD=jarvis
POSTGRES_DB=jarviscore

# Authentifizierung
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

### 3. Alle Services bauen

```bash
docker-compose build
```

### 4. Alle Services starten

```bash
docker-compose up -d
```

### 5. Service-Gesundheit prüfen

```bash
# Alle Services prüfen
docker-compose ps

# Logs anzeigen
docker-compose logs -f

# Health-Endpunkte
curl http://localhost:8080/health  # Auth
curl http://localhost:8081/health  # Security
curl http://localhost:8082/health  # Memory
curl http://localhost:8083/health  # Database
curl http://localhost:5050/health  # Backend
```

### 6. Zugriff auf Anwendung

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:5050
- **API-Dokumentation**: http://localhost:5050/docs

---

## 🔧 Lokale Entwicklungsumgebung

### Backend (Python)

```bash
cd backend

# Virtuelle Umgebung erstellen
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Dependencies installieren
pip install -r requirements.txt

# Server starten
uvicorn main:app --reload --host 0.0.0.0 --port 5050
```

### Frontend (Vue.js)

```bash
cd frontend

# Dependencies installieren
npm install

# Dev-Server starten
npm run dev
```

### Go Services

#### Auth Service
```bash
cd go-services/auth
go mod download
go run main.go
# Hört auf :8080
```

#### Security Service
```bash
cd go-services/security
go mod download
go run main.go
# Hört auf :8081
```

#### Memory Service
```bash
cd go-services/memory
go mod download
go run main.go
# Hört auf :8082
```

#### Database Service
```bash
cd go-services/database

# PostgreSQL zuerst starten
docker run -d \
  --name postgres \
  -e POSTGRES_USER=jarvis \
  -e POSTGRES_PASSWORD=jarvis \
  -e POSTGRES_DB=jarviscore \
  -p 5432:5432 \
  postgres:16-alpine

# Service starten
go mod download
go run main.go
# Hört auf :8083
```

---

## 🔑 API-Schlüssel-Management

### API-Schlüssel erstellen

```bash
curl -X POST http://localhost:8080/api/auth/keys/create \
  -H "Content-Type: application/json" \
  -d '{
    "key": "your-api-key-123",
    "rate_limit": 100,
    "burst": 20
  }'
```

### JWT Token generieren

```bash
curl -X POST http://localhost:8080/api/auth/token \
  -H "Content-Type: application/json" \
  -d '{"api_key": "your-api-key-123"}'
```

### API-Schlüssel verwenden

```bash
curl http://localhost:5050/api/models \
  -H "X-API-Key: your-api-key-123"
```

---

## 📦 Modell-Management

### Modelle herunterladen

Modelle werden über die Frontend-UI verwaltet:
1. Navigiere zum **Modelle** Tab
2. Klick auf **Herunterladen** beim gewünschten Modell
3. Wähle Quantization (Q4_K_M, Q5_K_M, Q6_K, Q8_0)
4. Warte auf Abschluss des Downloads

### Manuelle Modell-Installation

```bash
# Modell-Verzeichnis erstellen
mkdir -p models/llm

# Modell herunterladen (Beispiel)
wget https://huggingface.co/TheBloke/Llama-2-7B-GGUF/resolve/main/llama-2-7b.Q4_K_M.gguf \
  -O models/llm/llama-2-7b-q4.gguf

# Überprüfen
ls -lh models/llm/
```

---

## 🔒 Sicherheitskonfiguration

### Prompt-Injection-Schutz

Der Security-Service validiert automatisch alle Prompts:

```python
# Test-Validierung
import requests

response = requests.post('http://localhost:8081/api/security/validate', json={
    'input': 'Your prompt here',
    'strict': False  # True für strengere Validierung
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

Standard Rate Limits:
- **Demo Key**: 60 Anfragen/Minute, Burst 10
- **Admin Key**: 300 Anfragen/Minute, Burst 50

Anpassung in `go-services/auth/main.go`.

---

## 🗄️ Datenbank-Management

### Datenbank sichern

```bash
docker exec jarvis-postgres pg_dump -U jarvis jarviscore > backup.sql
```

### Datenbank wiederherstellen

```bash
docker exec -i jarvis-postgres psql -U jarvis jarviscore < backup.sql
```

### Mit Datenbank verbinden

```bash
docker exec -it jarvis-postgres psql -U jarvis -d jarviscore
```

---

## 🧪 Testen

### Alle Tests ausführen

```bash
# Backend-Tests
cd backend
pytest tests/ -v

# Frontend-Tests
cd frontend
npm run test

# Go Service-Tests
cd go-services/auth
go test -v ./...
```

### Endpunkte testen

```bash
# Health Checks
for port in 8080 8081 8082 8083 5050; do
  echo "Testing port $port:"
  curl -s http://localhost:$port/health | jq
done

# Modell laden
curl -X POST http://localhost:5050/api/models/llama-2-7b-q4/load

# Text generieren
curl -X POST http://localhost:5050/api/chat/message \
  -H "Content-Type: application/json" \
  -d '{"message": "Hallo JARVIS!"}'
```

---

## 📊 Monitoring

### Logs anzeigen

```bash
# Alle Services
docker-compose logs -f

# Spezifischer Service
docker-compose logs -f backend

# Letzte 100 Zeilen
docker-compose logs --tail=100 backend
```

### Service-Metriken

```bash
# Memory Service Stats
curl http://localhost:8082/api/memory/stats

# Database Stats
curl http://localhost:8083/api/stats

# Multi-Model Stats
curl http://localhost:5050/api/models/stats
```

---

## 🔄 Updates

### Neueste Änderungen abrufen

```bash
git pull origin main

# Services neu bauen
docker-compose build

# Neustarten
docker-compose down
docker-compose up -d
```

### Datenbank-Migrationen

```bash
# Migrationen ausführen (wird automatisch vom Database Service gemacht)
docker-compose restart database-service
```

---

## 🐛 Troubleshooting

### Service startet nicht

```bash
# Logs prüfen
docker-compose logs service-name

# Service neu starten
docker-compose restart service-name

# Neu bauen und neustarten
docker-compose up -d --build service-name
```

### CUDA/GPU-Probleme

```bash
# NVIDIA Docker Runtime überprüfen
docker run --rm --gpus all nvidia/cuda:12.0-base nvidia-smi

# GPU-Verfügbarkeit prüfen
nvidia-smi

# Backend mit CUDA neu bauen
cd backend
docker build --build-arg CUDA_VERSION=12.0 -t jarvis-backend .
```

### Datenbank-Verbindungsprobleme

```bash
# PostgreSQL Status prüfen
docker-compose ps postgres

# Datenbank zurücksetzen
docker-compose down -v  # WARNUNG: Löscht alle Daten!
docker-compose up -d postgres
```

### Port-Konflikte

Wenn Ports bereits genutzt werden, bearbeite `docker-compose.yml`:

```yaml
services:
  frontend:
    ports:
      - "3000:5173"  # Verwende Port 3000 statt 5173
```

---

## 🚀 Production-Deployment

### Sicherheits-Checkliste

- [ ] Standardpasswörter in `.env` ändern
- [ ] Starkes `SECRET_KEY` generieren
- [ ] HTTPS aktivieren (Nginx Reverse Proxy verwenden)
- [ ] Firewall-Regeln konfigurieren
- [ ] Rate Limiting auf allen Services aktivieren
- [ ] Monitoring einrichten (Prometheus + Grafana)
- [ ] Automatische Backups konfigurieren
- [ ] Docker Health Checks aktivieren
- [ ] Secrets Management verwenden (HashiCorp Vault)

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

### Skalierung

Für High-Traffic Deployments:

```bash
# Backend-Instanzen skalieren
docker-compose up -d --scale backend=3

# Load Balancer verwenden (nginx/HAProxy)
# Redis für Session Management hinzufügen
# Verwaltete PostgreSQL nutzen (AWS RDS, Google Cloud SQL)
```

---

## 📞 Support

- **Issues**: https://github.com/Lautloserspieler/JarvisCore/issues
- **Diskussionen**: https://github.com/Lautloserspieler/JarvisCore/discussions
- **Dokumentation**: https://github.com/Lautloserspieler/JarvisCore/wiki

---

## 📝 Lizenz

MIT Lizenz - Siehe [LICENSE](LICENSE) Datei für Details.