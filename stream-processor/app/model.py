from datetime import datetime
from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class Filter(BaseModel):
    name: str
    operator: Literal["eq", "ne", "gt", "gte", "lt", "lte"]  # 일단
    condition_value: Any


class Campaign(BaseModel):
    id: str
    status: str
    trigger_event: str
    exception_event: str | None


class UserEventData(BaseModel):
    user_id: int
    event_name: str
    event_properties: dict[str, Any] = {}


class ChangeData(BaseModel, Generic[DataT]):
    op: Literal["c", "u", "d"]  # Create/Update/Delete
    before: DataT | None
    after: DataT | None


CampaignChangeData = ChangeData[Campaign]
