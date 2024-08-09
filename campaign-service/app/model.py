from enum import StrEnum, auto
from datetime import datetime, date, time, timedelta
from typing import Any, Generic, Literal, Sequence, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class CampaignChannel(StrEnum):
    push = auto()
    kakao = auto()


class CampaignDeliveryType(StrEnum):
    immediate = auto()
    scheduled = auto()
    action_based = auto()


class Segment(BaseModel):
    ...


class Filter(BaseModel):
    name: str
    operator: Any  # TODO
    condition_value: Any


AndCondition = Sequence


class OrCondition(BaseModel, Generic[T]):
    or_: Sequence[T]


class ScheduledDeliveryMetadata(BaseModel):
    frequency: Literal["daily", "weekly", "monthly"]
    start_time: time
    recurrence: int | None
    start_date: date | None
    end_date: date | None


class Delay(BaseModel):
    """
    op 해석 방법
     - weekday: 다음 {value}요일 {at_time}에
     - days: {value}일 후 {at_time}에
    """
    op: Literal["weekday", "days"]
    value: int
    at_time: time


class ActionBasedDeliveryMetadata(BaseModel):
    trigger_event: str
    event_property_filters: AndCondition[Filter | OrCondition[Filter]] | None = None
    schedule_delay: timedelta | Delay
    exception_events: AndCondition[Filter | OrCondition[Filter]] | None = None
    start_time: datetime
    end_time: datetime | None = None
    re_eligible: timedelta | None = None


class Campaign(BaseModel):
    name: str
    channel: CampaignChannel
    delivery_type: CampaignDeliveryType
    delivery_metadata: ScheduledDeliveryMetadata | ActionBasedDeliveryMetadata | None
    target_segment_ids: list[str]
    additional_filters: AndCondition[Filter | OrCondition[Filter]] | None = None
