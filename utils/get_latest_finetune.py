from huggingface_hub import HfApi
from huggingface_hub import hf_hub_download
from huggingface_hub.utils import HfHubHTTPError

from dotenv import load_dotenv

import os

load_dotenv()

"""
Please run this before starting

cd ~/vision-workers/utils
apt install git-lfs
git lfs install
huggingface-cli lfs-enable-largefiles .

git clone https://huggingface.co/zzttbrdd/sn6_00l


"""

api = HfApi(token=os.getenv("ACCESS_TOKEN"))

source_repo_id = "zzttbrdd/sn6_00l"
destination_repo_id = "tau-vision/sn6-finetune"
new_branch_name = "21/04/2024"

# Create a new branch in the destination repository


try:
    # Create a new branch in the destination repository
    api.create_branch(repo_id=destination_repo_id, branch=new_branch_name)
except HfHubHTTPError as e:
    if e.response.status_code == 409:
        print(
            f"Branch '{new_branch_name}' already exists in the destination repository."
        )
    else:
        raise e


# # Get the list of files in the source repository
# # Get the list of files in the source repository
# source_files = api.list_repo_files(repo_id=source_repo_id)

# # Copy each file from the source repository to the destination repository
# for file_path in source_files:
#     try:
#         # Download the file content from the source repository
#         file_content = hf_hub_download(repo_id=source_repo_id, filename=file_path)

#         # Upload the file to the destination repository
#         api.upload_file(
#             path_or_fileobj=file_content,
#             path_in_repo=file_path,
#             repo_id=destination_repo_id,
#             repo_type="model",
#             branch=new_branch_name,
#         )
#         print(f"Copied file: {file_path}")
#     except Exception as e:
#         print(f"Error copying file '{file_path}': {str(e)}")
