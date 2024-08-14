from typing import Any, Generic, Literal, Sequence, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Filter(BaseModel):
    name: str
    operator: Any  # TODO
    condition_value: Any


AndCondition = Sequence


class OrCondition(BaseModel, Generic[T]):
    or_: Sequence[T]
