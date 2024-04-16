#!/bin/bash
cleanup() {
    echo "Stopping the ComfyUI server..."
    kill $COMFY_SERVER_PID
    wait $COMFY_SERVER_PID 2>/dev/null
    echo "Both servers have been stopped."
}

trap cleanup SIGINT SIGTERM

source activate venv

cd /app/image_server/

./setup.sh

vram_mode=${VRAM_MODE:-}
warmup=$(echo ${WARMUP:-true} | tr '[:upper:]' '[:lower:]')
device=${DEVICE:-0}
port=${PORT:-6919}

if [ -n "$vram_mode" ]
then
    cd /app/image_server/ComfyUI
    python main.py $vram_mode --cuda-device $device --disable-xformers &
else
    cd /app/image_server/ComfyUI
    python main.py --disable-xformers  --cuda-device $device &
fi


COMFY_SERVER_PID=$!
echo "ComfyUI server started with PID: $COMFY_SERVER_PID"
sleep 5

if [ "$warmup" = "true" ]
then
    cd /app/image_server/
    if [ -n "$vram_mode" ] && [ "$vram_mode" = "--highvram" ]
    then
        python warmup.py --highvram
    else
        python warmup.py
    fi
else
    sleep 1
fi

cd /app/image_server/
uvicorn main:app --host 0.0.0.0 --port $port --workers 1
cleanup
