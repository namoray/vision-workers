```bash
# Loop through and remove specific docker-related packages if they are installed
for pkg in docker.io docker-doc docker-compose docker-compose-v2 podman-docker containerd runc; do 
    sudo apt-get remove $pkg -y; 
done

# Update the package lists for upgrades and new package installations
sudo apt-get update -y

# Install necessary packages for fetching files over HTTPS
sudo apt-get install ca-certificates curl -y

# Create a directory for apt keyrings and set permissions
sudo install -m 0755 -d /etc/apt/keyrings

# Download Docker's official GPG key and save it to the keyrings directory
sudo curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc

# Set read permissions for the Docker GPG key for all users
sudo chmod a+r /etc/apt/keyrings/docker.asc

# Add Docker's APT repository to the sources list of apt package manager
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" | \
  sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Update the apt package list after adding new repository
sudo apt-get update -y

# Install Docker Engine, CLI, containerd, and Docker compose plugins
sudo apt-get install docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin -y

# Test Docker installation by running the hello-world container
docker run hello-world
```