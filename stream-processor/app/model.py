from typing import Any, Generic, Literal, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class Campaign(BaseModel):
    id: int
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

CampaignEventType = Literal["trigger_event", "exception_event"]


# class CampaignTrigger(BaseModel):
#     type: CampaignEventType
#     campaign_id: int
#     user_id: int
