import db_connect as db
import datetime
import pandas as pd
import os
import mail
import schedule
import time

folder_path = os.makedirs(os.path.join(os.getcwd(),'report_csv'), exist_ok=True)
folder_path = r"D:\DD Projects\DD Projects\Tender Management System V2\report_csv"

# bot_csv_path = os.path.join(folder_path, 'inserted_by_bot.csv')

# def all_tat_list():
#     # query = """SELECT * FROM tender.tender_tat where stage <> 'rejected' ; """
#     # query = """select * from tender.tender_tat tt where t_id not in (select t_id from tender.tender_tat tt where stage  = 'rejected' group by t_id having count(*) < 3); """
#     # query = """select *  from tender.tender_tat tt where t_id not in 
#     #         (select t_id from tender.tender_tat where stage in 
#     #         ('approved-Not Submitted','rejected-Open','rejected-Not Submitted',
#     #         'closed-Close-LOSE', 'approved-Submitted', 'rejected')); """
#     query = """
#         SELECT * FROM tender.tender_tat tt
#         WHERE t_id NOT IN (
#             SELECT tender_id
#             FROM tender.tender_management
#             WHERE verification_1 ILIKE 'reje%'
#                 OR done IN ('Submitted', 'Not Submitted', 'Close-WIN', 'Close-LOSE', 'Close-Cancel')
#         )
#         AND t_id NOT IN (
#             SELECT t_id
#             FROM tender.tender_tat
#             WHERE stage IN ('approved-Not Submitted','rejected-Open','rejected-Not Submitted', 'closed-Close-LOSE', 'approved-Submitted', 'rejected')
#         )
#         AND t_id NOT IN (
#             SELECT t_id
#             FROM tender.tender_tat
#             WHERE status IN ('Not Submitted', 'Not Submitted', 'Close-LOSE', 'Submitted')
#                 OR stage IN ('rejected', 'closed')
#         );
#     """

#     data = db.get_row_as_dframe(query)
#     data['tat'] = pd.to_timedelta(data['tat'], errors='coerce')

#     pivot_table = pd.pivot_table(data, values='tat', index='t_id', columns='stage', aggfunc='sum', fill_value=pd.Timedelta(seconds=0))
#     pivot_table['Total TAT'] = pivot_table.sum(axis=1)

#     oem_query = """
#         WITH turnaround_times AS (
#             SELECT tender_id,
#                 CASE
#                     WHEN tat IS NULL OR tat = '' THEN
#                         AGE(NOW(), NOW())
#                     ELSE
#                         AGE(
#                             NOW(),
#                             NOW() - REPLACE(tat, 'days', '')::INTERVAL
#                         )
#                 END AS total_interval
#             FROM tender.oem_management
#         )
#         SELECT tender_id as t_id, 
#             CASE WHEN EXTRACT(DAY FROM MAX(total_interval) - MIN(total_interval)) >= 0
#                 THEN EXTRACT(DAY FROM MAX(total_interval) - MIN(total_interval)) || ' days '
#                 ELSE '0:'
#             END
#             || LPAD(ABS(EXTRACT(HOUR FROM MAX(total_interval) - MIN(total_interval)))::TEXT, 2, '0')
#             || ':'
#             || LPAD(ABS(EXTRACT(MINUTE FROM MAX(total_interval) - MIN(total_interval)))::TEXT, 2, '0')
#             || ':'
#             || ABS(EXTRACT(SECOND FROM MAX(total_interval) - MIN(total_interval)))
#             AS oem_tat
#         FROM turnaround_times
#         GROUP BY tender_id;
#     """

#     oem_tat = db.get_row_as_dframe(oem_query)

#     try:
#         # mrg_df = pd.merge(pivot_table, oem_tat, on='t_id', how='left')
#         mrg_df = pd.merge(pivot_table, oem_tat, on='t_id', how='left')

#         # # Fill NaN values in 'oem_tat' with '0 days 00:00:00.000000'
#         mrg_df['oem_tat'].fillna('0 days 00:00:00.000000', inplace=True)

#         # # Convert 'oem_tat' column to Timedelta
#         mrg_df['oem_tat'] = pd.to_timedelta(mrg_df['oem_tat'], errors='coerce')
#     except:
#         pass
#     mrg_df.drop('OEM', axis=1)
#     column_order = ['t_id', 'FOR UPDATE', 'pre_approved', 'approved', 'Total TAT', 'oem_tat']
#     mrg_df = mrg_df[column_order]
#     mrg_df.fillna(pd.Timedelta(0), inplace=True)
#     columns_to_replace_nan = ['FOR UPDATE', 'pre_approved', 'approved', 'Total TAT', 'oem_tat']
#     mrg_df[columns_to_replace_nan] = mrg_df[columns_to_replace_nan].fillna('0 days 00:00:00.000000', inplace=False).astype('timedelta64[s]')


def reports():

    query_bot = """
    SELECT tender_id, name_of_work, customer, inserted_time, done as "Status", verification_1 as "Stage", inserted_user_id
    FROM tender.tender_management
    WHERE TO_DATE(inserted_time, 'DD-MM-YYYY HH24:MI:SS')::date >= current_date - 7;
    """
    df_bot = db.get_row_as_dframe(query_bot)
    ins_path = os.path.join(folder_path, 'inserted.csv')
    df_bot.to_csv(ins_path, index=False)

    # Query for rejected
    query_rejected = """
    SELECT DISTINCT ON (t.tender_id)
        t.tender_id as "Tender ID", t.name_of_work as "Name", t.customer as "Customer", t.verification_1 as "Stage", t.done as "Status",
        t.inserted_time as "inserted Time", t.inserted_user_id as "Inserted User ID"
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
    rej_path = os.path.join(folder_path, 'rejected.csv')
    df_rejected.to_csv(rej_path, index=False)

    # Query for submitted
    query_submitted = """
    SELECT DISTINCT ON (t.tender_id)
        t.tender_id as "Tender ID", t.name_of_work as "Name", t.customer as "Customer", t.verification_1 as "Stage", t.done as "Status",
        t.inserted_time as "inserted Time", t.inserted_user_id as "Inserted User ID"
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
    sub_path = os.path.join(folder_path, 'submitted.csv')
    df_submitted.to_csv(sub_path, index=False)

    query_close = """
    SELECT DISTINCT ON (t.tender_id)
        t.tender_id as "Tender ID", t.name_of_work as "Name", t.customer as "Customer", t.verification_1 as "Stage", t.done as "Status",
        t.inserted_time as "inserted Time", t.inserted_user_id as "Inserted User ID"
    FROM tender.tender_management_history t
    WHERE t.change_timestamp IN (
        SELECT DISTINCT ON (t2.tender_id) t2.change_timestamp
        FROM tender.tender_management_history t2
        WHERE t2.done IN ('Close-WIN', 'Close-LOSE', 'Close-Cancel')
        ORDER BY t2.tender_id, t2.change_timestamp DESC
    ) AND t.change_timestamp::date >= current_date - 7
    ORDER BY t.tender_id, t.change_timestamp DESC;
    """
    df_close = db.get_row_as_dframe(query_close)
    close_path = os.path.join(folder_path, 'closed.csv')
    df_close.to_csv(close_path, index=False)
    

    query_approve = """
    SELECT DISTINCT ON (t.tender_id)
        t.tender_id as "Tender ID", t.name_of_work as "Name", t.customer as "Customer", t.verification_1 as "Stage", t.done as "Status",
        t.inserted_time as "inserted Time", t.inserted_user_id as "Inserted User ID"
    FROM tender.tender_management_history t
    WHERE t.change_timestamp IN (
        SELECT DISTINCT ON (t2.tender_id) t2.change_timestamp
        FROM tender.tender_management_history t2
        WHERE t2.verification_1 = 'approved' and 
            t2.done not IN ('Submitted', 'Not Submitted', 'Close-WIN', 'Close-LOSE', 'Close-Cancel')
        ORDER BY t2.tender_id, t2.change_timestamp DESC
    ) AND t.change_timestamp::date >= current_date - 7
    ORDER BY t.tender_id, t.change_timestamp DESC;
    """
    df_approve = db.get_row_as_dframe(query_approve)
    app_path = os.path.join(folder_path, 'approved.csv')
    df_approve.to_csv(app_path, index=False)

    return [ins_path, rej_path, sub_path, close_path, app_path]


def summery_report():
    ins_query = f"""SELECT count(*) FROM tender.tender_management WHERE TO_DATE(inserted_time, 'DD-MM-YYYY HH24:MI:SS')::date >= current_date - 7;"""
    try:
        ins_data = db.get_data_in_list_of_tuple(ins_query)[0][0]
    except:
        ins_data = 0
    pass


def send_report_mail(paths):
    sub = 'Weekly reports of Tenders'
    body = 'Hello team,\n\nBelow are the reports of tender.\n\nThanks,\nSend Tender Report BOT'
    to = ['ashish@shreenathgroup.in']
    cc = ['ramit.shreenath@gmail.com']
    
    # attach = [paths[0], paths[1], paths[2], paths[3], paths[4]]
    # attach = paths
    mail.send_mail(to_add=to, to_cc=cc, sub=sub,body=body,attach=paths)

def main():
    paths = reports()
    send_report_mail(paths)

schedule.every().saturday.at("09:00").do(main)

if __name__=='__main__':
    while True:
        schedule.run_pending()
        time.sleep(60) 

