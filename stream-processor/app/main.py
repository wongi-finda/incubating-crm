from dataclasses import dataclass
from operator import attrgetter
import json
from typing import Literal

from bytewax.dataflow import Dataflow
from bytewax import operators as op
from bytewax.testing import TestingSource

from app.model import (
    Campaign,
    UserEventData,
    CampaignChangeData,
    CampaignEventType,
)
from app.sink import CampaignServiceSink
from pb.campaign_service_pb2 import UserEventMessage

flow = Dataflow("crm")

# 1. Flat map by create/update/delete events
# 2. Key by events
# 3. Stateful by event
#   -> for event X, trigger campaigns {a,b} and cancel campaign {c}
campaign_cdc_data = [
    CampaignChangeData(
        op="c",
        before=None,
        after=Campaign(id=1, trigger_event="event_A", exception_event=None),
    ),
    CampaignChangeData(
        op="c",
        before=None,
        after=Campaign(id=2, trigger_event="event_B", exception_event=None),
    ),
    CampaignChangeData(
        op="c",
        before=None,
        after=Campaign(id=3, trigger_event="event_A", exception_event="event_B"),
    ),
    CampaignChangeData(
        op="u",
        before=Campaign(id=1, trigger_event="event_A", exception_event=None),
        after=Campaign(id=1, trigger_event="event_A", exception_event="event_C"),
    ),
    CampaignChangeData(
        op="c",
        before=None,
        after=Campaign(id=4, trigger_event="event_C", exception_event="event_A"),
    ),
    CampaignChangeData(
        op="d",
        before=Campaign(id=2, trigger_event="event_B", exception_event=None),
        after=None,
    ),
]
campaign_change_stream = op.input("campaigns", flow, TestingSource(campaign_cdc_data))


@dataclass
class CampaignTriggerChangeRecord:
    event: str
    op: Literal["create", "delete"]
    type: CampaignEventType
    campaign_id: int


def flat_campaign_change_datasets(item: CampaignChangeData) -> list[CampaignTriggerChangeRecord]:
    out = []

    def new_record(
            _op: Literal["create", "delete"],
            _type: CampaignEventType,
            _data: Campaign,
    ) -> CampaignTriggerChangeRecord:
        return CampaignTriggerChangeRecord(
            event=getattr(_data, _type),
            op=_op,
            type=_type,
            campaign_id=_data.id,
        )

    match item.op:
        case "c":
            out.append(new_record("create", "trigger_event", item.after))
            if item.after.exception_event:
                out.append(new_record("create", "exception_event", item.after))
        case "u":
            if item.before.trigger_event != item.after.trigger_event:
                out.append(new_record("delete", "trigger_event", item.before))
                out.append(new_record("create", "trigger_event", item.after))
            if item.before.exception_event != item.after.exception_event:
                if item.before.exception_event:
                    out.append(new_record("delete", "exception_event", item.before))
                if item.after.exception_event:
                    out.append(new_record("create", "exception_event", item.after))
        case "d":
            out.append(new_record("delete", "trigger_event", item.before))
            if item.before.exception_event:
                out.append(new_record("delete", "exception_event", item.before))

    return out


flatten_campaign_cdc = op.flat_map(
    "flat_campaign_cdc",
    campaign_change_stream,
    flat_campaign_change_datasets,
)
# op.inspect("inspect_cdc", flatten_campaign_cdc)

keyed_cdc = op.key_on("keyed_cdc", flatten_campaign_cdc, attrgetter("event"))
# op.inspect("inspect_keyed_cdc", keyed_cdc)


class EventState(dict[CampaignEventType, set[int]]):
    def __init__(self, event: str):
        super().__init__()
        self.event = event
        self["trigger_event"] = set[int]()
        self["exception_event"] = set[int]()
        self.in_use = self._check_in_use()

    def apply(self, record: CampaignTriggerChangeRecord) -> None:
        match record:
            case CampaignTriggerChangeRecord(op="create", type=_type, campaign_id=campaign_id):
                self[_type].add(campaign_id)
            case CampaignTriggerChangeRecord(op="delete", type=_type, campaign_id=campaign_id):
                self[_type].remove(campaign_id)

        self.in_use = self._check_in_use()

    def _check_in_use(self) -> bool:
        return bool(self["trigger_event"]) or bool(self["exception_event"])


def mapper(
        state: EventState | None,
        value: CampaignTriggerChangeRecord,
) -> tuple[EventState | None, bool]:
    if state is None:
        state = EventState(value.event)
    state.apply(value)
    return state, state.in_use


event_in_use_stream = op.stateful_map("stateful_triggers", keyed_cdc, mapper)
# op.inspect("inspect_actions", actions)


# [EVENT STREAM]
# 1. Key by events
# 2. Join event stream with event-action stream
# 3. Key on user_id
# 4. Stateful by user_id
# 5. Sink to scheduler
# 참고: 발송 완료 이벤트도 같이 들어온다. state 유지 시 사용
events_data = [
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
]
events = op.input("events", flow, TestingSource(events_data))

# TODO: 추후에 running join이 아닌 enrich_cached 방식을 고려해보자.
keyed_events = op.key_on("key_on_events", events, attrgetter("event_name"))
keyed_joined_events = op.join("join_actions", keyed_events, event_in_use_stream, emit_mode="running")
# op.inspect("inspect_keyed_joined_events", keyed_joined_events)


def as_campaign_service_request(item: tuple[UserEventData | None, bool | None]) -> UserEventMessage | None:
    event, in_use = item
    if (event is not None) and (in_use is True):
        return UserEventMessage(
            user_id=event.user_id,
            event_data={
                "json": json.dumps({
                    "event_name": event.event_name,
                    "event_properties": event.event_properties,
                }),
            },
        )


keyed_requests = op.filter_map_value("filter_value", keyed_joined_events, as_campaign_service_request)
# op.inspect("inspect_keyed_requests", keyed_requests)

requests = op.key_rm("unkey_requests", keyed_requests)
# op.inspect("inspect_requests", requests)

op.output("sink_to_executor", requests, sink=CampaignServiceSink())

# def flat_requests(item: tuple[UserEvent | None, EventState | None]) -> list[CampaignTrigger]:
#     # join 된 tuple 중 유효한 것만 살리고, 하나로 merge 한다.
#     event, action = item
#     if (event is None) or (action is None):
#         return []
#
#     # TODO: campaign state가 변경된 경우에는 skip 할 수 있을까?
#
#     def create_requests(_type: CampaignEventType):
#         return [
#             CampaignTrigger(
#                 type=_type,
#                 campaign_id=campaign_id,
#                 user_id=event.user_id,
#             )
#             for campaign_id in action[_type]
#         ]
#
#     return create_requests("trigger_event") + create_requests("exception_event")
#
#
# keyed_requests = op.flat_map_value("flat_requests", keyed_joined_events, flat_requests)
# # op.inspect("inspect_keyed_requests", keyed_requests)
# requests = op.key_rm("unkey_requests", keyed_requests)
# # op.inspect("inspect_requests", requests)
# op.output("sink_to_executor", requests, sink=CampaignServiceSink())
