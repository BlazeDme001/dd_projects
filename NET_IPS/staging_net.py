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


logging.basicConfig(filename='net_brodband.log', level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

logger = logging.getLogger('net_brodband')

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

bot_name = 'NETPLUS BOT'

def login(driver):
    try:
        driver.get("https://partner.netplus.co.in/Partner/Login.aspx")
        user_name = driver.find_element(By.XPATH,'//*[@id="txtUserName"]')
        user_name.clear()
        user_name.click()
        user_name.send_keys('CHDGBO0292')
        
        password = driver.find_element(By.XPATH, '//*[@id="txtPassword"]')
        password.clear()
        password.click()
        password.send_keys('Shree@202')
        # password.send_keys('Shree@2024')
        # password.send_keys('Shree@2025')
        
        driver.find_element(By.XPATH, '//*[@id="save"]').click()
        logger.info('Login to the portal')
    except Exception as er:
        driver.quit()
        print(str(er))
    

def search_for_accounts(driver):
    try:
        logger.info('Searching for accounts')
        acc_btn = driver.find_element(By.XPATH, '//*[@id="lbAccount"]')
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
        check_and_update_acc_in_db(acc_df, driver)
        time.sleep(5)
        # new_acc = get_table_data(driver)
        # Compare the acc_df with the new_acc_df, if any mismatch found then check and update teh new data.
        pass
    except Exception as er:
        # print(str(er))
        logger.error(f"Error in search for accounts: {str(er)}")


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


def check_and_update_acc_in_db(acc_df, driver):
    acc_nos = tuple(acc_df['Account No'].to_list())
    logger.info('Checking and updating function.')
    logger.info(f'Total accounts: {acc_nos}')
    deactive_nf_query = f""" UPDATE net_broadband.netplus
    set status = 'Deactive - Not Found', updated_by = '{bot_name}'
    where status ilike 'Deactive%' and acc_no not in {acc_nos} ;"""
    logger.info(f"Deactive account query: {deactive_nf_query}")
    db.execute(deactive_nf_query)
    # all_data_query = f""" select acc_no, status from net_broadband.netplus ;"""
    # all_data_df = db.get_row_as_dframe(all_data_query)
    acc_list_done = []
    for acc in acc_nos:
        print(acc)
        logger.info("================================================================================================")
        logger.info(f"Account Nop. {acc}")
        wi.processing_check_wait(driver=driver, xpath='//*[@id="ContentPlaceHolder1_ddlPageSize"]/option[7]',time=30)
        driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_ddlPageSize"]/option[7]').click()
        try:
            get_acc_details_query = f"""select acc_no ,acc_name , status, mobile ,email , address , perm_address , 
                    payment_address ,dob , cur_plan , doj , mac_id , project , block , 
                    block_no from net_broadband.netplus WHERE acc_no = '{acc}' ;"""
            logger.info(f'Get Account details query: {get_acc_details_query}')
            data = db.get_data_in_list_of_tuple(get_acc_details_query)
            
            # Click on the user name.
            try:
                acc_no_xpath = f"//a[text()='{acc}']"
                wi.processing_check_wait(driver=driver, xpath=acc_no_xpath, time=30)
                # driver.find_element(By.XPATH, acc_no_xpath).click()
                acc_no_element = driver.find_element(By.XPATH, acc_no_xpath)
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", acc_no_element)
                acc_no_element.click()
                logger.info(f"Account number xpath: {acc_no_element}.")
            except Exception as error:
                # print(str(error))
                logger.error(f'Error while click on user id: {error}')
                raise Exception(f'Error while click on user id: {error}')

            time.sleep(10)
            # Get all the details (Status, Acc name, mobile, email, all 3 address, dob, acc number, cur plan, created date, user name, mac add)
            logger.info('Trying to get Account Name')
            acc_name_xpath = '//*[@id="ContentPlaceHolder1_lbl_AccName"]'
            wi.processing_check_wait(driver, acc_name_xpath, 60)
            try:
                try:
                    acc_name = driver.find_element(By.XPATH, acc_name_xpath).text
                except:
                    acc_name = ''
                    # acc_name = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_AccName"]').text
                try:
                    status = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lblactivity"]').text
                except:
                    status = ''
                try:
                    mobile = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_MOBILENUMBER"]').text
                except:
                    mobile = ''
                try:
                    email = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_EMAIL"]').text
                except:
                    email = ''
                try:
                    address = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_Address"]').text
                except:
                    address = ''
                try:
                    permanent_address = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_Address"]').text
                except:
                    permanent_address = ''
                try:
                    payment_address = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lblAddress_Pay"]').text
                except:
                    payment_address = ''
                try:
                    dob = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_DateOfBirth"]').text
                except:
                    dob = None
                try:
                    acc_no = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_AccNum"]').text
                except:
                    acc_no = ''
                try:
                    plan = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_CurrentPlan"]').text
                except:
                    plan = ''
                try:
                    created_date = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_CreatedDate"]').text
                except:
                    created_date = None
                try:
                    mac = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_MACID"]').text
                except:
                    mac = None
                try:
                    crf = driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_lbl_CRF"]').text
                except:
                    crf = ''
            except Exception as er:
                print(er)
                continue

            temp_add = address or permanent_address or payment_address or ''
            match = re.search(r'\d{4}', temp_add)
            temp_block = match.group() if match else None

            project = 'Nirvana'
            
            update_clauses = []
            columns = []
            values = []
            if data:
                logger.info('Got the account data from DB and now checking for changes')
                if acc_name and acc_name != data[0][1]:
                    update_clauses.append(f'acc_name = "{acc_name}"')
                if status and status != data[0][2]:
                    update_clauses.append(f'status = "{status}"')
                if mobile and mobile != data[0][3]:
                    update_clauses.append(f'mobile = "{mobile}"')
                if email and email != data[0][4]:
                    update_clauses.append(f'email = "{email}"')
                if address and address != data[0][5]:
                    update_clauses.append(f'address = "{address}"')
                if permanent_address and permanent_address != data[0][6]:
                    update_clauses.append(f'perm_address = "{permanent_address}"')
                if payment_address and payment_address != data[0][7]:
                    update_clauses.append(f'payment_address = "{payment_address}"')
                if dob and dob != data[0][8]:
                    update_clauses.append(f'dob = "{dob}"')
                if plan and plan != data[0][9]:
                    update_clauses.append(f'cur_plan = "{plan}"')
                if created_date and created_date != data[0][10]:
                    update_clauses.append(f'doj = "{created_date}"')
                if mac and mac != data[0][11]:
                    update_clauses.append(f'mac_id = "{mac}"')
                if project and project != data[0][12]:
                    update_clauses.append(f'project = "{project}"')

                if temp_block:
                    block = block_selection(temp_block)
                    if block and block != data[0][13]:
                        update_clauses.append(f'block = "{block}"')
                    if temp_block != data[0][14]:
                        update_clauses.append(f'block_no = "{temp_block}"')
                if bot_name:
                    update_clauses.append(f'bot_name = "{bot_name}"')

                if update_clauses:
                    update_query = f'UPDATE net_broadband.netplus SET ' + ', '.join(update_clauses) + f" WHERE acc_no = '{acc}' ;"
                    print(update_query)
                    logger.info(f"Update query: {update_query}")
                    db.execute(update_query)
                else:
                    print("No updates required.")
                    logger.info("No updates required")
            else:
                logger.info("No data available")
                print("No data found.")
                
                if acc_no:
                    columns.append("acc_no")
                    values.append(f"'{acc_no}'")
                if acc_name:
                    columns.append("acc_name")
                    values.append(f"'{acc_name}'")
                if status:
                    columns.append("status")
                    values.append(f"'{status}'")
                if mobile:
                    columns.append("mobile")
                    values.append(f"'{mobile}'")
                if email:
                    columns.append("email")
                    values.append(f"'{email}'")
                if address:
                    columns.append("address")
                    values.append(f"'{address}'")
                if permanent_address:
                    columns.append("perm_address")
                    values.append(f"'{permanent_address}'")
                if payment_address:
                    columns.append("payment_address")
                    values.append(f"'{payment_address}'")
                if dob:
                    columns.append("dob")
                    values.append(f"'{dob}'")
                if plan:
                    columns.append("cur_plan")
                    values.append(f"'{plan}'")
                if created_date:
                    columns.append("doj")
                    values.append(f"'{created_date}'")
                if mac:
                    columns.append("mac_id")
                    values.append(f"'{mac}'")
                if project:
                    columns.append("project")
                    values.append(f"'{project}'")

                if temp_block:
                    block = block_selection(temp_block)
                    if block:
                        columns.append("block")
                        values.append(f"'{block}'")
                    columns.append("block_no")
                    values.append(f"'{temp_block}'")

                columns.append("user_name")
                values.append(f"'{acc}'")
                columns.append('created_date')
                values.append(f"now()")
                columns.append('updated_by')
                values.append(f"'{bot_name}'")

                insert_query = f"INSERT INTO net_broadband.netplus ({', '.join(columns)}) VALUES ({', '.join(values)});"
                print("Insert Query:", insert_query)
                logger.info(f"Insert Query: {insert_query}")
                db.execute(insert_query)

            acc_list_done.append(acc)
            acc_btn = driver.find_element(By.XPATH, '//*[@id="lbAccount"]')
            logger.info('Trying to click the account button')
            driver.execute_script("arguments[0].click();", acc_btn)
            wi.processing_check_wait(driver=driver, xpath='//*[@id="ContentPlaceHolder1_ddlPageSize"]/option[7]',time=30)
            driver.find_element(By.XPATH, '//*[@id="ContentPlaceHolder1_ddlPageSize"]/option[7]').click()
            time.sleep(20)
            logger.info("================================================================================================")

        except Exception as err:
            print(str(err))
            logger.error("================================================================================================")
            acc_btn = driver.find_element(By.XPATH, '//*[@id="lbAccount"]')
            driver.execute_script("arguments[0].click();", acc_btn)
            logger.error(f"Error in check and update acc in db : {str(err)}")
            logger.error("================================================================================================")
            continue
        time.sleep(5)
    return acc_list_done


def block_selection(num):
    block_dict = {
                '1001 - 1100': 'A1A',
                '1101 - 1200': 'A1B',
                '1201 - 1300': 'A1C',
                '1301 - 1400': 'A2A',
                '1401 - 1500': 'A2B',
                '1501 - 1600': 'A2C',
                '1601 - 1700': 'A3A',
                '1701 - 1800': 'A3B',
                '1801 - 1900': 'A3C',
                '1901 - 2000': 'A4A',
                '2001 - 2100': 'A4B',
                '2101 - 2200': 'A4C',
                '2201 - 2300': 'A5A',
                '2301 - 2400': 'A5B',
                '2401 - 2500': 'A5C',
                '2501 - 2600': 'A6A',
                '2601 - 2700': 'A6B',
                '2701 - 2800': 'A6C',
                '2801 - 2900': 'A7A',
                '2901 - 3000': 'A7B',
                '3001 - 3100': 'A7C',
                
                '3101 - 3200': 'B1A',
                '3201 - 3300': 'B1B',
                '3301 - 3400': 'B1C',
                '3401 - 3500': 'B1D',
                '3501 - 3600': 'B2A',
                '3601 - 3700': 'B2B',
                '3701 - 3800': 'B2C',
                '3801 - 3900': 'B2D',
                '3901 - 4000': 'B3A',
                '4001 - 4100': 'B3B',
                '4101 - 4200': 'B3C',
                '4201 - 4300': 'B3D',
                '4301 - 4400': 'B4A',
                '4401 - 4500': 'B4B',
                '4501 - 4600': 'B4C',
                '4601 - 4700': 'B4D',
                '4701 - 4800': 'B4E',
                
                '4801 - 4900': 'C1A',
                '4901 - 5000': 'C1B',
                '5001 - 5100': 'C2A',
                '5101 - 5200': 'C2B',
                '5201 - 5300': 'C3A',
                '5301 - 5400': 'C3B',
                '5401 - 5500': 'C4A',
                '5501 - 5600': 'C4B',
                '5601 - 5700': 'C5A',
                '5701 - 5800': 'C5B',
            }
    result = None
    if not num:
        return result
    try:
        for key, value in block_dict.items():
            # Parse the range
            start, end = map(int, key.split(' - '))
            # Check if temp_clock falls within the range
            if start <= int(num) <= end:
                result = value
                break
    except Exception as err:
        logger.error(f"Error in block section: {str(err)}")
    return result


def main():
    try:
        driver = webdriver.Chrome(options=chrome_options)
        login(driver)
        search_for_accounts(driver)
    except Exception as er:
        driver.quit()

def job():
    print("Bot started ...")
    main()

schedule.every().saturday.at("06:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)

