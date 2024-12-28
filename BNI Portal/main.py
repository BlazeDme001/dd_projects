import pytesseract
from PIL import Image
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
import re
import shutil


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
    driver = webdriver.Chrome(options=chrome_options)
    driver.get('https://www.bniconnectglobal.com/')
    # time.sleep(10)
    wi.processing_check_wait(driver, '//*[@id="app"]/div/div/div[1]/div/div[1]/section[2]/div[2]/form[1]/div[1]/div/div/div/input', time=30)
    u_name = driver.find_element(By.XPATH, '//*[@id="app"]/div/div/div[1]/div/div[1]/section[2]/div[2]/form[1]/div[1]/div/div/div/input')
    u_name.send_keys('ashish@shreenathgroup.in')
    pass_word = driver.find_element(By.XPATH, '//*[@id="app"]/div/div/div[1]/div/div[1]/section[2]/div[2]/form[1]/div[2]/div/div/div/input')
    pass_word.send_keys('Guasd073@')
    submit_btn = driver.find_element(By.XPATH, '//*[@id="app"]/div/div/div[1]/div/div[1]/section[2]/div[2]/form[1]/div[3]/div/button')
    submit_btn.click()
    # time.sleep(10)
    # c = 0
    # while c < 10:
    #     try:
    #         search_btn = driver.find_element(By.XPATH, '//*[@id="nav"]/a[4]')
    #         search_btn.click()
    #     except:
    #         time.sleep(5)
    #         driver.refresh()
    #         c+=1
    wi.processing_check_wait(driver, '//*[@id="nav"]/a[4]', time=10)
    search_btn = driver.find_element(By.XPATH, '//*[@id="nav"]/a[4]')
    search_btn.click()
    adv_search_btn = driver.find_element(By.XPATH, '//*[@id="advancedSearch"]')
    adv_search_btn.click()

    keyword = driver.find_element(By.XPATH, '//*[@id="memberKeywords"]')
    keyword.send_keys('Security System')
    
    country_select = driver.find_element(By.XPATH, '//*[@id="memberIdCountry"]/option[60]')
    country_select.click()
    
    state_text = driver.find_element(By.XPATH, '//*[@id="memberState"]')
    state_text.send_keys('punjab')
    
    search_members = driver.find_element(By.XPATH, '//*[@id="searchConnections"]')
    search_members.click()
    time.sleep(5)
    mem_list = driver.find_elements(By.XPATH, '//*[@id="datalist"]')
    mem_list_txt = []
    u_det = {}
    n = []
    com = []
    com2 = []
    loc = []
    type = []
    data_list = []
    for i in mem_list:
        print(i.text)
        mem_list_txt.append(i.text)
    for j in range(5):
        print(f'Page {str(j)}')
        driver.find_element(By.XPATH, '//*[@id="datalist_length"]/select/option[4]').click()
        for k in range(150):
            print(k)
            try:
                a_n = driver.find_element(By.XPATH, f'//*[@id="tableBody"]/tr[{k}]/td[1]').text
                a_com = driver.find_element(By.XPATH, f'//*[@id="tableBody"]/tr[{k}]/td[2]').text
                a_com2 = driver.find_element(By.XPATH, f'//*[@id="tableBody"]/tr[{k}]/td[3]').text
                a_loc = driver.find_element(By.XPATH, f'//*[@id="tableBody"]/tr[{k}]/td[4]').text
                a_type = driver.find_element(By.XPATH, f'//*[@id="tableBody"]/tr[{k}]/td[5]').text
                if not 'security systems' in a_type.lower():
                    continue
                    # raise Exception('Not Security System')
                n.append(a_n)
                com.append(a_com)
                com2.append(a_com2)
                loc.append(a_loc)
                type.append(a_type)
                u_det['name'] = a_n
                u_det['com'] = a_com
                u_det['com2'] = a_com2
                u_det['loc'] = a_loc
                u_det['type'] = a_type

                # det = driver.find_element(By.XPATH, '//*[@id="tableBody"]/tr[2]/td[1]/a')
                name=driver.find_element(By.XPATH, f'//*[@id="tableBody"]/tr[{k}]/td[1]/a')
                name.click()
                time.sleep(5)
                driver.switch_to.window(driver.window_handles[1])
                # phone = driver.find_element(By.XPATH, '//*[@id="Profile"]/div/label[8]').text
                # direct_mobile = driver.find_element(By.XPATH, '//*[@id="Profile"]/div/label[9]').text
                try:
                    mobile = driver.find_element(By.XPATH, '//*[contains(text(),"Mobile Number")]/..').text
                    u_det['mobile'] = mobile.split('\n')[1]
                except:
                    u_det['mobile'] = ''
                try:
                    email = driver.find_element(By.XPATH, '//*[contains(text(),"Email")]/..').text
                    u_det['email'] = email.split('\n')[1]
                except:
                    u_det['email'] = ''
                data_list.append(u_det)
                driver.close()
                driver.switch_to.window(driver.window_handles[0])
            except Exception as e:
                print(str(e))
                driver.switch_to.window(driver.window_handles[0])
                pass

        try:
            driver.find_element(By.XPATH, '//*[@id="datalist_next"]').click()
        except:
            pass

        df = pd.DataFrame(data_list)
        df.to_csv('BNI_List.csv')

main()

