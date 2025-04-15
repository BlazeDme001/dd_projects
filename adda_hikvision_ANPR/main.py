import os
import requests
import pandas as pd
import json
from datetime import datetime
from requests.auth import HTTPDigestAuth
import time
import schedule


base_path = 'Downloads'
os.makedirs(base_path, exist_ok=True)


def check_service():
    url = "http://103.223.15.47:5023//api/services"
    headers = {"Content-Type": "application/json"}
    data = {
        "username": "Nirwana_API",
        "password": "Qn@62",
        "project": "Nirwana Groups",
        "sub_project": "Nirwana Hights",
        "service": "ANPR"
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
    except:
        print('Driver stopped')
        return 'OFF', '30'  # Default status OFF with a check time of 30 days

    if response.status_code == 200 and response.json().get('services'):
        service_data = response.json()['services'][0]
        status = service_data.get('status', 'OFF')
        return status

    return 'OFF'


def get_adda_access_token():
    url = "https://indiaapi.adda.io/api/auth/login"

    payload = json.dumps({
    "email": "ashish@shreenathgroup.in",
    "password": "W,#yxeNC2E2RMO!^"
    })
    headers = {
    'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)
    if response.status_code == 200:
        response_json = response.json()  # Parse the response to JSON
        access_token = response_json.get('access_token')  # Safely get 'access_token'
        print("Access Token:", access_token)
        return access_token
    else:
        print("Failed to login:", response.status_code, response.text)
        return None


def get_adda_vehicle_data():
    access_token = get_adda_access_token()
    if not access_token:
        return None

    url = "https://indiaapi.adda.io/api/vehicle/sync?timestamp="

    headers = {
        'token': 'r8mts953ndsm7bu4zqc7qs6wdajnt49m',
        # 'apt': '000153922',
        'apt': '133516',
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.request("GET", url, headers=headers)

    if response.status_code == 200:
        print("Vehicle data received!")
        return response.json()
    else:
        print("Failed to fetch vehicle data:", response.status_code, response.text)
        return None


def save_vehicle_data_to_csv():
    try:
        vehicle_data = get_adda_vehicle_data()
    except:
        print("Error fetching vehicle data")
    if not vehicle_data:
        print("No vehicle data to save.")
        return False
    try:
        df = pd.DataFrame(vehicle_data)
        current_time = datetime.now().strftime('%Y%m%d%H%M')
        file_path = os.path.join('Downloads', f'vehicle_data_{current_time}.csv')
        df.to_csv(file_path, index=True)

        print(f"Vehicle data saved to {file_path}")
        return file_path
    except:
        print("Error saving vehicle data to CSV")
        return False


def compire_csv(new_file_path):
    try:
        # List all CSV files in Downloads folder
        csv_files = [f for f in os.listdir(base_path) if f.startswith('vehicle_data_') and f.endswith('.csv')]
        if len(csv_files) < 2:
            print("Not enough CSV files to compare.")
            return None, None

        # Sort files by timestamp extracted from filename
        csv_files.sort(reverse=True)

        latest_file = os.path.join(base_path, csv_files[0])
        second_latest_file = os.path.join(base_path, csv_files[1])

        print(f"Comparing:\nLatest: {latest_file}\nOld: {second_latest_file}")

        # Read both CSVs
        df_new = pd.read_csv(latest_file)
        df_old = pd.read_csv(second_latest_file)

        # Assuming you are comparing on 'vehicle_no' column
        new_vehicle_nos = set(df_new['vehicle_no'])
        old_vehicle_nos = set(df_old['vehicle_no'])

        only_in_new = new_vehicle_nos - old_vehicle_nos
        only_in_old = old_vehicle_nos - new_vehicle_nos

        df_only_in_new = df_new[df_new['vehicle_no'].isin(only_in_new)].reset_index(drop=True)
        df_only_in_old = df_old[df_old['vehicle_no'].isin(only_in_old)].reset_index(drop=True)

        return df_only_in_new, df_only_in_old

    except Exception as e:
        print("Error comparing CSVs:", e)
        return None, None
    
    
def add_vehicle_to_hikvision(v_no):
    url = "https://103.223.15.97:810/ISAPI/ITC/Entrance/VCL"

    payload = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n
    <SetVCLData>\r\n
    <VCLDataList>\r\n
    <singleVCLData>\r\n
    <id>0</id>\r\n
    <runNum>0</runNum>\r\n
    <listType>0</listType>\r\n
    <plateNum>{v_no}</plateNum>\r\n
    <cardNo></cardNo>\r\n
    <startTime>0000-00-00T00:00:00Z</startTime>\r\n
    <endTime>0000-00-00T00:00:00Z</endTime>\r\n
    </singleVCLData>\r\n
    </VCLDataList>\r\n
    </SetVCLData>"""

    headers = {
    'Content-Type': 'application/xml'
    }
    username = 'admin'
    password = 'Nirwana@40000'

    # response = requests.request("PUT", url, headers=headers, data=payload, auth=HTTPDigestAuth(username, password), verify=False)

    # if response.status_code == 200:
    #     return True
    # return False
    print('Added')
    return True


def del_vehicle_to_hikvision(v_no):
    url = "https://103.223.15.97:810/ISAPI/ITC/Entrance/VCL"

    payload = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>\r\n
    <VCLDelCond>\r\n
    <delVCLCond>1</delVCLCond>\r\n
    <plateNum>{v_no}</plateNum>\r\n
    <plateColor>0</plateColor>\r\n
    <plateType>0</plateType>\r\n
    <cardNo>12345</cardNo>\r\n
    </VCLDelCond>"""

    headers = {
    'Content-Type': 'application/xml'
    }
    username = 'admin'
    password = 'Nirwana@40000'

    # response = requests.request("DELETE", url, headers=headers, data=payload, auth=HTTPDigestAuth(username, password), verify=False)
    # if response.status_code == 200:
    #     return True
    # else:
    #     return False

    print('Deleted')
    return True


def keep_latest_csv_and_cleanup(latest_csv_path):
    try:
        csv_files = [f for f in os.listdir(base_path) if f.startswith('vehicle_data_') and f.endswith('.csv')]

        csv_paths = [os.path.join(base_path, f) for f in csv_files]

        for file_path in csv_paths:
            if file_path != latest_csv_path:
                try:
                    os.remove(file_path)
                    print(f"Deleted old CSV file: {file_path}")
                except Exception as e:
                    print(f"Error deleting file {file_path}: {e}")

        print("Cleanup completed! Only the latest CSV is kept.")
        return True

    except Exception as e:
        print("Error during CSV cleanup:", e)
        return False


def main():
    service = check_service()
    if service != 'ON':
        return False
    saved = save_vehicle_data_to_csv()
    print(f'Path: {saved}')
    if not saved:
        return False

    new_df, old_df = compire_csv(new_file_path=saved)
    if new_df.empty or old_df.empty:
        return False
    if not new_df.empty:
        new_vehicle_list = set(new_df['vehicle_no'])
        for v_no in new_vehicle_list:
            print(f'Going to add: {v_no}')
            if v_no not in ('Null', 'NULL', 'null', 'NA', 'N/A', 'na', None):
                add_status = add_vehicle_to_hikvision(v_no)
                if add_status:
                    print(f"Vehicle {v_no} added to Hikvision successfully.")
                else:
                    print(f"Failed to add vehicle {v_no} to Hikvision.")
    if not old_df.empty:
        old_vehicle_list = set(old_df['vehicle_no'])
        for v_no in old_vehicle_list:
            print(f'Going to del: {v_no}')
            if v_no not in ('Null', 'NULL', 'null', 'NA', 'N/A', 'na', None):
                del_status = del_vehicle_to_hikvision(v_no)
                if del_status:
                    print(f"Vehicle {v_no} deleted to Hikvision successfully.")
                else:
                    print(f"Failed to deleted vehicle {v_no} to Hikvision.")
    time.sleep(10)
    keep_latest_csv_and_cleanup(latest_csv_path=saved)



# **Run the script every day at a fixed time (e.g., 9 AM)**
schedule.every().day.at("09:00").do(main)

if __name__ == "__main__":
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)
        except:
            print('Error occurred')
        

