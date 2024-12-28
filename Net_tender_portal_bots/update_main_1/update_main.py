from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import os
import datetime
import db_connect as db
import mail
import web_interface as wbi
import others


download_folder = os.path.join(os.getcwd(), 'downloads')
os.makedirs(name=download_folder, exist_ok=True)

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


def AndamanTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocure.andaman.gov.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}' and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]', time=5)
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
            except:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_2"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        try:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        except:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink_11"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def APTenders_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)

    driver.get('https://arunachaltenders.gov.in/')
    query = """select tender_id , submission_date from tender.tender_management tm where inserted_user_id = 'APTenders NICGEP BOT' and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]', time=5)
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
            except:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_2"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        try:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        except:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink_11"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Assam_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://assamtenders.gov.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_8"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
            except:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_2"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text


            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        try:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        except:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink_11"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Centerl_GOV_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocure.gov.in/eprocure/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver,xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()
            try:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
            except:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def CHDTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://etenders.chd.nic.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]', time=5)
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
            except:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_2"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        try:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        except:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink_11"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Coalindiatenders_NIC_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://coalindiatenders.nic.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
            except:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text


            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Cpcletenders_NIC_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://cpcletenders.nic.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
            except:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text


            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def DadrahaveliTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://dnhtenders.gov.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]', time=5)
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
            except:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_2"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        try:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        except:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink_11"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Defproc_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://defproc.gov.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def DelhiTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://govtprocurement.delhi.gov.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]', time=5)
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
            except:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_2"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        try:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        except:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink_11"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Eproc_Rajasthan_GOV_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eproc.rajasthan.gov.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                try:
                   s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_8"]/td[3]').text
            except:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        try:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        except:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink_11"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Eprocure_Epublish_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocure.gov.in/epublish/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go_0"]')
            go.click()

            s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Eprocurebel_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocurebel.co.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Eprocuregrse_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocurebel.co.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Eprocuregsl_Nic_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocuregsl.nic.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Eprocurehsl_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocurehsl.nic.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Eprocuremdl_Nic_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocuremdl.nic.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Eprocurentpc_Nic_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocurentpc.nic.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()
            try:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
            except:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Etenders_GOV_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://etenders.gov.in/eprocure/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_2"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
            except:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text

            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        try:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        except:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink_11"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])


def Etenders_UP_NIC_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://etender.up.nic.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]', time=5)
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            go.click()

            try:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_2"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
            except:
                try:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_1"]/td[3]').text


            try:
                sub_date = datetime.datetime.strptime(s_date_p.strip(), '%d-%b-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
            except:
                sub_date = None

            if sub_date and sub_date != row['submission_date']:

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', 
                done = 'New-Corrigendum', user_id = '{name}'  where tender_id = '{row['tender_id']}' ;"""
                db.execute(update_query)
                updated_df.loc[len(updated_df)] = [row['tender_id'],  row['submission_date'], sub_date]
        except:
            pass
        try:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink"]')
        except:
            back_btn = driver.find_element(By.XPATH, '//*[@id="DirectLink_11"]')
        back_btn.click()

    try:
        driver.close()
    except:
        pass
    updated_df.to_csv(f'{name}_tender_data.csv')
    others.delete_folder(download_folder)
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = f'Updated tender submission date in {name}'
        body = f'''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        {name}'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=[f'{name}_tender_data.csv'])





