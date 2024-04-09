#!/bin/bash

cleanup() {
  echo "Stopping the LLM_SERVER_PID server..."
  kill $LLM_SERVER_PID
  wait $LLM_SERVER_PID 2>/dev/null
  echo "Stopped"
}


original_dir=$(pwd)

# Change Directory to 'llm_server' and run the entrypoint script in the background
cd llm_server
./entrypoint.sh &
LLM_SERVER_PID=$!
cd "$original_dir"

# Run the llm_autoupdate script
python run_autoupdater.py --restart_script autoupdate_llm.sh --process_pid $LLM_SERVER_PID


cleanup()