from dataclasses import dataclass
from datetime import datetime
from typing import NewType, Literal
from uuid import UUID

UserId = NewType("UserId", UUID)
ProductId = NewType("ProductId", UUID)
CategoryId = NewType("CategoryId", UUID)
SellerId = NewType("SellerId", int)
SellerStaffId = NewType("SellerStaffId", int)
RoleId = NewType("RoleId", int)
PermissionId = NewType("PermissionId", int)

# ======================== User management bounded context ======================== #
# Seller different roles: products_manager, inventory_manager, orders_manager,


@dataclass
class User:
    id: UserId
    role: Literal["Customer", "Seller", "Admin"]
    email: str
    phone_number: str
    hashed_password: str


@dataclass
class Profile:
    user_id: UserId
    first_name: str
    last_name: str
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
