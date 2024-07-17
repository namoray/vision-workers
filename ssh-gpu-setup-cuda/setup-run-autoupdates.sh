#!/bin/bash

usage() {
  echo "Usage: $0 -h <SSH_HOST> -k <SSH_KEY> -r <GIT_REPO> [-b <BRANCH_NAME>] [-u <SSH_USER>] [-p <SSH_PORT>] [-o <ORCHESTRATOR_IMAGE>] [-l <LLM_IMAGE>] [-i <IMAGE_SERVER_IMAGE>]"
  exit 1
}

SSH_USER="root"
SSH_PORT="22"
BRANCH_NAME="main"
ORCHESTRATOR_IMAGE="corcelio/vision:orchestrator-latest"
LLM_IMAGE="corcelio/vision:llm_server-latest"
IMAGE_SERVER_IMAGE="corcelio/vision:image_server-latest"

while getopts ":h:k:u:p:r:b:o:l:i:" opt; do
  case ${opt} in
    h)
      SSH_HOST=$OPTARG
      ;;
    k)
      SSH_KEY=$OPTARG
      ;;
    u)
      SSH_USER=$OPTARG
      ;;
    p)
      SSH_PORT=$OPTARG
      ;;
    r)
      GIT_REPO=$OPTARG
      ;;
    b)
      BRANCH_NAME=$OPTARG
      ;;
    o)
      ORCHESTRATOR_IMAGE=$OPTARG
      ;;
    l)
      LLM_IMAGE=$OPTARG
      ;;
    i)
      IMAGE_SERVER_IMAGE=$OPTARG
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      usage
      ;;
    :)
      echo "Option -$OPTARG requires an argument." >&2
      usage
      ;;
  esac
done

if [ -z "$SSH_HOST" ] || [ -z "$SSH_KEY" ] || [ -z "$GIT_REPO" ]; then
  usage
fi

echo -n "Enter Personal Access Token (PAT) for private repository (leave blank if public): "
read -s PAT
echo

echo -n "Enter Docker Username (leave blank if not needed): "
read DOCKER_USER
echo

if [ -n "$DOCKER_USER" ]; then
  echo -n "Enter Docker Password: "
  read -s DOCKER_PASSWORD
  echo
fi

chmod +x meta-setup.sh 
./meta-setup.sh -h $SSH_HOST -k $SSH_KEY -u $SSH_USER -p $SSH_PORT

if [ $? -eq 0 ]; then
  echo "meta-setup.sh completed successfully. Proceeding with git clone."

  if [ -z "$PAT" ]; then
    GIT_CMD="if [ -d '$(basename $GIT_REPO .git)' ]; then cd $(basename $GIT_REPO .git) && git pull origin $BRANCH_NAME; else git clone -b $BRANCH_NAME $GIT_REPO; fi"
  else
    GIT_CMD="if [ -d '$(basename $GIT_REPO .git)' ]; then cd $(basename $GIT_REPO .git) && git pull origin $BRANCH_NAME; else git clone -b $BRANCH_NAME https://$PAT@$GIT_REPO; fi"
  fi

  ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $SSH_KEY -p $SSH_PORT $SSH_USER@$SSH_HOST "$GIT_CMD"

  if [ $? -eq 0 ]; then
    echo "Git repository cloned and checked out to branch $BRANCH_NAME successfully."
    
    if [ -n "$DOCKER_USER" ] && [ -n "$DOCKER_PASSWORD" ]; then
      DOCKER_LOGIN_CMD="docker login -u $DOCKER_USER -p $DOCKER_PASSWORD &&"
    else
      DOCKER_LOGIN_CMD=""
    fi

    RUN_AUTO_UPDATES="${DOCKER_LOGIN_CMD} cd $(basename $GIT_REPO .git) && pm2 start --name run_autoupdates_validator --interpreter python3 run_autoupdates_validator.py -- --orchestrator_image $ORCHESTRATOR_IMAGE --llm_image $LLM_IMAGE --image_server_image $IMAGE_SERVER_IMAGE"
    ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -i $SSH_KEY -p $SSH_PORT $SSH_USER@$SSH_HOST "$RUN_AUTO_UPDATES"

    if [ $? -eq 0 ]; then
      echo "autoupdates started successfully."
    else
      echo "Failed to start autoupdates."
      exit 1
    fi

  else
    echo "Failed to clone the git repository or checkout to branch $BRANCH_NAME."
    exit 1
  fi
else
  echo "meta-setup.sh failed. Exiting."
  exit 1
fi