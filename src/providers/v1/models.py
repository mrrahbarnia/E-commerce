from datetime import datetime
from uuid import uuid4

import sqlalchemy as sa
import sqlalchemy.orm as so

from src.database import Base
from src.providers.v1 import types
from src.auth.v1.types import UserId, RoleId


class Provider(Base):
    __tablename__ = "providers"
    __table_args__ = (sa.PrimaryKeyConstraint("id"),)
    name: so.Mapped[str] = so.mapped_column(sa.String(200), unique=True)
    created_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
    is_active: so.Mapped[bool] = so.mapped_column(default=False)
    id: so.Mapped[types.ProviderId] = so.mapped_column(default=lambda: uuid4())


class ProviderStaff(Base):
    __tablename__ = "provider_staff"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint(
            "NOT (is_founder = true AND is_active = false)",
            name="founder_must_be_active",
        ),
    )
    id: so.Mapped[types.ProviderStaffId] = so.mapped_column(autoincrement=True)
    user_id: so.Mapped[UserId] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True
    )
    provider_id: so.Mapped[types.ProviderId] = so.mapped_column(
        sa.ForeignKey(f"{Provider.__tablename__}.id", ondelete="CASCADE"), index=True
    )
    joined_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
    is_founder: so.Mapped[bool] = so.mapped_column(default=False)
    is_active: so.Mapped[bool] = so.mapped_column(default=True)


class ProviderInvitation(Base):
    __tablename__ = "provider_invitations"
    __table_args__ = (
        sa.PrimaryKeyConstraint("user_id", "provider_id"),
        sa.Index(
            "uq_user_only_one_accepted",
            "user_id",
            unique=True,
            postgresql_where=sa.text("status = 'ACCEPTED'"),
        ),
    )
    user_id: so.Mapped[UserId] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider_id: so.Mapped[types.ProviderId] = so.mapped_column(
        sa.ForeignKey(f"{Provider.__tablename__}.id", ondelete="CASCADE"), index=True
    )
    sent_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
    status: so.Mapped[types.InvitationStatus] = so.mapped_column(
        sa.Enum(types.InvitationStatus),
        default=types.InvitationStatus.PENDING,
    )


class ProviderStaffRole(Base):
    __tablename__ = "provider_staff_roles"
    __table_args__ = (sa.PrimaryKeyConstraint("provider_staff_id", "role_id"),)
    provider_staff_id: so.Mapped[types.ProviderStaffId] = so.mapped_column(
        sa.ForeignKey(f"{ProviderStaff.__tablename__}.id", ondelete="CASCADE"),
        index=True,
    )
    role_id: so.Mapped[RoleId] = so.mapped_column(
        sa.ForeignKey("roles.id", ondelete="CASCADE"), index=True
    )


class StaffInvitation(Base):
    __tablename__ = "staff_invitations"
    __table_args__ = (
        sa.PrimaryKeyConstraint("user_id", "provider_id"),
        sa.Index(
            "uq_user_invitaion_status_accepted",
            "user_id",
            unique=True,
            postgresql_where=sa.text("status = 'ACCEPTED'"),
        ),
    )
    user_id: so.Mapped[UserId] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    provider_id: so.Mapped[types.ProviderId] = so.mapped_column(
        sa.ForeignKey(f"{Provider.__tablename__}.id", ondelete="CASCADE"), index=True
    )
    sent_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
    status: so.Mapped[types.InvitationStatus] = so.mapped_column(
        sa.Enum(types.InvitationStatus),
        default=types.InvitationStatus.PENDING,
    )
