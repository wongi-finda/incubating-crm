from enum import StrEnum, auto
from datetime import datetime, date, time, timedelta
from typing import Any, Literal, TypedDict, NotRequired

from bson import ObjectId

from app.schemas.filter import Filter, AndCondition, OrCondition


class CampaignStatus(StrEnum):
    draft = auto()
    active = auto()
    stopped = auto()
    archived = auto()
    idle = auto()


class CampaignChannel(StrEnum):
    noti_10000 = auto()  # 금명보 알림 via mobile push
    noti_10001 = auto()  # 금명보 알림 via 카카오 알림톡


class CampaignSchedule(TypedDict):
    frequency: Literal["once", "daily", "weekly", "monthly"]
    start_date: datetime
    end_date: datetime | None
    # recurrence: int  # TODO: 한 유저에게 몇 번까지 반복할 지


class CampaignTarget(TypedDict):
    target_segment_ids: AndCondition[str]
    additional_filters: AndCondition[Filter | OrCondition[Filter]] | None


class Delay(TypedDict):
    """
    op 해석 방법
     - weekday: 다음 {value}요일 {at_time}에
     - days: {value}일 후 {at_time}에
    """
    op: Literal["weekday", "days"]
    value: int
    at_time: time


class EventTriggerAction(TypedDict):
    type: Literal["event-trigger"]
    trigger_event: str
    property_filters: AndCondition[Filter | OrCondition[Filter]] | None


class AttributeTriggerAction(TypedDict):
    type: Literal["attribute-trigger"]
    attribute_name: str
    value: bool | int | str | None  # Triggered when the attribute changes to a specific value if set


class ScheduledDeliveryCampaign(TypedDict):
    # Common
    _id: NotRequired[ObjectId]
    name: str
    status: CampaignStatus
    channel: CampaignChannel

    # Scheduling
    delivery_type: Literal["scheduled"]
    schedule: CampaignSchedule | None  # Send immediately if not set

    target: CampaignTarget


class ActionBasedDeliveryCampaign(TypedDict):
    # Common
    _id: NotRequired[ObjectId]
    name: str
    status: CampaignStatus
    channel: CampaignChannel

    # Scheduling
    delivery_type: Literal["action-based"]
    trigger_action: EventTriggerAction | AttributeTriggerAction
    # delay: timedelta | Delay | None
    delay: int | Delay | None
    exception_event: str | None
    start_time: datetime
    end_time: datetime | None
    # re_eligible: timedelta | None
    re_eligible: int | None

    target: CampaignTarget
    re_eval_before_send: bool  # Re-evaluate segment membership at send-time
