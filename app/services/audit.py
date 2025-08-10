from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog

def log_action(db: Session, actor_type: str, action: str, actor_id=None, meta_json: str | None = None):
    db.add(AuditLog(actor_type=actor_type, actor_id=actor_id, action=action, meta_json=meta_json))
    db.commit()
