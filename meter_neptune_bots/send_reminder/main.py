import requests
import db_connect as db
import send_wp as wp
import time
import mail
import schedule
from datetime import datetime, timedelta


def check_service():
    url = "http://192.168.1.94:5001/api/services"
    headers = {"Content-Type": "application/json"}
    data = {
        "username": "Nirwana_API",
        "password": "Qn@62",
        "project": "Nirwana Groups",
        "sub_project": "Nirwana Hights",
        "service": "Meter Reading"
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


def main():
    status = check_service()
    
    if status == 'ON':
        check_last_send_query = """SELECT ext_col_2 FROM services.services WHERE service ='Meter Whatsapp';"""
        check_last_send_data = db.get_data_in_list_of_tuple(check_last_send_query)

        if check_last_send_data and check_last_send_data[0][0]:
            last_check_time = (datetime.now() - timedelta(days=1)).date()  # Compare with yesterday
            stored_date = datetime.strptime(check_last_send_data[0][0], '%Y-%m-%d %H:%M:%S').date()

            if stored_date == last_check_time:
                check_query = """
                SELECT DEVICE_SLNO, CA_NAME, PV_BAL, check_time, mobile, email, ca_address 
                FROM meter_api.meter_user_details 
                WHERE PV_BAL < REQ_BAL AND STATUS = 'Active';
                """
                check_data = db.get_data_in_list_of_tuple(check_query)
                
                if check_data:
                    for data in check_data:
                        print(data)
                        sub = f'Low balance reminder for device: {data[0]}'
                        body = f"""Dear {data[1]},\n\nYour prepaid DG meter balance for {data[6]} is low ({data[2]}).  
                        You are requested to recharge at the earliest to enjoy uninterrupted services.  

                        Regards,  
                        Team Nirwana Heights"""
                        
                        to_cc = []
                        to_add = [data[5]]  # Email
                        mob = data[4]  # Mobile
                        
                        wp.send_wp_msg(mob=mob, msg=body)
                        mail.send_mail(to_add=to_add, to_cc=to_cc, sub=sub, body=body)


# **Run the script every day at a fixed time (e.g., 9 AM)**
schedule.every().day.at("09:00").do(main)  # Change time if needed

if __name__ == "__main__":
    while True:
        try:
            schedule.run_pending()
            time.sleep(3600)  # Check every minute
        except:
            print('Error occurred')
        
