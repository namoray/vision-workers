#!/bin/bash

if [ "$#" -lt 1 ]; then
  echo "Usage: $0 container_name_or_id_1 [container_name_or_id_2 ... container_name_or_id_N]"
  exit 1
fi

detach_tmux() {
  tmux kill-session -t my_session
  exit 0
}

trap 'detach_tmux' SIGINT

# Kill any existing session with the same name
tmux kill-session -t my_session 2>/dev/null

# Start a new tmux session with a name
tmux new-session -d -s my_session

index=0
pane_index=0
for container in "$@"; do
  if [ $index -gt 0 ]; then
    tmux split-window -h -t $pane_index
    tmux select-layout -t my_session tiled
    pane_index=$((pane_index + 1))
  fi
  tmux send-keys -t $pane_index "watch -n 1 docker logs --tail 10 $container" C-m
  index=$((index + 1))
done

tmux attach-session -t my_session

detach_tmux