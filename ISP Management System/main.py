from flask import Flask, flash, request, render_template, redirect, url_for, send_file, session, make_response
import os
from werkzeug.utils import secure_filename
import paramiko
import db_connect as db
import requests
import logging
from tempfile import NamedTemporaryFile
import requests
import smtplib
from email.mime.text import MIMEText
from functools import wraps
import datetime
import mail
import random
import string
import re
import send_wp



# app = Flask(__name__)
app = Flask(__name__, static_folder='static')

logging.basicConfig(filename='isp.log',
                    format='%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

NAS_HOST = '192.168.0.9'
NAS_PORT = 22
NAS_USERNAME = 'dme'
NAS_PASSWORD = '`1Qs9y]p'
NAS_UPLOAD_FOLDER = '/FTTH/'

app.config['UPLOAD_FOLDER'] = ''

app.secret_key = '1234567890'


class User:
    def __init__(self, identifier):
        self.identifier = identifier


def is_valid_mobile(mobile):
    return re.match(r'^\d{10}$', mobile)


def is_valid_email(email):
    return re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email)


def authenticate(identifier):
    if is_valid_mobile(identifier):
        # Check if the mobile number is already present in the database
        query = f"""SELECT mobile FROM isp.login_details WHERE mobile ilike '%{identifier}%' """
        result = db.get_row_as_dframe(query)
        if not result.empty:
            # Mobile number found in the database
            return User(identifier)
    elif is_valid_email(identifier):
        # Check if the email address is already present in the database
        query = f"""SELECT email FROM isp.login_details WHERE email ilike '%{identifier}%' """
        result = db.get_row_as_dframe(query)
        if not result.empty:
            # Email address found in the database
            return User(identifier)
    return None


def generate_otp():
    digits = string.digits
    return ''.join(random.choice(digits) for i in range(4))


def send_otp_via_email(to_add, otp):
    # Replace this with your existing send_mail function
    subject = 'Your OTP for Login'
    body = f'Your OTP is: {otp}'
    print("Sending OTP via email to:", to_add)
    try:
        mail.send_mail(to_add=to_add, to_cc=[], sub=subject, body=body)
        print('OTP sent successfully via email!')
    except Exception as e:
        print('Error sending OTP via email:', str(e))


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'identifier' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)

    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        new_identifier = request.form['identifier']

        try:
            session.pop('user_name', None)
            session.pop('user_mob_no', None)
            session.pop('user_email', None)

            try:
                for key in session.keys():
                    if not '_flashes' in key:
                        session.pop(key, None)
            except KeyError:
                # Handle the KeyError (e.g., log or take appropriate action)
                pass

            # Set the new identifier in the session
            session['identifier'] = new_identifier
        except:
            pass
        identifier = request.form['identifier']  # This can be either mobile or email
        user = authenticate(identifier)

        try:
            otp = generate_otp()
            session['otp'] = otp
            session['identifier'] = identifier

            otp_status = 'True' if user else 'False'
            session['otp_status'] = 'True' if user else 'False'
            print(otp_status)
            # send_otp_via_email(identifier, otp) if '@' in identifier else send_wp.send_otp_via_wp(identifier, otp)
            return redirect(url_for('verify_otp'))

        except:
            return render_template('login.html', error_message="Invalid mobile number or email address")

    return render_template('login.html', error_message=None)


def nas_upload(path, files):
    current_session = requests.Session()
    current_session.auth = (NAS_USERNAME, NAS_PASSWORD)
    nas_file_paths = []
    with paramiko.SSHClient() as ssh_client:
        ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        ssh_client.connect(NAS_HOST, NAS_PORT, NAS_USERNAME, NAS_PASSWORD)
        
        # Split the provided path into individual folders
        path_components = path.split('/')
        
        # Initialize the base folder
        base_folder = NAS_UPLOAD_FOLDER
        
        try:
            sftp = ssh_client.open_sftp()
            
            # Create the nested folders if they don't exist
            for component in path_components:
                base_folder = os.path.join(base_folder, component)
                try:
                    sftp.mkdir(base_folder, mode=0o755)
                except:
                    pass

            sftp.close()
        except Exception as e:
            return ["Failed to create ISP folder on NAS"]

        for file in files:
            if file:
                filename = secure_filename(file.filename)
                nas_file_path = os.path.join(base_folder, filename)
                with NamedTemporaryFile(delete=False) as tmp_file:
                    file.save(tmp_file.name)
                    try:
                        sftp = ssh_client.open_sftp()
                        sftp.chdir(base_folder)
                        sftp.put(tmp_file.name, filename)
                        sftp.close()
                        nas_file_paths.append(nas_file_path)
                    except Exception as e:
                        logger.error(f"Failed to upload file to NAS: {str(e)}")
                        return ["Failed to upload file to NAS"]

    return nas_file_paths


@app.route('/document_upload', methods=['GET', 'POST'])
@login_required
def document_upload():
    if request.method == 'POST':
        files = request.files.getlist('document')
        # identifier = session.get('identifier')  # Assuming you have the user identifier in the session

        nas_file_paths = nas_upload(session['folder_path'], files)
        # try:
        identifier = session.get('identifier')
        query = f""" select * from isp.user_details ud where ph = '{identifier}' or email = '{identifier}' ; """
        data = db.get_data_in_list_of_tuple(query)
        query_2 = f""" update isp.cust_isp_details set folder_path = '{session['folder_path']}' where cust_id = '{data[0][1]}' """
        print(query_2)
        db.execute(query_2)
        # except:
        #     pass
        return redirect(url_for('dashboard'))

    return render_template('document_upload.html')


@app.route('/resend_otp', methods=['POST'])
def resend_otp():
    identifier = session['identifier']
    otp = generate_otp()
    session['otp'] = otp
    if '@' in identifier:
        send_otp_via_email(identifier, otp)
    else:
        send_wp.send_otp_via_wp(identifier, otp)
    return redirect(url_for('verify_otp'))


# @app.route('/welcome', methods=['GET', 'POST'])
# def welcome():
#     username = session.get('identifier')

#     get_acc_query = f"""select mobile, email, name from isp.login_details  where (mobile ilike '%{username}%' or email ilike '%{username}%') limit 1;"""
#     print('get_acc_query', get_acc_query)
#     data_cont = db.get_data_in_list_of_tuple(get_acc_query)[0]
#     get_acc_id = data_cont[0]
#     session['user_name'] = data_cont[3]
#     session['user_mob_no'] = data_cont[1]
#     session['user_email'] = data_cont[2]

#     return render_template('welcome.html')


@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    check_resp = session.get('otp_status', False)
    otp = session.get('otp')
    if request.method == 'POST':
        identifier = session.get('identifier')
        if 'otp' in session and 'identifier' in session and session['otp'] == request.form.get('otp') and identifier:
            # Clear the OTP and identifier from the session after successful verification
            session.pop('otp')
            # session.pop('identifier')
            user = authenticate(identifier)
            if user:
                return redirect(url_for('dashboard'))
            else:
                return redirect(url_for('registration_form_cont'))
        return render_template('verify_otp.html', error_message="Invalid OTP")
    return render_template('verify_otp.html', otp=otp, error_message=None)


# ========================================================================

@app.route('/dashboard')
@login_required
def dashboard():
    # Access user details from the session
    identifier = session.get('identifier')
    query = f""" select * from isp.user_details ud where ph = '{identifier}' or email = '{identifier}' ; """
    data = db.get_data_in_list_of_tuple(query)
    query_2 = f""" select amount from isp.cust_isp_details cid where cust_id = '{data[0][1]}' ; """
    print(query_2)
    try:
        amount = db.get_data_in_list_of_tuple(query_2)[0][0]
    except:
        amount = '0'
    # cust_id = data[0][1]
    # name = data[0][2]
    # mob_no = data[0][3]
    # email = data[0][4]
    # flat_no = data[0][5]
    # tower_no = data[0][6]
    # apt_no = data[0][7]
    return render_template('dashboard.html', data=data, amount=amount)


def register_user(name, ph, email, flat_no, tower_no, apartment_name, isp, plan):
    logger.info("""Registers a new user with the given information""")
    cust_id_query = 'select cust_id from isp.login_details order by id desc limit 1'
    cust_id_data = db.get_data_in_list_of_tuple(cust_id_query)
    new_cust_id = 'C-1'
    if cust_id_data:
        new_cust_id = 'C-' + str(int(str(new_cust_id).split('-')[1]) + 1)

    insert_cust_login_query = f"""
        INSERT INTO isp.login_details (
            cust_id, name, mobile, email, status
        ) VALUES (
            '{new_cust_id}', '{name}', '{ph}', '{email}', 'ACTIVE'
        );
    """
    insert_cust_query = f"""
        INSERT INTO isp.user_details (
            cust_id, name, ph, email, flat_no, tower_no, apartment_name, isp_id
        ) VALUES (
            '{new_cust_id}', '{name}', '{ph}', '{email}', '{flat_no}', '{tower_no}', '{apartment_name}', '{isp}'
        );
    """

    get_isp_query = f""" select i.name as isp_name, p.name as plan_name, p.amnt, p.net_spped 
                    from isp.isp_details as i join isp.isp_plans as p on i.isp_id = p.isp_id 
                    where i.isp_id = '{isp}' and p.id = '{plan}' ; """
    get_isp_data = db.get_data_in_list_of_tuple(get_isp_query)
    
    try:
        isp_name = str(get_isp_data[0][0])
        plan_name = f'{plan}-{str(get_isp_data[0][1])}'
        amount = float(str(str(get_isp_data[0][2]).split(' pm')[0]))
        net_speed = str(get_isp_data[0][3])
    except:
        isp_name = ''
        plan_name = ''
        amount = ''
        net_speed = ''

    insert_cust_isp_query = f"""
        INSERT INTO isp.cust_isp_details (
            cust_id, cust_name, isp_id, isp_name, plan, amount, network_speed, status, created_time
        ) VALUES (
            '{new_cust_id}', '{name}', '{isp}', '{isp_name}', '{plan_name}', {amount}, '{net_speed}', 'Pending Verification', now()
        );
    """
    # print(insert_cust_login_query)
    # db.execute(insert_cust_isp_query)

    # isp_select = f""" select name from isp.isp_details where  isp_id = '{isp}' ; """
    # isp_select_data = db.get_data_in_list_of_tuple(isp_select)[0][0]
    
    session['new_cust_id'] = new_cust_id
    session['folder_path'] = os.path.join(apartment_name, isp_name, flat_no, new_cust_id)
    session['insert_cust_login_query'] = insert_cust_login_query
    session['insert_cust_query'] = insert_cust_query
    session['insert_cust_isp_query'] = insert_cust_isp_query

    # print(insert_cust_query)
    # logger.info(insert_cust_query)
    # db.execute(insert_cust_query)
    # db.execute(insert_cust_login_query)


@app.route('/registration_form_cont', methods=['GET', 'POST'])
def registration_form_cont():
    identifier = session.get('identifier', None)
    error_msg = session.get('error_msg', None)
    if request.method == 'POST':
        name = request.form['name']
        ph = request.form['ph']
        email = request.form['email']
        # flat_no = request.form['flat_no']
        # tower_no = request.form['tower_no']
        # apartment_name = request.form['apartment_name']
        # isp = request.form['isp']

        # register_user(name, ph, email, flat_no, tower_no, apartment_name, isp)

        # Set user details in the session for future use
        session['user_name'] = name
        session['user_mob_no'] = ph
        session['user_email'] = email
        otp = generate_otp()
        session['otp'] = otp
        session['identifier_2'] = ph if '@' in identifier else email
        check_query = f""" select count(*) from isp.login_details where 
                mobile = '{session['identifier']}' or email = '{session['identifier']}' """
        result = db.get_data_in_list_of_tuple(check_query)
        if int(result[0][0]) > 0:
            error_msg = f"""'{session['identifier_2']}' is already present, 
                        Please login with '{session['identifier_2']}'."""
            return render_template('registration_form_cont.html', identifier=identifier, error_msg=error_msg)
        else:
            send_otp_via_email(session['identifier_2'], otp) if '@' in session['identifier_2'] else send_wp.send_otp_via_wp(session['identifier_2'], otp)
            return redirect(url_for('verify_otp_2'))

    # isp_search_query = f""" select isp_id, name from isp.isp_details; """
    # isp_search_data = db.get_data_in_list_of_tuple(isp_search_query)
    # isp_data = {i:k for i, k in isp_search_data}

    return render_template('registration_form_cont.html', identifier=identifier)


@app.route('/registration_form', methods=['GET', 'POST'])
def registration_form():
    identifier = session.get('identifier', None)
    error_msg = session.get('error_msg', None)
    name = session['user_name']
    ph = session['user_mob_no']
    email = session['user_email']

    if request.method == 'POST':
        # name = request.form['name']
        # ph = request.form['ph']
        # email = request.form['email']
        flat_no = request.form['flat_no']
        tower_no = request.form['tower_no']
        apartment_name = request.form['apartment_name']
        isp = request.form['isp']
        plan = request.form['plans']

        register_user(name, ph, email, flat_no, tower_no, apartment_name, isp, plan)
        db.execute(session['insert_cust_login_query'])
        db.execute(session['insert_cust_query'])
        db.execute(session['insert_cust_isp_query'])
        # return redirect(url_for('dashboard'))
        return redirect(url_for('document_upload'))

    isp_search_query = f""" select isp_id, name from isp.isp_details; """
    isp_search_data = db.get_data_in_list_of_tuple(isp_search_query)
    isp_data = {i:k for i, k in isp_search_data}

    isp_plans_query = f""" select id, isp_id , name, amnt, net_spped , duration , ext_col_1  from isp.isp_plans; """
    isp_plans_data = db.get_row_as_dframe(isp_plans_query)
    isp_plans_data_list = isp_plans_data.to_dict(orient='records')

    # print(isp_plans_data_list)

    return render_template('registration_form.html', identifier=identifier, isp_data=isp_data, isp_plans_data_list=isp_plans_data_list)

# ========================================================================


def mask_email(value):
    atIndex = value.index('@') if '@' in value else None
    if atIndex:
        firstPart = value[:2]
        middlePart = '*' * (atIndex - 2)
        lastPart = value[atIndex - 2:atIndex] + value[atIndex:]
        return firstPart + middlePart + lastPart
    return value


def mask_mobile(value):
    if len(value) <= 4:
        return value  # Do not mask if the mobile number is too short

    maskedPart = '*' * (len(value) - 4)
    lastPart = value[-3:]
    fp = value[0]
    return fp + maskedPart + lastPart


@app.route('/verify_otp_2', methods=['GET', 'POST'])
def verify_otp_2():
    otp = session.get('otp', '')
    if request.method == 'POST':
        mob_no = session['user_mob_no']
        email = session['user_email']
        name = session['user_name']
        # c_id = session['comp_id']
        # query_1 = session['insert_cust_query']
        # query_2 = session['insert_cust_login_query'] 
        # para = session['para']
        otp = request.form['otp']
        if 'otp' in session and 'identifier_2' in session and session['otp'] == otp:
            # Clear the OTP and identifier from the session after successful verification
            session.pop('otp')
            # db.execute(query_1)
            # db.execute(query_2)
            # return render_template('work_form.html', p_h_mob=mob_no, p_h_email=email, quote=request.args.get('quote'))
            return redirect(url_for('registration_form'))
            # return redirect(url_for('thank_you', mobile=mob_no,email=email,c_name=name,comp_id=c_id))
        return render_template('verify_otp_2.html', error_message="Invalid OTP")
    return render_template('verify_otp_2.html', error_message=None)


@app.route('/resend_otp_2', methods=['POST'])
def resend_otp_2():
    identifier = session['identifier_2']
    otp = generate_otp()
    session['otp'] = otp

    if '@' in identifier:
        send_otp_via_email(identifier, otp)
    else:
        send_wp.send_otp_via_wp(identifier, otp)
    return redirect(url_for('verify_otp_2'))


@app.route('/thank_you')
@login_required
def thank_you():
    # otp = request.args.get('otp', None)
    # comp_id = request.args.get('comp_id')
    comp_id = session['com_id']
    # p_name = request.args.get('p_name')
    # c_name = request.args.get('c_name')
    # email = request.args.get('email')
    # mobile = request.args.get('mobile')
    c_name = session['user_name']
    mobile = session['user_mob_no']
    email = session['user_email']
    to_add = [email]
    to_cc = []
    # Compose the email subject and body
    subject = f'Your Complaint ID: {comp_id}'
    body = f'Hello {c_name},\n\nThank you for your submission! \n\nBest regards,\nShreenath Enterprise'
    print(session.keys())
    # Send the email using your existing mail.send_mail function
    # mail.send_mail(to_add=to_add, to_cc=to_cc, sub=subject, body=body)

    # send_wp.send_wp_msg(mobile, msg=body)

    return render_template('thank_you.html', comp_id=comp_id)


@app.route('/terms')
@login_required
def terms():
    return render_template('terms.html')

if __name__ == '__main__':
    # app.run(host='192.168.0.16', port=5026, debug=True)
    app.run(host='192.168.0.16', port=5026, debug=True)


