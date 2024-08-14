import json
from typing import Any, Self

from pydantic import BaseModel

from pb.campaign_service_pb2 import UserEventMessage, UserAttributeMessage


class UserEvent(BaseModel):
    user_id: int
    event_name: str
    event_properties: dict[str, Any]

    @classmethod
    def from_message(cls, message: UserEventMessage) -> Self:
        event_data = json.loads(message.event_data.json)
        return cls(
            user_id=message.user_id,
            event_name=event_data["event_name"],
            event_properties=event_data["event_properties"],
        )


class UserAttribute(BaseModel):
    user_id: int
    attribute_name: str
    attribute_value: Any

    @classmethod
    def from_message(cls, message: UserAttributeMessage) -> Self:
        attribute_data = json.loads(message.attribute_data.json)
        return cls(
            user_id=message.user_id,
            attribute_name=attribute_data["attribute_name"],
            attribute_value=attribute_data["attribute_value"],
        )
