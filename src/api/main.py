from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
import math

from src.screener.engine import ScreenerEngine

app = FastAPI(
    title="Nifty 100 Analytics API",
    description="FastAPI service for Nifty 100 financial analytics",
    version="1.0.0"
)

engine = ScreenerEngine()


def clean_value(value):
    if value is None:
        return None

    if isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            return None

    return value


def clean_records(records):
    cleaned = []

    for record in records:
        cleaned_record = {}

        for key, value in record.items():
            cleaned_record[key] = clean_value(value)

        cleaned.append(cleaned_record)

    return cleaned


@app.get("/")
def root():
    return {
        "message": "Nifty 100 Analytics API is running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "rows": len(engine.df),
        "companies": int(engine.df["company_id"].nunique())
    }


@app.get("/screener/presets")
def get_presets():
    return {
        "presets": list(engine.config["presets"].keys())
    }


@app.get("/screener/{preset_name}")
def run_screener(preset_name: str):
    if preset_name not in engine.config["presets"]:
        raise HTTPException(
            status_code=404,
            detail=f"Unknown preset: {preset_name}"
        )

    try:
        result = engine.run_preset(preset_name)

        records = result.to_dict(orient="records")

        return JSONResponse(
            content={
                "preset": preset_name,
                "rows": len(result),
                "companies": int(result["company_id"].nunique()),
                "results": clean_records(records)
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )