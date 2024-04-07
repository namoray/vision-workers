#!/bin/bash
cleanup() {
  echo "Stopping the ComfyUI server..."
  kill $COMFY_SERVER_PID
  wait $COMFY_SERVER_PID 2>/dev/null
  echo "Both servers have been stopped."
}

trap cleanup SIGINT SIGTERM

./setup.sh

vram_mode=${VRAM_MODE:-}
warmup=$(echo ${WARMUP:-true} | tr '[:upper:]' '[:lower:]')

if [ -n "$vram_mode" ]
then
    python ComfyUI/main.py $vram_mode --disable-xformers &
else
    python ComfyUI/main.py --disable-xformers &
fi


COMFY_SERVER_PID=$!
echo "ComfyUI server started with PID: $COMFY_SERVER_PID"
sleep 5

if [ "$warmup" = "true" ]
then
    python warmup.py
else
    sleep 1
fi

uvicorn main:app --host 0.0.0.0 --port 6919
cleanup
