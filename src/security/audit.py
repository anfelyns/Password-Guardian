# -*- coding: utf-8 -*-
"""Audit log helper.

Centralizes security-relevant event logging so the app can show an
"Audit Logs" view.
"""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from database.engine import SessionLocal
from database.models import ActivityLog


def log_action(
    user_id: int,
    action: str,
    details: Optional[str] = None,
    ip_address: Optional[str] = None,
) -> None:
    try:
        with SessionLocal() as s:
            s.add(
                ActivityLog(
                    user_id=user_id,
                    action=action,
                    details=details,
                    ip_address=ip_address,
                    created_at=datetime.utcnow(),
                )
            )
            s.commit()
    except Exception:
        # Audit logging should never crash the app
        return
