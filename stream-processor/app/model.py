from typing import Generic, Literal, TypeVar

from pydantic import BaseModel

DataT = TypeVar("DataT")


class Campaign(BaseModel):
    id: int
    trigger_event: str
    exception_event: str | None


class UserEvent(BaseModel):
    user_id: int
    event_name: str


class ChangeData(BaseModel, Generic[DataT]):
    op: Literal["c", "u", "d"]  # Create/Update/Delete
    before: DataT | None
    after: DataT | None


CampaignChangeData = ChangeData[Campaign]

CampaignEventType = Literal["trigger_event", "exception_event"]


class ActionBasedCampaignTrigger(BaseModel):
    type: CampaignEventType
    campaign_id: int
    user_id: int
