import requests
import db_connect as db
import json
import mail
import schedule
import time

url = "https://api-lb-ext.unolo.com/api/protected/employeeMaster"


def get_emp_unolo():
    payload = {}
    headers = {
    'id': '15657',
    'token': 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpZCI6MTU2NTcsImtleSI6ImZ2ZnYwdnR3IiwidGltZXN0YW1wIjoxNzE4MjU4OTc5OTcxfQ.LD83O6b-k7NzZ-YzboiDX5KwUzS0K4tfHLuodWbiKsw'
    }

    response = requests.request("GET", url, headers=headers, data=payload)
    return json.loads(response.text)


def get_emp_ums():
    query = """select user_id, name, mobile, email from ums.user_details;"""
    data = db.get_row_as_dframe(query)
    return data


def main():
    try:
        unolo_data = get_emp_unolo()
        ums_data = get_emp_ums()
        if not unolo_data or ums_data.empty:
            return print('No data found')
        elif not unolo_data[0]['empPhoneNumber']:
            return print('Not empPhoneNumber found')
        # unolo_dict = {i['empPhoneNumber'].replace('+91', ''): i for i in unolo_data}

        # Dictionary to store unique phone numbers and their corresponding data
        unolo_dict = {}
        phone_count = {}

        # Single pass to build phone_count and unolo_dict
        for i in unolo_data:
            phone_number = i['empPhoneNumber'].replace('+91', '')
            if phone_number in phone_count:
                phone_count[phone_number] += 1
            else:
                phone_count[phone_number] = 1
                unolo_dict[phone_number] = i

        # Remove duplicates from unolo_dict
        unolo_dict = {phone: data for phone, data in unolo_dict.items() if phone_count[phone] == 1}

        # Check for duplicates
        duplicates = {phone for phone, count in phone_count.items() if count > 1}
        if duplicates:
            print("Duplicate phone numbers found and removed:")
            for number in duplicates:
                print(number)
            body = f"""
                    Hi all,
                    There are duplicates numbers are present in Unolo api. 
                    Duplicate Numbers: {duplicates}

                    Thanks,
                    Unolo UMS Mapping Bot
                    """
            mail.send_mail(to_add=['ramit.shreenathgroup.in'], to_cc=[], sub='Duplicate number found for Unolo', body=body)
        else:
            print("No duplicate phone numbers found.")

        for _, row in ums_data.iterrows():
            ums_mobile = row['mobile'].replace('+91', '')
            if ums_mobile in unolo_dict:
                # print(ums_data)
                unolo_json = json.dumps(unolo_dict[ums_mobile])
                query = f""" update ums.user_details set unolo_data = '{unolo_json}' where user_id = '{row['user_id']}' ;"""
                db.execute(query)
                # print(query)
    except Exception as err:
        print(str(err))
        body = f"""
        Hi all,
        There are error in bot. 
        Error: {str(err)}

        Thanks,
        Unolo UMS Mapping Bot
        """
        mail.send_mail(to_add=['ramit.shreenathgroup.in'], to_cc=[], sub='Error in Unolo UMS Mapping Bot', body=body)

# def test():
#     query = "select user_id, name, mobile, email, unolo_data from ums.user_details where user_id = 'U-2' ;"
#     data =  db.get_row_as_dframe(query).to_dict()
#     emp_id = data['unolo_data'][0]['empID']
#     employee_id = data['unolo_data'][0]['employeeID']

#     pass

# def job():
#     main()

# schedule.every().day.at("10:00").do(job)

# while True:
#     schedule.run_pending()
#     time.sleep(1) 

# app_query = "select app_id, app_name, concat(primary_ip,login_url) as urls from ums.app_data ad ;"
# app_data = db.get_row_as_dframe(app_query)

# url = app_data[app_data['app_name'] == 'User Management System'].urls[0]
