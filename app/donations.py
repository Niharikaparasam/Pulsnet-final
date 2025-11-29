# app/donations.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from typing import Optional, List
import sqlite3
from app.config import DB_PATH
from app.auth import get_current_user  # reuse auth's current_user

router = APIRouter(prefix="/api/donations", tags=["donations"])


# ---------- DB helpers ----------

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_donors_table():
    # DB_PATH already points to data/users.db
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS user_donors (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            donor_id TEXT UNIQUE,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT,
            blood_group TEXT,
            lat REAL,
            lon REAL,
            address TEXT,
            availability TEXT DEFAULT 'yes',
            last_donation_date TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.commit()
    conn.close()


# run table creation at import
init_donors_table()


# ---------- Schemas ----------

class DonorRegister(BaseModel):
    address: Optional[str] = Field(None, description="Human readable location")
    lat: Optional[float] = Field(None, description="Latitude of donor")
    lon: Optional[float] = Field(None, description="Longitude of donor")
    availability: str = Field("yes", description="yes/no/temporary_unavailable")
    last_donation_date: Optional[str] = Field(
        None, description="YYYY-MM-DD (optional)"
    )
    phone: Optional[str] = None
    notes: Optional[str] = None


class DonorProfile(BaseModel):
    donor_id: str
    full_name: str
    email: str
    phone: Optional[str]
    blood_group: Optional[str]
    lat: Optional[float]
    lon: Optional[float]
    address: Optional[str]
    availability: str
    last_donation_date: Optional[str]
    notes: Optional[str]


# ---------- Internal helpers ----------

def row_to_profile(row: sqlite3.Row) -> DonorProfile:
    return DonorProfile(
        donor_id=row["donor_id"],
        full_name=row["full_name"],
        email=row["email"],
        phone=row["phone"],
        blood_group=row["blood_group"],
        lat=row["lat"],
        lon=row["lon"],
        address=row["address"],
        availability=row["availability"],
        last_donation_date=row["last_donation_date"],
        notes=row["notes"],
    )


def get_donor_for_user(user_id: int) -> Optional[sqlite3.Row]:
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_donors WHERE user_id = ?", (user_id,))
    row = cur.fetchone()
    conn.close()
    return row


# ---------- Routes ----------

@router.post("/register", response_model=DonorProfile)
def register_donor(
    data: DonorRegister,
    current_user=Depends(get_current_user),
):
    """
    Register or update the current logged-in user as a donor.
    Creates/updates a record in user_donors with donor_id like 'U<user_id>'.
    """
    user_id = current_user["id"]
    full_name = current_user["full_name"]
    email = current_user["email"]
    user_phone = current_user["phone"]
    user_bg = current_user["blood_group"]

    phone = data.phone or user_phone
    donor_id = f"U{user_id}"

    existing = get_donor_for_user(user_id)
    conn = get_db()
    cur = conn.cursor()

    if existing:
        # UPDATE
        cur.execute(
            """
            UPDATE user_donors
            SET donor_id = ?,
                full_name = ?,
                email = ?,
                phone = ?,
                blood_group = ?,
                lat = ?,
                lon = ?,
                address = ?,
                availability = ?,
                last_donation_date = ?,
                notes = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
            """,
            (
                donor_id,
                full_name,
                email,
                phone,
                user_bg,
                data.lat,
                data.lon,
                data.address,
                data.availability,
                data.last_donation_date,
                data.notes,
                user_id,
            ),
        )
    else:
        # INSERT
        cur.execute(
            """
            INSERT INTO user_donors (
                user_id, donor_id, full_name, email, phone, blood_group,
                lat, lon, address, availability, last_donation_date, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                user_id,
                donor_id,
                full_name,
                email,
                phone,
                user_bg,
                data.lat,
                data.lon,
                data.address,
                data.availability,
                data.last_donation_date,
                data.notes,
            ),
        )

    conn.commit()
    conn.close()

    row = get_donor_for_user(user_id)
    return row_to_profile(row)


@router.get("/me", response_model=DonorProfile)
def my_donor_profile(current_user=Depends(get_current_user)):
    """
    Get current user's donor profile.
    """
    row = get_donor_for_user(current_user["id"])
    if not row:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="You are not registered as a donor yet.",
        )
    return row_to_profile(row)


@router.get("/all", response_model=List[DonorProfile])
def list_all_user_donors(current_user=Depends(get_current_user)):
    """
    List all user donors (for admin/demo). Can be restricted later.
    """
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM user_donors")
    rows = cur.fetchall()
    conn.close()
    return [row_to_profile(r) for r in rows]
