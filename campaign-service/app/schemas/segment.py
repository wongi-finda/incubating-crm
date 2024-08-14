from typing import TypedDict, NotRequired

from bson import ObjectId


class Segment(TypedDict):
    _id: NotRequired[ObjectId]
    name: str
    description: str
    # TODO: filter
