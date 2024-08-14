import grpc

from pb.campaign_service_pb2_grpc import CampaignServicer
from pb.campaign_service_pb2 import UserEventMessage, Response
from app.models import UserEvent
from app.services.campaign import CampaignService


class CampaignRouter(CampaignServicer):
    def __init__(self, campaign_service: CampaignService):
        self.campaign_service = campaign_service

    def NotifyUserEventEmitted(
            self,
            message: UserEventMessage,
            context: grpc.ServicerContext,
    ):
        try:
            event = UserEvent.from_message(message)
            self.campaign_service.handle_user_event(event)
            return Response(success=True, reason="OK")
        except Exception as e:
            print(e)
            return Response(success=False, reason=str(e))
