import grpc

from pb.campaign_service_pb2_grpc import CampaignServicer
from pb.campaign_service_pb2 import UserEvent, Response
from app.services.campaign import CampaignService


class CampaignRouter(CampaignServicer):
    def __init__(self, campaign_service: CampaignService):
        self.campaign_service = campaign_service

    def NotifyUserEvent(self, request: UserEvent, context: grpc.ServicerContext):
        try:
            self.campaign_service.handle_user_event(request)
            return Response(success=True, reason="OK")
        except Exception as e:
            print(e)
            return Response(success=False, reason=str(e))
