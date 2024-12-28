import pytesseract
# from PIL import Image
from selenium import webdriver
from PIL import Image, ImageEnhance, ImageFilter
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import os
import time
import glob
import web_interface as wi
import datetime
import db_connect as db
import re
import shutil
import others
import schedule
import mail
import logging
import os
from selenium.webdriver.common.alert import Alert


logs_folder = os.path.join(os.getcwd(),'Logs')
os.makedirs(logs_folder, exist_ok=True)

os.makedirs(os.path.join(os.getcwd(), 'CSV Files'), exist_ok=True)

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

time_stamp = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")  
log_file = os.path.join(logs_folder, f'all_{time_stamp}.log')
file_handler = logging.FileHandler(log_file)

formatter = logging.Formatter('%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s')
file_handler.setFormatter(formatter)

logger.addHandler(file_handler)


download_folder = os.path.join(os.getcwd(), 'all_downloads')

chrome_options = Options()
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')

prefs = {
    'download.default_directory': download_folder,
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'safebrowsing.enabled': True
}

chrome_options.add_experimental_option('prefs', prefs)

pytesseract.pytesseract.tesseract_cmd = r"C:\Users\dme\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"


# def get_captch_text(captcha_element):
#     captcha_screenshot = captcha_element.screenshot_as_png

#     with open('captcha.png', 'wb') as file:
#         file.write(captcha_screenshot)

#     captcha_image = Image.open('captcha.png')

#     captcha_text = pytesseract.image_to_string(captcha_image, config='--psm 7')

#     captcha_text = ''.join(c for c in captcha_text if c.isalnum())

#     return captcha_text

def get_captch_text(captcha_element):
    # Capture the screenshot of the CAPTCHA element
    captcha_screenshot = captcha_element.screenshot_as_png
    
    # Save the screenshot to a file
    with open('captcha.png', 'wb') as file:
        file.write(captcha_screenshot)
    
    # Open the image using PIL
    captcha_image = Image.open('captcha.png')

    # Preprocessing the CAPTCHA image (Enhance contrast, convert to grayscale, etc.)
    captcha_image = captcha_image.convert('L')  # Convert to grayscale
    captcha_image = captcha_image.filter(ImageFilter.MedianFilter())  # Reduce noise
    enhancer = ImageEnhance.Contrast(captcha_image)
    captcha_image = enhancer.enhance(2)  # Increase contrast
    
    # Save preprocessed image (optional, for debugging)
    captcha_image.save('processed_captcha.png')

    # Use pytesseract to extract text
    captcha_text = pytesseract.image_to_string(captcha_image, config='--psm 8')  # Try different psm modes
    
    # Clean up the extracted text (remove any non-alphanumeric characters)
    captcha_text = ''.join(c for c in captcha_text if c.isalnum())

    return captcha_text

def get_latest_downloaded_file(type):
    list_of_files = glob.glob(os.path.join(download_folder, '*'))
    if type == 'pdf':
        filtered_files = [
            file for file in list_of_files
            if "Tendernotice_1.pdf" in file
        ]
    else:
        filtered_files = [
            file for file in list_of_files
            if not re.search(r"\([^()]+\)", file)
        ]

    if filtered_files:
        latest_file = max(filtered_files, key=os.path.getctime)
        return latest_file
    else:
        return None


def manual_insert(t_id, remarks, name, link):
    try:
        check_query = f"""select tender_id from tender.manual_tender where tender_id = '{t_id}' and mail_send = 'False';"""
        data = db.get_data_in_list_of_tuple(check_query)
        if data:
            return False
        to_add = ['raman@shreenathgroup.in', 'sentmhl@gmail.com', 'sentmhl1@gmail.com', 'ramit.shreenath@gmail.com']
        sub = f'Unable to insert the tender {t_id}'
        body = f"""
        Hello Team,

        It is noticed that a tender is not inserted by bot.
        Please check and do needfull.
        Tender ID: {t_id}
        link: {link}

        """
        mail.send_mail(to_add=to_add, sub=sub, body=body)
        now_time = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        query = f"""insert into tender.manual_tender (tender_id, remarks, mail_send, user_id, ext_col_1) values ('{t_id}', '{remarks}', 'True', '{name}', '{now_time}') """
        db.execute(query)
        return True
    except:
        return False


def Tntenders_GOV_NIC_BOT_main(key_word):
    name = 'Tntenders GOV NIC BOT'
    print(f'Starting the bot {name}')
    link = 'https://tntenders.gov.in/'
    logger.info('='*100)
    logger.info(f'Starting the bot {name}')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://tntenders.gov.in/nicgep/app?page=FrontEndAdvancedSearch&service=page')
    tender_type = driver.find_element(By.XPATH, '//*[@id="TenderType"]/option[2]')
    tender_type.click()
    tender_search_press = driver.find_element(By.XPATH, '//*[@id="workItemTitle"]')
    tender_search_press.click()
    tender_search_press.send_keys(key_word)
    time.sleep(5)
    while True:
        logger.info('Trying to get the Captcha')
        try:
            while True:
                captcha_element = driver.find_element(By.XPATH, '//*[@id="captchaImage"]')
                c_data = get_captch_text(captcha_element)
                if c_data:
                    time.sleep(20)
                    break
                time.sleep(5)
                ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                ref_btn.click()
            captcha_data = driver.find_element(By.XPATH, '//*[@id="captchaText"]')
            captcha_data.send_keys(c_data)

            submit_button = driver.find_element(By.XPATH, '//*[@id="submit"]')
            submit_button.click()
            time.sleep(2)
            try:
                alert = Alert(driver)
                alert_text = alert.text
                try:
                    alert.accept()
                except:
                    alert.dismiss()
                ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                ref_btn.click()
            except:
                pass
            tender_list = driver.find_element(By.XPATH, '//*[@id="table"]/tbody')
            if tender_list:
                break
        except Exception as err:
            try:
                no_tend = driver.find_element(By.XPATH, '//*[contains(text(), "No Tenders found.")]')
                logger.info('No tenders in portal')
                break
            except:
                pass
            # logger.error('Getting Error while gatting Captcha, Error: %s', str(err))
    tender_data = []
    while True:
        try:
            no_tend = driver.find_element(By.XPATH, '//*[contains(text(), "No Tenders found.")]')
            if no_tend:
                logger.info('No tenders in portal')
                break
        except:
            pass
        tender_list = driver.find_element(By.XPATH, '//*[@id="table"]/tbody')
        all_tender_list = tender_list.text.split('\n')[1:]
        try:
            new_list_1 = [i for i in all_tender_list if "<<" not in i or ">>" not in i or ' ' not in i]
            new_list = []
            for i in new_list_1:
                if i != ' ':
                    new_list.append(i)
        except:
            new_list = all_tender_list
        
        count = -1
        for i in new_list:
            print(i)
            if count == -1:
                xpath_a = '//*[@id="DirectLink_0"]'
            else:
                xpath_a = f'//*[@id="DirectLink_0_{count}"]'

            count += 1
            print(xpath_a)
            if i or i != " ":
                pattern = r"\[(.*?)\]"
                try:
                    match = re.search(pattern, i)
                except:
                    match = None

                try:
                    pattern_1 = r'\[(\w+)\]'
                    matches = re.findall(pattern_1, i)

                    if len(matches) > 1:
                        t_id = matches[1]
                    else:
                        t_id = matches[0]
                except:
                    t_id = None
                print(t_id)
                if t_id:
                    query = f"select tender_id from tender.tender_management where tender_id = '{t_id}';"
                    data = db.get_data_in_list_of_tuple(query)
                if data:
                    logger.info('Tender ID is found in DB, Tender ID %s', str(t_id))
                    continue
                if match:
                    # print('yes')
                    logger.info('Working on Tender ID: %s', str(t_id))
                    extracted_text = match.group(1)
                    time_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    try:
                        tender = driver.find_element(By.XPATH, xpath_a)
                        tender.click()
                        print('Clicked XPATH')
                    except:
                        try:
                            tender = driver.find_element(By.XPATH, f'//*[contains(text(),"{extracted_text}")]')
                            tender.click()
                        except:
                            print('Unable to enter')
                            remarks = 'Unable to click on tender (maybe same name issue)'
                            manual_insert(t_id, remarks, name, link)
                            # logger.error("Getting error in tender click part for %s", str(t_id))
                            continue
                    time.sleep(3)
                    try:
                        tender_id = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/b').text
                    except:
                        try:
                            tender_id = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/b').text
                        except:
                            remarks = 'Unable to click on tender (maybe same name issue)'
                            manual_insert(t_id, remarks, name, link)
                            continue
                    try:
                        try:
                            cust = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/b').text.replace("'", "''")
                        except:
                            cust = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/b').text.replace("'", "''")
                        try:
                            loc = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[7]/td[2]').text.replace("'", "''")
                        except:
                            loc = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[7]/td[2]').text.replace("'", "''")
                        try:
                            work_desp = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[2]/td[2]/b').text.replace("'", "''")
                        except:
                            work_desp = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[2]/td[2]/b').text.replace("'", "''")
                        try:
                            p_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody/tr[1]/td[2]').text
                        except:
                            p_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[1]/td[2]').text
                        try:
                            s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody/tr[4]/td[4]').text
                        except:
                            try:
                                s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[4]/td[4]').text
                            except:
                                s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[23]/td/table/tbody/tr[4]/td[4]').text
                        try:
                            emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                        except:
                            try:
                                emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                            except:
                                emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                        try:
                            pbm_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[8]/td[4]').text
                        except:
                            pbm_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[8]/td[4]').text
                        try:
                            e_value = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[5]/td[2]').text.replace(",", "")
                        except:
                            e_value = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[5]/td[2]').text.replace(",", "")
                    except:
                        remarks = 'Unable to get the tender data from portal, Please insert manually.'
                        manual_insert(t_id, remarks, name, link)
                        back_btn = driver.find_element(By.XPATH,'//*[@id="DirectLink_11"]')
                        back_btn.click()
                        continue

                    try:
                        pub_date = datetime.datetime.strptime(p_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        pub_date = None
                    try:
                        sub_date = datetime.datetime.strptime(s_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        sub_date = None
                    try:
                        pbm = datetime.datetime.strptime(pbm_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        pbm = pbm_date
                        if 'NA' in pbm_date:
                            pbm = None

                    if (('camera' in work_desp.lower() and 'DSLR' not in work_desp.upper()) or ('CCTV' in work_desp.upper() and 'DSLR' not in work_desp.upper()) or \
                        ('LAN ' in work_desp.upper() or ' LAN' in work_desp.upper()) or ('network' in work_desp.lower()) or ('surveillance' in work_desp.lower()) or \
                            ('switch' in work_desp.lower()) or ('unmanned aerial vehicle' in work_desp.lower()) or ('UAV' in work_desp.upper()) or ('drone' in work_desp.lower())) \
                            and (' lt ' not in work_desp.lower()) and (' kv ' not in work_desp.lower()) and (' cement ' not in work_desp.lower()) and (' ht ' not in work_desp.lower()):

                        tender_dict = {
                            'tender_id': tender_id,
                            'customer': cust,
                            'location': loc,
                            'name_of_work': work_desp,
                            'publish_date': pub_date,
                            'submission_date': sub_date,
                            'emd': emd,
                            'pbm': pbm,
                            'e_value': e_value,
                            'inserted_time': time_now,
                            'inserted_user_id': name
                        }
                        # logger.info(tender_dict)
                        tender_data.append(tender_dict)
                        others.delete_folder(download_folder=download_folder)

                        try:
                            try:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="docDownoad"]')
                                pdf_doc.click()
                            except:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="DirectLink_0"]')
                                pdf_doc.click()
                            try:
                                while True:
                                    while True:
                                        try:
                                            captcha_element = driver.find_element(By.XPATH, '//*[@id="captchaImage"]')
                                        except:
                                            raise Exception('Captcha Not found')
                                        c_data = get_captch_text(captcha_element)
                                        if c_data:
                                            break
                                        time.sleep(5)
                                        ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                                        ref_btn.click()
                                    captcha_data = driver.find_element(By.XPATH, '//*[@id="captchaText"]')
                                    captcha_data.send_keys(c_data)
                                    submit_button = driver.find_element(By.XPATH, '//*[@id="Submit"]')
                                    submit_button.click()
                                    try:
                                        driver.find_element(By.XPATH, '//*[contains(text(),"Invalid Captcha! Please Enter Correct Captcha.")]')
                                    except:
                                        break
                            except Exception as err:
                                print(err)
                                # logger.error('Getting error in pdf_doc captcha, Error: %s', str(err))
                        except:
                            logger.info('Documents are not downloadable')
                            # continue
                        # nas_path = os.path.join(os.getcwd(), 'downloads', str(tender_id))
                        nas_path = os.path.join(r'\\Digitaldreams\tender auto', tender_id)
                        os.makedirs(nas_path, exist_ok=True)

                        try:
                            try:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="DirectLink_0"]')
                            except:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="docDownoad"]')
                            pdf_doc.click()
                            time.sleep(5)
                            print('Download pdf files')

                            while True:
                                try:
                                    latest_file = get_latest_downloaded_file('pdf')
                                    new_file_path = os.path.join(nas_path, os.path.basename(latest_file))
                                    shutil.move(latest_file, new_file_path)
                                    print('Move pdf files')
                                    break
                                except:
                                    time.sleep(5)
                        except Exception as err:
                            # logger.error('Getting error in pdf download, Error: %s', str(err))
                            new_file_path = nas_path

                        tries = 5
                        while tries > 0:
                            tries -= 1
                            try:
                                try:
                                    zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_7"]')
                                except:
                                    zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_6"]')
                                zip_file.click()
                                time.sleep(5)

                                while True:
                                    crdownload_files = glob.glob(os.path.join(download_folder, '*.crdownload'))
                                    if crdownload_files:
                                        time.sleep(5)
                                    else:
                                        try:
                                            latest_file = get_latest_downloaded_file('.zip')
                                            if latest_file.endswith('.zip'):
                                                new_file_path = os.path.join(nas_path, os.path.basename(latest_file))
                                                shutil.move(latest_file, new_file_path)
                                                break
                                        except:
                                            raise Exception("No file found.")
                                break
                            except Exception as err:
                                # logger.error('Getting error in ZIP download, Error: %s', str(err))
                                new_file_path = nas_path
                                time.sleep(5)

                        loc_t_id = tender_id + '_' + loc.replace(" ","")

                        query = f"""INSERT INTO tender.tender_management (local_tender_id, tender_id, customer, name_of_work, submission_date, link,
                        file_location, folder_location, inserted_time, user_id, inserted_user_id, publish_date, verification_1, emd, pbm, location, e_value) 
                        VALUES ('{loc_t_id}','{tender_id}', '{str(cust).replace("'","''")}','{str(work_desp).replace("'","''")}', '{str(sub_date)}', '{link}',
                        '{new_file_path}','{nas_path}', '{time_now}', '{name}', '{name}', '{str(pub_date)}', 'FOR UPDATE', '{str(emd)}',
                        '{str(pbm)}', '{str(loc)}', '{str(e_value)}')  on conflict (local_tender_id) do nothing ;"""
                        logger.info(query)
                        db.execute(query)

                        emd_dict = {
                            "tender_id": str(tender_id),
                            "emd_required": "NO",
                            "emd_form": None,
                            "emd_amount": f'{str(emd)}',
                            "in_favour_of": None,
                            "mail_to_fin": None,
                            "remarks": "EMD Details Not Inserted",
                            "time_stamp": datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
                        }

                        db.insert_dict_into_table("tender.tender_emd", emd_dict)

                        folder_dict = {
                                    "tender_id": tender_id,
                                    "current_time_col": datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
                                    "user_id": name
                                }
                        db.insert_dict_into_table("tender.tender_folder", folder_dict)

                        try:
                            ass_name = 'Farzana'
                            # tat_query = f""" insert into tender.tender_tat (t_id, stage, assign_time, assign_to, ext_col_1) 
                            # values('{tender_id}', 'FOR UPDATE-Open', now(), '{ass_name}', 'BOT'); """
                            # tat_query = f""" INSERT INTO tender.tender_tat (t_id, stage, assign_time, assign_to, ext_col_1)
                            #             SELECT '{tender_id}', 'FOR UPDATE-Open', NOW(), '{ass_name}', 'BOT'
                            #             FROM (SELECT 1) AS dummy
                            #             LEFT JOIN tender.tender_tat tt ON tt.t_id = '{tender_id}' AND tt.stage = 'FOR UPDATE-Open'
                            #             WHERE tt.t_id IS NULL; """
                            check_query_tat = f""" select 1 from tender.tender_tat where t_id = '{tender_id}' ; """
                            check_data_tat = db.get_data_in_list_of_tuple(check_query_tat)
                            if not check_data_tat:
                                tat_query = f""" INSERT INTO tender.tender_tat (t_id, stage, status, assign_time, assign_to, ext_col_1)
                                            VALUES ('{tender_id}', 'FOR UPDATE', 'Open', NOW(), '{ass_name}', 'BOT'); """
                                db.execute(tat_query)
                        except Exception as err:
                            print(err)
                            pass

                        others.delete_folder(download_folder=download_folder)


                    back_btn = driver.find_element(By.XPATH,'//*[@id="DirectLink_11"]')
                    back_btn.click()
                    time.sleep(3)

        try:
            nxt_pg = driver.find_element(By.XPATH, '//*[@id="linkFwd"]')
            nxt_pg.click()
            time.sleep(3)
        except Exception as err:
            # logger.error("Getting error while click on next page button, Error: %s", str(err))
            break

    try:
        driver.close()
    except:
        logger.info('Unable to close the driver')
        pass
    result_df = pd.DataFrame(tender_data)

    # result_df.to_csv(f'CSV Files/all_tender_data_{key_word}.csv')
    result_df.to_csv(os.path.join(os.getcwd(),'CSV Files',f'all_tender_data_{name}_{key_word}.csv'))


def TripuraTenders_GOV_NICGEP_BOT_main(key_word):
    name = 'TripuraTenders GOV NICGEP BOT'
    print(f'Starting the bot {name}')
    link = 'https://tripuratenders.gov.in/'
    logger.info('='*100)
    logger.info(f'Starting the bot {name}')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://tripuratenders.gov.in/nicgep/app?page=FrontEndAdvancedSearch&service=page')
    tender_type = driver.find_element(By.XPATH, '//*[@id="TenderType"]/option[2]')
    tender_type.click()
    tender_search_press = driver.find_element(By.XPATH, '//*[@id="workItemTitle"]')
    tender_search_press.click()
    tender_search_press.send_keys(key_word)
    time.sleep(5)
    while True:
        logger.info('Trying to get the Captcha')
        try:
            while True:
                captcha_element = driver.find_element(By.XPATH, '//*[@id="captchaImage"]')
                c_data = get_captch_text(captcha_element)
                if c_data:
                    time.sleep(20)
                    break
                time.sleep(5)
                ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                ref_btn.click()
            captcha_data = driver.find_element(By.XPATH, '//*[@id="captchaText"]')
            captcha_data.send_keys(c_data)

            submit_button = driver.find_element(By.XPATH, '//*[@id="submit"]')
            submit_button.click()
            time.sleep(2)
            try:
                alert = Alert(driver)
                alert_text = alert.text
                try:
                    alert.accept()
                except:
                    alert.dismiss()
                ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                ref_btn.click()
            except:
                pass
            tender_list = driver.find_element(By.XPATH, '//*[@id="table"]/tbody')
            if tender_list:
                break
        except Exception as err:
            try:
                no_tend = driver.find_element(By.XPATH, '//*[contains(text(), "No Tenders found.")]')
                logger.info('No tenders in portal')
                break
            except:
                pass
            # logger.error('Getting Error while gatting Captcha, Error: %s', str(err))
    tender_data = []
    while True:
        try:
            no_tend = driver.find_element(By.XPATH, '//*[contains(text(), "No Tenders found.")]')
            if no_tend:
                logger.info('No tenders in portal')
                break
        except:
            pass
        tender_list = driver.find_element(By.XPATH, '//*[@id="table"]/tbody')
        all_tender_list = tender_list.text.split('\n')[1:]
        try:
            new_list_1 = [i for i in all_tender_list if "<<" not in i or ">>" not in i or ' ' not in i]
            new_list = []
            for i in new_list_1:
                if i != ' ':
                    new_list.append(i)
        except:
            new_list = all_tender_list
        
        count = -1
        for i in new_list:
            print(i)
            if count == -1:
                xpath_a = '//*[@id="DirectLink_0"]'
            else:
                xpath_a = f'//*[@id="DirectLink_0_{count}"]'

            count += 1
            print(xpath_a)
            if i or i != " ":
                pattern = r"\[(.*?)\]"
                try:
                    match = re.search(pattern, i)
                except:
                    match = None

                try:
                    pattern_1 = r'\[(\w+)\]'
                    matches = re.findall(pattern_1, i)

                    if len(matches) > 1:
                        t_id = matches[1]
                    else:
                        t_id = matches[0]
                except:
                    t_id = None
                print(t_id)
                if t_id:
                    query = f"select tender_id from tender.tender_management where tender_id = '{t_id}';"
                    data = db.get_data_in_list_of_tuple(query)
                if data:
                    logger.info('Tender ID is found in DB, Tender ID %s', str(t_id))
                    continue
                if match:
                    # print('yes')
                    logger.info('Working on Tender ID: %s', str(t_id))
                    extracted_text = match.group(1)
                    time_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    try:
                        tender = driver.find_element(By.XPATH, xpath_a)
                        tender.click()
                        print('Clicked XPATH')
                    except:
                        try:
                            tender = driver.find_element(By.XPATH, f'//*[contains(text(),"{extracted_text}")]')
                            tender.click()
                        except:
                            print('Unable to enter')
                            remarks = 'Unable to click on tender (maybe same name issue)'
                            manual_insert(t_id, remarks, name, link)
                            # logger.error("Getting error in tender click part for %s", str(t_id))
                            continue
                    time.sleep(3)
                    try:
                        tender_id = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/b').text
                    except:
                        try:
                            tender_id = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/b').text
                        except:
                            remarks = 'Unable to click on tender (maybe same name issue)'
                            manual_insert(t_id, remarks, name, link)
                            continue
                    try:
                        try:
                            cust = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/b').text.replace("'", "''")
                        except:
                            cust = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/b').text.replace("'", "''")
                        try:
                            loc = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[7]/td[2]').text.replace("'", "''")
                        except:
                            loc = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[7]/td[2]').text.replace("'", "''")
                        try:
                            work_desp = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[2]/td[2]/b').text.replace("'", "''")
                        except:
                            work_desp = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[2]/td[2]/b').text.replace("'", "''")
                        try:
                            p_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody/tr[1]/td[2]').text
                        except:
                            p_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[1]/td[2]').text
                        try:
                            s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody/tr[4]/td[4]').text
                        except:
                            try:
                                s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[4]/td[4]').text
                            except:
                                s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[23]/td/table/tbody/tr[4]/td[4]').text
                        try:
                            emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                        except:
                            try:
                                emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                            except:
                                emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                        try:
                            pbm_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[8]/td[4]').text
                        except:
                            pbm_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[8]/td[4]').text
                        try:
                            e_value = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[5]/td[2]').text.replace(",", "")
                        except:
                            e_value = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[5]/td[2]').text.replace(",", "")
                    except:
                        remarks = 'Unable to get the tender data from portal, Please insert manually.'
                        manual_insert(t_id, remarks, name, link)
                        back_btn = driver.find_element(By.XPATH,'//*[@id="DirectLink_11"]')
                        back_btn.click()
                        continue

                    try:
                        pub_date = datetime.datetime.strptime(p_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        pub_date = None
                    try:
                        sub_date = datetime.datetime.strptime(s_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        sub_date = None
                    try:
                        pbm = datetime.datetime.strptime(pbm_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        pbm = pbm_date
                        if 'NA' in pbm_date:
                            pbm = None

                    if (('camera' in work_desp.lower() and 'DSLR' not in work_desp.upper()) or ('CCTV' in work_desp.upper() and 'DSLR' not in work_desp.upper()) or \
                        ('LAN ' in work_desp.upper() or ' LAN' in work_desp.upper()) or ('network' in work_desp.lower()) or ('surveillance' in work_desp.lower()) or \
                            ('switch' in work_desp.lower()) or ('unmanned aerial vehicle' in work_desp.lower()) or ('UAV' in work_desp.upper()) or ('drone' in work_desp.lower())) \
                            and (' lt ' not in work_desp.lower()) and (' kv ' not in work_desp.lower()) and (' cement ' not in work_desp.lower()) and (' ht ' not in work_desp.lower()):

                        tender_dict = {
                            'tender_id': tender_id,
                            'customer': cust,
                            'location': loc,
                            'name_of_work': work_desp,
                            'publish_date': pub_date,
                            'submission_date': sub_date,
                            'emd': emd,
                            'pbm': pbm,
                            'e_value': e_value,
                            'inserted_time': time_now,
                            'inserted_user_id': name
                        }
                        # logger.info(tender_dict)
                        tender_data.append(tender_dict)
                        others.delete_folder(download_folder=download_folder)

                        try:
                            try:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="docDownoad"]')
                                pdf_doc.click()
                            except:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="DirectLink_0"]')
                                pdf_doc.click()
                            try:
                                while True:
                                    while True:
                                        try:
                                            captcha_element = driver.find_element(By.XPATH, '//*[@id="captchaImage"]')
                                        except:
                                            raise Exception('Captcha Not found')
                                        c_data = get_captch_text(captcha_element)
                                        if c_data:
                                            break
                                        time.sleep(5)
                                        ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                                        ref_btn.click()
                                    captcha_data = driver.find_element(By.XPATH, '//*[@id="captchaText"]')
                                    captcha_data.send_keys(c_data)
                                    submit_button = driver.find_element(By.XPATH, '//*[@id="Submit"]')
                                    submit_button.click()
                                    try:
                                        driver.find_element(By.XPATH, '//*[contains(text(),"Invalid Captcha! Please Enter Correct Captcha.")]')
                                    except:
                                        break
                            except Exception as err:
                                print(err)
                                # logger.error('Getting error in pdf_doc captcha, Error: %s', str(err))
                        except:
                            logger.info('Documents are not downloadable')
                            # continue
                        # nas_path = os.path.join(os.getcwd(), 'downloads', str(tender_id))
                        nas_path = os.path.join(r'\\Digitaldreams\tender auto', tender_id)
                        os.makedirs(nas_path, exist_ok=True)

                        try:
                            try:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="DirectLink_0"]')
                            except:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="docDownoad"]')
                            pdf_doc.click()
                            time.sleep(5)
                            print('Download pdf files')

                            while True:
                                try:
                                    latest_file = get_latest_downloaded_file('pdf')
                                    new_file_path = os.path.join(nas_path, os.path.basename(latest_file))
                                    shutil.move(latest_file, new_file_path)
                                    print('Move pdf files')
                                    break
                                except:
                                    time.sleep(5)
                        except Exception as err:
                            # logger.error('Getting error in pdf download, Error: %s', str(err))
                            new_file_path = nas_path

                        tries = 5
                        while tries > 0:
                            tries -= 1
                            try:
                                try:
                                    zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_7"]')
                                except:
                                    try:
                                        zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_8"]')
                                    except:
                                        zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_6"]')
                                zip_file.click()
                                time.sleep(5)

                                while True:
                                    crdownload_files = glob.glob(os.path.join(download_folder, '*.crdownload'))
                                    if crdownload_files:
                                        time.sleep(5)
                                    else:
                                        try:
                                            latest_file = get_latest_downloaded_file('.zip')
                                            if latest_file.endswith('.zip'):
                                                new_file_path = os.path.join(nas_path, os.path.basename(latest_file))
                                                shutil.move(latest_file, new_file_path)
                                                break
                                        except:
                                            raise Exception("No file found.")
                                break
                            except Exception as err:
                                # logger.error('Getting error in ZIP download, Error: %s', str(err))
                                new_file_path = nas_path
                                time.sleep(5)

                        loc_t_id = tender_id + '_' + loc.replace(" ","")

                        query = f"""INSERT INTO tender.tender_management (local_tender_id, tender_id, customer, name_of_work, submission_date, link,
                        file_location, folder_location, inserted_time, user_id, inserted_user_id, publish_date, verification_1, emd, pbm, location, e_value) 
                        VALUES ('{loc_t_id}','{tender_id}', '{str(cust).replace("'","''")}','{str(work_desp).replace("'","''")}', '{str(sub_date)}', '{link}',
                        '{new_file_path}','{nas_path}', '{time_now}', '{name}', '{name}', '{str(pub_date)}', 'FOR UPDATE', '{str(emd)}',
                        '{str(pbm)}', '{str(loc)}', '{str(e_value)}')  on conflict (local_tender_id) do nothing ;"""
                        logger.info(query)
                        db.execute(query)

                        emd_dict = {
                            "tender_id": str(tender_id),
                            "emd_required": "NO",
                            "emd_form": None,
                            "emd_amount": f'{str(emd)}',
                            "in_favour_of": None,
                            "mail_to_fin": None,
                            "remarks": "EMD Details Not Inserted",
                            "time_stamp": datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
                        }

                        db.insert_dict_into_table("tender.tender_emd", emd_dict)

                        folder_dict = {
                                    "tender_id": tender_id,
                                    "current_time_col": datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
                                    "user_id": name
                                }
                        db.insert_dict_into_table("tender.tender_folder", folder_dict)

                        try:
                            ass_name = 'Farzana'
                            # tat_query = f""" insert into tender.tender_tat (t_id, stage, assign_time, assign_to, ext_col_1) 
                            # values('{tender_id}', 'FOR UPDATE-Open', now(), '{ass_name}', 'BOT'); """
                            # tat_query = f""" INSERT INTO tender.tender_tat (t_id, stage, assign_time, assign_to, ext_col_1)
                            #             SELECT '{tender_id}', 'FOR UPDATE-Open', NOW(), '{ass_name}', 'BOT'
                            #             FROM (SELECT 1) AS dummy
                            #             LEFT JOIN tender.tender_tat tt ON tt.t_id = '{tender_id}' AND tt.stage = 'FOR UPDATE-Open'
                            #             WHERE tt.t_id IS NULL; """
                            check_query_tat = f""" select 1 from tender.tender_tat where t_id = '{tender_id}' ; """
                            check_data_tat = db.get_data_in_list_of_tuple(check_query_tat)
                            if not check_data_tat:
                                tat_query = f""" INSERT INTO tender.tender_tat (t_id, stage, status, assign_time, assign_to, ext_col_1)
                                            VALUES ('{tender_id}', 'FOR UPDATE', 'Open', NOW(), '{ass_name}', 'BOT'); """
                                db.execute(tat_query)
                        except Exception as err:
                            print(err)
                            pass

                        others.delete_folder(download_folder=download_folder)


                    back_btn = driver.find_element(By.XPATH,'//*[@id="DirectLink_11"]')
                    back_btn.click()
                    time.sleep(3)

        try:
            nxt_pg = driver.find_element(By.XPATH, '//*[@id="linkFwd"]')
            nxt_pg.click()
            time.sleep(3)
        except Exception as err:
            # logger.error("Getting error while click on next page button, Error: %s", str(err))
            break

    try:
        driver.close()
    except:
        logger.info('Unable to close the driver')
        pass
    result_df = pd.DataFrame(tender_data)

    # result_df.to_csv(f'CSV Files/all_tender_data_{key_word}.csv')
    result_df.to_csv(os.path.join(os.getcwd(),'CSV Files',f'all_tender_data_{name}_{key_word}.csv'))


def UKtenders_GOV_NICGEP_BOT_main(key_word):
    name = 'UKtenders GOV NICGEP BOT'
    print(f'Starting the bot {name}')
    link = 'https://uktenders.gov.in/'
    logger.info('='*100)
    logger.info(f'Starting the bot {name}')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://uktenders.gov.in/nicgep/app?page=FrontEndAdvancedSearch&service=page')
    tender_type = driver.find_element(By.XPATH, '//*[@id="TenderType"]/option[2]')
    tender_type.click()
    tender_search_press = driver.find_element(By.XPATH, '//*[@id="workItemTitle"]')
    tender_search_press.click()
    tender_search_press.send_keys(key_word)
    time.sleep(5)
    while True:
        logger.info('Trying to get the Captcha')
        try:
            while True:
                captcha_element = driver.find_element(By.XPATH, '//*[@id="captchaImage"]')
                c_data = get_captch_text(captcha_element)
                if c_data:
                    time.sleep(20)
                    break
                time.sleep(5)
                ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                ref_btn.click()
            captcha_data = driver.find_element(By.XPATH, '//*[@id="captchaText"]')
            captcha_data.send_keys(c_data)

            submit_button = driver.find_element(By.XPATH, '//*[@id="submit"]')
            submit_button.click()
            time.sleep(2)
            try:
                alert = Alert(driver)
                alert_text = alert.text
                try:
                    alert.accept()
                except:
                    alert.dismiss()
                ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                ref_btn.click()
            except:
                pass
            tender_list = driver.find_element(By.XPATH, '//*[@id="table"]/tbody')
            if tender_list:
                break
        except Exception as err:
            try:
                no_tend = driver.find_element(By.XPATH, '//*[contains(text(), "No Tenders found.")]')
                logger.info('No tenders in portal')
                break
            except:
                pass
            # logger.error('Getting Error while gatting Captcha, Error: %s', str(err))
    tender_data = []
    while True:
        try:
            no_tend = driver.find_element(By.XPATH, '//*[contains(text(), "No Tenders found.")]')
            if no_tend:
                logger.info('No tenders in portal')
                break
        except:
            pass
        tender_list = driver.find_element(By.XPATH, '//*[@id="table"]/tbody')
        all_tender_list = tender_list.text.split('\n')[1:]
        try:
            new_list_1 = [i for i in all_tender_list if "<<" not in i or ">>" not in i or ' ' not in i]
            new_list = []
            for i in new_list_1:
                if i != ' ':
                    new_list.append(i)
        except:
            new_list = all_tender_list
        
        count = -1
        for i in new_list:
            print(i)
            if count == -1:
                xpath_a = '//*[@id="DirectLink_0"]'
            else:
                xpath_a = f'//*[@id="DirectLink_0_{count}"]'

            count += 1
            print(xpath_a)
            if i or i != " ":
                pattern = r"\[(.*?)\]"
                try:
                    match = re.search(pattern, i)
                except:
                    match = None

                try:
                    pattern_1 = r'\[(\w+)\]'
                    matches = re.findall(pattern_1, i)

                    if len(matches) > 1:
                        t_id = matches[1]
                    else:
                        t_id = matches[0]
                except:
                    t_id = None
                print(t_id)
                if t_id:
                    query = f"select tender_id from tender.tender_management where tender_id = '{t_id}';"
                    data = db.get_data_in_list_of_tuple(query)
                if data:
                    logger.info('Tender ID is found in DB, Tender ID %s', str(t_id))
                    continue
                if match:
                    # print('yes')
                    logger.info('Working on Tender ID: %s', str(t_id))
                    extracted_text = match.group(1)
                    time_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    try:
                        tender = driver.find_element(By.XPATH, xpath_a)
                        tender.click()
                        print('Clicked XPATH')
                    except:
                        try:
                            tender = driver.find_element(By.XPATH, f'//*[contains(text(),"{extracted_text}")]')
                            tender.click()
                        except:
                            print('Unable to enter')
                            remarks = 'Unable to click on tender (maybe same name issue)'
                            manual_insert(t_id, remarks, name, link)
                            # logger.error("Getting error in tender click part for %s", str(t_id))
                            continue
                    time.sleep(3)
                    try:
                        tender_id = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/b').text
                    except:
                        try:
                            tender_id = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/b').text
                        except:
                            remarks = 'Unable to click on tender (maybe same name issue)'
                            manual_insert(t_id, remarks, name, link)
                            continue
                    try:
                        try:
                            cust = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/b').text.replace("'", "''")
                        except:
                            cust = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/b').text.replace("'", "''")
                        try:
                            loc = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[7]/td[2]').text.replace("'", "''")
                        except:
                            loc = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[7]/td[2]').text.replace("'", "''")
                        try:
                            work_desp = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[2]/td[2]/b').text.replace("'", "''")
                        except:
                            work_desp = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[2]/td[2]/b').text.replace("'", "''")
                        try:
                            p_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[1]/td[2]').text
                        except:
                            p_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody/tr[1]/td[2]').text
                        try:
                            s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[4]/td[4]').text
                        except:
                            try:
                                s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody/tr[4]/td[4]').text
                            except:
                                s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[23]/td/table/tbody/tr[4]/td[4]').text
                        try:
                             emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                        except:
                            try:
                                emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                            except:
                                emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                        try:
                            pbm_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[8]/td[4]').text
                        except:
                            pbm_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[8]/td[4]').text
                        try:
                            e_value = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[5]/td[2]').text.replace(",", "")
                        except:
                            e_value = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[5]/td[2]').text.replace(",", "")
                    except:
                        remarks = 'Unable to get the tender data from portal, Please insert manually.'
                        manual_insert(t_id, remarks, name, link)
                        back_btn = driver.find_element(By.XPATH,'//*[@id="DirectLink_11"]')
                        back_btn.click()
                        continue

                    try:
                        pub_date = datetime.datetime.strptime(p_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        pub_date = None
                    try:
                        sub_date = datetime.datetime.strptime(s_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        sub_date = None
                    try:
                        pbm = datetime.datetime.strptime(pbm_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        pbm = pbm_date
                        if 'NA' in pbm_date:
                            pbm = None

                    if (('camera' in work_desp.lower() and 'DSLR' not in work_desp.upper()) or ('CCTV' in work_desp.upper() and 'DSLR' not in work_desp.upper()) or \
                        ('LAN ' in work_desp.upper() or ' LAN' in work_desp.upper()) or ('network' in work_desp.lower()) or ('surveillance' in work_desp.lower()) or \
                            ('switch' in work_desp.lower()) or ('unmanned aerial vehicle' in work_desp.lower()) or ('UAV' in work_desp.upper()) or ('drone' in work_desp.lower())) \
                            and (' lt ' not in work_desp.lower()) and (' kv ' not in work_desp.lower()) and (' cement ' not in work_desp.lower()) and (' ht ' not in work_desp.lower()):

                        tender_dict = {
                            'tender_id': tender_id,
                            'customer': cust,
                            'location': loc,
                            'name_of_work': work_desp,
                            'publish_date': pub_date,
                            'submission_date': sub_date,
                            'emd': emd,
                            'pbm': pbm,
                            'e_value': e_value,
                            'inserted_time': time_now,
                            'inserted_user_id': name
                        }
                        # logger.info(tender_dict)
                        tender_data.append(tender_dict)
                        others.delete_folder(download_folder=download_folder)

                        try:
                            try:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="docDownoad"]')
                                pdf_doc.click()
                            except:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="DirectLink_0"]')
                                pdf_doc.click()
                            try:
                                while True:
                                    while True:
                                        try:
                                            captcha_element = driver.find_element(By.XPATH, '//*[@id="captchaImage"]')
                                        except:
                                            raise Exception('Captcha Not found')
                                        c_data = get_captch_text(captcha_element)
                                        if c_data:
                                            break
                                        time.sleep(5)
                                        ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                                        ref_btn.click()
                                    captcha_data = driver.find_element(By.XPATH, '//*[@id="captchaText"]')
                                    captcha_data.send_keys(c_data)
                                    submit_button = driver.find_element(By.XPATH, '//*[@id="Submit"]')
                                    submit_button.click()
                                    try:
                                        driver.find_element(By.XPATH, '//*[contains(text(),"Invalid Captcha! Please Enter Correct Captcha.")]')
                                    except:
                                        break
                            except Exception as err:
                                print(err)
                                # logger.error('Getting error in pdf_doc captcha, Error: %s', str(err))
                        except:
                            logger.info('Documents are not downloadable')
                            # continue
                        # nas_path = os.path.join(os.getcwd(), 'downloads', str(tender_id))
                        nas_path = os.path.join(r'\\Digitaldreams\tender auto', tender_id)
                        os.makedirs(nas_path, exist_ok=True)

                        try:
                            try:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="docDownoad"]')
                            except:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="DirectLink_0"]')
                            pdf_doc.click()
                            time.sleep(5)
                            print('Download pdf files')

                            while True:
                                try:
                                    latest_file = get_latest_downloaded_file('pdf')
                                    new_file_path = os.path.join(nas_path, os.path.basename(latest_file))
                                    shutil.move(latest_file, new_file_path)
                                    print('Move pdf files')
                                    break
                                except:
                                    time.sleep(5)
                        except Exception as err:
                            # logger.error('Getting error in pdf download, Error: %s', str(err))
                            new_file_path = nas_path

                        tries = 5
                        while tries > 0:
                            tries -= 1
                            try:
                                try:
                                    zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_8"]')
                                except:
                                    try:
                                        zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_7"]')
                                    except:
                                        zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_6"]')
                                zip_file.click()
                                time.sleep(5)

                                while True:
                                    crdownload_files = glob.glob(os.path.join(download_folder, '*.crdownload'))
                                    if crdownload_files:
                                        time.sleep(5)
                                    else:
                                        try:
                                            latest_file = get_latest_downloaded_file('.zip')
                                            if latest_file.endswith('.zip'):
                                                new_file_path = os.path.join(nas_path, os.path.basename(latest_file))
                                                shutil.move(latest_file, new_file_path)
                                                break
                                        except:
                                            raise Exception("No file found.")
                                break
                            except Exception as err:
                                # logger.error('Getting error in ZIP download, Error: %s', str(err))
                                new_file_path = nas_path
                                time.sleep(5)

                        loc_t_id = tender_id + '_' + loc.replace(" ","")

                        query = f"""INSERT INTO tender.tender_management (local_tender_id, tender_id, customer, name_of_work, submission_date, link,
                        file_location, folder_location, inserted_time, user_id, inserted_user_id, publish_date, verification_1, emd, pbm, location, e_value) 
                        VALUES ('{loc_t_id}','{tender_id}', '{str(cust).replace("'","''")}','{str(work_desp).replace("'","''")}', '{str(sub_date)}', '{link}',
                        '{new_file_path}','{nas_path}', '{time_now}', '{name}', '{name}', '{str(pub_date)}', 'FOR UPDATE', '{str(emd)}',
                        '{str(pbm)}', '{str(loc)}', '{str(e_value)}')  on conflict (local_tender_id) do nothing ;"""
                        logger.info(query)
                        db.execute(query)

                        emd_dict = {
                            "tender_id": str(tender_id),
                            "emd_required": "NO",
                            "emd_form": None,
                            "emd_amount": f'{str(emd)}',
                            "in_favour_of": None,
                            "mail_to_fin": None,
                            "remarks": "EMD Details Not Inserted",
                            "time_stamp": datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
                        }

                        db.insert_dict_into_table("tender.tender_emd", emd_dict)

                        folder_dict = {
                                    "tender_id": tender_id,
                                    "current_time_col": datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
                                    "user_id": name
                                }
                        db.insert_dict_into_table("tender.tender_folder", folder_dict)

                        try:
                            ass_name = 'Farzana'
                            # tat_query = f""" insert into tender.tender_tat (t_id, stage, assign_time, assign_to, ext_col_1) 
                            # values('{tender_id}', 'FOR UPDATE-Open', now(), '{ass_name}', 'BOT'); """
                            # tat_query = f""" INSERT INTO tender.tender_tat (t_id, stage, assign_time, assign_to, ext_col_1)
                            #             SELECT '{tender_id}', 'FOR UPDATE-Open', NOW(), '{ass_name}', 'BOT'
                            #             FROM (SELECT 1) AS dummy
                            #             LEFT JOIN tender.tender_tat tt ON tt.t_id = '{tender_id}' AND tt.stage = 'FOR UPDATE-Open'
                            #             WHERE tt.t_id IS NULL; """
                            check_query_tat = f""" select 1 from tender.tender_tat where t_id = '{tender_id}' ; """
                            check_data_tat = db.get_data_in_list_of_tuple(check_query_tat)
                            if not check_data_tat:
                                tat_query = f""" INSERT INTO tender.tender_tat (t_id, stage, status, assign_time, assign_to, ext_col_1)
                                            VALUES ('{tender_id}', 'FOR UPDATE', 'Open', NOW(), '{ass_name}', 'BOT'); """
                                db.execute(tat_query)
                        except Exception as err:
                            print(err)
                            pass

                        others.delete_folder(download_folder=download_folder)


                    back_btn = driver.find_element(By.XPATH,'//*[@id="DirectLink_11"]')
                    back_btn.click()
                    time.sleep(3)

        try:
            nxt_pg = driver.find_element(By.XPATH, '//*[@id="linkFwd"]')
            nxt_pg.click()
            time.sleep(3)
        except Exception as err:
            # logger.error("Getting error while click on next page button, Error: %s", str(err))
            break

    try:
        driver.close()
    except:
        logger.info('Unable to close the driver')
        pass
    result_df = pd.DataFrame(tender_data)

    # result_df.to_csv(f'CSV Files/all_tender_data_{key_word}.csv')
    result_df.to_csv(os.path.join(os.getcwd(),'CSV Files',f'all_tender_data_{name}_{key_word}.csv'))


def WBtenders_GOV_NICGEP_BOT_main(key_word):
    name = 'WBtenders GOV NICGEP BOT'
    print(f'Starting the bot {name}')
    link = 'https://wbtenders.gov.in/'
    logger.info('='*100)
    logger.info(f'Starting the bot {name}')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://wbtenders.gov.in/nicgep/app?page=FrontEndAdvancedSearch&service=page')
    tender_type = driver.find_element(By.XPATH, '//*[@id="TenderType"]/option[2]')
    tender_type.click()
    tender_search_press = driver.find_element(By.XPATH, '//*[@id="workItemTitle"]')
    tender_search_press.click()
    tender_search_press.send_keys(key_word)
    time.sleep(5)
    while True:
        logger.info('Trying to get the Captcha')
        try:
            while True:
                captcha_element = driver.find_element(By.XPATH, '//*[@id="captchaImage"]')
                c_data = get_captch_text(captcha_element)
                if c_data:
                    time.sleep(20)
                    break
                time.sleep(5)
                ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                ref_btn.click()
            captcha_data = driver.find_element(By.XPATH, '//*[@id="captchaText"]')
            captcha_data.send_keys(c_data)

            submit_button = driver.find_element(By.XPATH, '//*[@id="submit"]')
            submit_button.click()
            time.sleep(2)
            try:
                alert = Alert(driver)
                alert_text = alert.text
                try:
                    alert.accept()
                except:
                    alert.dismiss()
                ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                ref_btn.click()
            except:
                pass
            tender_list = driver.find_element(By.XPATH, '//*[@id="table"]/tbody')
            if tender_list:
                break
        except Exception as err:
            try:
                no_tend = driver.find_element(By.XPATH, '//*[contains(text(), "No Tenders found.")]')
                logger.info('No tenders in portal')
                break
            except:
                pass
            # logger.error('Getting Error while gatting Captcha, Error: %s', str(err))
    tender_data = []
    while True:
        try:
            no_tend = driver.find_element(By.XPATH, '//*[contains(text(), "No Tenders found.")]')
            if no_tend:
                logger.info('No tenders in portal')
                break
        except:
            pass
        tender_list = driver.find_element(By.XPATH, '//*[@id="table"]/tbody')
        all_tender_list = tender_list.text.split('\n')[1:]
        try:
            new_list_1 = [i for i in all_tender_list if "<<" not in i or ">>" not in i or ' ' not in i]
            new_list = []
            for i in new_list_1:
                if i != ' ':
                    new_list.append(i)
        except:
            new_list = all_tender_list
        
        count = -1
        for i in new_list:
            print(i)
            if count == -1:
                xpath_a = '//*[@id="DirectLink_0"]'
            else:
                xpath_a = f'//*[@id="DirectLink_0_{count}"]'

            count += 1
            print(xpath_a)
            if i or i != " ":
                pattern = r"\[(.*?)\]"
                try:
                    match = re.search(pattern, i)
                except:
                    match = None

                try:
                    pattern_1 = r'\[(\w+)\]'
                    matches = re.findall(pattern_1, i)

                    if len(matches) > 1:
                        t_id = matches[1]
                    else:
                        t_id = matches[0]
                except:
                    t_id = None
                print(t_id)
                if t_id:
                    query = f"select tender_id from tender.tender_management where tender_id = '{t_id}';"
                    data = db.get_data_in_list_of_tuple(query)
                if data:
                    logger.info('Tender ID is found in DB, Tender ID %s', str(t_id))
                    continue
                if match:
                    # print('yes')
                    logger.info('Working on Tender ID: %s', str(t_id))
                    extracted_text = match.group(1)
                    time_now = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
                    try:
                        tender = driver.find_element(By.XPATH, xpath_a)
                        tender.click()
                        print('Clicked XPATH')
                    except:
                        try:
                            tender = driver.find_element(By.XPATH, f'//*[contains(text(),"{extracted_text}")]')
                            tender.click()
                        except:
                            print('Unable to enter')
                            remarks = 'Unable to click on tender (maybe same name issue)'
                            manual_insert(t_id, remarks, name, link)
                            # logger.error("Getting error in tender click part for %s", str(t_id))
                            continue
                    time.sleep(3)
                    try:
                        tender_id = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/b').text
                    except:
                        try:
                            tender_id = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[3]/td[2]/b').text
                        except:
                            remarks = 'Unable to click on tender (maybe same name issue)'
                            manual_insert(t_id, remarks, name, link)
                            continue
                    try:
                        try:
                            cust = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/b').text.replace("'", "''")
                        except:
                            cust = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]/b').text.replace("'", "''")
                        try:
                            loc = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[7]/td[2]').text.replace("'", "''")
                        except:
                            loc = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[7]/td[2]').text.replace("'", "''")
                        try:
                            work_desp = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[2]/td[2]/b').text.replace("'", "''")
                        except:
                            work_desp = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[2]/td[2]/b').text.replace("'", "''")
                        try:
                            p_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody/tr[1]/td[2]').text
                        except:
                            p_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[1]/td[2]').text
                        try:
                            s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[20]/td/table/tbody/tr[4]/td[4]').text
                        except:
                            try:
                                s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[4]/td[4]').text
                            except:
                                s_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[23]/td/table/tbody/tr[4]/td[4]').text
                        try:
                            emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                        except:
                            try:
                                emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[12]/td/table/tbody/tr/td/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                            except:
                                emd = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[9]/td/table/tbody/tr/td[2]/table/tbody/tr[2]/td/table/tbody/tr[1]/td[2]').text.replace(',', '')
                        try:
                            pbm_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[8]/td[4]').text
                        except:
                            pbm_date = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[8]/td[4]').text
                        try:
                            e_value = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[17]/td/table/tbody/tr[5]/td[2]').text.replace(",", "")
                        except:
                            e_value = driver.find_element(By.XPATH, '//*[@id="content"]/table/tbody/tr[2]/td/table/tbody/tr/td[2]/table/tbody/tr[4]/td/table[2]/tbody/tr/td/table/tbody/tr[14]/td/table/tbody/tr[5]/td[2]').text.replace(",", "")
                    except:
                        remarks = 'Unable to get the tender data from portal, Please insert manually.'
                        manual_insert(t_id, remarks, name, link)
                        back_btn = driver.find_element(By.XPATH,'//*[@id="DirectLink_11"]')
                        back_btn.click()
                        continue

                    try:
                        pub_date = datetime.datetime.strptime(p_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        pub_date = None
                    try:
                        sub_date = datetime.datetime.strptime(s_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        sub_date = None
                    try:
                        pbm = datetime.datetime.strptime(pbm_date.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    except:
                        pbm = pbm_date
                        if 'NA' in pbm_date:
                            pbm = None

                    if (('camera' in work_desp.lower() and 'DSLR' not in work_desp.upper()) or ('CCTV' in work_desp.upper() and 'DSLR' not in work_desp.upper()) or \
                        ('LAN ' in work_desp.upper() or ' LAN' in work_desp.upper()) or ('network' in work_desp.lower()) or ('surveillance' in work_desp.lower()) or \
                            ('switch' in work_desp.lower()) or ('unmanned aerial vehicle' in work_desp.lower()) or ('UAV' in work_desp.upper()) or ('drone' in work_desp.lower())) \
                            and (' lt ' not in work_desp.lower()) and (' kv ' not in work_desp.lower()) and (' cement ' not in work_desp.lower()) and (' ht ' not in work_desp.lower()):

                        tender_dict = {
                            'tender_id': tender_id,
                            'customer': cust,
                            'location': loc,
                            'name_of_work': work_desp,
                            'publish_date': pub_date,
                            'submission_date': sub_date,
                            'emd': emd,
                            'pbm': pbm,
                            'e_value': e_value,
                            'inserted_time': time_now,
                            'inserted_user_id': name
                        }
                        # logger.info(tender_dict)
                        tender_data.append(tender_dict)
                        others.delete_folder(download_folder=download_folder)

                        try:
                            try:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="docDownoad"]')
                                pdf_doc.click()
                            except:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="DirectLink_0"]')
                                pdf_doc.click()
                            try:
                                while True:
                                    while True:
                                        try:
                                            captcha_element = driver.find_element(By.XPATH, '//*[@id="captchaImage"]')
                                        except:
                                            raise Exception('Captcha Not found')
                                        c_data = get_captch_text(captcha_element)
                                        if c_data:
                                            break
                                        time.sleep(5)
                                        ref_btn = driver.find_element(By.XPATH, '//*[@id="captcha"]')
                                        ref_btn.click()
                                    captcha_data = driver.find_element(By.XPATH, '//*[@id="captchaText"]')
                                    captcha_data.send_keys(c_data)
                                    submit_button = driver.find_element(By.XPATH, '//*[@id="Submit"]')
                                    submit_button.click()
                                    try:
                                        driver.find_element(By.XPATH, '//*[contains(text(),"Invalid Captcha! Please Enter Correct Captcha.")]')
                                    except:
                                        break
                            except Exception as err:
                                print(err)
                                # logger.error('Getting error in pdf_doc captcha, Error: %s', str(err))
                        except:
                            logger.info('Documents are not downloadable')
                            # continue
                        # nas_path = os.path.join(os.getcwd(), 'downloads', str(tender_id))
                        nas_path = os.path.join(r'\\Digitaldreams\tender auto', tender_id)
                        os.makedirs(nas_path, exist_ok=True)

                        try:
                            try:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="docDownoad"]')
                            except:
                                pdf_doc = driver.find_element(By.XPATH, '//*[@id="DirectLink_0"]')
                            pdf_doc.click()
                            time.sleep(5)
                            print('Download pdf files')

                            while True:
                                try:
                                    latest_file = get_latest_downloaded_file('pdf')
                                    new_file_path = os.path.join(nas_path, os.path.basename(latest_file))
                                    shutil.move(latest_file, new_file_path)
                                    print('Move pdf files')
                                    break
                                except:
                                    time.sleep(5)
                        except Exception as err:
                            # logger.error('Getting error in pdf download, Error: %s', str(err))
                            new_file_path = nas_path

                        tries = 5
                        while tries > 0:
                            tries -= 1
                            try:
                                try:
                                    zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_7"]')
                                except:
                                    try:
                                        zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_8"]')
                                    except:
                                        zip_file = driver.find_element(By.XPATH, '//*[@id="DirectLink_6"]')
                                zip_file.click()
                                time.sleep(5)

                                while True:
                                    crdownload_files = glob.glob(os.path.join(download_folder, '*.crdownload'))
                                    if crdownload_files:
                                        time.sleep(5)
                                    else:
                                        try:
                                            latest_file = get_latest_downloaded_file('.zip')
                                            if latest_file.endswith('.zip'):
                                                new_file_path = os.path.join(nas_path, os.path.basename(latest_file))
                                                shutil.move(latest_file, new_file_path)
                                                break
                                        except:
                                            raise Exception("No file found.")
                                break
                            except Exception as err:
                                # logger.error('Getting error in ZIP download, Error: %s', str(err))
                                new_file_path = nas_path
                                time.sleep(5)

                        loc_t_id = tender_id + '_' + loc.replace(" ","")

                        query = f"""INSERT INTO tender.tender_management (local_tender_id, tender_id, customer, name_of_work, submission_date, link,
                        file_location, folder_location, inserted_time, user_id, inserted_user_id, publish_date, verification_1, emd, pbm, location, e_value) 
                        VALUES ('{loc_t_id}','{tender_id}', '{str(cust).replace("'","''")}','{str(work_desp).replace("'","''")}', '{str(sub_date)}', '{link}',
                        '{new_file_path}','{nas_path}', '{time_now}', '{name}', '{name}', '{str(pub_date)}', 'FOR UPDATE', '{str(emd)}',
                        '{str(pbm)}', '{str(loc)}', '{str(e_value)}')  on conflict (local_tender_id) do nothing ;"""
                        logger.info(query)
                        db.execute(query)

                        emd_dict = {
                            "tender_id": str(tender_id),
                            "emd_required": "NO",
                            "emd_form": None,
                            "emd_amount": f'{str(emd)}',
                            "in_favour_of": None,
                            "mail_to_fin": None,
                            "remarks": "EMD Details Not Inserted",
                            "time_stamp": datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
                        }

                        db.insert_dict_into_table("tender.tender_emd", emd_dict)

                        folder_dict = {
                                    "tender_id": tender_id,
                                    "current_time_col": datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S"),
                                    "user_id": name
                                }
                        db.insert_dict_into_table("tender.tender_folder", folder_dict)

                        try:
                            ass_name = 'Farzana'
                            # tat_query = f""" insert into tender.tender_tat (t_id, stage, assign_time, assign_to, ext_col_1) 
                            # values('{tender_id}', 'FOR UPDATE-Open', now(), '{ass_name}', 'BOT'); """
                            # tat_query = f""" INSERT INTO tender.tender_tat (t_id, stage, assign_time, assign_to, ext_col_1)
                            #             SELECT '{tender_id}', 'FOR UPDATE-Open', NOW(), '{ass_name}', 'BOT'
                            #             FROM (SELECT 1) AS dummy
                            #             LEFT JOIN tender.tender_tat tt ON tt.t_id = '{tender_id}' AND tt.stage = 'FOR UPDATE-Open'
                            #             WHERE tt.t_id IS NULL; """
                            check_query_tat = f""" select 1 from tender.tender_tat where t_id = '{tender_id}' ; """
                            check_data_tat = db.get_data_in_list_of_tuple(check_query_tat)
                            if not check_data_tat:
                                tat_query = f""" INSERT INTO tender.tender_tat (t_id, stage, status, assign_time, assign_to, ext_col_1)
                                            VALUES ('{tender_id}', 'FOR UPDATE', 'Open', NOW(), '{ass_name}', 'BOT'); """
                                db.execute(tat_query)
                        except Exception as err:
                            print(err)
                            pass

                        others.delete_folder(download_folder=download_folder)


                    back_btn = driver.find_element(By.XPATH,'//*[@id="DirectLink_11"]')
                    back_btn.click()
                    time.sleep(3)

        try:
            nxt_pg = driver.find_element(By.XPATH, '//*[@id="linkFwd"]')
            nxt_pg.click()
            time.sleep(3)
        except Exception as err:
            # logger.error("Getting error while click on next page button, Error: %s", str(err))
            break

    try:
        driver.close()
    except:
        logger.info('Unable to close the driver')
        pass
    result_df = pd.DataFrame(tender_data)

    # result_df.to_csv(f'CSV Files/all_tender_data_{key_word}.csv')
    result_df.to_csv(os.path.join(os.getcwd(),'CSV Files',f'all_tender_data_{name}_{key_word}.csv'))




