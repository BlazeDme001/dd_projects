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
os.makedirs(download_folder, exist_ok=True)

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


def GoaTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eprocure.goa.gov.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            try:
                wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]', time=5)
                tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
                tender_search_press.click()
                tender_search_press.send_keys(row['tender_id'])
                go = driver.find_element(By.XPATH, '//*[@id="Go"]')
                go.click()

                try:
                    try:
                        s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
                    except:
                        s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
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
        except Exception as err:
            # sub = 'Portal Error'
            # mail.send_mail()
            pass
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


def HPtenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://hptenders.gov.in/')
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


def HRYtenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://etenders.hry.nic.in/')
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
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
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


def Iocletenders_NIC_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://iocletenders.nic.in/nicgep/app')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        # if row['tender_id']=='2024_WRRAJ_178353_1':
        #     break
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]')
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            go = driver.find_element(By.XPATH, '//*[@id="Go"]')
            driver.execute_script("window.scrollBy(0, 1000);")
            go.click()

            driver.execute_script("window.scrollBy(0, 500);")
            try:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_15"]/td[4]').text
            except:
                s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_14"]/td[3]').text

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


def J_KTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://jktenders.gov.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]', time=15)
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


def JKDTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://jharkhandtenders.gov.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver,xpath='//*[@id="SearchDescription"]', time=5)
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


def KeralaTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://etenders.kerala.gov.in/')
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
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_13"]/td[3]').text
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


def LEHTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://tenders.ladakh.gov.in/')
    query = f"""select tender_id , submission_date from tender.tender_management tm where inserted_user_id = '{name}'
    and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            wbi.processing_check_wait(driver=driver, xpath='//*[@id="SearchDescription"]', time=60)
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


def LKDPTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://tendersutl.gov.in/')
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


def Mahatenders_GOV_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://mahatenders.gov.in/')
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


def ManipurTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://manipurtenders.gov.in/')
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


def MeghTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://meghalayatenders.gov.in/')
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


def MizoramTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://mizoramtenders.gov.in/')
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


def Mptenders_GOV_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://mptenders.gov.in/')
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


def NagalandTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://nagalandtenders.gov.in/')
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


def Pmgsytenders_GOV_Nicgep_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://pmgsytenders.gov.in/nicgep/app')
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


def PuducherryTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://pudutenders.gov.in/')
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
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal_0"]/td[3]').text
                except:
                    s_date_p = driver.find_element(By.XPATH, '//*[@id="informal"]/td[3]').text
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


def PBTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://eproc.punjab.gov.in/')
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


def SikkimTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://sikkimtender.gov.in/')
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


def Tendersodisha_GOV_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://tendersodisha.gov.in/nicgep/app')
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


def Tntenders_GOV_NIC_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://tntenders.gov.in/')
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


def TripuraTenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://tripuratenders.gov.in/')
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


def UKtenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://uktenders.gov.in/')
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


def WBtenders_GOV_NICGEP_BOT_main(name):
    print('Starting the bot')
    # driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://wbtenders.gov.in/')
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




