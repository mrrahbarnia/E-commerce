from uuid import uuid4
from datetime import datetime

import sqlalchemy.orm as so
import sqlalchemy as sa

from src.database import Base
from src.auth.v1 import types


class User(Base):
    __tablename__ = "users"
    __table_args__ = (sa.PrimaryKeyConstraint("id"),)
    role: so.Mapped[types.UserRole] = so.mapped_column(sa.Enum(types.UserRole))
    registered_at: so.Mapped[datetime] = so.mapped_column(server_default=sa.func.now())
    hashed_password: so.Mapped[str] = so.mapped_column(sa.String(250))
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
        sa.CheckConstraint(
            """
            (identity_type = 'EMAIL' AND identity_value ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$')
            OR
            (identity_type = 'PHONE_NUMBER' AND identity_value ~* '[0-9]{11}')
            """,
            name="check_identity_type_identity_value",
        ),
    )
    id: so.Mapped[types.UserIdentityId] = so.mapped_column(autoincrement=True)
    identity_type: so.Mapped[types.IdentityType] = so.mapped_column(
        sa.Enum(types.IdentityType)
    )
    identity_value: so.Mapped[str] = so.mapped_column(sa.String(200))
    full_name: so.Mapped[str] = so.mapped_column(sa.String(200))
    username: so.Mapped[str] = so.mapped_column(sa.String(200))
    avatar: so.Mapped[str] = so.mapped_column(sa.String(200))
    user_id: so.Mapped[types.UserId] = so.mapped_column(
        sa.ForeignKey(f"{User.__tablename__}.id", ondelete="CASCADE"), index=True
    )
