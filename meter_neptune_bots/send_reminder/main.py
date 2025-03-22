import requests
import db_connect as db
import send_wp as wp
import time
import mail
import schedule
from datetime import datetime, timedelta
import pandas as pd

from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.lib import colors


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


def main():
    try:
        status = check_service()
        if status == 'ON':
            check_last_send_query = """SELECT ext_col_1, ext_col_2 FROM services.services WHERE service ='Meter Whatsapp';"""
            check_last_send_data = db.get_data_in_list_of_tuple(check_last_send_query)

            if check_last_send_data and check_last_send_data[0][0]:
                last_check_time = (datetime.now() - timedelta(days=int(check_last_send_data[0][0]))).date()  # Compare with yesterday
                stored_date = datetime.strptime(check_last_send_data[0][1], '%Y-%m-%d %H:%M:%S').date()

                if stored_date == last_check_time:
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
                                # body = f"""
                                # Dear *{data[1].strip()}*,\n
                                # Kindly note that the current reading of the Prepaid Electrical Meter for Unit No *{data[6]}* is *{total_unit:.2f}* Units, and your Current Balance is *Rs {data[2]}*.\n
                                # To ensure uninterrupted power supply, we kindly request you to maintain a sufficient balance in your account. This will help in avoiding any disruptions in your services.\n
                                # This is an automated message, if you feel there is an error, please call undersigned.
                                # Please ignore if already paid.\n
                                # Best regards,
                                # Sweta Sharma(9592555516)
                                # Customer Experience Manager
                                # *Team Nirwana*\n
                                # _*Powered by DIGITAL DREAMS*_
                                # """
                                body = f"""
                                Dear *{data[1].strip()}*,\n
                                Kindly note that the current reading of the prepaid electrical meter for Unit No *{data[6]}* is *{total_unit:.2f}* units as of today, and your current balance is *Rs {data[2]}*.\n
                                To ensure uninterrupted power supply, we kindly request you to maintain a sufficient balance in your account. This will help in avoiding any disruptions in your services.\n
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

# **Run the script every day at a fixed time (e.g., 9 AM)**
schedule.every().day.at("09:00").do(main)  # Change time if needed

if __name__ == "__main__":
    while True:
        try:
            schedule.run_pending()
            time.sleep(1)  # Check every minute
        except:
            print('Error occurred')
        
