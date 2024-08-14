from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Mapping as _Mapping, Optional as _Optional, Union as _Union

DESCRIPTOR: _descriptor.FileDescriptor

class JsonSerialized(_message.Message):
    __slots__ = ("json",)
    JSON_FIELD_NUMBER: _ClassVar[int]
    json: str
    def __init__(self, json: _Optional[str] = ...) -> None: ...

class UserEventMessage(_message.Message):
    __slots__ = ("user_id", "event_data")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    EVENT_DATA_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    event_data: JsonSerialized
    def __init__(self, user_id: _Optional[int] = ..., event_data: _Optional[_Union[JsonSerialized, _Mapping]] = ...) -> None: ...

class UserAttributeMessage(_message.Message):
    __slots__ = ("user_id", "attribute_data")
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    ATTRIBUTE_DATA_FIELD_NUMBER: _ClassVar[int]
    user_id: int
    attribute_data: JsonSerialized
    def __init__(self, user_id: _Optional[int] = ..., attribute_data: _Optional[_Union[JsonSerialized, _Mapping]] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("success", "reason")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    success: bool
    reason: str
    def __init__(self, success: bool = ..., reason: _Optional[str] = ...) -> None: ...
