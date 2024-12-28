import os
import db_connect as db
import logging
import datetime
import mail
import shutil
import pandas as pd
import time


logs_folder = os.path.join(os.getcwd(),'Logs')
os.makedirs(logs_folder, exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

time_stamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
log_file = os.path.join(logs_folder, f'reject_tenders_{time_stamp}.log')
file_handler = logging.FileHandler(log_file)

formatter = logging.Formatter('%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)

# NAS_UPLOAD_FOLDER = r'/mnt/tender_auto/'
# REJECT_FOLDER = r'/mnt/tender_auto/Rejected Tenders/'

NAS_UPLOAD_FOLDER = r'\\Digitaldreams\tender auto'
REJECT_FOLDER = r'\\Digitaldreams\tender auto\Rejected Tenders'



os.makedirs(REJECT_FOLDER, exist_ok=True)

def move_reject_main():
    query = """select tender_id, folder_location from tender.tender_management where (rejected_moved is null or rejected_moved = 'False') and
    tender_id not in ('2024_MAWS_490627_4','2024_MAWS_490627_2','2024_MAWS_490627_3','2024_MAWS_490627_1','2024_TIDCO_468903_1','2024_MAWS_466068_1') and
    ((verification_1 = 'rejected' and to_date(submission_date, 'YYYY-MM-DD HH24:MI') < current_date - 60) or 
    (verification_1 = 'direct_rejected' and to_date(submission_date, 'YYYY-MM-DD HH24:MI') < current_date - 10));"""
    
    data = db.get_row_as_dframe(query)
    total_tenders = data['tender_id'].tolist()
    logger.info('All Tenders')
    logger.info(total_tenders)
    success_list = []
    failure_list = []
    result_data = []
    for _,row in data.iterrows():
        print(row)
        try:
            source = os.path.join(NAS_UPLOAD_FOLDER, row['tender_id'])
            destination = os.path.join(NAS_UPLOAD_FOLDER, 'Rejected Tenders')
            try:
                try:
                    moved_dir = shutil.move(source, destination)
                except Exception as er:
                    print(er)
                    error = str(er)
                    if  'No such file or directory:' in error:
                        update_query = f"""update tender.tender_management set user_id = 'Reject Folder BOT', rejected_moved = 'True' where tender_id = '{str(row['tender_id'])}' """
                        db.execute(update_query)
                    if 'already exists' in str(error).lower():
                        base_folder_name = os.path.basename(source)
                        new_folder_name = base_folder_name + '_present'
                        new_destination = os.path.join(destination, 'Already_exist')
                        moved_dir = shutil.move(source, new_destination)
                        pass
            except Exception as err:
                error_2 = str(err)
                update_query = f"""update tender.tender_management set user_id = 'Reject Folder BOT', rejected_moved = 'True' where tender_id = '{str(row['tender_id'])}' """
                db.execute(update_query)

            if moved_dir:
                update_query = f"""update tender.tender_management set folder_location = '{str(moved_dir)}', user_id = 'Reject Folder BOT', rejected_moved = 'True' where tender_id = '{str(row['tender_id'])}' """
                db.execute(update_query)

            success_list.append(str(row['tender_id']))

            result_data.append({'Tender ID': row['tender_id'], 'Success': 'True', 'Folder Location': row['folder_location'], 'New Folder Location': moved_dir})
            logger.info('Tender sucessfuly moved')

        except Exception as error:
            logger.info(str(error))
            failure_list.append(str(row['tender_id']))

            result_data.append({'Tender ID': row['tender_id'], 'Success': 'False', 'Folder Location': row['folder_location'], 'New Folder Location': row['folder_location']})


    result_df = pd.DataFrame(result_data)
    # result_df.to_csv(os.path.join(logs_folder, f'reject_tenders_{time_stamp}.csv'), index=False)
    result_df.to_csv('reject_moved_tenders.csv', index=False)
    # result_df=pd.read_csv('reject_moved_tenders.csv')
    try:
        if not result_df.empty:
            to_add = ['ramit.shreenath@gmail.com']
            sub = 'Reject folder moved'
            body = '''Hello Team,
            Attach file contains the records of tenders which have moved to rejected folders.
            
            PFA
            
            Thanks,
            Reject Moved BOT
            '''
            mail.send_mail(to_add=to_add, to_cc=[], sub=sub, body=body, attach=['reject_moved_tenders.csv'])
    except Exception as err:
        logger.info('Error while sending mail, %s', str(err))

    logger.info('Success Tender List')
    logger.info(success_list)
    logger.info('Failure Tender List')
    logger.info(failure_list)


# def move_approve_main():
#     query = """select tender_id, folder_location from tender.tender_management where verification_1 <> 'rejected' and rejected_moved = 'True' and to_date(submission_date, 'YYYY-MM-DD HH24:MI') < current_date - 10;"""
#     data = db.get_row_as_dframe(query)

# def delete_reject_main():
#     # query = """select tender_id, folder_location from tender.tender_management where verification_1 = 'rejected' and (rejected_moved is null or rejected_moved = 'False') and to_date(submission_date, 'YYYY-MM-DD HH24:MI') < current_date - 10;"""
#     query = """select * from tender.tender_management where verification_1 = 'rejected' and rejected_moved = 'True' and to_date(submission_date, 'YYYY-MM-DD HH24:MI') < current_date - 120;"""
#     data = db.get_row_as_dframe(query)
#     total_tenders = data['tender_id'].tolist()
#     logger.info('All Tenders')
#     logger.info(total_tenders)
#     success_list = []
#     failure_list = []
#     result_data = []
#     for _,row in data.iterrows():
#         print(row)
#         print(row['folder_location'])
#         try:
#             # source = os.path.join(NAS_UPLOAD_FOLDER, row['tender_id'])
#             # destination = os.path.join(REJECT_FOLDER)

#             query = f"""INSERT INTO tender.rejected_tenders_management (local_tender_id, tender_id, customer, "location", name_of_work, submission_date, emd, pbm, e_value, link, file_location, folder_location, done, verification_1, verification_2, remarks, mail_send, ext_col_1, inserted_time, user_id, submitted_value, inserted_user_id, publish_date, to_whom, rejected_moved, reminder_date, lose_remarks, lose_state, l1_amount, our_amount)
#             VALUES (
#                 '{row["local_tender_id"]}','{row["tender_id"]}','{row["customer"]}','{row["location"]}','{row["name_of_work"]}','{row["submission_date"]}','{row["emd"]}','{row["pbm"]}',
#                 '{row["e_value"]}','{row["link"]}','{row["file_location"]}','{row["folder_location"]}','{row["done"]}','{row["verification_1"]}','{row["verification_2"]}','{row["remarks"]}',
#                 '{row["mail_send"]}','{row["ext_col_1"]}','{row["inserted_time"]}','{row["user_id"]}','{row["submitted_value"]}','{row["inserted_user_id"]}','{row["publish_date"]}',
#                 '{row["to_whom"]}','{row["rejected_moved"]}','{row["reminder_date"]}','{row["lose_remarks"]}','{row["lose_state"]}','{row["l1_amount"]}','{row["our_amount"]}'
#             );"""

#             db.execute(query)

#             del_query = f"""DELETE FROM tender.tender_management WHERE tender_id = '{row['tender_id']}' ;"""
#             db.execute(del_query)

#             del_path = os.path.join(REJECT_FOLDER, row['tender_id'])
#             delete_folder(del_path)
#             # moved_dir = shutil.move(source, destination)

#             # update_query = f"""update tender.tender_management set folder_location = '{str(moved_dir)}', user_id = 'Reject Folder BOT', rejected_moved = 'True' where tender_id = '{str(row['tender_id'])}' """
#             # db.execute(update_query)

#             success_list.append(str(row['tender_id']))

#             result_data.append({'Tender ID': row['tender_id'], 'Success': 'True'})
#             logger.info('Tender sucessfuly moved')

#         except Exception as error:
#             logger.info(str(error))
#             failure_list.append(str(row['tender_id']))

#             result_data.append({'Tender ID': row['tender_id'], 'Success': 'False'})
    


#     result_df = pd.DataFrame(result_data)
#     # result_df.to_csv(os.path.join(logs_folder, f'reject_tenders_{time_stamp}.csv'), index=False)
#     result_df.to_csv('delete_reject_tenders.csv', index=False)
#     # result_df=pd.read_csv('reject_moved_tenders.csv')
#     try:
#         if not result_df.empty:
#             to_add = ['ramit.shreenath@gmail.com']
#             sub = 'Reject Tenders delete'
#             body = '''Hello Team,
#             Attach file contains the records of tenders which have deleted.
            
#             PFA
            
#             Thanks,
#             Reject Delete BOT
#             '''
#             mail.send_mail(to_add=to_add, to_cc=[], sub=sub, body=body, attach=['delete_reject_tenders.csv'])
#     except Exception as err:
#         logger.info('Error while sending mail, %s', str(err))

#     logger.info('Success Tender List')
#     logger.info(success_list)
#     logger.info('Failure Tender List')
#     logger.info(failure_list)



# def delete_folder(folder_path):
#     try:
#         # Delete the folder and its contents
#         shutil.rmtree(folder_path)
#         print(f"Folder '{folder_path}' and its contents deleted successfully.")
#     except Exception as e:
#         print(f"Error deleting folder: {e}")


if __name__ == "__main__":
    move_reject_main()
    time.sleep(28800)