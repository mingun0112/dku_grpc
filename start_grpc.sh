#!/bin/bash

echo "Updating system packages..."
sudo apt update -y

echo "Installing Python and pip..."
sudo apt install python3 python3-pip -y
sudo apt install tmux
python3 -m grpc_tools.protoc -I./proto --python_out=. --grpc_python_out=. ./proto/video_concat.proto

pip3 install -r requirements.txt

tmux new-session -d -s dku_grpc

echo "Starting server..."
tmux send-keys "python3 server.py" C-m
sleep 2

tmux split-window -h


tmux split-window -v

tmux select-pane -t 1


tmux split-window -v

tmux select-pane -t 3

tmux split-window -v

tmux select-pane -t 1
echo "Starting client1..."
tmux send-keys "python3 client.py client1 ./video/1.mp4" C-m
sleep 2

tmux select-pane -t 2
echo "Starting client2..."
tmux send-keys "python3 client.py client2 ./video/2.mp4" C-m
sleep 2

tmux select-pane -t 3
echo "Starting client3..."
tmux send-keys "python3 client.py client3 ./video/3.mp4" C-m
sleep 2

tmux select-pane -t 4
echo "Starting client4..."
tmux send-keys "python3 client.py client4 ./video/4.mp4" C-m
sleep 2

tmux attach -t dku_grpc
