from pymongo.collection import Collection

from app.db.mongo import db
from app.models import UserEvent, UserAttribute
from app.schemas.campaign import (
    ScheduledDeliveryCampaign, ActionBasedDeliveryCampaign, CampaignStatus
)
from app.services.schedule import ScheduleService
from app.services.messaging import MessagingService
from app.services.campaign.evaluators.user import UserEvaluator
from app.services.campaign.evaluators.event import EventPropertyEvaluator

Campaign = ScheduledDeliveryCampaign | ActionBasedDeliveryCampaign


class CampaignService:
    def __init__(
            self,
            schedule_service: ScheduleService,
            messaging_service: MessagingService,
    ):
        self.collection: Collection[Campaign] = db.campaign

        self.schedule_service = schedule_service
        self.messaging_service = messaging_service

        self.user_evaluator = UserEvaluator()
        self.event_property_evaluator = EventPropertyEvaluator()

    # def set_active(self, campaign: Campaign):
    #     # Make state 'active'
    #     self.collection.update_one(
    #         filter={"_id": campaign["_id"]},
    #         update={"$set": {"status": CampaignStatus.active}},
    #     )
    #
    #     # Trigger scheduled delivery campaign
    #     if isinstance(campaign, ScheduledDeliveryCampaign):
    #         self.schedule_service.add_scheduled_delivery(
    #             callback=self._deliver_scheduled_campaign,
    #             campaign=campaign,
    #         )

    def handle_user_event(self, event: UserEvent) -> None:
        # Find trigger campaigns
        trigger_campaigns = self.collection.find({
            "status": CampaignStatus.active,
            "delivery_type": "action-based",
            "trigger_action.type": "event-trigger",
            "trigger_action.trigger_event": event.event_name,
        })

        for campaign in trigger_campaigns:
            # Evaluate qualifications
            if not self.event_property_evaluator.evaluate(campaign, event):
                continue
            if not self.user_evaluator.evaluate(campaign, event.user_id):
                continue

            # Schedule the delivery
            if not self.schedule_service.exists(campaign=campaign, action=event):
                self.schedule_service.add_action_based_delivery(
                    callback=self._deliver_event_triggered_campaign,
                    campaign=campaign,
                    action=event,
                )

        # Find exception campaigns
        exception_campaigns = self.collection.find({
            "status": CampaignStatus.active,
            "delivery_type": "action-based",
            "exception_event": event.event_name,
        })

        for campaign in exception_campaigns:
            # Unschedule the delivery
            if self.schedule_service.exists(campaign=campaign, action=event):
                self.schedule_service.remove(
                    campaign=campaign,
                    action=event,
                )

    def handle_user_attribute(self, attr: UserAttribute):
        # Find trigger campaigns
        trigger_campaigns = self.collection.find({
            "status": CampaignStatus.active,
            "delivery_type": "action-based",
            "trigger_action.type": "attribute-trigger",
            "trigger_action.trigger_event": attr.attribute_name,
        })

        for campaign in trigger_campaigns:
            # Evaluate qualifications
            if not self.user_evaluator.evaluate(campaign, attr.user_id):
                continue

            # Schedule the delivery
            if not self.schedule_service.exists(campaign=campaign, action=attr):
                self.schedule_service.add_action_based_delivery(
                    callback=self._deliver_attribute_triggered_campaign,
                    campaign=campaign,
                    action=attr,
                )

    def _deliver_scheduled_campaign(
            self,
            campaign: ScheduledDeliveryCampaign,
    ) -> None:
        campaign_id = campaign["_id"]

        # TODO: implement me
        print(f"Deliver scheduled delivery campaign[{campaign_id}]")

    def _deliver_event_triggered_campaign(
            self,
            campaign: ActionBasedDeliveryCampaign,
            event: UserEvent,
    ) -> None:
        # TODO: Re-evaluate segment membership at send-time

        campaign_id = campaign["_id"]
        print(f"Deliver action-based delivery campaign[{campaign_id}](user_id={event.user_id})")

    def _deliver_attribute_triggered_campaign(
            self,
            campaign: ActionBasedDeliveryCampaign,
            attr: UserAttribute,
    ) -> None:
        ...
