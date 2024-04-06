#!/bin/bash
cleanup() {
  echo "Stopping the ComfyUI server..."
  kill $COMFY_SERVER_PID
  wait $COMFY_SERVER_PID 2>/dev/null
  echo "Both servers have been stopped."
}

trap cleanup SIGINT SIGTERM

./setup.sh
python ComfyUI/main.py --lowvram &


COMFY_SERVER_PID=$!
echo "ComfyUI server started with PID: $COMFY_SERVER_PID"
sleep 5

uvicorn main:app --host 0.0.0.0 --port 6919
cleanup
