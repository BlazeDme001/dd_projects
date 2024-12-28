import subprocess
import platform
import multiprocessing


def run_batch_files_parallel(batch_files):
    processes = []

    for batch_file in batch_files:
        # Start a new process for each batch file
        process = subprocess.Popen(batch_file, shell=True)
        processes.append(process)

    # Wait for all processes to finish
    for process in processes:
        process.wait()

def run_batch_in_windows():
    try:
        batch_files = ["cctv.bat", "camera.bat", "lan.bat", "network.bat", "surveillance.bat", "switchs.bat", "UAN.bat", "UAV2.bat", "drone.bat"]
        run_batch_files_parallel(batch_files)
    except:
        pass


def run_py_files_script(script):
    subprocess.run(['python3', script])
    
def run_batch_in_linux():
    files = ['main_camera.py', 'main_lan.py', 'main_network.py', 'main_cctv.py', 'main_drone.py', 'main_surveillance.py', 'main_switch.py', 'main_uav.py', 'main_uav2.py']
    try:
        with multiprocessing.Pool() as pool:
            pool.map(run_py_files_script, files)
    except:
        pass


cur_os_1 = platform.system()
if cur_os_1 == 'Windows':
    run_batch_in_windows()
elif cur_os_1 == 'Linux':
    run_batch_in_linux()
