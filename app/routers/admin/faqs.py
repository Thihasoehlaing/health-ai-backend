from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.pg import get_db
from app.security.deps import require_admin_token
from app.models.faq import Faq
from app.schemas.faq import FaqCreate, FaqUpdate, FaqOut

router = APIRouter(prefix="/admin/faqs", tags=["admin-faqs"])


@router.get("/", response_model=list[FaqOut], dependencies=[Depends(require_admin_token)])
def list_faqs(
    db: Session = Depends(get_db),
    q: str | None = Query(None, description="Search by intent_key or question"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    include_inactive: bool = Query(False, description="Include inactive FAQs"),
):
    query = db.query(Faq)
    if not include_inactive:
        query = query.filter(Faq.is_active.is_(True))
    if q:
        like = f"%{q.lower()}%"
        query = query.filter(
            func.lower(Faq.intent_key).like(like) | func.lower(Faq.question).like(like)
        )
    rows = query.order_by(Faq.intent_key).limit(limit).offset(offset).all()
    return rows


@router.get("/{faq_id}", response_model=FaqOut, dependencies=[Depends(require_admin_token)])
def get_faq(faq_id: UUID, db: Session = Depends(get_db)):
    row = db.get(Faq, faq_id)
    if not row:
        raise HTTPException(status_code=404, detail="FAQ not found")
    return row


@router.post("/", response_model=FaqOut, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_admin_token)])
def create_faq(payload: FaqCreate, db: Session = Depends(get_db)):
    # enforce unique intent_key (case-insensitive)
    dup = db.query(Faq).filter(func.lower(Faq.intent_key) == payload.intent_key.lower()).first()
    if dup:
        raise HTTPException(status_code=409, detail="intent_key already exists")
    row = Faq(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.patch("/{faq_id}", response_model=FaqOut, dependencies=[Depends(require_admin_token)])
def update_faq(faq_id: UUID, payload: FaqUpdate, db: Session = Depends(get_db)):
    row = db.get(Faq, faq_id)
    if not row:
        raise HTTPException(status_code=404, detail="FAQ not found")

    # if changing intent_key, enforce uniqueness
    if payload.intent_key and payload.intent_key.lower() != row.intent_key.lower():
        dup = db.query(Faq).filter(func.lower(Faq.intent_key) == payload.intent_key.lower()).first()
        if dup and dup.id != faq_id:
            raise HTTPException(status_code=409, detail="intent_key already exists")

    for k, v in payload.model_dump(exclude_unset=True).items():
        setattr(row, k, v)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{faq_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(require_admin_token)])
def delete_faq(faq_id: UUID, db: Session = Depends(get_db)):
    row = db.get(Faq, faq_id)
    if not row:
        raise HTTPException(status_code=404, detail="FAQ not found")
    db.delete(row)
    db.commit()
    return None
