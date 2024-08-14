import sys
from abc import abstractmethod
from typing import Any

from requests import Request, Session

from app.models import UserEvent
from app.services.messaging.channels.base import BaseChannel, SendResult

__all__ = (
    "Noti10000Sender",
    "Noti10001Sender",
)


class _NotiSender(BaseChannel[UserEvent]):
    def __init__(self):
        self.request = Request(
            method=self.method,
            url=f"http://stg-eks-backend-internal.findainsight.co.kr/{self.path}",
            headers=self.headers,
        )

    def send(self, data: UserEvent) -> SendResult:
        with Session() as session:
            prepared = session.prepare_request(self.request)
            prepared.prepare_body(None, None, self.json(data))

            print(f"""> {prepared.method} {prepared.url} {prepared.body.decode("unicode_escape")}""")

            resp = session.send(prepared)
            if not resp.ok:
                print(f"{resp.status_code} {resp.reason} {resp.request.body}", file=sys.stderr)

            return SendResult(ok=resp.ok, reason=resp.reason)

    @property
    @abstractmethod
    def method(self) -> str:
        raise NotImplementedError()

    @property
    @abstractmethod
    def path(self) -> str:
        raise NotImplementedError()

    @property
    def headers(self) -> dict[str, str]:
        return {
            "Content-Type": "application/json",
        }

    @abstractmethod
    def json(self, data: UserEvent) -> dict[str, Any]:
        raise NotImplementedError()


class Noti10000Sender(_NotiSender):
    @property
    def name(self) -> str:
        return "noti_10000"

    @property
    def method(self) -> str:
        return "PUT"

    @property
    def path(self):
        return "/noti/internal/v2/send/10000"

    def json(self, data: UserEvent) -> dict[str, Any]:
        return {
            "userId": data.user_id,
            "properties": {
                "inqu_org_nm": data.event_properties.get("inquiry_org_name"),
            },
            "checkMktAgree": False,
        }


class Noti10001Sender(_NotiSender):
    @property
    def name(self):
        return "noti_10001"

    @property
    def method(self) -> str:
        return "PUT"

    @property
    def path(self) -> str:
        return "/noti/internal/v2/send/10001"

    def json(self, data: UserEvent) -> dict[str, Any]:
        return {
            "userId": data.user_id,
            "properties": {
                "inqu_org_nm": data.event_properties.get("inquiry_org_name"),
            },
        }
