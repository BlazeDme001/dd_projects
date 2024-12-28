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

NAS_UPLOAD_FOLDER = r'\\Digitaldreams\tender auto'
REJECT_FOLDER = r'\\Digitaldreams\tender auto\Rejected Tenders'


os.makedirs(REJECT_FOLDER, exist_ok=True)

def move_reject_main():
    query = """SELECT tender_id, folder_location FROM tender.tender_management WHERE done in ('Close-WIN', 'Close-LOSE', 'Close-Cancel');"""
    data = db.get_row_as_dframe(query)
    total_tenders = data['tender_id'].tolist()
    logger.info('All Tenders')
    logger.info(total_tenders)
    success_list = []
    failure_list = []
    result_data = []
    for _,row in data.iterrows():
        print(row)
        destination = os.path.join(NAS_UPLOAD_FOLDER)
        source = os.path.join(REJECT_FOLDER, row['tender_id'])

        moved_dir = shutil.move(source, destination)
