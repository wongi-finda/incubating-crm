from concurrent import futures

import grpc

from pb.campaign_service_pb2_grpc import add_CampaignServicer_to_server
from app.routers.campaign import CampaignRouter
from app.services.schedule import ScheduleService
from app.services.campaign import CampaignService


def serve():
    port = 50051
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    server.add_insecure_port(f"[::]:{port}")

    # Create services
    schedule_service = ScheduleService()
    campaign_service = CampaignService(
        schedule_service=schedule_service,
    )

    # Add router(servicer)s to the server
    servicer = CampaignRouter(campaign_service=campaign_service)
    add_CampaignServicer_to_server(servicer, server)

    server.start()
    print(f"Server started, listening on {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
