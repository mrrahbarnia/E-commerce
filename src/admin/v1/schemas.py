from datetime import datetime

from pydantic import BaseModel

from src.providers.v1.types import ProviderId


class ProvidersOut(BaseModel):
    provider_id: ProviderId
    founder_identity_value: str
    is_active: bool
    name: str
    created_at: datetime
