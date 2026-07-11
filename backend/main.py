"""
Expense Tracker — FastAPI Backend
===================================
Modello Expense + CRUD + summary per categoria.
Auth via X-API-Key header, letta da variabile d'ambiente API_KEY.
Se API_KEY non è impostata, l'app NON parte (crash pulito).
"""

import os
import sqlite3
import sys
from contextlib import asynccontextmanager
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

# ── Ambiente: API KEY obbligatoria ──────────────────────────────────────────

API_KEY = os.environ.get("API_KEY")
if not API_KEY:
    print("FATAL: La variabile d'ambiente API_KEY non è impostata.", file=sys.stderr)
    print("Esempio: export API_KEY='mia-chiave-segreta'", file=sys.stderr)
    sys.exit(1)

# ── Database ─────────────────────────────────────────────────────────────────

DB_PATH = Path(__file__).parent / "expenses.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_connection()
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            descrizione TEXT    NOT NULL,
            importo     REAL    NOT NULL,
            categoria   TEXT    NOT NULL DEFAULT 'altro',
            data        TEXT    NOT NULL
        )
        """
    )
    conn.commit()
    conn.close()


# ── Schema Pydantic ─────────────────────────────────────────────────────────

CATEGORIE_VALIDE = {"cibo", "trasporti", "casa", "svago", "altro"}


class ExpenseCreate(BaseModel):
    descrizione: str = Field(..., min_length=1, max_length=200)
    importo: float = Field(..., gt=0)
    categoria: str = Field(default="altro")
    data: str = Field(...)  # ISO date, es. "2026-07-11"

    class Config:
        json_schema_extra = {
            "example": {
                "descrizione": "Pizza",
                "importo": 15.50,
                "categoria": "cibo",
                "data": "2026-07-11",
            }
        }


class ExpenseUpdate(BaseModel):
    descrizione: Optional[str] = Field(None, min_length=1, max_length=200)
    importo: Optional[float] = Field(None, gt=0)
    categoria: Optional[str] = Field(None)
    data: Optional[str] = Field(None)


class ExpenseOut(BaseModel):
    id: int
    descrizione: str
    importo: float
    categoria: str
    data: str


# ── Security dependency ──────────────────────────────────────────────────────


async def verify_api_key(request: Request) -> None:
    key = request.headers.get("X-API-Key")
    if not key or key != API_KEY:
        raise HTTPException(status_code=401, detail="API Key mancante o non valida")


# ── App ──────────────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="Expense Tracker API",
    version="1.0.0",
    lifespan=lifespan,
    dependencies=[Depends(verify_api_key)],
)

# CORS: permetti al frontend (ovunque sia servito) di chiamare l'API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Helper ───────────────────────────────────────────────────────────────────


def row_to_expense(row: sqlite3.Row) -> ExpenseOut:
    return ExpenseOut(
        id=row["id"],
        descrizione=row["descrizione"],
        importo=row["importo"],
        categoria=row["categoria"],
        data=row["data"],
    )


# ── Endpoint CRUD ────────────────────────────────────────────────────────────


@app.post("/expenses", response_model=ExpenseOut, status_code=201)
def create_expense(body: ExpenseCreate):
    if body.categoria not in CATEGORIE_VALIDE:
        raise HTTPException(
            status_code=422,
            detail=f"Categoria non valida. Scegli tra: {', '.join(sorted(CATEGORIE_VALIDE))}",
        )
    conn = get_connection()
    cur = conn.execute(
        "INSERT INTO expenses (descrizione, importo, categoria, data) VALUES (?, ?, ?, ?)",
        (body.descrizione, body.importo, body.categoria, body.data),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (cur.lastrowid,)).fetchone()
    conn.close()
    return row_to_expense(row)


@app.get("/expenses", response_model=list[ExpenseOut])
def list_expenses(categoria: Optional[str] = Query(None)):
    conn = get_connection()
    if categoria:
        if categoria not in CATEGORIE_VALIDE:
            conn.close()
            raise HTTPException(
                status_code=422,
                detail=f"Categoria non valida: {categoria}",
            )
        rows = conn.execute(
            "SELECT * FROM expenses WHERE categoria = ? ORDER BY id DESC", (categoria,)
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM expenses ORDER BY id DESC").fetchall()
    conn.close()
    return [row_to_expense(r) for r in rows]


@app.get("/expenses/summary")
def summary():
    """
    Contratto esplicito con il frontend:
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
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT categoria, SUM(importo) as totale FROM expenses GROUP BY categoria"
    ).fetchall()
    total = conn.execute("SELECT COALESCE(SUM(importo), 0) as totale FROM expenses").fetchone()["totale"]
    conn.close()

    categorie = {c: 0.0 for c in CATEGORIE_VALIDE}
    for r in rows:
        categorie[r["categoria"]] = round(r["totale"], 2)

    return {"total": round(total, 2), "categorie": categorie}


@app.get("/expenses/{expense_id}", response_model=ExpenseOut)
def get_expense(expense_id: int):
    conn = get_connection()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Spesa non trovata")
    return row_to_expense(row)


@app.put("/expenses/{expense_id}", response_model=ExpenseOut)
def update_expense(expense_id: int, body: ExpenseUpdate):
    conn = get_connection()
    existing = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Spesa non trovata")

    new_desc = body.descrizione if body.descrizione is not None else existing["descrizione"]
    new_imp = body.importo if body.importo is not None else existing["importo"]
    new_cat = body.categoria if body.categoria is not None else existing["categoria"]
    new_data = body.data if body.data is not None else existing["data"]

    if new_cat not in CATEGORIE_VALIDE:
        conn.close()
        raise HTTPException(
            status_code=422,
            detail=f"Categoria non valida. Scegli tra: {', '.join(sorted(CATEGORIE_VALIDE))}",
        )

    conn.execute(
        "UPDATE expenses SET descrizione=?, importo=?, categoria=?, data=? WHERE id=?",
        (new_desc, new_imp, new_cat, new_data, expense_id),
    )
    conn.commit()
    row = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    conn.close()
    return row_to_expense(row)


@app.delete("/expenses/{expense_id}", status_code=204)
def delete_expense(expense_id: int):
    conn = get_connection()
    existing = conn.execute("SELECT * FROM expenses WHERE id = ?", (expense_id,)).fetchone()
    if not existing:
        conn.close()
        raise HTTPException(status_code=404, detail="Spesa non trovata")
    conn.execute("DELETE FROM expenses WHERE id = ?", (expense_id,))
    conn.commit()
    conn.close()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
