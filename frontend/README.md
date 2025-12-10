# J.A.R.V.I.S. Web UI

Moderne React-basierte Web-Oberfläche für JARVIS.

## 🚀 Quick Start

```bash
# Install dependencies
npm install

# Development (hot reload)
npm run dev
# -> http://localhost:5173

# Build for production
npm run build
# -> Output: dist/

# Preview production build
npm run preview
```

## 🎨 Design System

### Colors
- **Cyan**: `#00f0ff` - Primary accent
- **Blue**: `#0088ff` - Secondary accent
- **Dark**: `#0a0e27` - Background
- **Darker**: `#050814` - Deep background

### Fonts
- **Orbitron**: Headings, buttons (futuristic)
- **Space Grotesk**: Body text (readable)

### Components
- `jarvis-card` - Card with border & glow
- `jarvis-button` - Styled button
- `jarvis-input` - Styled input field
- `jarvis-glow` - Glow shadow effect

## 📚 Tech Stack

- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Lucide React** - Icons
- **Recharts** - Charts (optional)

## 📁 Structure

```
src/
├── main.tsx          # Entry point
├── App.tsx           # Root component
├── index.css         # Global styles
├── pages/
│   └── Index.tsx      # Main dashboard
├── components/
│   └── VoiceVisualizer.tsx
└── lib/
    └── api.ts         # API helpers
```

## 🔌 API Integration

The frontend connects to the FastAPI backend at `http://localhost:8000`.

### REST Endpoints
- `GET /api/health` - Health check
- `GET /api/system/metrics` - System metrics
- `GET /api/llm/status` - LLM status
- `POST /api/chat/message` - Send message

### WebSocket
- `ws://localhost:8000/ws` - Realtime updates

## 🛠️ Development

### Hot Reload
```bash
npm run dev
```

Vite dev server runs on `http://localhost:5173` and proxies API calls to backend.

### Build
```bash
npm run build
```

Output goes to `dist/` folder, which is served by FastAPI.

### Lint
```bash
npm run lint
```

## 🌐 Deployment

### Production Build
```bash
npm run build
```

### Serve via FastAPI
The main JARVIS server (`main.py`) automatically serves the built frontend:

```bash
python main.py
# -> Web UI at http://localhost:8000
```

## 🐛 Troubleshooting

### Port 5173 already in use
```bash
# Kill process on port 5173
netstat -ano | findstr :5173
taskkill /PID <PID> /F
```

### Frontend not loading
1. Check if `dist/` folder exists
2. Rebuild: `npm run build`
3. Restart backend: `python main.py`

### API calls failing
- Check if backend is running on port 8000
- Check browser console for CORS errors
- Verify proxy config in `vite.config.ts`

## ✨ Features

- ✅ **Realtime Metrics** - CPU, RAM, Storage
- ✅ **Voice Visualizer** - Animated Arc Reactor effect
- ✅ **Chat Interface** - Send commands to JARVIS
- ✅ **LLM Status** - Model management
- ✅ **Responsive Design** - Mobile-friendly
- ✅ **Dark Theme** - JARVIS futuristic aesthetic

## 📄 License

MIT License - see root LICENSE file
