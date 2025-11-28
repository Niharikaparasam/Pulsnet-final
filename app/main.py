# app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from app.store import (
    save_uploaded_file,
    load_donors,
    load_requests,
    load_hospitals,
    DONORS_CSV,
    REQUESTS_CSV,
    HOSPITALS_CSV,
)
from app.match_engine import rank_donors_for_request
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import joblib
from app.config import MATCH_MODEL_PATH
import os
from fastapi import APIRouter, Depends

from app.google_maps import distance_matrix
from app.auth import router as auth_router, get_current_user  # 🔒 add get_current_user
from app.alerts import trigger_match_alert

app = FastAPI(title="PulseNet - Blood Matching Backend (CSV-based)")

# ---------- CORS (for React frontend) ----------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # adjust if you deploy frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Include auth router ----------
app.include_router(auth_router)

# ---------- Schemas ----------
class MatchRequest(BaseModel):
    required_blood_group: str
    hospital_id: Optional[str] = None
    lat: Optional[float] = None
    lon: Optional[float] = None
    units_needed: Optional[int] = 1
    urgency_level: Optional[str] = None
    top_n: Optional[int] = 10

# ---------- Health ----------
@app.get("/api/health")
def health():
    return {"status": "ok"}

# ---------- Upload CSV endpoints ----------
@app.post("/api/upload/donors")
async def upload_donors(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)   # 🔒 require login
):
    content = await file.read()
    target = Path(DONORS_CSV)
    target.write_bytes(content)
    df = load_donors(force=True)
    return {"status": "ok", "rows": len(df)}


@app.post("/api/upload/requests")
async def upload_requests(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)   # 🔒
):
    content = await file.read()
    target = Path(REQUESTS_CSV)
    target.write_bytes(content)
    df = load_requests(force=True)
    return {"status": "ok", "rows": len(df)}


@app.post("/api/upload/hospitals")
async def upload_hospitals(
    file: UploadFile = File(...),
    current_user = Depends(get_current_user)   # 🔒
):
    content = await file.read()
    target = Path(HOSPITALS_CSV)
    target.write_bytes(content)
    df = load_hospitals(force=True)
    return {"status": "ok", "rows": len(df)}


# ---------- Info endpoints ----------
@app.get("/api/donors/sample")
def donors_sample(n: int = 5):
    df = load_donors()
    if df.empty:
        return {"status": "no_data", "sample": []}
    return {"status": "ok", "sample": df.head(n).to_dict(orient="records")}

@app.get("/api/donors/cols")
def donors_cols():
    df = load_donors()
    if df.empty:
        return {"status": "no_data"}
    return {"status": "ok", "columns": df.columns.tolist()}

@app.get("/api/requests/cols")
def requests_cols():
    df = load_requests()
    if df.empty:
        return {"status": "no_data"}
    return {"status": "ok", "columns": df.columns.tolist()}

@app.get("/api/hospitals/cols")
def hospitals_cols():
    df = load_hospitals()
    if df.empty:
        return {"status": "no_data"}
    return {"status": "ok", "columns": df.columns.tolist()}

@app.post("/api/match")
def match_handler(
    req: MatchRequest,
    current_user = Depends(get_current_user)  # keep protection
):
    reqd = req.dict()
    ranked = rank_donors_for_request(reqd, top_n=req.top_n)

    # 🔔 ask alert system if this needs an alert
    alert = trigger_match_alert(reqd, ranked)

    return {
        "status": "ok",
        "matches": ranked,
        "alert": alert,  # can be None or alert dict
    }



# ---------- Model upload (optional) ----------
@app.post("/api/model/upload")
async def upload_model(file: UploadFile = File(...)):
    content = await file.read()
    Path(MATCH_MODEL_PATH).write_bytes(content)
    # quick load
    try:
        _ = joblib.load(MATCH_MODEL_PATH)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Model load failed: {e}")
    return {"status": "ok", "message": "model uploaded and validated"}

@app.get("/api/model/status")
def model_status():
    if Path(MATCH_MODEL_PATH).exists():
        return {"status": "ok", "path": str(MATCH_MODEL_PATH)}
    return {"status": "no_model"}

# ---------- Distance API (using ORS or your wrapper) ----------
@app.post("/api/google/distance")
def google_distance(origin: dict, destinations: list,  current_user = Depends(get_current_user)):
    """
    origin: { "lat": 12.97, "lon": 77.59 } or { "address": "..." }
    destinations: [ { "lat": x, "lon": y }, ... ]
    """
    # build origin string
    if "lat" in origin and "lon" in origin:
        orig_str = f"{origin['lat']},{origin['lon']}"
    elif "address" in origin:
        orig_str = origin["address"]
    else:
        raise HTTPException(status_code=400, detail="Invalid origin")

    dest_strs = []
    for d in destinations:
        if "lat" in d and "lon" in d:
            dest_strs.append(f"{d['lat']},{d['lon']}")
        elif "address" in d:
            dest_strs.append(d["address"])
        else:
            dest_strs.append("")  # keep placeholder

    # call distance_matrix from app.google_maps (now ORS-based)
    try:
        res = distance_matrix([orig_str], dest_strs)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # parse useful info: durations (seconds), distance (meters)
    parsed = []
    rows = res.get("durations", [])
    dists = res.get("distances", [])
    if rows and dists:
        # origin is index 0, destinations start from index 1
        # you already tested this logic earlier
        for i in range(1, len(rows[0])):
            duration_s = rows[0][i]
            distance_m = dists[0][i]
            parsed.append(
                {
                    "destination": dest_strs[i],
                    "distance_m": distance_m,
                    "distance_text": f"{distance_m/1000:.1f} km",
                    "duration_s": duration_s,
                    "duration_text": f"{duration_s/60:.0f} mins",
                }
            )

    return {"raw": res, "parsed": parsed}
