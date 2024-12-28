import requests
import mail
import send_wp as wp
import time


tender_url = "http://103.223.15.56:5010/login"
crm_url = "http://103.223.15.56:5020/login"
chd_url = "http://103.223.15.56:5021/login"
cms_url = "http://103.223.15.56:5022/login"
tms_url = "http://103.223.15.56:5023/login"
ums_url = "http://103.223.15.56:5030/login"



urls = [tender_url, crm_url, chd_url, cms_url, tms_url, ums_url]


def check_url(url):
    payload = {}
    headers = {}
    try:
        time.sleep(2)
        response = requests.request("GET", url, headers=headers, data=payload, timeout=120)
        time.sleep(3)
        if response.status_code == 200:
            return True
        return False
    except:
        return False

def main():
    working = []
    not_working = []
    for url in urls:
        if check_url(url):
            working.append(url)
        else:
            not_working.append(url)
    if not_working:
        print(f"The following URLs are not working: {not_working}")
        to_add = ['ramit.shreenath@gmail.com']
        to_cc = []
        sub = 'URLs are not working'
        body = f"Hi Team,\n\nThe following urls are not working:\n\n{not_working}\n\nPlease take action. Bot will check after 1 Hour.\n\nThanks,\nURL notify bot"
        mail.send_mail(to_add=to_add, to_cc=to_cc, sub=sub, body=body)
        wp.send_msg_in_group(group_id='120363312007762707@g.us', msg=body)
        return False
    return True


while True:
    check = main()
    if not check:
        print('Portals are not working, will check them after 1 hr')
        time.sleep(3600)
    else:
        print('Portals are working fine, will check them after 5 min')
        time.sleep(300)
    