#!/bin/bash
cleanup() {
  echo "Stopping the ComfyUI server..."
  kill $COMFY_SERVER_PID
  wait $COMFY_SERVER_PID 2>/dev/null
  echo "Both servers have been stopped."
}

trap cleanup SIGINT SIGTERM

./setup.sh

lowvram=false
highvram=false
warmup=false

while (( "$#" )); do
  case "$1" in
    --lowvram)
      lowvram=true
      shift
      ;;
    --highvram)
      highvram=true
      shift
      ;;
    --warmup)
      warmup=true
      shift
      ;;
    *)
      shift
      ;;
  esac
done

if $lowvram
then
    python ComfyUI/main.py --lowvram --disable-xformers &
elif $highvram
then
    python ComfyUI/main.py --highvram --disable-xformers  &
else
    python ComfyUI/main.py --disable-xformers  &
fi

COMFY_SERVER_PID=$!
echo "ComfyUI server started with PID: $COMFY_SERVER_PID"
sleep 5

if $warmup
then
    python warmup.py
else
    sleep 1
fi

uvicorn main:app --host 0.0.0.0 --port 6919
cleanup
