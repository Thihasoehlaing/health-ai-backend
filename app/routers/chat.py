from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Path
from bson import ObjectId
from sqlalchemy.orm import Session
from sqlalchemy import or_, func

from app.db.mongo import get_mongo
from app.db.pg import get_db
from app.services.nlu import detect_intent
from app.schemas.chat import StartSessionRequest, AddMessageRequest
from app.models.appointment import Appointment
from app.models.patient import Patient
from app.models.doctor import Doctor

router = APIRouter(prefix="/chat", tags=["chat"])


def _oid(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid sessionId")


def _format_time(dt) -> str:
    # 10 Aug 2025, 10:30
    return dt.astimezone(timezone.utc).strftime("%d %b %Y, %H:%M")


async def _fetch_appointments_by_token(
    db: Session, token: str, upcoming_only: bool = True, limit: int = 5
) -> List[dict]:
    """
    token can be:
      - Patient UUID (internal id)
      - external_patient_id (exact)
      - partial/full name (case-insensitive)
    """
    token = (token or "").strip()
    if not token:
        return []

    # try UUID
    as_uuid = None
    try:
        from uuid import UUID
        as_uuid = UUID(token)
    except Exception:
        pass

    q = (
        db.query(Appointment, Patient, Doctor)
        .join(Patient, Patient.id == Appointment.patient_id)
        .join(Doctor, Doctor.id == Appointment.doctor_id)
    )

    if as_uuid:
        q = q.filter(Patient.id == as_uuid)
    else:
        q = q.filter(
            or_(
                Patient.external_patient_id == token,
                func.lower(Patient.full_name).like(f"%{token.lower()}%"),
            )
        )

    if upcoming_only:
        now = datetime.now(timezone.utc)
        q = q.filter(Appointment.start_time >= now)

    rows = q.order_by(Appointment.start_time.asc()).limit(limit).all()

    items: List[dict] = []
    for (a, p, d) in rows:
        items.append(
            {
                "appointmentId": str(a.id),
                "patientName": p.full_name,
                "doctorName": d.name,
                "departmentId": str(d.department_id),
                "start_time": a.start_time,
                "end_time": a.end_time,
                "status": a.status,
            }
        )
    return items


@router.post("/sessions")
async def start_session(payload: StartSessionRequest, dbm=Depends(get_mongo)):
    now = datetime.now(timezone.utc)
    doc = {
        "deviceId": payload.deviceId,
        "startedAt": now,
        "endedAt": None,
        "channel": payload.channel,
        "status": "active",
        "context": {},
    }
    res = await dbm.chat_sessions.insert_one(doc)
    return {"sessionId": str(res.inserted_id), "startedAt": now}


@router.post("/sessions/{sessionId}/messages")
async def add_message(
    sessionId: str = Path(..., description="Chat session ObjectId string"),
    payload: AddMessageRequest = ...,
    dbm=Depends(get_mongo),
    dbp: Session = Depends(get_db),
):
    sid = _oid(sessionId)

    sess = await dbm.chat_sessions.find_one({"_id": sid})
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.get("status") == "ended":
        raise HTTPException(status_code=409, detail="Session already ended")

    now = datetime.now(timezone.utc)

    # Store user message
    intent = detect_intent(payload.text)
    await dbm.messages.insert_one(
        {
            "sessionId": sid,
            "role": payload.role,
            "text": payload.text,
            "nlu": {"intent": intent},
            "timestamp": now,
        }
    )

    reply: str
    extra: dict = {}

    # --- NEW: real check_appointment intent ---
    if intent == "check_appointment":
        # Priority order for token:
        # 1) existing session patientRef.token
        # 2) if message starts with "id: ..." or "pid: ..."
        token: Optional[str] = None
        pr = (sess or {}).get("patientRef") or {}
        if isinstance(pr, dict):
            token = pr.get("token")

        txt = (payload.text or "").strip()
        lowered = txt.lower()
        if not token and (lowered.startswith("id:") or lowered.startswith("pid:")):
            token = txt.split(":", 1)[1].strip()

        if not token:
            reply = "Please tell me your patient ID or your full name to check appointments. For example: `ID: MRN-12345`."
        else:
            items = await _fetch_appointments_by_token(dbp, token, upcoming_only=True, limit=5)
            extra["items"] = [
                {
                    **it,
                    "start_time": it["start_time"].isoformat(),
                    "end_time": it["end_time"].isoformat() if it["end_time"] else None,
                }
                for it in items
            ]

            if not items:
                reply = "I couldn’t find any upcoming appointments. Would you like me to check past ones?"
            else:
                # Build a short human reply (show up to 3)
                lines = []
                for it in items[:3]:
                    when = _format_time(it["start_time"])
                    lines.append(f"- {when} with Dr. {it['doctorName']} ({it['status']})")
                more = "" if len(items) <= 3 else f" and {len(items)-3} more…"
                reply = "Here are your upcoming appointments:\n" + "\n".join(lines) + more

    # --- Existing sample intents / fallback ---
    elif intent == "ask_directions":
        reply = "Please follow the signs to Wing B, 2nd floor. (Sample)"
    elif intent == "clinic_hours":
        reply = "Hospital is open 24/7. Clinics: 8am–5pm, Mon–Fri. (Sample)"
    else:
        reply = "Sorry, I didn’t catch that. You can ask for directions, clinic hours, or say `Check my appointment`."

    # Store assistant reply
    await dbm.messages.insert_one(
        {
            "sessionId": sid,
            "role": "assistant",
            "text": reply,
            "timestamp": datetime.now(timezone.utc),
            "extra": extra or None,
        }
    )

    # Update session context with last intent
    await dbm.chat_sessions.update_one(
        {"_id": sid},
        {"$set": {"context.intent": intent}}
    )

    # Return reply and any structured items (frontend can render a card/list)
    res = {"reply": reply, "intent": intent}
    if extra:
        res.update(extra)
    return res


@router.patch("/sessions/{sessionId}/attach-patient")
async def attach_patient(
    sessionId: str,
    patientIdOrName: str,
    dbm=Depends(get_mongo),
):
    sid = _oid(sessionId)
    sess = await dbm.chat_sessions.find_one({"_id": sid})
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.get("status") == "ended":
        raise HTTPException(status_code=409, detail="Session already ended")

    await dbm.chat_sessions.update_one(
        {"_id": sid},
        {
            "$set": {
                "patientRef": {
                    "token": patientIdOrName,
                    "attachedAt": datetime.now(timezone.utc),
                }
            }
        },
    )
    return {"ok": True}


@router.post("/sessions/{sessionId}/end")
async def end_session(sessionId: str, dbm=Depends(get_mongo)):
    sid = _oid(sessionId)
    sess = await dbm.chat_sessions.find_one({"_id": sid})
    if not sess:
        raise HTTPException(status_code=404, detail="Session not found")
    if sess.get("status") == "ended":
        return {"ok": True}  # idempotent

    await dbm.chat_sessions.update_one(
        {"_id": sid},
        {"$set": {"status": "ended", "endedAt": datetime.now(timezone.utc)}},
    )
    return {"ok": True}
