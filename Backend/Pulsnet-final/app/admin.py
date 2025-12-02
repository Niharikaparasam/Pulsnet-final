# app/admin.py
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import get_current_user  # assumes this returns sqlite Row with "role" or dict
from app.store import delete_donor_by_id

router = APIRouter(prefix="/api/admin", tags=["admin"])

def require_hospital(user):
    # current_user may be a sqlite Row or dict, handle both
    role = None
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication required")
    try:
        role = user.get("role") if isinstance(user, dict) else user["role"]
    except Exception:
        # fallback to default role if not present
        role = None

    if role != "hospital":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Hospital-only action")

    return True

@router.delete("/donors/{donor_id}")
def admin_delete_donor(donor_id: str, current_user = Depends(get_current_user)):
    # require hospital role
    require_hospital(current_user)
    # after successful delete
    try:
        with open("data/deletes.log","a", encoding="utf-8") as f:
            user_email = current_user.get("email") if isinstance(current_user, dict) else current_user["email"]
            f.write(f"{datetime.utcnow().isoformat()} | {user_email} | deleted donor {donor_id}\n")
    except Exception:
        pass

    ok = delete_donor_by_id(donor_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Donor not found")
    return {"status": "ok", "message": f"Donor {donor_id} deleted"}
