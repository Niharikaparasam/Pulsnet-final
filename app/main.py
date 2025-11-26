# app/main.py
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from app.store import save_uploaded_file, load_donors, load_requests, load_hospitals, DONORS_CSV, REQUESTS_CSV, HOSPITALS_CSV
from app.match_engine import rank_donors_for_request
from pydantic import BaseModel
from typing import Optional
from pathlib import Path
import joblib
from app.config import MATCH_MODEL_PATH
import os
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import List, Dict
from app.google_maps import distance_matrix









app = FastAPI(title="PulseNet - Blood Matching Backend (CSV-based)")

class GoogleDistanceRequest(BaseModel):
    origin: Dict
    destinations: List[Dict]
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
    return {"status":"ok"}

# ---------- Upload CSV endpoints ----------
@app.post("/api/upload/donors")
async def upload_donors(file: UploadFile = File(...)):
    content = await file.read()
    target = Path(DONORS_CSV)
    target.write_bytes(content)
    # force load
    df = load_donors(force=True)
    return {"status":"ok", "rows": len(df)}

@app.post("/api/upload/requests")
async def upload_requests(file: UploadFile = File(...)):
    content = await file.read()
    target = Path(REQUESTS_CSV)
    target.write_bytes(content)
    df = load_requests(force=True)
    return {"status":"ok", "rows": len(df)}

@app.post("/api/upload/hospitals")
async def upload_hospitals(file: UploadFile = File(...)):
    content = await file.read()
    target = Path(HOSPITALS_CSV)
    target.write_bytes(content)
    df = load_hospitals(force=True)
    return {"status":"ok", "rows": len(df)}

# ---------- Info endpoints ----------
@app.get("/api/donors/sample")
def donors_sample(n:int = 5):
    df = load_donors()
    if df.empty:
        return {"status":"no_data", "sample": []}
    return {"status":"ok", "sample": df.head(n).to_dict(orient="records")}

@app.get("/api/donors/cols")
def donors_cols():
    df = load_donors()
    if df.empty:
        return {"status":"no_data"}
    return {"status":"ok", "columns": df.columns.tolist()}

@app.get("/api/requests/cols")
def requests_cols():
    df = load_requests()
    if df.empty:
        return {"status":"no_data"}
    return {"status":"ok", "columns": df.columns.tolist()}

@app.get("/api/hospitals/cols")
def hospitals_cols():
    df = load_hospitals()
    if df.empty:
        return {"status":"no_data"}
    return {"status":"ok", "columns": df.columns.tolist()}

# ---------- Matching ----------
@app.post("/api/match")
def match_handler(req: MatchRequest):
    reqd = req.dict()
    ranked = rank_donors_for_request(reqd, top_n=req.top_n)
    return {"status":"ok", "matches": ranked}

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
    return {"status":"ok", "message":"model uploaded and validated"}

@app.get("/api/model/status")
def model_status():
    if Path(MATCH_MODEL_PATH).exists():
        return {"status":"ok", "path": str(MATCH_MODEL_PATH)}
    return {"status":"no_model"}

@app.post("/api/google/distance")
def google_distance(payload: GoogleDistanceRequest):
    """
    origin: { "lat": 12.97, "lon": 77.59 } or { "address": "..." }
    destinations: [ { "lat": x, "lon": y }, ... ]
    Uses OpenRouteService matrix under the hood.
    """
    origin = payload.origin
    destinations = payload.destinations

    # build origin string "lat,lon"
    if "lat" in origin and "lon" in origin:
        orig_str = f"{origin['lat']},{origin['lon']}"
    elif "address" in origin:
        # if you later support address geocoding
        raise HTTPException(status_code=400, detail="Address origin not supported yet")
    else:
        raise HTTPException(status_code=400, detail="Invalid origin")

    # build destination strings "lat,lon"
    dest_strs = []
    for d in destinations:
        if "lat" in d and "lon" in d:
            dest_strs.append(f"{d['lat']},{d['lon']}")
        elif "address" in d:
            # same note as above
            raise HTTPException(status_code=400, detail="Address destination not supported yet")
        else:
            dest_strs.append("")

    # call ORS-based distance_matrix wrapper
    try:
        res = distance_matrix([orig_str], dest_strs, mode="driving")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # ---- ORS PARSING ----
    parsed = []
    dist_mat = res.get("distances")
    dur_mat = res.get("durations")

    # ORS returns a full matrix, origin is index 0, destinations are 1..N
    if dist_mat and dur_mat:
        dist_row = dist_mat[0]   # from origin to everyone
        dur_row = dur_mat[0]

        for i, dest in enumerate(dest_strs):
            # skip index 0 (origin->origin), so use i+1
            d_m = dist_row[i + 1]
            t_s = dur_row[i + 1]

            parsed.append({
                "destination": dest,
                "distance_m": d_m,
                "distance_text": f"{d_m / 1000:.1f} km",
                "duration_s": t_s,
                "duration_text": f"{int(t_s // 60)} mins"
            })

    return {"raw": res, "parsed": parsed}


