import requests
import db_connect as db
import send_wp as wp
import time
import mail
import schedule
from datetime import datetime, timedelta
import pandas as pd
import json
import requests

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors


LAST_RUN_FILE = "last_run.txt"

def read_last_run_date():
    try:
        with open(LAST_RUN_FILE, "r") as f:
            date_str = f.read().strip()
            return datetime.strptime(date_str, "%Y-%m-%d")
    except Exception:
        return None


def write_last_run_date(date):
    with open(LAST_RUN_FILE, "w") as f:
        f.write(date.strftime("%Y-%m-%d"))


def should_run_today():
    today = datetime.now().date()
    weekday = today.weekday()  # Monday = 0
    last_run = read_last_run_date()

    if weekday != 0:
        return False  # Not Monday

    if last_run is None:
        return True  # No history, run it

    days_since = (today - last_run).days
    return days_since >= 14  # Only run if 14+ days have passed


def check_service():
    url = "http://103.223.15.47:5023//api/services"
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


def send_good_bal():
    if not should_run_today():
        print("Skipping today. Either not Monday or it's been less than 14 days.")
        return
    check_query = """ SELECT DEVICE_SLNO, CA_NAME, PV_BAL, check_time, mobile, email, 
    ca_address, eb_pv_reading, dg_pv_reading FROM meter_api.meter_user_details 
    WHERE (PV_BAL > REQ_BAL or PV_BAL = REQ_BAL) AND STATUS = 'Active'; """
    check_data = db.get_data_in_list_of_tuple(check_query)
    if check_data:
        for data in check_data:
            print(data)
            try:
                total_unit = float(data[7]) + float(data[8])
                sub = f'Low balance reminder for device: {data[0]}'
                total_unit = float(data[7]) + float(data[8])
                body = f"""
                Dear *{data[1]} [Unit-{data[6]}*],\n
                Thank you for maintaining a positive balance in your prepaid electricity meter!
                # Current Meter Reading : *{total_unit:.2f} units*
                # Prepaid Wallet Balance: *₹{data[2]}/-*\n
                We appreciate your prompt recharges and request you to continue keeping a healthy balance to avoid any inconvenience.\n
                For any assistance, feel free and raise a *Support Ticket* in Adda App.\n
                Best Regards,
                Team Nirwana Maintainence\n
                _*Powered by DIGITAL DREAMS*_
                """
                mob = data[4]  # Mobile
                # mob = '9988880885'  # Mobile
                # mob = '7980328205'  # Mobile
                
                if mob and len(mob) > 9:
                    wp.send_wp_msg(mob=mob, msg=body)
            except:
                pass
                    

def main():
    try:
        status = check_service()
        if status == 'ON':
            try:
                get_all_api_data()
            except:
                pass
            check_last_send_query = """SELECT ext_col_1, ext_col_2 FROM services.services WHERE service ='Meter Whatsapp';"""
            check_last_send_data = db.get_data_in_list_of_tuple(check_last_send_query)

            if check_last_send_data and check_last_send_data[0][0]:
                last_check_time = (datetime.now() - timedelta(days=int(check_last_send_data[0][0]))).date()  # Compare with yesterday
                stored_date = datetime.strptime(check_last_send_data[0][1], '%Y-%m-%d %H:%M:%S').date()

                if stored_date <= last_check_time:
                    try:
                        send_good_bal()
                        pass
                    except:
                        pass
                    check_query = """ SELECT DEVICE_SLNO, CA_NAME, PV_BAL, check_time, mobile, email, 
                    ca_address, eb_pv_reading, dg_pv_reading FROM meter_api.meter_user_details 
                    WHERE PV_BAL < REQ_BAL AND STATUS = 'Active'; """
                    check_data = db.get_data_in_list_of_tuple(check_query)
                    msg_data = []
                    if check_data:
                        count = 0
                        sum = 0
                        send_count = 0
                        for data in check_data:
                            print(data)
                            try:
                                sub = f'Low balance reminder for device: {data[0]}'
                                total_unit = float(data[7]) + float(data[8])
                                body = f"""
                                Dear *{data[1].strip()}*,\n
                                Kindly note that the current reading of the prepaid electrical meter for Unit No *{data[6]}* is *{total_unit:.2f}* units as of today, and your current balance is *Rs {data[2]}*.\n
                                We kindly request you to maintain a *sufficient balance of Rs. 100* in your account to avoid any interruption in your power supply.\n
                                This is an automated message, please ignore if already paid.\n
                                Best regards,
                                Maintenance Team
                                Nirwana Group\n
                                _*Powered by DIGITAL DREAMS*_
                                """
                                
                                to_cc = []
                                to_add = [data[5]]  # Email
                                # to_add = ['ashish@shreenathgroup.in']  # Email
                                mob = data[4]  # Mobile
                                # mob = '9988880885'  # Mobile
                                # mob = '7980328205'  # Mobile
                                time.sleep(10)
                                msg_dict = {
                                    'Address': data[6],
                                    'Name': data[1].strip(),
                                    'Phone Number': mob,
                                    'PV Balance': data[2]
                                }
                                if mob and len(mob) > 9:
                                    send_count += 1
                                    wp.send_wp_msg(mob=mob, msg=body)
                                    msg_dict['Send'] = 'Yes'
                                else:
                                    msg_dict['Send'] = 'No'
                                # if data[5]:
                                #     mail.send_mail(to_add=to_add, to_cc=to_cc, sub=sub, body=body)
                                count += 1
                                try:
                                    sum += (float(data[2]))
                                except:
                                    sum += 0
                                msg_data.append(msg_dict)
                            except:
                                pass
                    
                    try:
                        msg_df = pd.DataFrame(msg_data, columns=['Address', 'Name', 'Phone Number', 'PV Balance', 'Send'])
                        generate_pdf_report(msg_df, "Low_Balance_Report.pdf")
                    except:
                        pass
                    try:
                        body = f"""
                        Dear Admin,\nTotal *{count}* UNITS have a low balance; where reminder has been sent to *{send_count}* users today. Contact details missing for *{count - send_count}* units.
                        Please note that Total Account Balance for these units is *Rs {sum:.2f}*. Details Attached Below.\n
                        Please follow up residents for low balances; as BOT will recheck balance after 2 days.\n
                        Regards,
                        Meter Check Balance BOT\n
                        _*Powered by Digital Dreams*_
                        """
                        # wp.send_wp_msg('6283287351', msg=body)
                        # wp.send_wp_msg('9988880885', msg=body)
                        wp.send_msg_in_group(group_id='919988880885-1625546417@g.us', msg=body)
                    except:
                        pass

                    now_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    update_check_time_query = f""" update services.services set ext_col_2 = '{now_time}' where service ='Meter Whatsapp'; """
                    db.execute(update_check_time_query)
    except:
        pass


def generate_pdf_report(df, filename):
    pdf = SimpleDocTemplate(filename, pagesize=landscape(letter))
    elements = []

    # Convert DataFrame to list of lists
    data = [df.columns.tolist()] + df.values.tolist()

    # Create a table
    table = Table(data)
    
    # Add table style
    style = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ])
    table.setStyle(style)

    elements.append(table)
    pdf.build(elements)


def get_master_data():
    url = "https://emsprepaidapi.neptuneenergia.com/service.asmx/liveEmsTransaction"
    payload = json.dumps({
    "TXN_NAME": "MASTERDATA",
    "DATA": "",
    "username": "Admin",
    "password": "NIRWANA#4321#ADMIN",
    "SITECODE": "160"
    })
    headers = {
    'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=120)
    except Exception as er:
        return f'<<|| Error: ||>> :{str(er)}'
    if response.status_code == 200:
        raw_text = response.text

        fixed_json_text = raw_text.split("}{")[0] + "}"
        data = json.loads(fixed_json_text)
        if 'data' in data:
            return data['data']


def get_ems_livedata():
    url = "https://emsprepaidapi.neptuneenergia.com/service.asmx/liveEmsTransaction"
    payload = json.dumps({
    "TXN_NAME": "LIVEDATA",
    "DATA": "",
    "username": "Admin",
    "password": "NIRWANA#4321#ADMIN",
    "SITECODE": "160"
    })
    headers = {
    'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=120)
    except Exception as er:
        return f'<<|| Error: ||>> :{str(er)}'
    if response.status_code == 200:
        raw_text = response.text
        fixed_json_text = raw_text.split("}{")[0] + "}"
        data = json.loads(fixed_json_text)
        if 'data' in data:
            return data['data']


def get_all_api_data():
    live_data = get_ems_livedata()
    try:
        if len(live_data) > 250:
            to_add = ['ashish@shreenathgroup.in']
            cc_add = ['ramit.shreenath@gmail.com']
            sub = 'Getting huge data in meter API'
            body = f"""
            Hello Team,\n
            The API data is huge. The length is {len(live_data)}.\n\n
            Thanks,\n
            Send Meter BOT"""
            mail.send_mail(to_add=to_add, to_cc=cc_add, sub=sub, body=body)
    except:
        pass
    for data in live_data:
        # if data['DEVICE_SLNO'] == '893074':
        #     break
        check_query = f""" SELECT CA_NAME, CA_ADDRESS, DEVICE_SLNO,
            EB_OPENING_READING, DG_OPENING_READING, EB_PV_READING, DG_PV_READING,
            OPENING_BALANCE, PV_BAL, STATUS, req_bal, check_time, remarks,
            inserted_by, inserted_date, updated_by, updated_date 
        FROM meter_api.meter_user_details where DEVICE_SLNO = '{data['DEVICE_SLNO']}' ; """
        check_data = db.get_data_in_list_of_tuple(check_query)
        if not check_data:
            col_names = ['CA_NAME', 'CA_ADDRESS', 'DEVICE_SLNO',
            'EB_OPENING_READING', 'DG_OPENING_READING', 'EB_PV_READING', 'DG_PV_READING',
            'OPENING_BALANCE', 'PV_BAL', 'STATUS', 'check_time',
            'inserted_by', 'inserted_date']

            insert_query = f""" insert into meter_api.meter_user_details 
            ({', '.join(col_names)}) VALUES ('Customer','{data['CA_ADDRESS']}', '{data['DEVICE_SLNO']}',
            '{data['EB_OPENING_READING']}','{data['DG_OPENING_READING']}','{data['EB_PV_READING']}',
            '{data['DG_PV_READING']}','{data['OPENING_BALANCE']}','{data['PV_BAL']}','{data['STATUS']}',
            NOW(),'BOT', NOW()) ;"""
            db.execute(insert_query)
        else:
            update_list = []
            if check_data[0][0] and check_data[0][0] != data['CA_NAME']:
                update_list.append(f"CA_NAME = '{data['CA_NAME']}'")
            if check_data[0][1] and check_data[0][1] != data['CA_ADDRESS']:
                update_list.append(f"CA_ADDRESS = '{data['CA_ADDRESS']}'")
            if check_data[0][3] and check_data[0][3] != data['EB_OPENING_READING']:
                update_list.append(f"EB_OPENING_READING = '{data['EB_OPENING_READING']}'")
            if check_data[0][4] and check_data[0][4] != data['DG_OPENING_READING']:
                update_list.append(f"DG_OPENING_READING = '{data['DG_OPENING_READING']}'")
            if check_data[0][5] and check_data[0][5] != data['EB_PV_READING']:
                update_list.append(f"EB_PV_READING = '{data['EB_PV_READING']}'")
            if check_data[0][6] and check_data[0][6] != data['DG_PV_READING']:
                update_list.append(f"DG_PV_READING = '{data['DG_PV_READING']}'")
            if check_data[0][7] and check_data[0][7] != data['OPENING_BALANCE']:
                update_list.append(f"OPENING_BALANCE = '{data['OPENING_BALANCE']}'")
            if check_data[0][8] and check_data[0][8] != data['PV_BAL']:
                update_list.append(f"PV_BAL = '{data['PV_BAL']}'")
            if check_data[0][9] and check_data[0][9] != data['STATUS']:
                update_list.append(f"STATUS = '{data['STATUS']}'")
            update_list.append(f"""updated_date = now(), updated_by = 'BOT'""")
            # update_data_list = ' , '.join(update_list)
            update_query = f""" update meter_api.meter_user_details set {' , '.join(update_list)} where DEVICE_SLNO = '{data['DEVICE_SLNO']}' ;"""

            db.execute(update_query)

    ref_query = f""" update meter_api.meter_user_details_refresh set updated_time = now() where id = 1 ; """
    db.execute(ref_query)


# **Run the script every day at a fixed time (e.g., 9 AM)**
schedule.every().day.at("09:00").do(main)  # Change time if needed

if __name__ == "__main__":
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)  # Check every minute
        except:
            print('Error occurred')
        
