from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import os
import time
import datetime
import db_connect as db
import mail

download_folder = os.path.join(os.getcwd(), 'downloads')

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


def main():
    print('Starting the bot')
    driver = webdriver.Chrome(ChromeDriverManager().install(), options=chrome_options)
    driver.get('https://mahatenders.gov.in/')
    query = """select tender_id , submission_date from tender.tender_management tm where inserted_user_id = 'Mahatenders GOV BOT' and (verification_1 <> 'rejected' or verification_1 is null) ; """
    data = db.get_row_as_dframe(query)
    updated_df = pd.DataFrame(columns=['Tender ID', 'Old Submission Date', 'New Submission Date'])
    for _,row in data.iterrows():
        print(row)
        try:
            tender_search_press = driver.find_element(By.XPATH, '//*[@id="SearchDescription"]')
            tender_search_press.click()
            tender_search_press.send_keys(row['tender_id'])
            # tender_search_press.send_keys('2023_UAD_294872_1')
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

                update_query = f"""update tender.tender_management set submission_date = '{sub_date}', done = 'New-Corrigendum', user_id = 'Mahatenders GOV BOT'  where tender_id = '{row['tender_id']}' ;"""
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
    updated_df.to_csv('updated_tender_data.csv')
    if not updated_df.empty:
        to_add = ['ramit.shreenath@gmail.com', 'raman@shreenathgroup.in']
        sub = 'Updated tender submission date in Eprocurebel Nicgep portal'
        body = '''Hello Team,\n
        Attach csv file contains the list of tenders which submission date revised.
        \n\n
        Thanks,
        Mahatenders GOV BOT'''
        mail.send_mail(to_add=to_add, sub=sub, body=body, attach=['updated_tender_data.csv'])



# def job():
#     main()
#     print('BOT executed at 3:00 AM')


# if __name__ == '__main__':
#     schedule.every().day.at('03:00').do(job)

#     while True:
#         schedule.run_pending()
#         time.sleep(1)

while True:
    main()
    time.sleep(14400)