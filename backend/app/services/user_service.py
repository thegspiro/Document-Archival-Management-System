"""User management service — CRUD, role assignment, and listing."""

from fastapi import HTTPException, status
from passlib.hash import bcrypt
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import Role, User, UserRole
from app.services.audit_service import AuditService


class UserService:
    """Business logic for user accounts and role assignments."""

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------

    @staticmethod
    async def create_user(
        db: AsyncSession,
        *,
        email: str,
        password: str,
        display_name: str,
        is_active: bool = True,
        is_superadmin: bool = False,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> User:
        """Create a new user with a bcrypt-hashed password.

        Raises 409 if the email is already taken.
        """
        existing = await db.execute(select(User).where(User.email == email))
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"A user with email '{email}' already exists",
            )

        user = User(
            email=email,
            password_hash=bcrypt.hash(password),
            display_name=display_name,
            is_active=is_active,
            is_superadmin=is_superadmin,
        )
        db.add(user)
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="user.create",
            resource_type="user",
            resource_id=user.id,
            detail={"email": email, "display_name": display_name},
            ip_address=ip_address,
        )
        return user

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    @staticmethod
    async def get_user(db: AsyncSession, *, user_id: int) -> User:
        """Return a single user by ID, or raise 404."""
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
        return user

    @staticmethod
    async def list_users(
        db: AsyncSession,
        *,
        page: int = 1,
        per_page: int = 25,
    ) -> dict:
        """Return a paginated list of users.

        Returns a dict compatible with ``PaginatedResponse``.
        """
        count_result = await db.execute(select(func.count(User.id)))
        total = count_result.scalar_one()

        offset = (page - 1) * per_page
        result = await db.execute(
            select(User).order_by(User.id).offset(offset).limit(per_page)
        )
        items = list(result.scalars().all())

        pages = (total + per_page - 1) // per_page if per_page else 0
        return {"items": items, "total": total, "page": page, "per_page": per_page, "pages": pages}

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    @staticmethod
    async def update_user(
        db: AsyncSession,
        *,
        user_id: int,
        data: dict,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> User:
        """Patch mutable user fields.  Hashes password if included."""
        user = await UserService.get_user(db, user_id=user_id)

        allowed_fields = {"email", "display_name", "is_active", "is_superadmin", "password"}
        changes: dict = {}
        for key, value in data.items():
            if key not in allowed_fields:
                continue
            if key == "password":
                user.password_hash = bcrypt.hash(value)
                changes["password"] = "***"
            else:
                setattr(user, key, value)
                changes[key] = value

        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="user.update",
            resource_type="user",
            resource_id=user.id,
            detail=changes,
            ip_address=ip_address,
        )
        return user

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    @staticmethod
    async def delete_user(
        db: AsyncSession,
        *,
        user_id: int,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Soft-delete a user by setting ``is_active = False``."""
        user = await UserService.get_user(db, user_id=user_id)
        user.is_active = False
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="user.delete",
            resource_type="user",
            resource_id=user.id,
            detail={"email": user.email},
            ip_address=ip_address,
        )

    # ------------------------------------------------------------------
    # Roles
    # ------------------------------------------------------------------

    @staticmethod
    async def assign_role(
        db: AsyncSession,
        *,
        user_id: int,
        role_name: str,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> UserRole:
        """Assign a role to a user.  Raises 404 if the role does not exist
        and 409 if the user already holds that role.
        """
        user = await UserService.get_user(db, user_id=user_id)

        result = await db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found",
            )

        existing = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role_id == role.id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User already has role '{role_name}'",
            )

        user_role = UserRole(user_id=user.id, role_id=role.id)
        db.add(user_role)
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="user.assign_role",
            resource_type="user",
            resource_id=user.id,
            detail={"role": role_name},
            ip_address=ip_address,
        )
        return user_role

    @staticmethod
    async def remove_role(
        db: AsyncSession,
        *,
        user_id: int,
        role_name: str,
        acting_user_id: int | None = None,
        ip_address: str | None = None,
    ) -> None:
        """Remove a role from a user."""
        result = await db.execute(select(Role).where(Role.name == role_name))
        role = result.scalar_one_or_none()
        if role is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Role '{role_name}' not found",
            )

        await db.execute(
            delete(UserRole).where(
                UserRole.user_id == user_id,
                UserRole.role_id == role.id,
            )
        )
        await db.flush()

        await AuditService.log(
            db,
            user_id=acting_user_id,
            action="user.remove_role",
            resource_type="user",
            resource_id=user_id,
            detail={"role": role_name},
            ip_address=ip_address,
        )

    @staticmethod
    async def get_user_roles(db: AsyncSession, *, user_id: int) -> list[str]:
        """Return the list of role names held by a user."""
        user = await UserService.get_user(db, user_id=user_id)
        return [ur.role.name for ur in user.user_roles]
