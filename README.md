# GitMind — Frontend

React app. See the root `README.md` for the full integration guide.

## Start

```bash
npm start        # dev server on http://localhost:3000
npm run build    # production build
```

## Key files

| File | Purpose |
|------|---------|
| `src/App.js` | All state, WebSocket connection, tab routing |
| `src/api.js` | `postChat(sessionId, question)` and `checkHealth()` |
| `src/components/AgentProgress.jsx` | Live agent status panel |
| `src/components/DiagramTab.jsx` | Mermaid diagram renderer with zoom |
| `src/components/DocsTab.jsx` | API endpoints table with method filters |
| `src/components/SecurityTab.jsx` | Security findings with expandable cards |
| `src/components/ChatTab.jsx` | RAG chat interface |
| `src/components/CrisisChat.jsx` | Crisis room slide-in panel |

## Backend expected on

```
ws://localhost:8000/ws/analyze   ← analysis pipeline
POST http://localhost:8000/chat  ← chat Q&A
GET  http://localhost:8000/health
```

See root `README.md` → Section 4 for the full WebSocket message contract.
