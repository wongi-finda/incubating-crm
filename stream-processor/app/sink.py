from bytewax.outputs import StatelessSinkPartition, DynamicSink
import grpc

from pb.campaign_service_pb2_grpc import CampaignStub
from pb.campaign_service_pb2 import UserEventMessage


class _CampaignServiceSinkPartition(StatelessSinkPartition[UserEventMessage]):
    def __init__(self, stub: CampaignStub):
        self.stub = stub

    def write_batch(self, items: list[UserEventMessage]) -> None:
        for item in items:
            res = self.stub.NotifyUserEvent(item)
            print(res)


class CampaignServiceSink(DynamicSink):
    def __init__(self):
        channel = grpc.insecure_channel("localhost:50051")
        self.stub = CampaignStub(channel)

    def build(
            self,
            step_id: str,
            worker_index: int,
            worker_count: int,
    ) -> _CampaignServiceSinkPartition:
        return _CampaignServiceSinkPartition(stub=self.stub)
