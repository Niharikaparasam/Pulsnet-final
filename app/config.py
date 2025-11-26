# app/config.py
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# Default paths (these will be used if you copy your uploaded files into data/)
DONORS_CSV = DATA_DIR / "donors.csv"
REQUESTS_CSV = DATA_DIR / "requests.csv"
HOSPITALS_CSV = DATA_DIR / "hospitals.csv"

# If you already uploaded to /mnt/data, these are the expected uploaded file paths:
UPLOADED_DONORS = Path(r"C:\Users\Niharika PM\OneDrive\Desktop\projects\Pulsenet\Backend\data\donors.csv")
UPLOADED_REQUESTS = Path(r"C:\Users\Niharika PM\OneDrive\Desktop\projects\Pulsenet\Backend\data\requests.csv")
UPLOADED_HOSPITALS = Path(r"C:\Users\Niharika PM\OneDrive\Desktop\projects\Pulsenet\Backend\data\hospitals.csv")

# Optional ML model path
MATCH_MODEL_PATH = MODELS_DIR / "blood_match_model.joblib"
