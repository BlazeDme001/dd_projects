import os
import pandas as pd
import db_connect as db
import mail
import schedule
import time

def send_email(subject, body, to_email, attachment_path):
    to_add = to_email
    cc_add = []
    sub = subject

    with open(attachment_path, 'rb') as file:
        attachment = file.read()

    mail.send_mail(to_add, cc_add, sub, body, attach=attachment_path)

def main():
    folder_path = os.path.join(os.getcwd(), 'csv_folder')
    try:
        os.removedirs(folder_path)
        os.makedirs(folder_path, exist_ok=True)
    except:
        os.makedirs(folder_path, exist_ok=True)

    # Query for inserted by bot
    query_bot = """
    SELECT tender_id, name_of_work, customer, inserted_time, inserted_user_id
    FROM tender.tender_management
    WHERE TO_DATE(inserted_time, 'DD-MM-YYYY HH24:MI:SS')::date >= current_date - 7
    AND inserted_user_id ILIKE '%BOT';
    """
    df_bot = db.get_row_as_dframe(query_bot)
    bot_csv_path = os.path.join(folder_path, 'inserted_by_bot.csv')
    df_bot.to_csv(bot_csv_path, index=False)

    # Query for rejected
    query_rejected = """
    SELECT DISTINCT ON (t.tender_id)
        t.tender_id, t.name_of_work, t.customer, t.inserted_time, t.inserted_user_id, t.verification_1, t.done
    FROM tender.tender_management_history t
    WHERE t.change_timestamp IN (
        SELECT DISTINCT ON (t2.tender_id) t2.change_timestamp
        FROM tender.tender_management_history t2
        WHERE t2.verification_1 = 'rejected' OR t2.done = 'Not Submitted'
        ORDER BY t2.tender_id, t2.change_timestamp DESC
    ) AND t.change_timestamp::date >= current_date - 7
    ORDER BY t.tender_id, t.change_timestamp DESC;
    """
    df_rejected = db.get_row_as_dframe(query_rejected)
    rejected_csv_path = os.path.join(folder_path, 'rejected.csv')
    df_rejected.to_csv(rejected_csv_path, index=False)

    # Query for submitted
    query_submitted = """
    SELECT DISTINCT ON (t.tender_id)
        t.tender_id, t.name_of_work, t.customer, t.inserted_time, t.inserted_user_id, t.verification_1, t.done
    FROM tender.tender_management_history t
    WHERE t.change_timestamp IN (
        SELECT DISTINCT ON (t2.tender_id) t2.change_timestamp
        FROM tender.tender_management_history t2
        WHERE t2.done = 'Submitted'
        ORDER BY t2.tender_id, t2.change_timestamp DESC
    ) AND t.change_timestamp::date >= current_date - 7
    ORDER BY t.tender_id, t.change_timestamp DESC;
    """
    df_submitted = db.get_row_as_dframe(query_submitted)
    submitted_csv_path = os.path.join(folder_path, 'submitted.csv')
    df_submitted.to_csv(submitted_csv_path, index=False)

    # Emailing the files
    subject = 'Weekly Tender Data'
    body = 'Attached are the weekly tender data files.'
    to_email = ['ramit.shreenath@gmail.com', 'ashish@shreenathgroup.in', 'raman@shreenathgroup.in']

    send_email(subject, body, to_email, bot_csv_path)
    send_email(subject, body, to_email, rejected_csv_path)
    send_email(subject, body, to_email, submitted_csv_path)

# Schedule the script to run every Saturday at 9:00 PM
schedule.every().saturday.at("21:00").do(main)

while True:
    schedule.run_pending()
    time.sleep(1)
