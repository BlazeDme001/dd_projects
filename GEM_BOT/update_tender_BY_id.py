from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
import pandas as pd
import os
import time
import glob
import web_interface as wi
import datetime
import db_connect as db
import schedule
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


def read_df():
    folder_path = os.path.join(os.getcwd(),'csv_files')
    csv_files = glob.glob(folder_path + '/*.csv')
    dfs = []
    for file in csv_files:
        df = pd.read_csv(file)
        dfs.append(df)
    merged_data = pd.concat(dfs, ignore_index=True, verify_integrity=True)
    merged_data['bid_no_1'] = merged_data['BID NO'].str.replace("/", "_")
    merged_data.to_csv('merged_data.csv', index=False)
    return merged_data


def check_db(data):
    tender_ids = data['bid_no_1'].to_list()
    db_data = pd.DataFrame(columns=['tender_id','submission_date'])
    if tender_ids and len(tender_ids) != 1:
        query = f"""SELECT tender_id, submission_date FROM tender.tender_management WHERE
        verification_1 = 'approved' and tender_id ilike 'GEM%' and tender_id not in {tuple(tender_ids)};"""
    #     query = f"""SELECT tender_id, submission_date
    # FROM tender.tender_management
    # where done in ('New-Corrigendum') and submission_date = '2024-08-23 18:00' and
    # tender_id in ('GEM_2024_B_5257331',	'GEM_2024_B_5244275','GEM_2024_B_5243470',	'GEM_2024_B_5229531',	
    # 'GEM_2024_B_5193961',	'GEM_2024_B_5106849',	'GEM_2024_B_4995829',	'GEM_2023_B_4245256',	'GEM_2023_B_4227442',	
    # 'GEM_2023_B_4224053',	'GEM_2023_B_4209216',	'GEM_2023_B_4209177',	'GEM_2023_B_4208256',	'GEM_2023_B_4204683',	
    # 'GEM_2023_B_4195784',	'GEM_2023_B_4194900',	'GEM_2023_B_4189306',	'GEM_2023_B_4188209',	'GEM_2023_B_4183654',	
    # 'GEM_2023_B_4182278',	'GEM_2023_B_4181522',	'GEM_2023_B_4181075',	'GEM_2023_B_4179617',	'GEM_2023_B_4179584',	
    # 'GEM_2023_B_4176770',	'GEM_2023_B_4175412',	'GEM_2023_B_4170486',	'GEM_2023_B_4169665',	'GEM_2023_B_4167886',	
    # 'GEM_2023_B_4164934',	'GEM_2023_B_4163783',	'GEM_2023_B_4161398',	'GEM_2023_B_4160612',	'GEM_2023_B_4159342',	
    # 'GEM_2023_B_4152671',	'GEM_2023_B_4149839',	'GEM_2023_B_4148657',	'GEM_2023_B_4147105',	'GEM_2023_B_4141219',	
    # 'GEM_2023_B_4136490',	'GEM_2023_B_4133441',	'GEM_2023_B_4128374',	'GEM_2023_B_4127489',	'GEM_2023_B_4125036',	
    # 'GEM_2023_B_4117893',	'GEM_2023_B_4116759',	'GEM_2023_B_4110711',	'GEM_2023_B_4107404',	'GEM_2023_B_4101464',	
    # 'GEM_2023_B_4095625',	'GEM_2023_B_4084082',	'GEM_2023_B_4081963',	'GEM_2023_B_4080901',	'GEM_2023_B_4080359',	
    # 'GEM_2023_B_4077417',	'GEM_2023_B_4069839',	'GEM_2023_B_4051053',	'GEM_2023_B_4046181',	'GEM_2023_B_4036647',	
    # 'GEM_2023_B_4023555',	'GEM_2023_B_4022853',	'GEM_2023_B_4020955',	'GEM_2023_B_4011305',	'GEM_2023_B_3992211',	
    # 'GEM_2023_B_3990626',	'GEM_2023_B_3984926',	'GEM_2023_B_3983758',	'GEM_2023_B_3982803',	'GEM_2023_B_3977941',	
    # 'GEM_2023_B_3974957',	'GEM_2023_B_3972427',	'GEM_2023_B_3967865',	'GEM_2023_B_3967677',	'GEM_2023_B_3965924',	
    # 'GEM_2023_B_3963526',	'GEM_2023_B_3961471',	'GEM_2023_B_3961445',	'GEM_2023_B_3961089',	'GEM_2023_B_3960809',	
    # 'GEM_2023_B_3960650',	'GEM_2023_B_3960321',	'GEM_2023_B_3955569',	'GEM_2023_B_3955475',	'GEM_2023_B_3954330',	
    # 'GEM_2023_B_3952476',	'GEM_2023_B_3948265',	'GEM_2023_B_3947774',	'GEM_2023_B_3947697',	'GEM_2023_B_3947163',	
    # 'GEM_2023_B_3942291',	'GEM_2023_B_3941532',	'GEM_2023_B_3938546',	'GEM_2023_B_3933861',	'GEM_2023_B_3931874',	
    # 'GEM_2023_B_3931309',	'GEM_2023_B_3926717',	'GEM_2023_B_3925297',	'GEM_2023_B_3925015',	'GEM_2023_B_3923016',	
    # 'GEM_2023_B_3921877',	'GEM_2023_B_3921787',	'GEM_2023_B_3921542',	'GEM_2023_B_3921370',	'GEM_2023_B_3921311',	
    # 'GEM_2023_B_3920428',	'GEM_2023_B_3913974',	'GEM_2023_B_3913298',	'GEM_2023_B_3913104',	'GEM_2023_B_3912593',	
    # 'GEM_2023_B_3906993',	'GEM_2023_B_3906751',	'GEM_2023_B_3902521',	'GEM_2023_B_3898835',	'GEM_2023_B_3898045',	
    # 'GEM_2023_B_3896329',	'GEM_2023_B_3895256',	'GEM_2023_B_3894476',	'GEM_2023_B_3893871',	'GEM_2023_B_3893787',	
    # 'GEM_2023_B_3893508',	'GEM_2023_B_3892912',	'GEM_2023_B_3892595',	'GEM_2023_B_3891841',	'GEM_2023_B_3890636',	
    # 'GEM_2023_B_3890572',	'GEM_2023_B_3889767',	'GEM_2023_B_3888295',	'GEM_2023_B_3888119',	'GEM_2023_B_3887624',	
    # 'GEM_2023_B_3887326',	'GEM_2023_B_3886106',	'GEM_2023_B_3885409',	'GEM_2023_B_3885304',	'GEM_2023_B_3885241',	
    # 'GEM_2023_B_3884273',	'GEM_2023_B_3883562',	'GEM_2023_B_3882834',	'GEM_2023_B_3881073',	'GEM_2023_B_3879404',	
    # 'GEM_2023_B_3878869',	'GEM_2023_B_3878864',	'GEM_2023_B_3878211',	'GEM_2023_B_3876784',	'GEM_2023_B_3875830',	
    # 'GEM_2023_B_3875195',	'GEM_2023_B_3874389',	'GEM_2023_B_3873032',	'GEM_2023_B_3870919',	'GEM_2023_B_3870831',	
    # 'GEM_2023_B_3870510',	'GEM_2023_B_3870133',	'GEM_2023_B_3869982',	'GEM_2023_B_3869155',	'GEM_2023_B_3869130',	
    # 'GEM_2023_B_3868084',	'GEM_2023_B_3867496',	'GEM_2023_B_3867237',	'GEM_2023_B_3866851',	'GEM_2023_B_3866735',	
    # 'GEM_2023_B_3865956',	'GEM_2023_B_3865793',	'GEM_2023_B_3865669',	'GEM_2023_B_3865167',	'GEM_2023_B_3865096',	
    # 'GEM_2023_B_3864460',	'GEM_2023_B_3863973',	'GEM_2023_B_3863082',	'GEM_2023_B_3862735',	'GEM_2023_B_3862127',	
    # 'GEM_2023_B_3861918',	'GEM_2023_B_3861755',	'GEM_2023_B_3861228',	'GEM_2023_B_3860063',	'GEM_2023_B_3859594',	
    # 'GEM_2023_B_3859185',	'GEM_2023_B_3858956',	'GEM_2023_B_3858273',	'GEM_2023_B_3856614',	'GEM_2023_B_3856194',	
    # 'GEM_2023_B_3856143',	'GEM_2023_B_3856027',	'GEM_2023_B_3855440',	'GEM_2023_B_3854553',	'GEM_2023_B_3854087',	
    # 'GEM_2023_B_3853484',	'GEM_2023_B_3853263',	'GEM_2023_B_3852963',	'GEM_2023_B_3852521',	'GEM_2023_B_3846793',	
    # 'GEM_2023_B_3844386',	'GEM_2023_B_3843882',	'GEM_2023_B_3843781',	'GEM_2023_B_3843607',	'GEM_2023_B_3843544',	
    # 'GEM_2023_B_3842982',	'GEM_2023_B_3840548',	'GEM_2023_B_3837754',	'GEM_2023_B_3836869',	'GEM_2023_B_3836709',	
    # 'GEM_2023_B_3836643',	'GEM_2023_B_3834978',	'GEM_2023_B_3833002',	'GEM_2023_B_3830270',	'GEM_2023_B_3829601',	
    # 'GEM_2023_B_3828800',	'GEM_2023_B_3828605',	'GEM_2023_B_3828416',	'GEM_2023_B_3827594',	'GEM_2023_B_3825465',	
    # 'GEM_2023_B_3823257',	'GEM_2023_B_3822656',	'GEM_2023_B_3819159',	'GEM_2023_B_3818697',	'GEM_2023_B_3818179',
    # 'GEM_2023_B_3814862',	'GEM_2023_B_3814108',	'GEM_2023_B_3813919',	'GEM_2023_B_3812984',	'GEM_2023_B_3808648',
    # 'GEM_2023_B_3808085',	'GEM_2023_B_3807947',	'GEM_2023_B_3807910',	'GEM_2023_B_3807625',	'GEM_2023_B_3802091',	
    # 'GEM_2023_B_3801967',	'GEM_2023_B_3801394',	'GEM_2023_B_3801025',	'GEM_2023_B_3800638',	'GEM_2023_B_3797330',	
    # 'GEM_2023_B_3796352',	'GEM_2023_B_3796072',	'GEM_2023_B_3796005',	'GEM_2023_B_3795100',	'GEM_2023_B_3794075',	
    # 'GEM_2023_B_3793017',	'GEM_2023_B_3790057',	'GEM_2023_B_3788659',	'GEM_2023_B_3786916',	'GEM_2023_B_3786876',	
    # 'GEM_2023_B_3780562',	'GEM_2023_B_3772354',	'GEM_2023_B_3763507',	'GEM_2023_B_3761669',	'GEM_2023_B_3758254',	
    # 'GEM_2023_B_3756189',	'GEM_2023_B_3754242',	'GEM_2023_B_3751414',	'GEM_2023_B_3747643',	'GEM_2023_B_3740182',	
    # 'GEM_2023_B_3738824',	'GEM_2023_B_3733486',	'GEM_2023_B_3725916',	'GEM_2023_B_3721717',	'GEM_2023_B_3707634',	
    # 'GEM_2023_B_3686003',	'GEM_2023_B_3673399',	'GEM_2023_B_3672691',	'GEM_2023_B_3669824',	'GEM_2023_B_3658355',	
    # 'GEM_2023_B_3656759',	'GEM_2023_B_3646835',	'GEM_2023_B_3630925',	'GEM_2023_B_3586651',	'GEM_2023_B_3538005',	
    # 'GEM_2023_B_3447500',	'GEM_2023_B_3371724',	'GEM_2023_B_3350486',	'GEM_2023_B_3275973',	'GEM_2022_B_2840678',	
    # 'GEM_2022_B_2727144');"""
        db_data = db.get_row_as_dframe(query)
    db_dict = db_data.to_dict('records')
    return db_dict


def main():
    try:
        tender_dict = {}
        data = read_df()
        to_check = check_db(data)
        driver = webdriver.Chrome(options=chrome_options)
        driver.get('https://bidplus.gem.gov.in/all-bids')
        wi.processing_check_wait(driver, xpath='//*[@id="searchBid"]', time=300)
        for tender in to_check:
            print(tender)
            # if '2023' in tender['submission_date']:
            #     break
            try:
                bid_search = driver.find_element(By.XPATH, '//*[@id="searchBid"]')
                bid_search.click()
                bid_search.clear()
                bid_search.send_keys(tender['tender_id'].replace('_','/'))
                # bid_search.send_keys('GEM_2024_B_5197497'.replace('_','/'))
                bid_search_press = driver.find_element(By.XPATH, '//*[@id="searchBidRA"]')
                bid_search_press.click()
                wi.processing_check_wait(driver, xpath='//*[@id="light-pagination"]/a[6]', time=5)
                try:
                    no_tender = None
                    try:
                        end_dt = driver.find_element(By.XPATH, f'//*[@id="bidCard"]/div[2]/div[3]/div/div[3]/div[2]/span').text
                    except:
                        end_dt = driver.find_element(By.XPATH, f'//*[@id="bidCard"]/div[5]/div[3]/div[1]/div[3]/div[2]/span').text
                except:
                    end_dt = None
                    try:
                        no_tender = driver.find_element(By.XPATH,'//div[text()="No data found"]').text
                        continue
                    except:
                        no_tender = None
                    if not no_tender:
                        raise Exception(f"Unable to locate End date for {tender['tender_id']}")
                    # elif no_tender:
                    #     continue

                if end_dt:
                    formatted_end_dt = datetime.datetime.strptime(end_dt, '%d-%m-%Y %I:%M %p').strftime('%Y-%m-%d %H:%M')
                    if tender['submission_date'] != formatted_end_dt:
                        query = f"""update tender.tender_management set submission_date = '{formatted_end_dt}',
                        done = 'New-Corrigendum', user_id = 'GEM BOT' where tender_id = '{tender['tender_id']}' ;"""
                        db.execute(query)
                        tender_dict[tender['tender_id']] = formatted_end_dt
                # elif not end_dt and no_tender:
                #     print('Yes')
                #     query = f"""update tender.tender_management set done = 'Not Submitted', 
                #     user_id = 'GEM BOT 1' where tender_id = '{tender['tender_id']}' ;"""
                #     db.execute(query)


            except Exception as err:
                sub='Error in Gem Portal'
                to_add=['ramit.shreenath@gmail.com']
                to_cc=[]
                body=f'''Hello Team,\n\nBelow Error found in Portal.\nError: {str(err)}\n\n\nThanks,\nGEM BOT'''
                mail.send_mail(to_add=to_add, to_cc=to_cc, sub=sub, body=body)
        to_add = ['ramit.shreenath@gmail.com']
        to_cc = []
        sub = 'Submission date Updated'
        body = f"""Hello Team,\n\nBelow is the dict of tenders, which have updated submission date,\n\n{tender_dict}\n\nThanks,GEM BOT"""
        mail.send_mail(to_add, to_cc, sub, body)
    except Exception as error:
        print(str(error))
    try:
        driver.close()
    except:
        pass


def job():
    try:
        print('Bot Started')
        main()
    except Exception as e:
        print(str(e))
        pass
    print('BOT executed at 9:30 PM')


if __name__ == '__main__':
    schedule.every().day.at('21:30').do(job)


    while True:
        schedule.run_pending()
        time.sleep(1)


