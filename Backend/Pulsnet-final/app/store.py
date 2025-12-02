# app/store.py
import pandas as pd
from pathlib import Path
from app.config import (
    DONORS_CSV,
    REQUESTS_CSV,
    HOSPITALS_CSV,
    UPLOADED_DONORS,
    UPLOADED_REQUESTS,
    UPLOADED_HOSPITALS,
    DB_PATH,           # 🔹 add this
)
from typing import Dict, Any, List
import shutil
import sqlite3          # 🔹 add this


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

def _load_user_donors_from_db() -> pd.DataFrame:
    """
    Load user-registered donors from users.db (user_donors table)
    and map to same columns as donors.csv:
    donor_id, name, blood_group, phone, lat, lon, availability, last_donation_date
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM user_donors")
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return pd.DataFrame()

        records = []
        for r in rows:
            records.append(
                {
                    "donor_id": r["donor_id"],
                    "name": r["full_name"],
                    "blood_group": r["blood_group"],
                    "phone": r["phone"],
                    "lat": r["lat"],
                    "lon": r["lon"],
                    "availability": r["availability"],
                    "last_donation_date": r["last_donation_date"],
                }
            )
        return pd.DataFrame(records)
    except Exception:
        return pd.DataFrame()


def load_donors(force: bool = False) -> pd.DataFrame:
    global _donors
    _copy_uploaded_if_exists()

    if _donors is None or force:
        # base donors from CSV
        if DONORS_CSV.exists():
            base_df = pd.read_csv(DONORS_CSV)
        else:
            base_df = pd.DataFrame()

        # additional donors from user_donors table
        user_df = _load_user_donors_from_db()

        if not user_df.empty:
            if base_df.empty:
                _donors = user_df
            else:
                # ensure user_df has all columns in base_df
                missing_cols = [c for c in base_df.columns if c not in user_df.columns]
                for c in missing_cols:
                    user_df[c] = None
                _donors = pd.concat(
                    [base_df, user_df[base_df.columns]], ignore_index=True
                )
        else:
            _donors = base_df

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

# app/store.py  (add near other load/save helpers)

def delete_donor_by_id(donor_id: str) -> bool:
    """
    Delete donor row with donor_id from DONORS_CSV.
    Returns True if deleted, False if not found.
    """
    global _donors
    _copy_uploaded_if_exists()
    if not DONORS_CSV.exists():
        return False

    try:
        df = pd.read_csv(DONORS_CSV, dtype=str)
    except Exception:
        # if CSV cannot be read
        return False

    # find rows that match donor_id
    if "donor_id" not in df.columns:
        # try lower-case fallback or different id column names
        candidates = [c for c in df.columns if c.lower() in ("id", "donorid", "donor_id")]
        if not candidates:
            return False
        id_col = candidates[0]
    else:
        id_col = "donor_id"

    mask = df[id_col].astype(str) != str(donor_id)
    if mask.all():
        # nothing removed
        return False

    # write back only remaining rows
    df_new = df[mask]
    df_new.to_csv(DONORS_CSV, index=False)

    # clear cache so next load reads new CSV
    _donors = None
    load_donors(force=True)
    return True

