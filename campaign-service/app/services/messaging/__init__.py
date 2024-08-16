from app.schemas.campaign import CampaignChannel
from app.services.messaging.channels.base import BaseChannel
from app.services.messaging.channels import (
    StdoutSender, Noti10000Sender, Noti10001Sender,
)

all_channels = {
    StdoutSender(),
    Noti10000Sender(),
    Noti10001Sender(),
}


class MessagingService:
    def __init__(self):
        self._channel_sender_map: dict[str, BaseChannel] = {
            ch.name: ch
            for ch in all_channels
        }

    @property
    def available_senders(self) -> list[str]:
        return list(self._channel_sender_map.keys())

    def send(self, channel: CampaignChannel, data):
        sender = self._channel_sender_map.get(channel)
        if sender is None:
            # TODO
            raise KeyError()

        sender.send(data)
