from pymongo.collection import Collection

from app.db.mongo import db
from app.models import UserEvent
from app.schemas.campaign import (
    ScheduledDeliveryCampaign, ActionBasedDeliveryCampaign, CampaignStatus
)
from app.services.schedule import ScheduleService

Campaign = ScheduledDeliveryCampaign | ActionBasedDeliveryCampaign


class CampaignService:
    def __init__(self, schedule_service: ScheduleService):
        self.schedule_service = schedule_service
        self.collection: Collection[Campaign] = db.campaign

    def make_active(self, campaign: Campaign):
        # Make state 'active'
        self.collection.update_one(
            filter={"_id": campaign["_id"]},
            update={"$set": {"status": CampaignStatus.active}},
        )

        # Trigger scheduled delivery campaign
        if isinstance(campaign, ScheduledDeliveryCampaign):
            self.schedule_service.add_scheduled_delivery(
                callback=_deliver_scheduled_campaign,
                campaign=campaign,
            )

    def handle_user_event(self, event: UserEvent):
        # Find trigger campaigns
        trigger_campaigns = self.collection.find({
            "status": CampaignStatus.active,
            "delivery_type": "action-based",
            "trigger_action.type": "event-trigger",
            "trigger_action.trigger_event": event.event_name,
        })

        for campaign in trigger_campaigns:
            # TODO: property filters
            property_filters = campaign["trigger_action"]["property_filters"]
            if property_filters:
                ...

            # TODO: Evaluate user is qualified

            if not self.schedule_service.exists(campaign=campaign, user_id=event.user_id):
                self.schedule_service.add_action_based_delivery(
                    callback=_deliver_action_based_campaign,
                    campaign=campaign,
                    user_id=event.user_id,
                )

        # Find exception campaigns
        exception_campaigns = self.collection.find({
            "status": CampaignStatus.active,
            "delivery_type": "action-based",
            "exception_event": event.event_name,
        })

        for campaign in exception_campaigns:
            if self.schedule_service.exists(campaign=campaign, user_id=event.user_id):
                self.schedule_service.remove(
                    campaign=campaign,
                    user_id=event.user_id,
                )

    def handle_user_attribute(self):
        ...

    def launch(self, campaign: Campaign, **kwargs):
        campaign_id = campaign["_id"]

        match campaign:
            case ScheduledDeliveryCampaign():
                assert campaign["delivery_type"] == "scheduled"

                self.schedule_service.add_scheduled_delivery(
                    callback=_deliver_scheduled_campaign,
                    campaign=campaign,
                )

            case ActionBasedDeliveryCampaign():
                assert campaign["delivery_type"] == "scheduled"

                user_id = kwargs.get("user_id")
                if not user_id:
                    print(f"ERROR:  Try to launch action-based campaign[{campaign_id}] without user-id.")
                    raise RuntimeError()

                self.schedule_service.add_action_based_delivery(
                    callback=_deliver_action_based_campaign,
                    campaign=campaign,
                    user_id=user_id,
                )

            case _:
                delivery_type = campaign["delivery_type"]
                print(f"ERROR:  Invalid campaign[{campaign_id}] delivery type [{delivery_type}].")


def _deliver_scheduled_campaign(campaign: ScheduledDeliveryCampaign) -> None:
    campaign_id = campaign["_id"]
    print(f"Deliver scheduled delivery campaign[{campaign_id}]")


def _deliver_action_based_campaign(
        campaign: ActionBasedDeliveryCampaign,
        user_id: int,
) -> None:
    # Re-evaluate segment membership at send-time
    if campaign["re_eval_before_send"] and campaign["delay"]:
        ...

    campaign_id = campaign["_id"]
    print(f"Deliver action-based delivery campaign[{campaign_id}]({user_id=})")
