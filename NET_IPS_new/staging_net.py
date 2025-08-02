import db_connect as db
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time
import os
# import mail
import re
import web_interface as wi
import logging
import schedule

from flask import Flask, jsonify
import threading
from multiprocessing import Process


logging.basicConfig(filename='net_brodband.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger('net_brodband')

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--incognito')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--start-maximized')
chrome_options.add_argument('--disable-gpu')

download_folder = os.path.join(os.getcwd(), 'downloads')

prefs = {
    'download.default_directory': download_folder,
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'safebrowsing.enabled': True
}

chrome_options.add_experimental_option('prefs', prefs)

bot_name = 'NETPLUS BOT'

def login(driver, user, pass_word):
    try:
        driver.get("https://partner.netplus.co.in/Partner/Login.aspx")
        user_name = driver.find_element(By.XPATH,'//*[@id="txtUserName"]')
        user_name.clear()
        user_name.click()
        user_name.send_keys(user)
        
        password = driver.find_element(By.XPATH, '//*[@id="txtPassword"]')
        password.clear()
        password.click()
        password.send_keys(pass_word)
        
        driver.find_element(By.XPATH, '//*[@id="save"]').click()
        logger.info('Login to the portal')
    except Exception as er:
        driver.quit()
        print(str(er))
    

def search_for_accounts(driver, user):
    try:
        logger.info('Searching for accounts')
        wi.processing_check_wait(driver, xpath='//*[@id="lbAccount"]', time=90)
        acc_btn = driver.find_element(By.XPATH, '//*[@id="lbAccount"]')
        # time.sleep(60)
        driver.execute_script("arguments[0].click();", acc_btn)
        logger.info("Clicked to account button")
        time.sleep(5)
        driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_ddlPageSize"]/option[7]').click()
        time.sleep(10)
        c = 0
        while c <= 5:
            c += 1
            logger.info(f"Trying to get the data table. Try: {c}")
            acc_df = get_table_data(driver)
            time.sleep(5)
            if not acc_df.empty:
                logger.info('Got the data table')
                break
        time.sleep(5)
        try:
            acc_df.to_csv(f'abc_{user}.csv' , index=False)
        except:
            pass
        insert_into_db(acc_df, user)
        pass
    except Exception as er:
        # print(str(er))
        logger.error(f"Error in search for accounts: {str(er)}")


def clean_and_rename_df(df, user):
    # Remove columns with empty header
    df = df.loc[:, df.columns.str.strip() != '']
    # Rename columns
    if user == 'CHDGBO0292':
        df.columns = [
            "user_name", "acc_name", "acc_no", "mobile", "cur_plan",
            "expiry", "address", "cluster"
        ]
    elif user == 'CHDIPT0292':
        df.columns = [
            "user_name", "acc_name", "mobile", "cur_plan", "pre_auth_ip",
            "status", "expiry", "reg_date", "last_reneal"
        ]
        df["acc_no"] = df["user_name"]
    return df


def insert_into_db(df, user):
    try:
        if not df.empty:
            db.execute(f"DELETE FROM net_broadband.netplus where login_user_name = '{user}' ;")
            logger.info('Existing records deleted from net_broadband.netplus for user: ' + user)
            df = clean_and_rename_df(df, user)
            df['login_user_name'] = user
            df = df.drop_duplicates(subset=['acc_no'], keep='last')
            df = df.reset_index(drop=True)
            for index, row in df.iterrows():
                data_dict = row.to_dict()
                db.insert_dict_into_table('net_broadband.netplus', data_dict)
            logger.info('Data inserted into the database')
        else:
            logger.warning('DataFrame is empty, nothing to insert into the database')
    except Exception as e:
        logger.error(f'Error inserting data into the database: {str(e)}')


def get_table_data(driver):
    try:
        wi.processing_check_wait(driver, xpath='//*[@id="ContentPlaceHolder1_gdcomp"]', time=60)
        table = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_gdcomp"]')
        
        headers = table.find_elements(By.TAG_NAME, "th")
        header_list = [header.text for header in headers]

        rows = table.find_elements(By.TAG_NAME, "tr")
        data = []
        for row in rows[1:]:
            cells = row.find_elements(By.TAG_NAME, "td")
            data.append([cell.text for cell in cells])

        df = pd.DataFrame(data, columns=header_list)
    except Exception as e:
        print(f'Error: {str(e)}')
        df = pd.DataFrame([])
        
    return df


def main():
    try:
        logger.info('Starting the webdriver')
        login_user_name = ['CHDGBO0292','CHDIPT0292']
        login_password = ['Shree@2025','Fast@123']
        for user, password in zip(login_user_name, login_password):
            print(f'Logging in with user: {user}')
            print(f'Password: {password}')
            driver = webdriver.Chrome(options=chrome_options)
            logger.info(f'Logging in with user: {user}')
            login(driver, user, password)
            logger.info('Logged in successfully')
            search_for_accounts(driver, user)
            driver.quit()
    except Exception as er:
        driver.quit()
        logger.error(f"Error in main function: {str(er)}")


from flask import Flask, jsonify
import threading

# ...existing code...

def job():
    print("Bot started ...")
    main()

# Schedule: run every day at 06:00
schedule.every().day.at("06:30").do(job)
# schedule.every().day.at("22:50").do(job)

# Flask API for manual trigger
app = Flask(__name__)

@app.route('/run-job', methods=['POST'])
def trigger_job():
    Process(target=job).start()
    return jsonify({"status": "Job started"}), 202


@app.route('/get-accounts', methods=['GET'])
def get_accounts():
    try:
        query = """
            SELECT user_name, acc_name, acc_no, mobile, cur_plan, expiry, address,
            cluster, pre_auth_ip, status, reg_date, last_reneal, login_user_name,
            TO_CHAR(updated_date, 'DD Mon YYYY') AS updated_date,
            TO_CHAR(updated_date, 'HH12:MI:SS AM') AS update_time
            FROM net_broadband.netplus;
        """
        df = db.get_row_as_dframe(query)
        
        if df is None or df.empty:
            return jsonify({
                "status": "success",
                "data": [],
                "message": "No records found"
            }), 200
        
        data = df.to_dict(orient='records')
        return jsonify({
            "status": "success",
            "data": data
        }), 200

    except Exception as e:
        logger.error(f"Error fetching data from database: {str(e)}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@app.route('/health', methods=['GET'])
def health():
    return jsonify({"status": "ok"}), 200


def run_scheduler():
    while True:
        schedule.run_pending()
        time.sleep(1)

if __name__ == '__main__':
    # Start the scheduler in a separate thread
    threading.Thread(target=run_scheduler, daemon=True).start()
    # Start the Flask API server
    app.run(host='0.0.0.0',port=5011, debug=False)
