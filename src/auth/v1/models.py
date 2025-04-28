from uuid import uuid4
from datetime import datetime

import sqlalchemy.orm as so
import sqlalchemy as sa

from src.database import Base
from src.auth.v1 import types
from src.sellers.v1.types import SellerId, SellerStaffId


class User(Base):
    __tablename__ = "users"
    __table_args__ = (sa.PrimaryKeyConstraint("id"),)
    role: so.Mapped[types.UserRole] = so.mapped_column(sa.Enum(types.UserRole))
    registered_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
    hashed_password: so.Mapped[str] = so.mapped_column(sa.String(250))
    is_active: so.Mapped[bool] = so.mapped_column(default=False)
    id: so.Mapped[types.UserId] = so.mapped_column(default=lambda: uuid4())


class UserIdentity(Base):
    __tablename__ = "user_identities"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "identity_type",
            "identity_value",
            name="identity_type_identity_value_unique",
        ),
    )
    id: so.Mapped[types.UserIdentityId] = so.mapped_column(autoincrement=True)
    identity_type: so.Mapped[types.IdentityType] = so.mapped_column(
        sa.Enum(types.IdentityType)
    )
    identity_value: so.Mapped[str] = so.mapped_column(sa.String(200), index=True)
    full_name: so.Mapped[str] = so.mapped_column(sa.String(200))
    username: so.Mapped[str] = so.mapped_column(sa.String(200))
    avatar: so.Mapped[str] = so.mapped_column(sa.String(200))
    user_id: so.Mapped[types.UserId] = so.mapped_column(
        sa.ForeignKey(f"{User.__tablename__}.id", ondelete="CASCADE"), unique=True
    )


class Role(Base):
    # Only sellers can create or delete roles
    __tablename__ = "roles"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "seller_id", "name", name="uq_role_seller_name"
        ),  # Because "Manager" role in Seller A shouldn't conflict with "Manager" role in Seller B.
    )
    id: so.Mapped[types.RoleId] = so.mapped_column(autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(200))
    description: so.Mapped[str] = so.mapped_column(sa.Text)
    seller_id: so.Mapped[SellerId] = so.mapped_column(
        sa.ForeignKey("sellers.id", ondelete="CASCADE"), index=True
    )
    created_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
    updated_at: so.Mapped[datetime] = so.mapped_column(
        server_default=sa.func.now(), onupdate=sa.func.now()
    )


class Permission(Base):
    # Only admins can create or delete permissions
    __tablename__ = "permissions"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("name", name="uq_permission_name"),
    )
    id: so.Mapped[types.PermissionId] = so.mapped_column(autoincrement=True)
    name: so.Mapped[str] = so.mapped_column(sa.String(200))
    description: so.Mapped[str] = so.mapped_column(sa.Text)
    created_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
    updated_at: so.Mapped[datetime] = so.mapped_column(
        server_default=sa.func.now(), onupdate=sa.func.now()
    )


class RolePermission(Base):
    __tablename__ = "role_permissions"
    __table_args__ = (sa.PrimaryKeyConstraint("role_id", "permission_id"),)
    role_id: so.Mapped[types.RoleId] = so.mapped_column(
        sa.ForeignKey(f"{Role.__tablename__}.id", ondelete="CASCADE"), index=True
    )
    permission_id: so.Mapped[types.PermissionId] = so.mapped_column(
        sa.ForeignKey(f"{Permission.__tablename__}.id", ondelete="CASCADE"), index=True
    )


class StaffPermission(Base):
    __tablename__ = "staff_permissions"
    __table_args__ = (sa.PrimaryKeyConstraint("staff_id", "permission_id"),)
    staff_id: so.Mapped[SellerStaffId] = so.mapped_column(
        sa.ForeignKey("seller_staff.id", ondelete="CASCADE"), index=True
    )
    permission_id: so.Mapped[types.PermissionId] = so.mapped_column(
        sa.ForeignKey(f"{Permission.__tablename__}.id", ondelete="CASCADE"), index=True
    )
