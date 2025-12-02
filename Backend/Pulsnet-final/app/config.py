# app/config.py
from pathlib import Path

# Base directories
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)
MODELS_DIR = BASE_DIR / "models"
MODELS_DIR.mkdir(exist_ok=True)

# CSV data paths
DONORS_CSV = DATA_DIR / "donors.csv"
REQUESTS_CSV = DATA_DIR / "requests.csv"
HOSPITALS_CSV = DATA_DIR / "hospitals.csv"

# Uploaded file paths (you already had these – keep / adjust as per your system)
UPLOADED_DONORS = Path(
    r"C:\Users\Niharika PM\OneDrive\Desktop\projects\Pulsenet\Backend\data\donors.csv"
)
UPLOADED_REQUESTS = Path(
    r"C:\Users\Niharika PM\OneDrive\Desktop\projects\Pulsenet\Backend\data\requests.csv"
)
UPLOADED_HOSPITALS = Path(
    r"C:\Users\Niharika PM\OneDrive\Desktop\projects\Pulsenet\Backend\data\hospitals.csv"
)

# Optional ML model path
MATCH_MODEL_PATH = MODELS_DIR / "blood_match_model.joblib"

# 🔹 AUTH / DATABASE CONFIG 🔹

# SQLite DB for users (will be created automatically)
DB_PATH = DATA_DIR / "users.db"
# add near other paths
CHAT_DB_PATH = DATA_DIR / "chat.db"


# JWT settings – for project/demo this is fine; later move to .env
SECRET_KEY = "super-secret-key-change-this-later-1234567890"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60  # token expiry in minutes
