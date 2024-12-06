import grpc
from concurrent import futures
import cv2
import numpy as np
import video_concat_pb2
import video_concat_pb2_grpc

class VideoProcessingService(video_concat_pb2_grpc.VideoProcessingServiceServicer):
    def __init__(self):
        # 클라이언트별 최신 프레임 저장 (초기값은 None)
        self.frames = {f"client{i}": None for i in range(1, 5)}
        # 프레임 크기
        self.frame_width = 640
        self.frame_height = 480
        # 클라이언트 연결 상태 추적 (True: 연결됨, False: 연결 끊어짐)
        self.client_connected = {f"client{i}": False for i in range(1, 5)}

    def _concat_frames(self):
        """2x2로 프레임 합성"""
        black_frame = np.zeros((self.frame_height, self.frame_width, 3), dtype=np.uint8)

        # 각 클라이언트의 프레임 크기를 고정
        processed_frames = []
        for client_id in self.frames:
            if self.frames[client_id] is None or not self.client_connected[client_id]:
                processed_frames.append(black_frame)  # 연결이 끊어진 클라이언트는 검정 화면으로
            else:
                resized_frame = cv2.resize(self.frames[client_id], (self.frame_width, self.frame_height))
                processed_frames.append(resized_frame)

        # 2x2 합성
        top_row = cv2.hconcat(processed_frames[:2])  # client1 + client2
        bottom_row = cv2.hconcat(processed_frames[2:])  # client3 + client4
        final_frame = cv2.vconcat([top_row, bottom_row])  # 합치기

        return final_frame

    def StreamFrames(self, request_iterator, context):
        """클라이언트로부터 받은 프레임을 합성하여 전송"""
        for request in request_iterator:
            client_id = request.client_id
            frame_data = np.frombuffer(request.frame_data, dtype=np.uint8)
            frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)

            # 클라이언트 프레임 업데이트
            if not self.client_connected[client_id]:
                # 연결된 시점에 한 번만 출력
                self.client_connected[client_id] = True
                self._print_connected_clients()  # 연결된 클라이언트 출력

            self.frames[client_id] = frame

            # 2x2로 합성
            concat_frame = self._concat_frames()

            # 합성된 프레임을 JPEG로 인코딩
            _, buffer = cv2.imencode('.jpg', concat_frame)

            # 모든 클라이언트로 결과 전송
            yield video_concat_pb2.FrameResponse(frame_data=buffer.tobytes())

    def StopClient(self, client_id):
        """클라이언트가 종료되었을 때 호출되는 메서드로, 연결 상태를 변경"""
        if self.client_connected[client_id]:
            self.client_connected[client_id] = False
            self.frames[client_id] = None  # 프레임을 None으로 설정 (검정 화면으로 대체)
            self._print_connected_clients()  # 연결 끊긴 클라이언트 출력

    def _print_connected_clients(self):
        """현재 연결된 클라이언트와 해제된 클라이언트를 출력"""
        connected_clients = [client_id for client_id, connected in self.client_connected.items() if connected]
        disconnected_clients = [client_id for client_id, connected in self.client_connected.items() if not connected]

        print("Connected clients:", connected_clients)
        print("Disconnected clients:", disconnected_clients)

def serve():
    """서버 시작"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    video_concat_pb2_grpc.add_VideoProcessingServiceServicer_to_server(VideoProcessingService(), server)
    server.add_insecure_port('[::]:50051')
    print("Server started on port 50051.")
    server.start()
    server.wait_for_termination()

if __name__ == "__main__":
    serve()
