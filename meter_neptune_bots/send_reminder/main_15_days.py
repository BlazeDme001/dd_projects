import requests
import db_connect as db
import send_wp as wp
import time
import mail
import schedule
from datetime import datetime
import pandas as pd
import json

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


def main():
    if not should_run_today():
        print("Skipping today. Either not Monday or it's been less than 14 days.")
        return

    check_query = """ 
        SELECT DEVICE_SLNO, CA_NAME, PV_BAL, check_time, mobile, email, 
        ca_address, eb_pv_reading, dg_pv_reading 
        FROM meter_api.meter_user_details 
        WHERE (PV_BAL > REQ_BAL or PV_BAL = REQ_BAL) AND STATUS = 'Active'; 
    """
    check_data = db.get_data_in_list_of_tuple(check_query)
    
    if check_data:
        for data in check_data:
            print(data)
            try:
                total_unit = float(data[7]) + float(data[8])
                sub = f'Low balance reminder for device: {data[0]}'
                body = f"""
                Dear *{data[1]} [Unit-{data[6]}]*,\n
                Thank you for maintaining a positive balance in your prepaid electricity meter!
                # Current Meter Reading : *{total_unit:.2f} units*
                # Prepaid Wallet Balance: *₹{data[2]}/-*\n
                We appreciate your prompt recharges and request you to continue keeping a healthy balance to avoid any inconvenience.\n
                For any assistance, feel free and raise a *Support Ticket* in Adda App.\n
                Best Regards,
                Team Nirwana Maintenance\n
                _*Powered by DIGITAL DREAMS*_
                """
                mob = data[4]  # Mobile number
                if mob and len(mob) > 9:
                    wp.send_wp_msg(mob=mob, msg=body)
            except Exception as e:
                print(f"Error sending message: {e}")

    # Save the date after successful run
    write_last_run_date(datetime.now().date())
    print("Run completed and last_run.txt updated.")

# Scheduling part
schedule.every(2).weeks.at("09:00").do(main)

if __name__ == "__main__":
    while True:
        try:
            schedule.run_pending()
            time.sleep(60)  # Sleep 1 minute
        except Exception as e:
            print(f"Error occurred: {e}")
