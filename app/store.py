# app/store.py
import pandas as pd
from pathlib import Path
from app.config import DONORS_CSV, REQUESTS_CSV, HOSPITALS_CSV, UPLOADED_DONORS, UPLOADED_REQUESTS, UPLOADED_HOSPITALS
from typing import Dict, Any, List
import shutil

# In-memory cached DataFrames
_donors = None
_requests = None
_hospitals = None

def _copy_uploaded_if_exists():
    # If the user has uploaded files to /mnt/data, copy them to data/ for the service
    try:
        if UPLOADED_DONORS.exists() and not DONORS_CSV.exists():
            shutil.copy(UPLOADED_DONORS, DONORS_CSV)
        if UPLOADED_REQUESTS.exists() and not REQUESTS_CSV.exists():
            shutil.copy(UPLOADED_REQUESTS, REQUESTS_CSV)
        if UPLOADED_HOSPITALS.exists() and not HOSPITALS_CSV.exists():
            shutil.copy(UPLOADED_HOSPITALS, HOSPITALS_CSV)
    except Exception:
        pass

def load_donors(force: bool = False) -> pd.DataFrame:
    global _donors
    _copy_uploaded_if_exists()
    if _donors is None or force:
        if DONORS_CSV.exists():
            _donors = pd.read_csv(DONORS_CSV)
        else:
            _donors = pd.DataFrame()
    return _donors

def load_requests(force: bool = False) -> pd.DataFrame:
    global _requests
    _copy_uploaded_if_exists()
    if _requests is None or force:
        if REQUESTS_CSV.exists():
            _requests = pd.read_csv(REQUESTS_CSV)
        else:
            _requests = pd.DataFrame()
    return _requests

def load_hospitals(force: bool = False) -> pd.DataFrame:
    global _hospitals
    _copy_uploaded_if_exists()
    if _hospitals is None or force:
        if HOSPITALS_CSV.exists():
            _hospitals = pd.read_csv(HOSPITALS_CSV)
        else:
            _hospitals = pd.DataFrame()
    return _hospitals

def save_uploaded_file(file_bytes: bytes, target_path: Path):
    with open(target_path, "wb") as f:
        f.write(file_bytes)
    # force reload next time
    load_donors(force=True) if target_path == DONORS_CSV else None
    load_requests(force=True) if target_path == REQUESTS_CSV else None
    load_hospitals(force=True) if target_path == HOSPITALS_CSV else None
    return target_path

def donors_sample(n:int = 5) -> List[Dict[str,Any]]:
    df = load_donors()
    if df.empty:
        return []
    return df.head(n).to_dict(orient="records")
