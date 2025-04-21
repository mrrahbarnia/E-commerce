from uuid import uuid4
from datetime import datetime

import sqlalchemy.orm as so
import sqlalchemy as sa

from src.database import Base
from src.auth.domain import types


class User(Base):
    __tablename__ = "users"
    __table_args__ = (sa.PrimaryKeyConstraint("id"),)
    role: so.Mapped[types.UserRole] = so.mapped_column(sa.Enum(types.UserRole))
    registered_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
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
    identity_value: so.Mapped[str] = so.mapped_column(sa.String(200))
    full_name: so.Mapped[str] = so.mapped_column(sa.String(200))
    avatar: so.Mapped[str] = so.mapped_column(sa.String(200))
    user_id: so.Mapped[types.UserId] = so.mapped_column(
        sa.ForeignKey(f"{User.__tablename__}.id", ondelete="CASCADE"), index=True
    )
