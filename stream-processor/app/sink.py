from bytewax.outputs import StatelessSinkPartition, DynamicSink
import grpc

from pb.campaign_service_pb2_grpc import CampaignServiceStub
from pb.campaign_service_pb2 import UserEvent
from app.model import CampaignTrigger


class _CampaignServiceSinkPartition(StatelessSinkPartition[CampaignTrigger]):
    def __init__(self, campaign_service_stub: CampaignServiceStub):
        self.stub = campaign_service_stub

    def write_batch(self, items: list[CampaignTrigger]) -> None:
        for item in items:
            # print(f"An user[{item.user_id}] triggers '{item.type}' of the campaign[{item.campaign_id}]")
            user_event = UserEvent(event="event_A", user_id=item.user_id)
            res = self.stub.NotifyUserEvent(user_event)
            print(res)


class CampaignServiceSink(DynamicSink):
    def __init__(self):
        channel = grpc.insecure_channel("localhost:50051")
        self.stub = CampaignServiceStub(channel)

    def build(
            self,
            step_id: str,
            worker_index: int,
            worker_count: int,
    ) -> _CampaignServiceSinkPartition:
        return _CampaignServiceSinkPartition(campaign_service_stub=self.stub)
