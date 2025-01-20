import db_connect as db
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
# import pandas as pd
import time
import os
import mail
# import re
import web_interface as wi
import logging
import datetime
import schedule



logging.basicConfig(filename='net_brodband_search_mac.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger('net_brodband_search_mac')

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
chrome_options.add_argument('--start-maximized')

download_folder = os.path.join(os.getcwd(), 'downloads')

prefs = {
    'download.default_directory': download_folder,
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'safebrowsing.enabled': True
}

chrome_options.add_experimental_option('prefs', prefs)

bot_name = 'NETPLUS BOT 2'
mail_send_require = False

def login():
    try:
        logger.info('Login function')
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://vcs.netplus.co.in:8080/#/login')
        # user_name = driver.find_element("//input[@name='username']")
        # from selenium.webdriver.common.by import By

        user_name = driver.find_element(By.XPATH, "//input[@id='username']")

        user_name.click()
        user_name.clear()
        user_name.click()
        user_name.send_keys('riyaldesh@gmail.com')
        password = driver.find_element(By.XPATH, "//input[@id='password']")
        password.click()
        password.clear()
        password.click()
        password.send_keys('riyaldesh@gmail.com')
        driver.find_element(By.XPATH,"//button[@class='btn btn-primary account__btn btn btn-secondary'][//button[text()='Sign In']]").click()
        return driver
    except Exception as err:
        logger.error(f'Error in login: {str(err)}')
        raise Exception(f'Error in login: {str(err)}')
    

def search_mac(driver, mac):
    try:
        wi.processing_check_wait(driver, xpath='//label[text()="MAC Address"]/preceding::input[1]', time=30)
        mac_id = driver.find_element(By.XPATH, '//label[text()="MAC Address"]/preceding::input[1]')
        mac_id.click()
        mac_id_input = driver.find_element(By.XPATH, '//input[@id="wanId"]')
        mac_id_input.click()
        mac_id_input.clear()
        mac_id_input.click()
        mac_id_input.send_keys(mac[0])
        driver.find_element(By.XPATH, "//button[text()='Find Device']").click()
        # df = get_table_data(driver)
        time.sleep(5)
        logger.info(f'Searching for mac: {mac[0]}')
        wi.processing_check_wait(driver, xpath="//*[@class='rt-tr -odd'][1]/div[2]", time=30)        
        driver.find_element(By.XPATH,"//*[@class='rt-tr -odd'][1]/div[2]").click()
        try:
            wi.processing_check_wait(driver, xpath="//div[@class='ml-1']//small", time=30)
            status = driver.find_element(By.XPATH, "//div[@class='ml-1']//small").text
        except:
            status = ''
        try:
            tx_rx_power = driver.find_element(By.XPATH, "//div[@class='col-6 col-md-2 col-lg-6 col-xl-2'][1]").text
            tx_power = tx_rx_power.split('\n')[0].replace('Tx Power: ','').strip()
            rx_power = tx_rx_power.split('\n')[1].replace('Rx Power: ','').strip()

            if float(rx_power.replace('dBm','').strip()) <= -25.00:
                mail_send_require = True
                to_add = ['ashish@shreenathgroup.com']
                cc_add = ['dme@shreenathgroup.com']
                sub = 'RX Power is low'
                body = f'''Hello team,\nThe RX power is {str(rx_power)}, which is lower then -25.00.\nPlease look into it.\n\nThanks,\n{bot_name}'''
                mail.send_mail(to_add=to_add, to_cc=cc_add, sub=sub, body=body)
        except Exception as err:
            tx_power = ''
            rx_power = ''
            logger.error(f'Unable to get tx or/and rx power. || tx={tx_power}, rx={rx_power} || Error={str(err)}')
        try:
            device_name_element = driver.find_element(By.XPATH,'//input[@id="deviceName"]')
            device_name = device_name_element.get_attribute("value")
        except:
            device_name = ''
        try:
            serial_no_element = driver.find_element(By.XPATH,'//*[@id="deviceSerial"]')
            serial_no = serial_no_element.get_attribute('value')
        except:
            serial_no = ''
        try:
            lr_ut_element = driver.find_element(By.XPATH, "//p[contains(text(), 'Last Reported')]/../..").text
            last_reported = lr_ut_element.split('\n')[0].split(':', maxsplit=1)[1].strip()
            if len(last_reported.split()) < 4:
                last_reported += " 00:00 AM" 
            last_reported_dt = datetime.datetime.strptime(last_reported, "%b %d, %Y %I:%M %p")
            up_time = lr_ut_element.split('\n')[1].split(':', maxsplit=1)[1].strip()
        except:
            last_reported_dt = None
            up_time = ''
        try:
            check_query = f"select * from net_broadband.vcs where mac_id = '{mac[0]}' and acc_no = '{mac[1]}' ;"
            check_data = db.get_data_in_list_of_tuple(check_query)
            if not check_data:
                try:
                    insert_query = f""" INSERT INTO net_broadband.vcs (mac_id, acc_no, status, tx_power, 
                    rx_power, device_name, serial_no, last_reported, up_time, create_date, updated_by)
                    VALUES ('{mac[0]}','{mac[1]}','{status}','{tx_power}','{rx_power}','{device_name}',
                    '{serial_no}','{last_reported_dt}','{up_time}','now()','{bot_name}'); """
                    logger.info(f"Insert Query: {insert_query}")
                    check_insert_query = db.execute(insert_query)
                    logger.info(f"check_insert_query: {check_insert_query}")
                except Exception as err:
                    logger.error(f"Error in insert query: {str(err)}")
            else:
                try:
                    update_query = f""" update net_broadband.vcs set updated_by = '{bot_name}' """
                    update_required = False
                    if status and status != check_data[0][3]:
                        update_required = True
                        update_query += f", status = '{status}' "
                    if tx_power and tx_power != check_data[0][4]:
                        update_required = True
                        update_query += f", tx_power = '{tx_power}' "
                    if rx_power and rx_power != check_data[0][5]:
                        update_required = True
                        update_query += f", rx_power = '{rx_power}' "
                    if device_name and device_name != check_data[0][6]:
                        update_required = True
                        update_query += f", device_name = '{device_name}' "
                    if serial_no and serial_no != check_data[0][7]:
                        update_required = True
                        update_query += f", serial_no = '{serial_no}' "
                    if last_reported_dt and last_reported_dt != check_data[0][8]:
                        update_required = True
                        update_query += f", last_reported = '{last_reported_dt}' "
                    if up_time and up_time != check_data[0][9]:
                        update_required = True
                        update_query += f", up_time = '{up_time}' "
                    update_query += f""" where mac_id = '{mac[0]}' and acc_no = '{mac[1]}' ; """
                    logger.info(f"update_query: {update_query}")
                    if update_required:
                        check_db_update = db.execute(update_query)
                        logger.info(f'check_db_update: {check_db_update}')  
                except Exception as err:
                    logger.error(f"Error in update query: {str(err)}")
        except Exception as err:
            logger.error(f"Error while updating database: {err}")
            pass
            # raise Exception(f"Error while updating database: {err}")
        try:
            # driver.find_element(By.XPATH,'//i[@class="inline fa glyphicon glyphicon-arrow-left fa-long-arrow-left fa-20 mr-10"]').click()
            target_element = driver.find_element(By.XPATH, "//*[text()='CPE List']/preceding-sibling::i")
            driver.execute_script("arguments[0].click();", target_element)
        except Exception as err:
            logger.info(f"Error while clicking the closed button: {str(err)}")
            raise Exception(f"Error while clicking the closed button: {str(err)}")
            pass
        time.sleep(5)
    except Exception as err:
        logger.error(f'Error in search_mac: {str(err)}')
        raise Exception(f"Error while updating database: {err}")


def get_mac_list():
    all_mac_id = []
    try:
        all_mac_id_query = " select mac_id, acc_no from net_broadband.netplus n where status ilike 'Active%' ;"
        all_mac_id_data = db.get_data_in_list_of_tuple(all_mac_id_query)
        all_mac_id = [id for id in all_mac_id_data if len(id[0]) > 5]
    except Exception as err:
        logger.error(f'Error in get_mac_list: {str(err)}')
    return all_mac_id


def main():
    try:
        driver = login()
        mac_list = get_mac_list()
        if mac_list:
            print(f'Total mac is {len(mac_list)}')
            for mac in mac_list:
                print(mac)
                time.sleep(2)
                logger.info(f'Starting to check mac id {str(mac)} ===================================================')
                try:
                    search_mac(driver, mac)
                except Exception as e:
                    logger.error(f'Error in search mac id function {str(mac)} : Error: {str(e)} =======================================')
            try:
                driver.quit()
            except:
                pass
    except Exception as err:
        logger.error(f'Error in main: {str(err)}')
        try:
            driver.quit()
        except:
            pass

def job():
    print("Bot started ...")
    main()

schedule.every().saturday.at("06:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

