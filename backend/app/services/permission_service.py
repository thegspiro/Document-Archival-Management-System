"""Permission service — centralised permission resolution for all access checks.

Permission resolution order (highest priority wins):
1. Superadmin — all permissions everywhere
2. User-specific permission on the node
3. Role-based permission on the node
4. Inherited permission from parent node (walk up tree)
5. Global role default (no collection-specific grant)
"""

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.arrangement import ArrangementNode
from app.models.collection_permission import CollectionPermission
from app.models.user import User

# Maps global role names to their default action ceilings.
# These defaults are the floor; collection_permissions can elevate within
# the ceiling but never beyond the user's highest global role capability.
ROLE_DEFAULTS: dict[str, dict[str, bool]] = {
    "superadmin": {
        "can_view": True,
        "can_create": True,
        "can_edit": True,
        "can_delete": True,
        "can_manage_permissions": True,
    },
    "admin": {
        "can_view": True,
        "can_create": True,
        "can_edit": True,
        "can_delete": True,
        "can_manage_permissions": True,
    },
    "archivist": {
        "can_view": True,
        "can_create": True,
        "can_edit": True,
        "can_delete": False,
        "can_manage_permissions": False,
    },
    "contributor": {
        "can_view": True,
        "can_create": True,
        "can_edit": True,
        "can_delete": False,
        "can_manage_permissions": False,
    },
    "intern": {
        "can_view": True,
        "can_create": True,
        "can_edit": False,
        "can_delete": False,
        "can_manage_permissions": False,
    },
    "viewer": {
        "can_view": True,
        "can_create": False,
        "can_edit": False,
        "can_delete": False,
        "can_manage_permissions": False,
    },
}

# The action column name on ``CollectionPermission`` for each permission flag.
ACTION_COLUMNS = ("can_view", "can_create", "can_edit", "can_delete", "can_manage_permissions")


class PermissionService:
    """All permission checks go through this class.

    Routers must not contain inline permission logic.
    """

    @staticmethod
    async def check_permission(
        db: AsyncSession,
        *,
        user: User,
        node_id: int | None,
        action: str,
    ) -> bool:
        """Check whether *user* may perform *action* on the arrangement node
        identified by *node_id*.

        Parameters
        ----------
        action:
            One of ``'can_view'``, ``'can_create'``, ``'can_edit'``,
            ``'can_delete'``, ``'can_manage_permissions'``.
        node_id:
            The arrangement node to check.  ``None`` means a global-level
            action not scoped to a specific collection.

        Returns ``True`` if the action is permitted.
        """
        if action not in ACTION_COLUMNS:
            return False

        # 1. Superadmin bypass
        if user.is_superadmin:
            return True

        user_role_names = {ur.role.name for ur in user.user_roles}

        # If there is no specific node, fall back to global role defaults.
        if node_id is None:
            return PermissionService._global_default(user_role_names, action)

        # 2 & 3. Walk up the node tree looking for matching permissions.
        current_node_id: int | None = node_id
        user_role_ids = [ur.role_id for ur in user.user_roles]

        while current_node_id is not None:
            # 2. User-specific permission on this node
            result = await db.execute(
                select(CollectionPermission).where(
                    CollectionPermission.arrangement_node_id == current_node_id,
                    CollectionPermission.user_id == user.id,
                )
            )
            user_perm = result.scalar_one_or_none()
            if user_perm is not None:
                return bool(getattr(user_perm, action, False))

            # 3. Role-based permission on this node (take the most permissive)
            if user_role_ids:
                result = await db.execute(
                    select(CollectionPermission).where(
                        CollectionPermission.arrangement_node_id == current_node_id,
                        CollectionPermission.role_id.in_(user_role_ids),
                    )
                )
                role_perms = list(result.scalars().all())
                if role_perms:
                    return any(getattr(p, action, False) for p in role_perms)

            # 4. Walk up to parent node
            node_result = await db.execute(
                select(ArrangementNode.parent_id).where(
                    ArrangementNode.id == current_node_id
                )
            )
            row = node_result.one_or_none()
            current_node_id = row[0] if row else None

        # 5. Global role default
        return PermissionService._global_default(user_role_names, action)

    @staticmethod
    def _global_default(role_names: set[str], action: str) -> bool:
        """Compute the most permissive global default across the user's roles."""
        for rname in role_names:
            defaults = ROLE_DEFAULTS.get(rname, {})
            if defaults.get(action, False):
                return True
        return False

    @staticmethod
    async def require_permission(
        db: AsyncSession,
        *,
        user: User,
        node_id: int | None,
        action: str,
    ) -> None:
        """Raise ``HTTPException(403)`` if the permission check fails."""
        from fastapi import HTTPException, status

        allowed = await PermissionService.check_permission(
            db, user=user, node_id=node_id, action=action
        )
        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
