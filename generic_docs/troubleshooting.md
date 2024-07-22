# Troubleshooting

# Issues with dpkg

Some hosting providers run post-boot initialisation scripts that can block
`bootstrap.sh` from running. You will see this if the script complains that it
couldn't acquire a lock for dpkg because another process has it.

If this is the case, allow the machine to continue it's initialization (10-15 minutes) 
and then reattempt to run `bootstrap.sh`.

## `unknown or invalid runtime name: nvidia

Try this:

```bash
curl -s -L https://nvidia.github.io/nvidia-container-runtime/gpgkey | \
  sudo apt-key add -
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/nvidia-container-runtime/$distribution/nvidia-container-runtime.list | \
  sudo tee /etc/apt/sources.list.d/nvidia-container-runtime.list
sudo apt-get update
apt-get install nvidia-container-runtime
sudo systemctl restart docker
```

if that still doesn't work run this:

- If you're using conda, check conda is activated. Else;

```bash
apt-get install ubuntu-drivers-common \
	&& sudo ubuntu-drivers autoinstall

# reboot your machine, you may have to wait a while ot reconenct
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
**IF THAT STILL DOESN'T WORK**

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

If it still fails, I would advise doing a full cuda installation as detailed here:

[Full CUDA installation](full_cuda_install.md)

## `Unable to acquire the dpkg frontend lock (/var/lib/dpkg/lock-frontend), is another process using it?`
That implies you still have some installation process running. Options:

1. Wait a while (I would advise this first!)
2. Try to kill it (only if you're sure it shouldnt be running)
- ps aux | grep -i apt
-  kill -9 [PID OF PROCESS]