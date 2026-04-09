"""Unit tests for PermissionService — superadmin bypass, user-specific permissions,
role-based permissions, parent node inheritance, and global role defaults."""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import HTTPException

from app.services.permission_service import (
    ACTION_COLUMNS,
    ROLE_DEFAULTS,
    PermissionService,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_mock_user(
    *,
    user_id: int = 1,
    is_superadmin: bool = False,
    roles: list[str] | None = None,
) -> MagicMock:
    """Build a mock User with user_roles populated."""
    user = MagicMock()
    user.id = user_id
    user.is_superadmin = is_superadmin
    user.user_roles = []

    for role_name in (roles or []):
        mock_ur = MagicMock()
        mock_ur.role = MagicMock()
        mock_ur.role.name = role_name
        mock_ur.role_id = hash(role_name) % 1000
        user.user_roles.append(mock_ur)

    return user


def _make_mock_permission(*, action: str, granted: bool) -> MagicMock:
    """Build a mock CollectionPermission row with the given action granted/denied."""
    perm = MagicMock()
    for col in ACTION_COLUMNS:
        setattr(perm, col, col == action and granted)
    return perm


# ---------------------------------------------------------------------------
# ROLE_DEFAULTS data integrity
# ---------------------------------------------------------------------------


class TestRoleDefaults:
    """Verify the global role defaults map is complete and consistent."""

    def test_all_expected_roles_present(self) -> None:
        expected = {"superadmin", "admin", "archivist", "contributor", "intern", "viewer"}
        assert set(ROLE_DEFAULTS.keys()) == expected

    @pytest.mark.parametrize("role", ["superadmin", "admin"])
    def test_admin_roles_have_all_permissions(self, role: str) -> None:
        for action in ACTION_COLUMNS:
            assert ROLE_DEFAULTS[role][action] is True

    def test_viewer_can_only_view(self) -> None:
        viewer = ROLE_DEFAULTS["viewer"]
        assert viewer["can_view"] is True
        assert viewer["can_create"] is False
        assert viewer["can_edit"] is False
        assert viewer["can_delete"] is False
        assert viewer["can_manage_permissions"] is False

    def test_archivist_cannot_delete(self) -> None:
        assert ROLE_DEFAULTS["archivist"]["can_delete"] is False

    def test_contributor_cannot_delete_or_manage_perms(self) -> None:
        c = ROLE_DEFAULTS["contributor"]
        assert c["can_delete"] is False
        assert c["can_manage_permissions"] is False

    def test_intern_limited_permissions(self) -> None:
        i = ROLE_DEFAULTS["intern"]
        assert i["can_view"] is True
        assert i["can_create"] is True
        assert i["can_edit"] is False
        assert i["can_delete"] is False


# ---------------------------------------------------------------------------
# Superadmin bypass
# ---------------------------------------------------------------------------


class TestSuperadminBypass:
    """Superadmin should have all permissions everywhere."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize("action", ACTION_COLUMNS)
    async def test_superadmin_can_do_everything(self, action: str) -> None:
        user = _make_mock_user(is_superadmin=True)
        db = AsyncMock()
        result = await PermissionService.check_permission(
            db, user=user, node_id=42, action=action
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_superadmin_with_no_node(self) -> None:
        user = _make_mock_user(is_superadmin=True)
        db = AsyncMock()
        result = await PermissionService.check_permission(
            db, user=user, node_id=None, action="can_delete"
        )
        assert result is True


# ---------------------------------------------------------------------------
# Invalid action
# ---------------------------------------------------------------------------


class TestInvalidAction:
    """An unknown action should always return False."""

    @pytest.mark.asyncio
    async def test_invalid_action_returns_false(self) -> None:
        user = _make_mock_user(roles=["admin"])
        db = AsyncMock()
        result = await PermissionService.check_permission(
            db, user=user, node_id=1, action="can_fly"
        )
        assert result is False


# ---------------------------------------------------------------------------
# Global role defaults (no node)
# ---------------------------------------------------------------------------


class TestGlobalRoleDefaults:
    """When node_id is None, fall back to global role defaults."""

    @pytest.mark.asyncio
    async def test_viewer_global_can_view(self) -> None:
        user = _make_mock_user(roles=["viewer"])
        db = AsyncMock()
        assert await PermissionService.check_permission(
            db, user=user, node_id=None, action="can_view"
        ) is True

    @pytest.mark.asyncio
    async def test_viewer_global_cannot_create(self) -> None:
        user = _make_mock_user(roles=["viewer"])
        db = AsyncMock()
        assert await PermissionService.check_permission(
            db, user=user, node_id=None, action="can_create"
        ) is False

    @pytest.mark.asyncio
    async def test_archivist_global_can_create(self) -> None:
        user = _make_mock_user(roles=["archivist"])
        db = AsyncMock()
        assert await PermissionService.check_permission(
            db, user=user, node_id=None, action="can_create"
        ) is True

    @pytest.mark.asyncio
    async def test_archivist_global_cannot_delete(self) -> None:
        user = _make_mock_user(roles=["archivist"])
        db = AsyncMock()
        assert await PermissionService.check_permission(
            db, user=user, node_id=None, action="can_delete"
        ) is False

    @pytest.mark.asyncio
    async def test_multiple_roles_most_permissive_wins(self) -> None:
        """A user with both viewer and archivist roles gets archivist's create."""
        user = _make_mock_user(roles=["viewer", "archivist"])
        db = AsyncMock()
        assert await PermissionService.check_permission(
            db, user=user, node_id=None, action="can_create"
        ) is True

    @pytest.mark.asyncio
    async def test_no_roles_no_permissions(self) -> None:
        user = _make_mock_user(roles=[])
        db = AsyncMock()
        assert await PermissionService.check_permission(
            db, user=user, node_id=None, action="can_view"
        ) is False


# ---------------------------------------------------------------------------
# User-specific permission on node
# ---------------------------------------------------------------------------


class TestUserSpecificPermission:
    """User-specific collection permissions override role-based defaults."""

    @pytest.mark.asyncio
    async def test_user_perm_grants_access(self) -> None:
        user = _make_mock_user(user_id=10, roles=["viewer"])
        user_perm = _make_mock_permission(action="can_edit", granted=True)

        # First call: user-specific permission query returns the permission
        user_perm_result = MagicMock()
        user_perm_result.scalar_one_or_none.return_value = user_perm

        db = AsyncMock()
        db.execute.return_value = user_perm_result

        result = await PermissionService.check_permission(
            db, user=user, node_id=5, action="can_edit"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_user_perm_denies_access(self) -> None:
        user = _make_mock_user(user_id=10, roles=["admin"])
        user_perm = _make_mock_permission(action="can_delete", granted=False)

        user_perm_result = MagicMock()
        user_perm_result.scalar_one_or_none.return_value = user_perm

        db = AsyncMock()
        db.execute.return_value = user_perm_result

        result = await PermissionService.check_permission(
            db, user=user, node_id=5, action="can_delete"
        )
        assert result is False


# ---------------------------------------------------------------------------
# Role-based permission on node
# ---------------------------------------------------------------------------


class TestRoleBasedPermission:
    """Role-based collection permissions are checked when no user-specific perm exists."""

    @pytest.mark.asyncio
    async def test_role_perm_grants_access(self) -> None:
        user = _make_mock_user(user_id=10, roles=["intern"])
        role_perm = _make_mock_permission(action="can_edit", granted=True)

        # First call: user-specific query returns None
        user_perm_result = MagicMock()
        user_perm_result.scalar_one_or_none.return_value = None

        # Second call: role-based query returns a list with one perm
        role_perm_result = MagicMock()
        role_perm_result.scalars.return_value.all.return_value = [role_perm]

        db = AsyncMock()
        db.execute.side_effect = [user_perm_result, role_perm_result]

        result = await PermissionService.check_permission(
            db, user=user, node_id=5, action="can_edit"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_multiple_role_perms_most_permissive(self) -> None:
        user = _make_mock_user(user_id=10, roles=["intern", "viewer"])
        perm1 = _make_mock_permission(action="can_edit", granted=False)
        perm2 = _make_mock_permission(action="can_edit", granted=True)

        user_perm_result = MagicMock()
        user_perm_result.scalar_one_or_none.return_value = None

        role_perm_result = MagicMock()
        role_perm_result.scalars.return_value.all.return_value = [perm1, perm2]

        db = AsyncMock()
        db.execute.side_effect = [user_perm_result, role_perm_result]

        result = await PermissionService.check_permission(
            db, user=user, node_id=5, action="can_edit"
        )
        assert result is True


# ---------------------------------------------------------------------------
# Parent node inheritance
# ---------------------------------------------------------------------------


class TestParentNodeInheritance:
    """Permissions walk up the arrangement tree when no direct match is found."""

    @pytest.mark.asyncio
    async def test_inherits_from_parent(self) -> None:
        user = _make_mock_user(user_id=10, roles=["viewer"])

        # Node 5: no user perm, no role perm
        user_perm_result_5 = MagicMock()
        user_perm_result_5.scalar_one_or_none.return_value = None
        role_perm_result_5 = MagicMock()
        role_perm_result_5.scalars.return_value.all.return_value = []
        # Node 5's parent is node 2
        parent_result_5 = MagicMock()
        parent_result_5.one_or_none.return_value = (2,)

        # Node 2: user perm grants can_edit
        parent_user_perm = _make_mock_permission(action="can_edit", granted=True)
        user_perm_result_2 = MagicMock()
        user_perm_result_2.scalar_one_or_none.return_value = parent_user_perm

        db = AsyncMock()
        db.execute.side_effect = [
            user_perm_result_5,    # user perm on node 5
            role_perm_result_5,    # role perm on node 5
            parent_result_5,       # get parent_id of node 5
            user_perm_result_2,    # user perm on node 2 (parent)
        ]

        result = await PermissionService.check_permission(
            db, user=user, node_id=5, action="can_edit"
        )
        assert result is True

    @pytest.mark.asyncio
    async def test_falls_through_to_global_default(self) -> None:
        """When no node or parent has a permission, fall back to global role default."""
        user = _make_mock_user(user_id=10, roles=["archivist"])

        # Node 5: no user perm, no role perm
        user_perm_result = MagicMock()
        user_perm_result.scalar_one_or_none.return_value = None
        role_perm_result = MagicMock()
        role_perm_result.scalars.return_value.all.return_value = []
        # Node 5 has no parent
        parent_result = MagicMock()
        parent_result.one_or_none.return_value = None

        db = AsyncMock()
        db.execute.side_effect = [
            user_perm_result,
            role_perm_result,
            parent_result,
        ]

        # Archivist default for can_create is True
        result = await PermissionService.check_permission(
            db, user=user, node_id=5, action="can_create"
        )
        assert result is True


# ---------------------------------------------------------------------------
# require_permission
# ---------------------------------------------------------------------------


class TestRequirePermission:
    """Test the require_permission method raises 403 when not permitted."""

    @pytest.mark.asyncio
    async def test_require_permission_passes(self) -> None:
        user = _make_mock_user(is_superadmin=True)
        db = AsyncMock()
        # Should not raise
        await PermissionService.require_permission(
            db, user=user, node_id=1, action="can_delete"
        )

    @pytest.mark.asyncio
    async def test_require_permission_raises_403(self) -> None:
        user = _make_mock_user(roles=["viewer"])
        db = AsyncMock()

        with pytest.raises(HTTPException) as exc_info:
            await PermissionService.require_permission(
                db, user=user, node_id=None, action="can_create"
            )
        assert exc_info.value.status_code == 403
        assert "Insufficient permissions" in exc_info.value.detail


# ---------------------------------------------------------------------------
# _global_default helper
# ---------------------------------------------------------------------------


class TestGlobalDefaultHelper:
    """Verify the _global_default static method."""

    def test_single_role(self) -> None:
        assert PermissionService._global_default({"viewer"}, "can_view") is True
        assert PermissionService._global_default({"viewer"}, "can_create") is False

    def test_multiple_roles_most_permissive(self) -> None:
        assert PermissionService._global_default({"viewer", "admin"}, "can_delete") is True

    def test_unknown_role(self) -> None:
        assert PermissionService._global_default({"unknown_role"}, "can_view") is False

    def test_empty_roles(self) -> None:
        assert PermissionService._global_default(set(), "can_view") is False
