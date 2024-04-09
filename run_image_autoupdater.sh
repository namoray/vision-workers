#!/bin/bash
cleanup() {
  echo "Stopping the server..."
  kill $(lsof -t -i:${PORT})
  while lsof -i:${PORT} >/dev/null; do
    echo "Waiting for process to stop..."
    sleep 1
  # Kill comfy
  kill $(lsof -t -i:8188)
  while lsof -i:8188 >/dev/null; do
    echo "Waiting for process to stop..."
    sleep 1
  done
  
  echo "Stopped"
}

start_entrypoint() {
    cd image_server
    ./entrypoint.sh &
    cd ..
}


trap cleanup EXIT

start_entrypoint

while true; do
  # Get the current tag
  local_tag=$(git describe --abbrev=0 --tags)
  # Fetch the latest updates
  git fetch
  # Get the latest remote tag
  remote_tag=$(git describe --tags $(git rev-list --topo-order --tags HEAD --max-count=1))

  # Check if an update is required
  if [[ $local_tag != $remote_tag ]]; then
    echo "Local repo is not up-to-date. Updating..."
    git reset --hard $remote_tag
    if [ $? -eq 0 ]; then
      echo "Updated local repo to latest version: $remote_tag"
      echo "Running the autoupdate steps..."
      # Kill the old process

      cleanup

      # Run any steps needed to update, other than getting the new code
      ./autoupdate_image.sh

      # Restart the llm server
      start_entrypoint
      echo "Finished running the autoupdate steps! Ready to go 😎"
    else
      echo "Error in updating"
    fi
  else
    echo "Repo is up-to-date."
  fi
  # Wait for a while before checking again
  sleep 10
done


cleanup()