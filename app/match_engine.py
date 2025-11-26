# app/match_engine.py
from typing import Dict, Any, List, Optional
from app.store import load_donors, load_hospitals
from geopy.distance import geodesic
import pandas as pd
from pathlib import Path
from app.config import MATCH_MODEL_PATH
import joblib
import requests, os
from app.google_maps import distance_matrix  # ORS-based wrapper


# ABO donor->recipient compatibility
ABO_COMPAT = {
    "O": ["O","A","B","AB"],
    "A": ["A","AB"],
    "B": ["B","AB"],
    "AB": ["AB"]
}

def normalize_abo(bg: str) -> str:
    if not bg:
        return ""
    bg = str(bg).upper().strip()
    # remove Rh factor (+ / -)
    bg = bg.replace("+", "").replace("-", "")
    return bg  # returns "O", "A", "B" or "AB"

def abo_compatible(donor_bg: str, recipient_bg: str) -> bool:
    if pd.isna(donor_bg) or pd.isna(recipient_bg):
        return False
    d = normalize_abo(donor_bg)
    r = normalize_abo(recipient_bg)
    return r in ABO_COMPAT.get(d, [])


def distance_meters(coord1, coord2) -> Optional[float]:
    try:
        return geodesic(coord1, coord2).meters
    except Exception:
        return None

# Optional ML model (if you upload a model later)
_model = None
def load_model():
    global _model
    if _model is None:
        if Path(MATCH_MODEL_PATH).exists():
            _model = joblib.load(MATCH_MODEL_PATH)
    return _model

def ml_score(donor_row: Dict[str,Any], request: Dict[str,Any]) -> Optional[float]:
    model = load_model()
    if model is None:
        return None
    # prepare minimal features, ensure names match training pipeline
    df = pd.DataFrame([{
        "donor_blood_group": donor_row.get("blood_group"),
        "recipient_blood_group": request.get("required_blood_group"),
        # add more features if your model expects them
    }])
    try:
        prob = model.predict_proba(df)[0]
        # prefer class 1 probability
        if len(prob) == 2:
            return float(prob[1])
        return float(prob[0])
    except Exception:
        return None

def rank_donors_for_request(req: Dict[str,Any], top_n:int = 10, weights:Dict[str,float] = None) -> List[Dict[str,Any]]:
    """
    req keys: required_blood_group, hospital_id (optional), lat/lon (optional), urgency_level, units_needed

    Scoring:
      - blood_score: 0 or 1 based on ABO rules
      - distance_score: 0..1 (closer => higher), based on ORS driving distance when available,
                        falling back to geodesic distance otherwise
      - ml_score: optional ML probability (0..1) if model uploaded

      total_score = weights["blood"]*blood_score
                  + weights["distance"]*distance_score
                  + weights.get("ml",0.0)*ml_score
    """
    donors_df = load_donors()
    if donors_df is None or donors_df.empty:
        return []

    if weights is None:
        # blood rules high weight, distance secondary
        weights = {"blood":0.7, "distance":0.3, "ml":0.0}

    # Resolve target coordinate from request: prefer lat/lon, else hospital lookup
    target_coord = None
    if req.get("lat") is not None and req.get("lon") is not None:
        try:
            target_coord = (float(req["lat"]), float(req["lon"]))
        except:
            target_coord = None
    elif req.get("hospital_id"):
        hospitals = load_hospitals()
        if hospitals is not None and not hospitals.empty:
            key_col = "hospital_id" if "hospital_id" in hospitals.columns else hospitals.columns[0]
            row = hospitals[hospitals[key_col] == req["hospital_id"]]
            if not row.empty:
                r0 = row.iloc[0]
                if "lat" in r0.index and "lon" in r0.index:
                    try:
                        target_coord = (float(r0["lat"]), float(r0["lon"]))
                    except:
                        target_coord = None

    results = []

    # we will later overwrite distance_m & distance_score using ORS when possible
    ors_dest_coords = []    # list of (lat, lon)
    ors_result_indices = [] # index into results list

    for _, d in donors_df.iterrows():
        donor = d.to_dict()

        avail_raw = str(donor.get("availability", "")).strip().lower()
        if avail_raw in ["no", "not available", "0", "false"]:
            continue

        # ----- blood compatibility -----
        s_blood = 1.0 if abo_compatible(donor.get("blood_group"), req.get("required_blood_group")) else 0.0

        # ----- distance (initial: geodesic fallback) -----
        s_dist = 0.0
        dist_m = None

        if target_coord is not None and not pd.isna(donor.get("lat")) and not pd.isna(donor.get("lon")):
            try:
                donor_coord = (float(donor["lat"]), float(donor["lon"]))
                # straight-line distance as fallback
                dist_m = distance_meters(target_coord, donor_coord)
                if dist_m is not None:
                    km = dist_m / 1000.0
                    s_dist = max(0.0, 1.0 - (km / 200.0))  # within 200km => score 1..0

                    # collect for ORS driving distance refinement
                    ors_dest_coords.append((donor_coord[0], donor_coord[1]))  # (lat, lon)
            except Exception:
                dist_m = None
                s_dist = 0.0

        # ----- ML score (optional) -----
        s_ml = ml_score(donor, req) or 0.0

        # initial combined score (will recompute after ORS if available)
        score = (
            weights["blood"] * s_blood +
            weights["distance"] * s_dist +
            weights.get("ml", 0.0) * s_ml
        )

        result_entry = {
            "donor_id": donor.get("donor_id"),
            "name": donor.get("name"),
            "blood_group": donor.get("blood_group"),
            "phone": donor.get("phone"),
            "lat": donor.get("lat"),
            "lon": donor.get("lon"),
            "availability": donor.get("availability"),
            "last_donation_date": donor.get("last_donation_date"),
            "score": float(score),
            "blood_score": float(s_blood),
            "distance_m": dist_m if dist_m is not None else None,
            "distance_score": float(s_dist),
            "ml_score": float(s_ml),
        }

        results.append(result_entry)

        # track which result index corresponds to this ORS candidate
        if target_coord is not None and dist_m is not None:
            ors_result_indices.append(len(results) - 1)

    # ----- refine distance using ORS driving distance if possible -----
    if target_coord is not None and ors_dest_coords:
        try:
            origin_str = f"{target_coord[0]},{target_coord[1]}"
            dest_strs = [f"{lat},{lon}" for (lat, lon) in ors_dest_coords]

            ors_raw = distance_matrix([origin_str], dest_strs, mode="driving")
            dist_mat = ors_raw.get("distances")

            if dist_mat and len(dist_mat) > 0:
                dist_row = dist_mat[0]  # from origin to all points (origin + destinations)

                for i, res_idx in enumerate(ors_result_indices):
                    # ORS matrix: index 0 is origin->origin, so destinations start from index 1
                    d_m = dist_row[i + 1]
                    km = d_m / 1000.0
                    s_dist = max(0.0, 1.0 - (km / 200.0))

                    # update result entry
                    results[res_idx]["distance_m"] = d_m
                    results[res_idx]["distance_score"] = float(s_dist)
                    # recompute final blended score
                    b = results[res_idx]["blood_score"]
                    m = results[res_idx]["ml_score"]
                    results[res_idx]["score"] = (
                        weights["blood"] * b +
                        weights["distance"] * s_dist +
                        weights.get("ml", 0.0) * m
                    )
        except Exception:
            # if ORS fails for some reason, we keep geodesic fallback values
            pass

    # sort descending by score and clip to top_n
    results_sorted = sorted(results, key=lambda x: x["score"], reverse=True)
    return results_sorted[:top_n]


def compute_travel_info(server_url: str, origin: tuple, donors_coords: list):
    url = f"{server_url}/api/google/distance"
    origin_payload = {"lat": origin[0], "lon": origin[1]}
    dests = [{"lat": lat, "lon": lon} for lat, lon in donors_coords]
    r = requests.post(url, json={"origin": origin_payload, "destinations": dests}, timeout=20)
    r.raise_for_status()
    return r.json()["parsed"]  # list with distance_m, duration_s, ...