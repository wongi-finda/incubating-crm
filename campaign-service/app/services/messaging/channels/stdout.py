from app.models import UserEvent
from app.services.messaging.channels.base import BaseChannel, SendResult

__all__ = (
    "StdoutSender",
)


class StdoutSender(BaseChannel[UserEvent]):
    @property
    def name(self) -> str:
        return "stdout"

    def send(self, data: UserEvent) -> SendResult:
        print(f"Deliver[{self.name}] data: {data}")
        return SendResult(ok=True, reason="OK")
