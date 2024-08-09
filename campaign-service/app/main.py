from concurrent import futures

import grpc

from pb.campaign_service_pb2_grpc import (
    CampaignServiceServicer, add_CampaignServiceServicer_to_server,
)
from pb.campaign_service_pb2 import UserEvent, Response


class CampaignScheduler(CampaignServiceServicer):
    def NotifyUserEvent(self, request: UserEvent, context: grpc.ServicerContext):
        print(request)
        return Response(
            success=True,
            reason="OK",
        )


def serve():
    port = 50051
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
    add_CampaignServiceServicer_to_server(CampaignScheduler(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    print(f"Server started, listening on {port}")
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
