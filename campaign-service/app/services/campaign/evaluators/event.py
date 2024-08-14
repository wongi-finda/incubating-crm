from app.schemas.campaign import ActionBasedDeliveryCampaign
from app.models import UserEvent


class EventPropertyEvaluator:
    def evaluate(self, campaign: ActionBasedDeliveryCampaign, event: UserEvent) -> bool:
        property_filters = campaign["trigger_action"]["property_filters"]
        if not property_filters:
            return True

        return True
