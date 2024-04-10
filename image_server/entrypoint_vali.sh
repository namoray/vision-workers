#!/bin/bash
cleanup() {
  echo "Stopping the ComfyUI server..."
  kill $COMFY_SERVER_PID
  wait $COMFY_SERVER_PID 2>/dev/null
  echo "Both servers have been stopped."
}

trap cleanup SIGINT SIGTERM

device=${DEVICE:-0}

source activate venv
cd /app/image_server/ComfyUI
python main.py --highvram --disable-xformers --cuda-device $device &

COMFY_SERVER_PID=$!
echo "ComfyUI server started with PID: $COMFY_SERVER_PID"
sleep 5

cd /app/image_server/
uvicorn main:app --host 0.0.0.0 --port 6919
cleanup
