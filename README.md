# Expense Tracker

Full-stack web app per tracciare spese personali: **FastAPI** backend + **vanilla HTML/CSS/JS** frontend + **Chart.js** grafico a torta.

## Struttura

```
├── backend/
│   ├── main.py            # FastAPI app (CRUD + summary)
│   └── requirements.txt   # Dipendenze Python
├── frontend/
│   └── index.html         # SPA vanilla (Chart.js via CDN)
├── README.md
└── DIAGNOSTIC_REPORT.md
```

## Prerequisiti

- Python 3.10+
- `pip` o `uv`
- Un browser moderno

## Avvio Backend

```bash
cd backend

# Installa dipendenze
pip install -r requirements.txt
# oppure: uv pip install -r requirements.txt

# Imposta API Key (OBBLIGATORIA — l'app non parte senza)
export API_KEY='mia-chiave-segreta'
# Windows (cmd): set API_KEY=mia-chiave-segreta
# Windows (PowerShell): $env:API_KEY='mia-chiave-segreta'

# Avvia server (hot-reload attivo)
python main.py
```

Il server parte su **http://localhost:8000**. Il database SQLite (`expenses.db`) viene creato automaticamente.

## Avvio Frontend

Apri `frontend/index.html` nel browser (doppio click o trascina nella finestra).

1. Inserisci la stessa API Key nel campo in alto e clicca **Salva**
2. La key viene salvata in `localStorage`
3. Usa il form per aggiungere spese
4. Il grafico si aggiorna automaticamente

## API Endpoint

| Metodo | Path                     | Descrizione                     |
|--------|--------------------------|----------------------------------|
| POST   | `/expenses`              | Crea una nuova spesa             |
| GET    | `/expenses`              | Lista spese (filtro `?categoria=`) |
| GET    | `/expenses/summary`      | Totale per categoria + generale  |
| GET    | `/expenses/{id}`         | Dettaglio singola spesa          |
| PUT    | `/expenses/{id}`         | Modifica spesa                   |
| DELETE | `/expenses/{id}`         | Elimina spesa                    |

Tutti gli endpoint richiedono header `X-API-Key`.

## Contratto /expenses/summary

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
