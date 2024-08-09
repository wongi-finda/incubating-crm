from google.protobuf import descriptor as _descriptor
from google.protobuf import message as _message
from typing import ClassVar as _ClassVar, Optional as _Optional

DESCRIPTOR: _descriptor.FileDescriptor

class UserEvent(_message.Message):
    __slots__ = ("event", "user_id")
    EVENT_FIELD_NUMBER: _ClassVar[int]
    USER_ID_FIELD_NUMBER: _ClassVar[int]
    event: str
    user_id: int
    def __init__(self, event: _Optional[str] = ..., user_id: _Optional[int] = ...) -> None: ...

class Response(_message.Message):
    __slots__ = ("success", "reason")
    SUCCESS_FIELD_NUMBER: _ClassVar[int]
    REASON_FIELD_NUMBER: _ClassVar[int]
    success: bool
    reason: str
    def __init__(self, success: bool = ..., reason: _Optional[str] = ...) -> None: ...
