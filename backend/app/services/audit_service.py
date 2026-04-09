"""Audit logging service — writes immutable audit_log rows for all CUD operations."""

from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLog


class AuditService:
    """Centralised audit trail writer.

    Every create, update, delete, and permission change operation in the
    application must call ``AuditService.log`` so that the audit trail is
    complete and immutable.
    """

    @staticmethod
    async def log(
        db: AsyncSession,
        *,
        user_id: int | None,
        action: str,
        resource_type: str | None = None,
        resource_id: int | None = None,
        detail: dict[str, Any] | None = None,
        ip_address: str | None = None,
    ) -> AuditLog:
        """Write a single immutable audit log row.

        Parameters
        ----------
        db:
            Active async database session.
        user_id:
            The acting user.  ``None`` for system-initiated actions.
        action:
            Dot-notation action string, e.g. ``'document.create'``.
        resource_type:
            The entity type affected, e.g. ``'document'``, ``'user'``.
        resource_id:
            Primary key of the affected resource.
        detail:
            Arbitrary JSON-serialisable context about the operation.
        ip_address:
            Client IP address from the request.
        """
        entry = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            detail=detail,
            ip_address=ip_address,
        )
        db.add(entry)
        await db.flush()
        return entry
