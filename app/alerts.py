# app/alerts.py
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


def build_alert_message(request_data: Dict[str, Any], best_match: Dict[str, Any]) -> str:
    """
    Create a human-readable alert message for a critical match.
    """
    bg = request_data.get("required_blood_group")
    units = request_data.get("units_needed", 1)
    urgency = request_data.get("urgency_level", "unknown")

    name = best_match.get("name")
    donor_bg = best_match.get("blood_group")
    phone = best_match.get("phone")
    dist_km = (
        f"{(best_match['distance_m'] / 1000):.1f} km"
        if best_match.get("distance_m") is not None
        else "N/A"
    )

    msg = (
        f"URGENT BLOOD REQUEST\n"
        f"Required blood group: {bg}, Units: {units}, Urgency: {urgency}\n"
        f"Best donor: {name} ({donor_bg}), Phone: {phone}, Approx distance: {dist_km}"
    )
    return msg


def trigger_match_alert(request_data: Dict[str, Any], matches: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    """
    Decide whether to trigger an alert based on request + matches.
    Returns a dict describing the alert (for API response) or None if no alert.
    """

    # Case 1: No matches
    if not matches:
        urgency = str(request_data.get("urgency_level", "")).lower()
        if urgency in ["high", "critical"]:
            msg = (
                f"CRITICAL: No donors found for blood group "
                f"{request_data.get('required_blood_group')} "
                f"with urgency={urgency} and units={request_data.get('units_needed', 1)}."
            )
            logger.warning(msg)
            return {
                "type": "no_match",
                "level": "critical",
                "message": msg,
            }
        return None

    # Case 2: We have at least one match
    best = matches[0]
    urgency = str(request_data.get("urgency_level", "")).lower()

    dist_m = best.get("distance_m")
    trigger = False
    reason = []

    # Condition 1: urgency is high/critical
    if urgency in ["high", "critical"]:
        trigger = True
        reason.append("high_urgency")

    # Condition 2: best donor is within 10 km
    if dist_m is not None and dist_m <= 10_000:
        trigger = True
        reason.append("nearby_donor")

    if not trigger:
        return None

    alert_message = build_alert_message(request_data, best)
    logger.info(f"[ALERT] {alert_message}")

    return {
        "type": "match",
        "level": "critical" if urgency in ["high", "critical"] else "info",
        "reason": reason,
        "best_donor_id": best.get("donor_id"),
        "best_donor_name": best.get("name"),
        "best_donor_phone": best.get("phone"),
        "distance_m": dist_m,
        "message": alert_message,
    }
