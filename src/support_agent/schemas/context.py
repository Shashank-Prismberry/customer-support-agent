from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class UserRole(str, Enum):
    ORG_ADMIN = "Org_Admin"
    SUPPORT_AGENT = "Support_Agent"
    END_CUSTOMER = "End_Customer"


class AuthenticatedUser(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    user_id: UUID
    customer_id: UUID
    org_id: UUID
    role: UserRole
    email: str
