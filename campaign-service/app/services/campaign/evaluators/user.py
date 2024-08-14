from app.schemas.campaign import ScheduledDeliveryCampaign, ActionBasedDeliveryCampaign


class UserEvaluator:
    def evaluate(
            self,
            campaign: ScheduledDeliveryCampaign | ActionBasedDeliveryCampaign,
            user_id: int,
    ) -> bool:
        # TODO
        return True
