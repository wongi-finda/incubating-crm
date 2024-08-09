from bytewax.outputs import StatelessSinkPartition, DynamicSink

from app.model import ActionBasedCampaignTrigger


class _CampaignSchedulerSinkPartition(StatelessSinkPartition[ActionBasedCampaignTrigger]):
    def write_batch(self, items: list[ActionBasedCampaignTrigger]) -> None:
        # TODO: gRPC request
        for item in items:
            print(f"An user[{item.user_id}] triggers '{item.type}' of the campaign[{item.campaign_id}]")


class CampaignSchedulerSink(DynamicSink):
    def build(
            self,
            step_id: str,
            worker_index: int,
            worker_count: int,
    ) -> _CampaignSchedulerSinkPartition:
        return _CampaignSchedulerSinkPartition()
