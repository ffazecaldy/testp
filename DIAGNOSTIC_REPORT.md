# DIAGNOSTIC REPORT — Expense Tracker

## Execution Summary

- **Model**: deepseek-v4-flash
- **Provider**: opencode-go
- **Skill**: prometheus-engine v5.5.3
- **Push mode**: batch_end (consolidated)
- **Target repo**: https://github.com/ffazecaldy/testp.git

## Fasi Esecuzione

### Fase 1a: Prompt parsing
Il prompt richiedeva:
1. Backend FastAPI + SQLite
2. Frontend HTML/CSS/JS vanilla + Chart.js
3. Contratto esplicito per /expenses/summary
4. API Key da env var, nessun default hardcoded
5. CORS abilitato
6. Gestione errori HTTP visibili a schermo
7. README.md + DIAGNOSTIC_REPORT.md
8. Push consolidato batch_end

### Fase 1b: Contratto /expenses/summary
Forma concordata PRIMA dello sviluppo:

```json
{
  "total": 818.0,
  "categorie": {
    "cibo": 15.5,
    "trasporti": 2.5,
    "casa": 800.0,
    "altro": 0.0,
    "svago": 0.0
  }
}
```

- `total`: float, somma generale arrotondata a 2 decimali
- `categorie`: dict con tutte e 5 le categorie (anche a 0), nome → totale per categoria

### Fase 1c–1d: Scatter / Dispatch
Non sono stati usati sub-agenti separati (scatter-gather). Lo sviluppo è stato eseguito in sequenza monolitica: backend prima, poi frontend, poi assembly (modalità quick-start del prometheus-engine).

### Fase 2: Backend
File prodotto: `backend/main.py`
- FastAPI con lifespan per init DB
- Modelli Pydantic: ExpenseCreate, ExpenseUpdate, ExpenseOut
- SQLite con WAL mode
- Endpoint: POST, GET (lista + filtro), GET /summary, GET /{id}, PUT, DELETE
- Auth: `verify_api_key` dependency globale sull'app
- CORS: `allow_origins=["*"]`

### Fase 3: Frontend
File prodotto: `frontend/index.html`
- Form add/edit con validazione lato client
- Tabella filtra bile per categoria
- Chart.js doughnut chart da /expenses/summary
- Gestione errori HTTP: mostra messaggi a schermo (msg-box), non solo in console
- API Key salvata in localStorage

---

## Interface Contract Frontend↔Backend

### Forma dati concordata per /expenses/summary

Prima del dispatch è stato definito:

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

- Backend implementa: `{"total": round(total,2), "categorie": {c: 0.0 for c in CATEGORIE_VALIDE}}` + aggiorna con dati reali
- Frontend consuma: `data.total` per totale, `Object.keys(data.categorie)` / `Object.values(data.categorie)` per il chart

**Esito**: ✅ MATCH al primo tentativo. Nessun mismatch.

Il backend restituisce tutte e 5 le categorie anche se a zero, il frontend itera sulle chiavi — non c'era possibilità di disallineamento.

### CORS
Configurato al primo tentativo con `CORSMiddleware(allow_origins=["*"], ...)`.
Nessun fix necessario.

### API Key obbligatoria
Il vincolo "nessun default hardcoded" è stato rispettato.

```python
API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    print("FATAL: La variabile d'ambiente API_KEY non è impostata.", file=sys.stderr)
    sys.exit(1)
```

Se l'app parte senza `API_KEY`:
- Stampa errore su stderr
- **Crash pulito** con `sys.exit(1)` — nessun comportamento silenzioso

### Altri bug trovati in Assembly

1. **Routing conflict** — `/expenses/summary` dichiarato DOPO `/expenses/{expense_id}`. FastAPI matcha `summary` come `{expense_id}`. **Fix**: spostato summary prima dei path con parametro.

2. **Duplicato summary** — Durante la correzione del routing, la funzione summary è stata duplicata (una versione completa + una incompleta senza return). **Fix**: rimosso il duplicato.

3. **fastapi import Depends** — Il pacchetto fastapi nel venv era installato come namespace package (senza `__init__.py`), probabilmente da una precedente installazione corrotta. **Fix**: reinstallato con `uv pip install --force-reinstall fastapi uvicorn`.

### Metriche

| Metrica | Valore |
|---------|--------|
| Endpoint backend | 6 (POST, GET lista, GET summary, GET id, PUT, DELETE) |
| Endpoint testati | 6 |
| Test passati | 6/6 |
| Bug in assembly | 3 (routing order, duplicato, fastapi corrupto) |
| Mismatch contratto | 0 |
| Sub-agenti usati | 0 (monolitico) |
