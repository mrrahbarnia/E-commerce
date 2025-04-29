from datetime import datetime

import sqlalchemy as sa
import sqlalchemy.orm as so

from src.database import Base
from src.sellers.v1 import types
from src.auth.v1.types import UserId, RoleId


class Seller(Base):
    __tablename__ = "sellers"
    __table_args__ = (sa.PrimaryKeyConstraint("id"),)
    id: so.Mapped[types.SellerId] = so.mapped_column(autoincrement=True)
    company_name: so.Mapped[str] = so.mapped_column(sa.String(200), unique=True)
    user_id: so.Mapped[UserId] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE")
    )
    is_founder: so.Mapped[bool] = so.mapped_column(default=False)


class SellerStaff(Base):
    __tablename__ = "seller_staff"
    __table_args__ = (
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "seller_id", name="uq_user_seller"),
    )
    id: so.Mapped[types.SellerStaffId] = so.mapped_column(autoincrement=True)
    user_id: so.Mapped[UserId] = so.mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), index=True
    )
    seller_id: so.Mapped[types.SellerId] = so.mapped_column(
        sa.ForeignKey("sellers.id", ondelete="CASCADE"), index=True
    )
    role_id: so.Mapped[RoleId] = so.mapped_column(
        sa.ForeignKey("roles.id", ondelete="SET NULL"), nullable=True
    )
    created_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())


class StaffInvitation(Base):
    __tablename__ = "staff_invitations"
    __table_args__ = (
        sa.PrimaryKeyConstraint("user_id", "seller_id"),
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
    seller_id: so.Mapped[types.SellerId] = so.mapped_column(
        sa.ForeignKey(f"{Seller.__tablename__}.id", ondelete="CASCADE"), index=True
    )
    sent_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
    status: so.Mapped[types.InvitationStatus] = so.mapped_column(
        sa.Enum(types.InvitationStatus),
        default=types.InvitationStatus.PENDING,
    )
