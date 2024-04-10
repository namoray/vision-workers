```bash
PYTHON_VERSION=3.10.13
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
chmod 700 Miniconda3-latest-Linux-x86_64.sh
./Miniconda3-latest-Linux-x86_64.sh -b -u

# Setup Conda environment
echo 'source "$HOME/miniconda3/etc/profile.d/conda.sh"' >> ~/.bashrc && \
echo 'if [ -f ~/.bashrc ]; then . ~/.bashrc; fi' >> ~/.bash_profile && \
echo 'source "$HOME/miniconda3/etc/profile.d/conda.sh"' >> ~/.profile && \
source ~/.bashrc

conda create -n venv python=$PYTHON_VERSION -y
conda activate venv

echo "conda activate venv" >> ~/.bashrc
```