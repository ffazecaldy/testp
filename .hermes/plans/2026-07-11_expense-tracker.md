# Prometheus Engine Plan — Expense Tracker

## Goal
Full-stack expense tracker: FastAPI backend + vanilla JS frontend + Chart.js

## Tier
- Tier: 2 (2-5 files)
- Subagenti: 2 (backend + frontend paralleli)
- Soglia qualità: 7/10
- Push mode: batch_end

## Contratto /expenses/summary (Phase 1c — DA INIETTARE IN ENTRAMBI I SUBAGENTI)
```json
{
  "total": 1234.56,
  "categorie": {
    "cibo": 456.78,
    "trasporti": 234.50,
    "casa": 345.00,
    "svago": 120.00,
    "altro": 78.28
  }
}
```
Frontend consumerà `data.total` e `Object.keys(data.categorie)` / `Object.values(data.categorie)`.

## Decomposizione (2 subagenti paralleli)

### Task 1 — Backend (subagente 1)
File: `backend/main.py`, `backend/requirements.txt`
- FastAPI + SQLite
- Modello: Expense (id, descrizione, importo, categoria, data)
- Endpoint: POST/GET/PUT/DELETE /expenses + GET /expenses/summary
- Auth: X-API-Key da env var API_KEY, nessun default, sys.exit(1) se manca
- CORS: allow_origins=["*"]
- Security: niente hardcoded secrets, SQL parametrizzato

### Task 2 — Frontend (subagente 2)
File: `frontend/index.html`
- SPA vanilla HTML/CSS/JS (no framework, no build)
- Form add/edit con validazione
- Tabella spese filtrabile per categoria
- Chart.js doughnut chart (via CDN) da /expenses/summary
- Gestione errori HTTP visibili a schermo (401, 404, 422)
- API Key configurabile (localStorage)

### Post-gather (io)
- README.md
- DIAGNOSTIC_REPORT.md
- .gitignore
- Test live API
- Push consolidato

## Security Shield
- NO hardcoded secrets (API_KEY da env var, niente default)
- SQL parametrizzato (NO f-string)
- Input validation via Pydantic

## Quality criteria per subagenti
- Type hints obbligatori (backend)
- Gestione errori HTTP visibili (frontend)
- Contratto summary rispettato ESATTAMENTE
