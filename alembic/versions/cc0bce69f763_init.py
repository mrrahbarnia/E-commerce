"""init

Revision ID: cc0bce69f763
Revises: 
Create Date: 2025-05-07 11:17:32.877573

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cc0bce69f763'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('permissions',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_permissions')),
    sa.UniqueConstraint('name', name='uq_permission_name')
    )
    op.create_table('providers',
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_providers')),
    sa.UniqueConstraint('name', name=op.f('uq_providers_name'))
    )
    op.create_table('users',
    sa.Column('role', sa.Enum('ADMIN', 'CUSTOMER', 'PROVIDER', name='userrole'), nullable=False),
    sa.Column('registered_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('hashed_password', sa.String(length=250), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.Column('id', sa.UUID(), nullable=False),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_users'))
    )
    op.create_table('provider_invitations',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('provider_id', sa.UUID(), nullable=False),
    sa.Column('sent_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'CANCELED', name='invitationstatus'), nullable=False),
    sa.ForeignKeyConstraint(['provider_id'], ['providers.id'], name=op.f('fk_provider_invitations_provider_id_providers'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_provider_invitations_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'provider_id', name=op.f('pk_provider_invitations'))
    )
    op.create_index(op.f('ix_provider_invitations_provider_id'), 'provider_invitations', ['provider_id'], unique=False)
    op.create_index(op.f('ix_provider_invitations_user_id'), 'provider_invitations', ['user_id'], unique=False)
    op.create_index('uq_user_only_one_accepted', 'provider_invitations', ['user_id'], unique=True, postgresql_where=sa.text("status = 'ACCEPTED'"))
    op.create_table('provider_staff',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('provider_id', sa.UUID(), nullable=False),
    sa.Column('joined_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('is_founder', sa.Boolean(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=False),
    sa.CheckConstraint('NOT (is_founder = true AND is_active = false)', name=op.f('ck_provider_staff_founder_must_be_active')),
    sa.ForeignKeyConstraint(['provider_id'], ['providers.id'], name=op.f('fk_provider_staff_provider_id_providers'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_provider_staff_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_provider_staff')),
    sa.UniqueConstraint('user_id', name=op.f('uq_provider_staff_user_id'))
    )
    op.create_index(op.f('ix_provider_staff_provider_id'), 'provider_staff', ['provider_id'], unique=False)
    op.create_table('roles',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('provider_id', sa.UUID(), nullable=False),
    sa.Column('created_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['provider_id'], ['providers.id'], name=op.f('fk_roles_provider_id_providers'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
    sa.UniqueConstraint('provider_id', 'name', name='uq_role_provider_name')
    )
    op.create_index(op.f('ix_roles_provider_id'), 'roles', ['provider_id'], unique=False)
    op.create_table('staff_invitations',
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.Column('provider_id', sa.UUID(), nullable=False),
    sa.Column('sent_at', sa.TIMESTAMP(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('status', sa.Enum('PENDING', 'ACCEPTED', 'CANCELED', name='invitationstatus'), nullable=False),
    sa.ForeignKeyConstraint(['provider_id'], ['providers.id'], name=op.f('fk_staff_invitations_provider_id_providers'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_staff_invitations_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('user_id', 'provider_id', name=op.f('pk_staff_invitations'))
    )
    op.create_index(op.f('ix_staff_invitations_provider_id'), 'staff_invitations', ['provider_id'], unique=False)
    op.create_index(op.f('ix_staff_invitations_user_id'), 'staff_invitations', ['user_id'], unique=False)
    op.create_index('uq_user_invitaion_status_accepted', 'staff_invitations', ['user_id'], unique=True, postgresql_where=sa.text("status = 'ACCEPTED'"))
    op.create_table('user_identities',
    sa.Column('id', sa.INTEGER(), autoincrement=True, nullable=False),
    sa.Column('identity_type', sa.Enum('EMAIL', 'PHONE_NUMBER', name='identitytype'), nullable=False),
    sa.Column('identity_value', sa.String(length=200), nullable=False),
    sa.Column('full_name', sa.String(length=200), nullable=False),
    sa.Column('username', sa.String(length=200), nullable=False),
    sa.Column('avatar', sa.String(length=200), nullable=False),
    sa.Column('user_id', sa.UUID(), nullable=False),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_identities_user_id_users'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user_identities')),
    sa.UniqueConstraint('identity_type', 'identity_value', name='identity_type_identity_value_unique'),
    sa.UniqueConstraint('user_id', name=op.f('uq_user_identities_user_id'))
    )
    op.create_index(op.f('ix_user_identities_identity_value'), 'user_identities', ['identity_value'], unique=False)
    op.create_table('provider_staff_roles',
    sa.Column('provider_staff_id', sa.INTEGER(), nullable=False),
    sa.Column('role_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['provider_staff_id'], ['provider_staff.id'], name=op.f('fk_provider_staff_roles_provider_staff_id_provider_staff'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_provider_staff_roles_role_id_roles'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('provider_staff_id', 'role_id', name=op.f('pk_provider_staff_roles'))
    )
    op.create_index(op.f('ix_provider_staff_roles_provider_staff_id'), 'provider_staff_roles', ['provider_staff_id'], unique=False)
    op.create_index(op.f('ix_provider_staff_roles_role_id'), 'provider_staff_roles', ['role_id'], unique=False)
    op.create_table('role_permissions',
    sa.Column('role_id', sa.INTEGER(), nullable=False),
    sa.Column('permission_id', sa.INTEGER(), nullable=False),
    sa.ForeignKeyConstraint(['permission_id'], ['permissions.id'], name=op.f('fk_role_permissions_permission_id_permissions'), ondelete='CASCADE'),
    sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_role_permissions_role_id_roles'), ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('role_id', 'permission_id', name=op.f('pk_role_permissions'))
    )
    op.create_index(op.f('ix_role_permissions_permission_id'), 'role_permissions', ['permission_id'], unique=False)
    op.create_index(op.f('ix_role_permissions_role_id'), 'role_permissions', ['role_id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_role_permissions_role_id'), table_name='role_permissions')
    op.drop_index(op.f('ix_role_permissions_permission_id'), table_name='role_permissions')
    op.drop_table('role_permissions')
    op.drop_index(op.f('ix_provider_staff_roles_role_id'), table_name='provider_staff_roles')
    op.drop_index(op.f('ix_provider_staff_roles_provider_staff_id'), table_name='provider_staff_roles')
    op.drop_table('provider_staff_roles')
    op.drop_index(op.f('ix_user_identities_identity_value'), table_name='user_identities')
    op.drop_table('user_identities')
    op.drop_index('uq_user_invitaion_status_accepted', table_name='staff_invitations', postgresql_where=sa.text("status = 'ACCEPTED'"))
    op.drop_index(op.f('ix_staff_invitations_user_id'), table_name='staff_invitations')
    op.drop_index(op.f('ix_staff_invitations_provider_id'), table_name='staff_invitations')
    op.drop_table('staff_invitations')
    op.drop_index(op.f('ix_roles_provider_id'), table_name='roles')
    op.drop_table('roles')
    op.drop_index(op.f('ix_provider_staff_provider_id'), table_name='provider_staff')
    op.drop_table('provider_staff')
    op.drop_index('uq_user_only_one_accepted', table_name='provider_invitations', postgresql_where=sa.text("status = 'ACCEPTED'"))
    op.drop_index(op.f('ix_provider_invitations_user_id'), table_name='provider_invitations')
    op.drop_index(op.f('ix_provider_invitations_provider_id'), table_name='provider_invitations')
    op.drop_table('provider_invitations')
    op.drop_table('users')
    op.drop_table('providers')
    op.drop_table('permissions')
    # ### end Alembic commands ###
