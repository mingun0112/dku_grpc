import grpc
import cv2
import video_concat_pb2
import video_concat_pb2_grpc
import numpy as np
import os
import time
import argparse

def stream_video(client_id, video_path):
    with grpc.insecure_channel('localhost:50051') as channel:
        stub = video_concat_pb2_grpc.VideoProcessingServiceStub(channel)
        cap = cv2.VideoCapture(video_path)

        # 클라이언트 폴더가 없으면 생성
        if not os.path.exists(client_id):
            os.makedirs(client_id)

        def frame_generator():
            while cap.isOpened():
                ret, frame = cap.read()
                if not ret:
                    break
                _, buffer = cv2.imencode('.jpg', frame)
                yield video_concat_pb2.FrameRequest(
                    client_id=client_id,
                    frame_data=buffer.tobytes()
                )

        response_iterator = stub.StreamFrames(frame_generator())
        for idx, response in enumerate(response_iterator):
            # 수신한 합성 프레임 디코딩
            print(f"Received result {idx + 1}")
            concat_frame = np.frombuffer(response.frame_data, dtype=np.uint8)
            frame = cv2.imdecode(concat_frame, cv2.IMREAD_COLOR)

            # 결과를 폴더에 프레임 번호와 타임스탬프를 포함한 파일명으로 저장
            # timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"{client_id}/client_{client_id}_frame_{idx + 1}.jpg"
            cv2.imwrite(filename, frame)

        cap.release()
        cv2.destroyAllWindows()

def parse_arguments():
    parser = argparse.ArgumentParser(description="Stream video frames to the server")
    parser.add_argument("client_id", type=str, help="The client ID (e.g., client1, client2, etc.)")
    parser.add_argument("video_path", type=str, help="Path to the video file")
    return parser.parse_args()

if __name__ == "__main__":
    # 명령행 인자 파싱
    args = parse_arguments()

    # 클라이언트 ID와 비디오 경로를 인자로 받아서 실행
    stream_video(args.client_id, args.video_path)
