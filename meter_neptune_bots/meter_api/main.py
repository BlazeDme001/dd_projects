from flask import Flask, jsonify, render_template, request, redirect, url_for, session, flash
import db_connect as db
from functools import wraps
import mail
import requests
import json
import datetime

app = Flask(__name__)
app.secret_key = 'meter7301'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function



def check_service():
    url = "http://103.223.15.47:5023/api/services"
    headers = {"Content-Type": "application/json"}
    data = {
        "username": "Nirwana_API",
        "password": "Qn@62",
        "project": "Nirwana Groups",
        "sub_project": "Nirwana Hights",
        "service": "Meter Reading"
    }
    try:
        response = requests.post(url, json=data, headers=headers, timeout=30)
    except:
        pass
        status, check_time = 'OFF', '0'
        return (status, check_time)

    if response.status_code == 200 and response.json()['services']:
        if response.json()['services'][0].get('status', None):
            status = response.json()['services'][0].get('status', None)
        if response.json()['services'][0].get('check_time', None):
            check_time = response.json()['services'][0].get('check_time')
        return (status, check_time)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        (status, check_time) = check_service()
        username = request.form['username']
        password = request.form['password']

        if username == 'nirwana' and password == 'Nirwana54321%$#@!' and status == 'ON':
            session['user'] = username
            session['name'] = 'Admin'
            session['mobile'] = '6283287351'
            session['email'] = 'dme@shreenathgroup.in'
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid Credentials')
    
    return render_template('login.html')


@app.route('/home', methods=['GET', 'POST'])
@login_required
def home():
    if request.method == 'POST' and 'refresh' in request.form:
        get_all_api_data()  # Fetch latest API data
        session['last_refresh'] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # Store refresh time

    check_query = """ SELECT CA_NAME, CA_ADDRESS, DEVICE_SLNO, EB_OPENING_READING, 
                    DG_OPENING_READING, EB_PV_READING, DG_PV_READING, OPENING_BALANCE, 
                    PV_BAL, STATUS, req_bal, check_time, remarks, inserted_by, inserted_date, 
                    updated_by, updated_date, mobile, email FROM meter_api.meter_user_details; """
    check_data = db.get_data_in_list_of_tuple(check_query)

    ref_query = f""" select updated_time from meter_api.meter_user_details_refresh where id = 1 ; """
    ref_data = db.get_data_in_list_of_tuple(ref_query)
    session['last_refresh'] = ref_data[0][0] if ref_data else 'Not refreshed yet'
    last_refresh = session.get('last_refresh', 'Not refreshed yet')  # Get last refresh time
    return render_template('home.html', data=check_data, last_refresh=last_refresh)


@app.route('/update_contact/<dev_no>', methods=['GET', 'POST'])
@login_required
def update_contact(dev_no):
    if request.method == 'POST':
        name = request.form.get('name')
        mobile = request.form.get('mobile')
        email = request.form.get('email')

        if not mobile or mobile == 'None':
            mobile = ''
        if not email or email == 'None':
            email = ''

        update_query = f""" UPDATE meter_api.meter_user_details SET mobile = '{mobile}', 
        email = '{email}', ca_name = '{name}', updated_by = '{session['user']}', updated_date = NOW()
        WHERE DEVICE_SLNO = '{dev_no}'; """
        db.execute(update_query)
        flash("Contact details updated successfully!", "success")
        return redirect(url_for('home'))

    select_query = f"""SELECT CA_NAME, CA_ADDRESS, DEVICE_SLNO, mobile, email 
                    FROM meter_api.meter_user_details WHERE DEVICE_SLNO = '{dev_no}'; """
    select_data = db.get_data_in_list_of_tuple(select_query)
    
    return render_template('update_contact.html', data=select_data)


@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    session.pop('name', None)
    session.pop('mobile', None)
    session.pop('email', None)
    return redirect(url_for('login'))


def get_master_data():
    url = "https://emsprepaidapi.neptuneenergia.com/service.asmx/liveEmsTransaction"
    payload = json.dumps({
    "TXN_NAME": "MASTERDATA",
    "DATA": "",
    "username": "Admin",
    "password": "NIRWANA#4321#ADMIN",
    "SITECODE": "160"
    })
    headers = {
    'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=120)
    except Exception as er:
        return f'<<|| Error: ||>> :{str(er)}'
    if response.status_code == 200:
        raw_text = response.text

        fixed_json_text = raw_text.split("}{")[0] + "}"
        data = json.loads(fixed_json_text)
        if 'data' in data:
            return data['data']


def get_ems_livedata():
    url = "https://emsprepaidapi.neptuneenergia.com/service.asmx/liveEmsTransaction"
    payload = json.dumps({
    "TXN_NAME": "LIVEDATA",
    "DATA": "",
    "username": "Admin",
    "password": "NIRWANA#4321#ADMIN",
    "SITECODE": "160"
    })
    headers = {
    'Content-Type': 'application/json'
    }
    try:
        response = requests.request("POST", url, headers=headers, data=payload, timeout=120)
    except Exception as er:
        return f'<<|| Error: ||>> :{str(er)}'
    if response.status_code == 200:
        raw_text = response.text
        fixed_json_text = raw_text.split("}{")[0] + "}"
        data = json.loads(fixed_json_text)
        if 'data' in data:
            return data['data']


def get_all_api_data():
    live_data = get_ems_livedata()
    for data in live_data:
        # if data['DEVICE_SLNO'] == '893074':
        #     break
        check_query = f""" SELECT CA_NAME, CA_ADDRESS, DEVICE_SLNO,
            EB_OPENING_READING, DG_OPENING_READING, EB_PV_READING, DG_PV_READING,
            OPENING_BALANCE, PV_BAL, STATUS, req_bal, check_time, remarks,
            inserted_by, inserted_date, updated_by, updated_date 
        FROM meter_api.meter_user_details where DEVICE_SLNO = '{data['DEVICE_SLNO']}' ; """
        check_data = db.get_data_in_list_of_tuple(check_query)
        if not check_data:
            col_names = ['CA_NAME', 'CA_ADDRESS', 'DEVICE_SLNO',
            'EB_OPENING_READING', 'DG_OPENING_READING', 'EB_PV_READING', 'DG_PV_READING',
            'OPENING_BALANCE', 'PV_BAL', 'STATUS', 'check_time',
            'inserted_by', 'inserted_date']

            insert_query = f""" insert into meter_api.meter_user_details 
            ({', '.join(col_names)}) VALUES ('Customer','{data['CA_ADDRESS']}', '{data['DEVICE_SLNO']}',
            '{data['EB_OPENING_READING']}','{data['DG_OPENING_READING']}','{data['EB_PV_READING']}',
            '{data['DG_PV_READING']}','{data['OPENING_BALANCE']}','{data['PV_BAL']}','{data['STATUS']}',
            NOW(),'{session["user"]}', NOW()) ;"""
            db.execute(insert_query)
        else:
            update_list = []
            if check_data[0][0] and check_data[0][0] != data['CA_NAME']:
                update_list.append(f"CA_NAME = '{data['CA_NAME']}'")
            if check_data[0][1] and check_data[0][1] != data['CA_ADDRESS']:
                update_list.append(f"CA_ADDRESS = '{data['CA_ADDRESS']}'")
            if check_data[0][3] and check_data[0][3] != data['EB_OPENING_READING']:
                update_list.append(f"EB_OPENING_READING = '{data['EB_OPENING_READING']}'")
            if check_data[0][4] and check_data[0][4] != data['DG_OPENING_READING']:
                update_list.append(f"DG_OPENING_READING = '{data['DG_OPENING_READING']}'")
            if check_data[0][5] and check_data[0][5] != data['EB_PV_READING']:
                update_list.append(f"EB_PV_READING = '{data['EB_PV_READING']}'")
            if check_data[0][6] and check_data[0][6] != data['DG_PV_READING']:
                update_list.append(f"DG_PV_READING = '{data['DG_PV_READING']}'")
            if check_data[0][7] and check_data[0][7] != data['OPENING_BALANCE']:
                update_list.append(f"OPENING_BALANCE = '{data['OPENING_BALANCE']}'")
            if check_data[0][8] and check_data[0][8] != data['PV_BAL']:
                update_list.append(f"PV_BAL = '{data['PV_BAL']}'")
            if check_data[0][9] and check_data[0][9] != data['STATUS']:
                update_list.append(f"STATUS = '{data['STATUS']}'")
            update_list.append(f"""updated_date = now(), updated_by = '{session["user"]}'""")
            # update_data_list = ' , '.join(update_list)
            update_query = f""" update meter_api.meter_user_details set {' , '.join(update_list)} where DEVICE_SLNO = '{data['DEVICE_SLNO']}' ;"""

            db.execute(update_query)

    ref_query = f""" update meter_api.meter_user_details_refresh set updated_time = now() where id = 1 ; """
    db.execute(ref_query)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5024, debug=True)
