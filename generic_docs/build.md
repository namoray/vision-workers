
# Steps setup env, build and run docker image

## THIS IS TO BUID TO RUN LOCALLY, YOU WONT NEED TO DO THIS TO RUN IT. JUST FOLLOW THE READ ME IN IMAGE_SERVER/LLM_SERVER/ORCHESTRATOR

## Pre-requisties
`WITH_AUTOUPDATES=0 sudo -E ./bootstrap.sh`

### Building docker container

To build:
```bash
nohup docker build -t corcelio/vision:orchestrator-latest -f Dockerfile.orchestrator . > build.log 2>&1 &
```

To run:
```bash
docker run --gpus all --runtime=nvidia -p 6920:6920 corcelio/vision:orchestrator-latest
```

If that doesn't work:
```bash
docker run --gpus all  -p 6920:6920 corcelio/vision:orchestrator-latest
```


**Combined command**
```bash
docker build -t corcelio/vision:orchestrator-latest .
docker run --gpus all  -p 6920:6920 corcelio/vision:orchestrator-latest
```

**Combined command for local dev/ testing**
NOTE: this will use prod image server & llm server images unless otherwise specified
```bash
docker build -t corcelio/test:orch-test . -f Dockerfile.orchestrator
docker run -p 6920:6920 -e PORT=6920 -e CUDA_VISIBLE_DEVICES=0 -e DEVICE=0 --gpus '"device=0"' --runtime=nvidia corcelio/test:orch-test
```
or
NOTE: this will use prod image server & llm server images unless otherwise specified
```bash
docker kill orchestrator || true; docker build -t corcelio/test:orch-test . -f Dockerfile.orchestrator; ./launch_orchestrator.sh --orchestrator-image corcelio/test:orch-test --dont-refresh-local-images
```

**Build all**
```bash
docker build -t corcelio/test:orch-test . -f Dockerfile.orchestrator
docker build -t corcelio/test:llm-test . -f Dockerfile.llm_server
docker build -t corcelio/test:image-test . -f Dockerfile.image_server
```

**Run with orch**


```bash
./launch_orchestrator.sh --orchestrator-image corcelio/test:orch-test --llm-image corcelio/test:llm-test --image-server-image corcelio/test:image-test --dont-refresh-local-images
```

```bash
docker run --name image-test --rm -v HF:/app/cache -v COMFY:/app/image_server/ComfyUI -p 6918:6919 --runtime=nvidia --gpus=all -e PORT=6919 -e DEVICE=0  corcelio/test:image-test
```
or 
```bash
docker kill image-test || true; docker build -t corcelio/test:image-test . -f Dockerfile.image_server; docker run --name image-test --rm -v HF:/app/cache -v COMFY:/app/image_server/ComfyUI -p 6918:6919 --runtime=nvidia --gpus=all -e PORT=6919 -e DEVICE=0  corcelio/test:image-test
```


### Uploading to docker hub
Get your credentials ready for docker hub
```bash
docker login
```

```bash
docker push corcelio/vision:orchestrator-latest
```


### Trouble shooting
If you run into any Cuda prbs during build/run (especially with the argyment --runtime=nvidia), make sure to do this, then restart the last steps :
```bash
sudo nano /etc/docker/daemon.json
```

-> Change it to this : (define the default-runtime)
```json
{
  "default-runtime": "nvidia",
  "runtimes": {
    "nvidia": {
      "path": "nvidia-container-runtime",
      "runtimeArgs": []
    }
  }
}
```

```bash
sudo systemctl restart docker
```

-> If you still can't run the image using gpu, it's surely a problem with Nvidia Drivers, follow steps on this link
```bash
# make sure this generates a correct output (gpu is detected)
lspci -vv | grep -i nvidia

# install drivers
apt-get install ubuntu-drivers-common \
	&& sudo ubuntu-drivers autoinstall

# reboot
sudo reboot now

curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | \
  sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-runtime.list
sudo apt-get update
apt-get install nvidia-container-runtime
sudo systemctl restart docker
```