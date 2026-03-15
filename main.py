from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query

app = FastAPI(title="CRM Sales API", version="1.0.0")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DEALS_PATH = DATA_DIR / "deals.csv"
AGENTS_PATH = DATA_DIR / "agents.csv"


def load_deals() -> pd.DataFrame:
    if not DEALS_PATH.exists():
        raise FileNotFoundError("No se encontró data/deals.csv")
    return pd.read_csv(DEALS_PATH)


def load_agents() -> pd.DataFrame:
    if not AGENTS_PATH.exists():
        raise FileNotFoundError("No se encontró data/agents.csv")
    return pd.read_csv(AGENTS_PATH)


@app.get("/")
def root():
    return {"message": "CRM Sales API is running"}


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/agents")
def get_agents():
    df = load_agents()
    return {
        "count": len(df),
        "data": df.to_dict(orient="records")
    }


@app.get("/deals")
def get_deals(
    limit: int = Query(default=50, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    status: Optional[str] = Query(default=None),
    agent_id: Optional[str] = Query(default=None),
    lead_source: Optional[str] = Query(default=None),
):
    df = load_deals()

    if status:
        df = df[df["current_status"] == status]

    if agent_id:
        df = df[df["agent_id"] == agent_id]

    if lead_source:
        df = df[df["lead_source"] == lead_source]

    total = len(df)
    df_paginated = df.iloc[offset:offset + limit]

    return {
        "total": total,
        "limit": limit,
        "offset": offset,
        "filters": {
            "status": status,
            "agent_id": agent_id,
            "lead_source": lead_source,
        },
        "data": df_paginated.to_dict(orient="records"),
    }


@app.get("/deals/{deal_id}")
def get_deal_by_id(deal_id: str):
    df = load_deals()
    result = df[df["deal_id"] == deal_id]

    if result.empty:
        raise HTTPException(status_code=404, detail="Deal no encontrado")

    return result.iloc[0].to_dict()