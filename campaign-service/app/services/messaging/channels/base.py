from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Generic, TypeVar

T = TypeVar("T")


@dataclass
class SendResult:
    ok: bool
    reason: str


class BaseChannel(ABC, Generic[T]):
    @property
    @abstractmethod
    def name(self) -> str:
        raise NotImplementedError()

    @abstractmethod
    def send(self, data: T) -> SendResult:
        raise NotImplementedError()
