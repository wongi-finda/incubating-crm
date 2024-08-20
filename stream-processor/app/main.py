from dataclasses import dataclass, field
from operator import attrgetter, is_not
from functools import partial
import json
from typing import Literal, Self

from bytewax.dataflow import Dataflow
from bytewax import operators as op
from bytewax.testing import TestingSource

from app.model import (
    Campaign,
    CampaignChangeData,
    UserEventData,
)
from app.sink import CampaignServiceSink
from pb.campaign_service_pb2 import UserEventMessage

CampaignEventType = Literal["trigger_event", "exception_event"]

flow = Dataflow("crm")

campaign_cdc_data = [
    CampaignChangeData(
        op="c",
        before=None,
        after=Campaign(id="doc1", status="active", trigger_event="event_A", exception_event=None),
    ),
    CampaignChangeData(
        op="c",
        before=None,
        after=Campaign(id="doc2", status="active", trigger_event="event_B", exception_event=None),
    ),
    CampaignChangeData(
        op="c",
        before=None,
        after=Campaign(id="doc3", status="active", trigger_event="event_A", exception_event="event_B"),
    ),
    CampaignChangeData(
        op="u",
        before=Campaign(id="doc1", status="active", trigger_event="event_A", exception_event=None),
        after=Campaign(id="doc1", status="active", trigger_event="event_A", exception_event="event_C"),
    ),
    CampaignChangeData(
        op="c",
        before=None,
        after=Campaign(id="doc4", status="active", trigger_event="event_C", exception_event="event_A"),
    ),
    CampaignChangeData(
        op="u",
        before=Campaign(id="doc2", status="active", trigger_event="event_B", exception_event=None),
        after=Campaign(id="doc2", status="stopped", trigger_event="event_B", exception_event=None),
    ),
    CampaignChangeData(
        op="u",
        before=Campaign(id="doc3", status="active", trigger_event="event_A", exception_event="event_B"),
        after=Campaign(id="doc3", status="stopped", trigger_event="event_A", exception_event="event_B"),
    )
]
events_data = [
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
    UserEventData(user_id=1, event_name="event_A"),
]

campaign_change_stream = op.input("campaigns", flow, TestingSource(campaign_cdc_data))
event_stream = op.input("events", flow, TestingSource(events_data))


# 1. change stream을 event로 분해한다. event마다 trigger/exclude 할 campaign-id 유지해야 함
@dataclass
class CampaignTriggerChangeRecord:
    event_name: str
    op: Literal["set", "unset"]
    type: CampaignEventType
    campaign_id: str


def flat_campaign_change_datasets(item: CampaignChangeData) -> list[CampaignTriggerChangeRecord]:
    out = []

    def new_record(
            _op: Literal["set", "unset"],
            _type: CampaignEventType,
            _data: Campaign,
    ) -> CampaignTriggerChangeRecord:
        return CampaignTriggerChangeRecord(
            event_name=getattr(_data, _type),
            op=_op,
            type=_type,
            campaign_id=_data.id,
        )

    match item.op:
        case "c":
            out.append(new_record("set", "trigger_event", item.after))
            if item.after.exception_event:
                out.append(new_record("set", "exception_event", item.after))

        case "u":
            if item.before.trigger_event != item.after.trigger_event:
                out.append(new_record("unset", "trigger_event", item.before))
                out.append(new_record("set", "trigger_event", item.after))
            if item.before.exception_event != item.after.exception_event:
                if item.before.exception_event:
                    out.append(new_record("unset", "exception_event", item.before))
                if item.after.exception_event:
                    out.append(new_record("set", "exception_event", item.after))
            if item.before.status != item.after.status:
                if item.after.status == "active":
                    out.append(new_record("set", "trigger_event", item.after))
                    if item.after.exception_event:
                        out.append(new_record("set", "exception_event", item.after))
                elif item.before.status == "active":
                    out.append(new_record("unset", "trigger_event", item.before))
                    if item.before.exception_event:
                        out.append(new_record("unset", "exception_event", item.before))

        case "d":
            out.append(new_record("unset", "trigger_event", item.before))
            if item.before.exception_event:
                out.append(new_record("unset", "exception_event", item.before))

    return out


campaign_cdc = op.flat_map(
    "flat_campaign_cdc",
    campaign_change_stream,
    flat_campaign_change_datasets,
)
# op.inspect("inspect_cdc", campaign_cdc)

keyed_campaign_cdc = op.key_on("keyed_cdc", campaign_cdc, attrgetter("event_name"))
# op.inspect("inspect_keyed_campaign_cdc", keyed_campaign_cdc)

keyed_event = op.key_on("keyed_event", event_stream, attrgetter("event_name"))
# op.inspect("inspect_keyed_event", keyed_event)


@dataclass
class EventState:
    event: str = field(init=True)
    in_use: bool = field(default=False, init=False)

    _trigger_campaigns: set[str] = field(default_factory=set, init=False)
    _exception_campaigns: set[str] = field(default_factory=set, init=False)

    def update(self, record: CampaignTriggerChangeRecord) -> None:
        match record:
            case CampaignTriggerChangeRecord(op="set", type="trigger_event", campaign_id=campaign_id):
                self._trigger_campaigns.add(campaign_id)
            case CampaignTriggerChangeRecord(op="set", type="exception_event", campaign_id=campaign_id):
                self._exception_campaigns.add(campaign_id)
            case CampaignTriggerChangeRecord(op="unset", type="trigger_event", campaign_id=campaign_id):
                self._trigger_campaigns.discard(campaign_id)
            case CampaignTriggerChangeRecord(op="unset", type="exception_event", campaign_id=campaign_id):
                self._exception_campaigns.discard(campaign_id)

        self.in_use = bool(self._trigger_campaigns) or bool(self._exception_campaigns)


def mapper(
        state: EventState | None,
        value: CampaignTriggerChangeRecord | UserEventData,
) -> tuple[EventState | None, UserEventData | None]:
    if state is None:
        state = EventState(value.event_name)

    if isinstance(value, CampaignTriggerChangeRecord):
        state.update(value)
        value = None
    elif isinstance(value, UserEventData):
        if not state.in_use:
            value = None
    else:
        value = None

    return state, value


merged_stream = op.merge("merged", keyed_campaign_cdc, keyed_event)
# op.inspect("inspect_merged", merged_stream)

eval_stream = op.stateful_map("state", merged_stream, mapper)
# op.inspect("inspect_eval_stream", eval_stream)


def as_campaign_service_request(event: UserEventData | None) -> UserEventMessage | None:
    if event is not None:
        return UserEventMessage(
            user_id=event.user_id,
            event_data={
                "json": json.dumps({
                    "event_name": event.event_name,
                    "event_properties": event.event_properties,
                }),
            },
        )


keyed_requests = op.filter_map_value("filter_value", eval_stream, as_campaign_service_request)
# op.inspect("inspect_keyed_requests", keyed_requests)

requests = op.key_rm("unkey_requests", keyed_requests)
# op.inspect("inspect_requests", requests)

op.output("sink_to_executor", requests, sink=CampaignServiceSink())
