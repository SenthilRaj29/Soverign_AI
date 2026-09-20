import time
import os
import json
import hashlib
import asyncio
import logging
from typing import Dict, Any, List, Optional
from pydantic import BaseModel

from app.db.database import check_database_connection
from app.db.session import get_db_session_ctx
from app.db.repositories import AuditRepository

logger = logging.getLogger("sovereign.audit")

class AuditEvent(BaseModel):
    event_id: str
    task_id: str
    user_id: str
    timestamp: float
    action: str
    component: str
    details: Dict[str, Any]
    checksum: str

class AuditService:
    def __init__(self, log_dir: str = "e:/Soverign_AI/audit_logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
        self.events: List[AuditEvent] = []

    def _sanitize_details(self, details: Dict[str, Any]) -> Dict[str, Any]:
        """
        Scrub sensitive keys such as passwords, hashes, tokens, or secrets from details dictionary.
        """
        if not isinstance(details, dict):
            return {}
        sanitized = {}
        sensitive_keywords = {
            "password", "password_hash", "token", "access_token", "secret", 
            "authorization", "jwt", "database_password", "current_password", "new_password"
        }
        for k, v in details.items():
            if any(kw in k.lower() for kw in sensitive_keywords):
                sanitized[k] = "[REDACTED_SENSITIVE_DATA]"
            else:
                sanitized[k] = v
        return sanitized

    def record_event(self, task_id: str, user_id: str, action: str, component: str, details: Dict[str, Any]) -> AuditEvent:
        """
        Records audit event with SHA256 payload checksum and sanitized details.
        Appends to local JSONL log file and schedules async PostgreSQL database persistence.
        """
        ts = time.time()
        safe_details = self._sanitize_details(details)
        raw_payload = f"{task_id}:{user_id}:{action}:{component}:{ts}:{json.dumps(safe_details, sort_keys=True)}"
        checksum = hashlib.sha256(raw_payload.encode('utf-8')).hexdigest()
        event_id = f"aud_{checksum[:12]}"

        event = AuditEvent(
            event_id=event_id,
            task_id=task_id,
            user_id=user_id,
            timestamp=ts,
            action=action,
            component=component,
            details=safe_details,
            checksum=checksum
        )
        self.events.append(event)
        
        # 1. Persist to local JSONL file
        filepath = os.path.join(self.log_dir, f"audit_{task_id}.jsonl")
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(event.model_dump_json() + "\n")
        except Exception as e:
            logger.error(f"Failed to append audit event to JSONL file: {e}")

        # 2. Schedule background task for PostgreSQL persistence if event loop is running
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                loop.create_task(self._persist_to_postgres(event))
        except RuntimeError:
            pass

        return event

    async def _persist_to_postgres(self, event: AuditEvent):
        """Asynchronously persists audit event to PostgreSQL database."""
        try:
            async with get_db_session_ctx() as db:
                await AuditRepository.record_event(
                    db=db,
                    event_id=event.event_id,
                    task_id=event.task_id,
                    user_id=event.user_id,
                    timestamp=event.timestamp,
                    action=event.action,
                    component=event.component,
                    details=event.details,
                    checksum=event.checksum
                )
        except Exception as e:
            logger.warning(f"Background PostgreSQL audit persistence skipped: {e}")

    def get_task_audit_trail(self, task_id: str) -> List[Dict[str, Any]]:
        filepath = os.path.join(self.log_dir, f"audit_{task_id}.jsonl")
        if not os.path.exists(filepath):
            return [e.model_dump() for e in self.events if e.task_id == task_id]

        records = []
        with open(filepath, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    records.append(json.loads(line))
        return records
