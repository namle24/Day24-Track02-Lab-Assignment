"""FastAPI API exposing governed MedViet patient data."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from fastapi import Depends, FastAPI

from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

DATA_PATH = Path("data/raw/patients_raw.csv")


def _load_patients() -> pd.DataFrame:
    return pd.read_csv(DATA_PATH, dtype={"cccd": str, "so_dien_thoai": str})


@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(current_user: dict = Depends(get_current_user)):
    """Return raw patient data for admins only."""

    del current_user
    return _load_patients().head(10).to_dict(orient="records")


@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(current_user: dict = Depends(get_current_user)):
    """Return anonymized training data."""

    del current_user
    df_anon = anonymizer.anonymize_dataframe(_load_patients())
    return df_anon.head(10).to_dict(orient="records")


@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(current_user: dict = Depends(get_current_user)):
    """Return non-PII aggregate metrics."""

    del current_user
    df = _load_patients()
    disease_counts = df["benh"].value_counts().to_dict()
    return {
        "total_patients": int(len(df)),
        "patients_by_condition": {str(key): int(value) for key, value in disease_counts.items()},
        "avg_test_result": round(float(df["ket_qua_xet_nghiem"].mean()), 2),
    }


@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(patient_id: str, current_user: dict = Depends(get_current_user)):
    """Mock deletion endpoint restricted to admins."""

    del current_user
    return {"deleted": True, "patient_id": patient_id}


@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
