#!/bin/bash
cleanup() {
    echo "Stopping the server..."
    kill $(lsof -t -i:${PORT})
    while lsof -i:${PORT} >/dev/null; do
        echo "Waiting for process to stop..."
        sleep 1
    done
    
    echo "Stopped"
}


start_entrypoint() {
    cd llm_server
    ./entrypoint.sh &
    cd ..
}

trap cleanup EXIT

cleanup
start_entrypoint

while true; do
    branch_name=$(git rev-parse --abbrev-ref HEAD)
    

    local_commit=$(git rev-parse HEAD)
  
    git fetch origin ${branch_name}

    remote_commit=$(git rev-parse origin/${branch_name})
    
    # Check if an update is required
    if [[ ${local_commit} != ${remote_commit} ]]; then
        echo "Local branch is not up-to-date. Updating..."
        git reset --hard ${remote_commit}
        if [ $? -eq 0 ]; then
            echo "Updated local repo to latest version: $remote_tag"
            echo "Running the autoupdate steps..."
            # Kill the old process
            
            cleanup
            
            # Run any steps needed to update, other than getting the new code
            ./autoupdate_llm.sh
            
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