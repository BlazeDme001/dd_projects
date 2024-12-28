import os
import shutil

# download_folder = os.path.join(os.getcwd(), 'cctv_downloads')

def delete_folder(download_folder):
    # Get a list of all files in the folder
    try:
        # download_folder = os.path.join(os.getcwd(), 'cctv_downloads')

        # Remove the entire directory tree
        shutil.rmtree(download_folder)
        os.makedirs(download_folder, exist_ok=True)
    except:
        pass

