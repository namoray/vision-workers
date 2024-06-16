# Steps setup env, build and run docker image

1. **Start by creating a volume**

```bash
docker volume create validator
```

2. **Run orchestrator docker container**

```bash
docker run -d --name validator --gpus all --runtime=nvidia -p 6920:6920 -v validator:/app corcelio/vision:orchestrator-latest
```