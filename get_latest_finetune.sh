

cd ~/vision-workers/utils
apt install git-lfs
git lfs install
huggingface-cli lfs-enable-largefiles .
git clone https://huggingface.co/zzttbrdd/sn6_00l
mv sn6_00l sn6-finetune
cd sn6-finetune
rm -rf .git
git remote remove origin
git remote add origin https://huggingface.co/tau-vision/sn6-finetune
huggingface-cli upload --repo-type model --revision new_model  tau-vision/sn6-finetune
