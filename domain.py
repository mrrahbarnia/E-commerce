from dataclasses import dataclass
from datetime import datetime
from typing import NewType, Literal
from uuid import UUID

UserId = NewType("UserId", UUID)
UserIdentityId = NewType("UserIdentityId", int)
ProductId = NewType("ProductId", UUID)
CategoryId = NewType("CategoryId", UUID)
SellerId = NewType("SellerId", int)
SellerStaffId = NewType("SellerStaffId", int)
RoleId = NewType("RoleId", int)
PermissionId = NewType("PermissionId", int)

# ============= Two different bounded context ============= #
# If i have a user named MohammadReza
# AUTH only cares: “Can MohammadReza access the system?”
# SELLERS cares: “Which seller does MohammadReza work for, and what can he do for that seller?”


@dataclass
class User:
    id: UserId
    role: Literal["Customer", "Seller", "Admin"]
    hashed_password: str
    registered_at: datetime


@dataclass
class UserIdentity:
    id: UserIdentityId
    user_id: UserId
    identity_type: str  # email, phone_number, etc
    identity_value: str
    full_name: str
    username: str
    avatar: str


@dataclass
class Seller:
    id: SellerId
    company_name: str
    user_id: UserId


@dataclass
class SellerStaff:
    id: SellerStaffId
    seller_id: SellerId
    user_id: UserId
    created_at: datetime


# Only seller users can create their custom roles based on permissions
@dataclass
class Role:
    id: RoleId
    name: str  # Inventory manager, Finance, Order manager, etc
    seller_id: SellerId


# Only admin users can create this permissions
@dataclass
class Permission:
    id: PermissionId
    name: str  # manage_inventory, view_orders, process_payments


@dataclass
class RolePermission:
    role_id: RoleId
    permission_id: PermissionId


@dataclass
class UserRole:
    user_id: UserId
    seller_id: SellerId
    role_id: RoleId
