from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import pandas as pd
import os
import time
import glob
import web_interface as wi
import datetime
import db_connect as db

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


def create_dataframe(data_string):
    line_data = data_string.split('\n')
    lines = [av.strip() for av in line_data if 'RA NO' not in av]
    department_details = lines[3] + ' ' + lines[4] + ' '
    if ':' not in lines[5]:
        department_details += lines[5]

    new_av = [item for item in lines if ':' in item]

    new_av.remove('Department Name And Address:')
    new_av.append(department_details)
    data = {}
    for line in new_av:
        key, value = line.split(':', maxsplit=1)
        key = key.strip()
        value = value.strip()
        if key == 'End Date':
            value = datetime.datetime.strptime(value, '%d-%m-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
        if key == 'Start Date':
            value = datetime.datetime.strptime(value, '%d-%m-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
        data[key] = [value]
    df = pd.DataFrame(data)
    return df, data['BID NO']


# def check_in_db(bid_id, end_date):
#     query = f"""select submission_date from tender.tender_management where tender_id = '{bid_id}' ;"""
#     data = db.get_data_in_list_of_tuple(query)
#     if len(data[0]) == 1:
        


def get_latest_downloaded_file():
    list_of_files = glob.glob(os.path.join(download_folder, '*'))
    latest_file = max(list_of_files, key=os.path.getctime)
    return latest_file


def main():
    print('Starting the bot')
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://bidplus.gem.gov.in/all-bids')
    wi.processing_check_wait(driver, xpath='//*[@id="searchBid"]', time=300)
    bid_search = driver.find_element(By.XPATH, '//*[@id="searchBid"]')
    bid_search.click()
    bid_search.send_keys('CCTV')
    bid_search_press = driver.find_element(By.XPATH, '//*[@id="searchBidRA"]')
    bid_search_press.click()
    wi.processing_check_wait(driver, xpath='//*[@id="light-pagination"]/a[6]', time=5)
    total_pages = driver.find_element(By.XPATH, '//*[@id="light-pagination"]/a[6]')
    total_pages.text

    result_df = pd.DataFrame()
    for k in range(int(total_pages.text)):
        print(f'Page {k+1}')
        wi.processing_check_wait(driver, cls='card', time=10)
        bids_page_data = driver.find_elements(By.CLASS_NAME, "card")
        c = 1
        for i in bids_page_data:
            bid_data = i.text.replace("View Corrigendum/Representation\n", "").replace("Bid No.:", "BID NO:")
            c += 1
            bid_df, bid = create_dataframe(bid_data)
            print(str(bid).replace("['", "").replace("']", ""))
            time.sleep(2)
            try:
                a = driver.find_element(By.XPATH,f'//*[@id="bidCard"]/div[{c}]/div[3]/div/div[1]/div[1]/a')
                atb = a.get_attribute('data-content')
                bid_df['new_itm'] = atb
            except:
                bid_df['new_itm'] = bid_df['Items']

            subfolder_path = os.path.join(download_folder, str(bid).replace("['", "").replace("']", "").replace('/','_'))
            os.makedirs(subfolder_path, exist_ok=True)
            bid_no = str(bid).replace("['", "").replace("']", "")
            bid_file = driver.find_element(By.XPATH, f'//*[contains(text(),"{bid_no}")]')
            bid_file.click()
            time.sleep(5)

            latest_file = get_latest_downloaded_file()
            new_file_path = os.path.join(subfolder_path, os.path.basename(latest_file))
            os.rename(latest_file, new_file_path)

            result_df = pd.concat([result_df, bid_df], ignore_index=True)

        next_btn = driver.find_element(By.XPATH, '//*[text()="Next"]')
        next_btn.click()

    result_df.to_csv('csv_files\bid_data.csv')

# if __name__ == '__main__':
#     main()
