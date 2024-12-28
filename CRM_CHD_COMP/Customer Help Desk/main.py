from flask import Flask, request, render_template, redirect, url_for, send_file, session, make_response
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


app = Flask(__name__)

logging.basicConfig(filename='customer_data.log',
                    format='%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

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
        query = f"""SELECT cont_phone FROM CRM.contact_master WHERE cont_phone ilike '%{identifier}%' """
        result = db.get_row_as_dframe(query)
        if not result.empty:
            # Mobile number found in the database
            return User(identifier)
    elif is_valid_email(identifier):
        # Check if the email address is already present in the database
        query = f"""SELECT cont_email FROM CRM.contact_master WHERE cont_email ilike '%{identifier}%' """
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
    
    try:
        mail.send_mail(to_add=to_add, to_cc=[], sub=subject, body=body)  # Use your existing send_mail function here
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
        identifier = request.form['identifier']  # This can be either mobile or email
        user = authenticate(identifier)
        if user:
            # User found, generate and send OTP
            otp = generate_otp()
            session['otp'] = otp
            session['identifier'] = identifier
            # query = f"""select cont_phone, cont_email from CRM.contact_master cm where cont_phone ilike '%{identifier}%' or cont_email ilike '%{identifier}%' ; """
            # data = db.get_data_in_list_of_tuple(query)
            if '@' in identifier:
                send_otp_via_email(identifier, otp)
            else:
                send_wp.send_otp_via_wp(identifier, otp)
            return redirect(url_for('verify_otp'))
        else:
            return render_template('login.html', error_message="Invalid mobile number or email address")

    return render_template('login.html', error_message=None)

@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():
    if request.method == 'POST':
        identifier = session['identifier']  # This can be either mobile or email
        otp = request.form['otp']
        if 'otp' in session and 'identifier' in session and session['otp'] == otp and session['identifier'] == identifier:
            # Clear the OTP and identifier from the session after successful verification
            session.pop('otp')
            # session.pop('identifier')
            return redirect(url_for('user_form'))
        else:
            return render_template('verify_otp.html', error_message="Invalid OTP")

    return render_template('verify_otp.html', error_message=None)

@app.route('/user_form', methods=['GET', 'POST'])
@login_required
def user_form():
    username = session.get('identifier')

    get_acc_query = f"""select acc_id from crm.contact_master cm  where (cont_phone ilike '%{username}%' or cont_email ilike '%{username}%') limit 1;"""
    get_acc_id = db.get_data_in_list_of_tuple(get_acc_query)[0][0]

    if request.method == 'POST':
        # Process the form data here
        # customer_id = session['username']
        product = request.form['product_name']
        product_id = product.split('-', maxsplit=1)[0]
        query_complaint = request.form['query_complaint']

        ex_work_id = ""
        ex_work_price = ""
        ex_work = request.form.get('selected_work')
        if ex_work:
            ex_work_id = ex_work.split('-', maxsplit=1)[0]
            ex_work_price = ex_work.split('-', maxsplit=1)[1]

        # check_query = f"""select * from chd.cust_product_table where (mobile_no ilike '%{username}%' or email_id ilike '%{username}%') and p_id = '{product_id.strip()}' ;"""
        check_query = f"""select * from chd.cust_product_table where c_id = '{get_acc_id}' and p_id = '{product_id.strip()}' ;"""
        check_data = db.get_data_in_list_of_tuple(check_query)
        if not check_data:
            return 'Wrong query'
        c_id = check_data[0][1]
        product_name = check_data[0][10]
        werranty = check_data[0][15]
        # amc = check_data[0][18]
        amc = 'NO' if check_data[0][18] in (None, 'none', 'NO') else 'YES'
        mobile = check_data[0][3]
        email = check_data[0][4]
        c_name = check_data[0][2]
        otp = generate_otp()
        comp_status = 'OPEN'
        is_reopen = 'NO'
        reopen_times = '0'
        created_date = datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
        check_comp = f"""select comp_id from chd.query_table order by id desc limit 1 """
        print(check_comp)
        check_comp_data = db.get_data_in_list_of_tuple(check_comp)
        print(check_comp_data)
        old_comp_id = 'COMP00001'
        if check_comp_data:
            old_comp_id = check_comp_data[0][0] if check_comp_data[0] else 'COMP00001'

        numaric_part = int(old_comp_id[4:])
        new_numaric_part = numaric_part+1
        new_comp_id = old_comp_id[:4] + f'{new_numaric_part:05}'

        insert_query = f"""insert into chd.query_table (comp_id, otp, c_id, c_name, mobile_no , email_id , p_id , p_name ,in_warranty , in_amc , complaint, complaint_status , is_reopen , reopen_times , created_date, ex_work_id, ex_work_price) 
        values ('{new_comp_id}', {int(otp)}, '{c_id}', '{c_name}', '{mobile}', '{email}', '{product_id}', '{product_name}', '{werranty}', '{amc}', '{query_complaint}', '{comp_status}', '{is_reopen}', '{reopen_times}', '{created_date}', '{ex_work_id}', '{ex_work_price}') on conflict do nothing;"""
        logger.info(insert_query)
        db.execute(insert_query)
        return redirect(url_for('thank_you', p_name=product_name, comp_id=new_comp_id, c_name=c_name, email=email, mobile=mobile))

    # query = f"""select * from chd.cust_product_table where (mobile_no ilike '%{username}%' or email_id ilike '%{username}%') order by id desc; """
    query = f"""select * from chd.cust_product_table where c_id = '{get_acc_id}' order by id desc; """
    data = db.get_data_in_list_of_tuple(query)
    ex_work_query = """select * from chd.ex_product_list;"""
    ex_work_data = db.get_data_in_list_of_tuple(ex_work_query)
    if data:
        product_names = []
        for item in data:
            p_id = item[9]
            p_name = item[10]
            warranty = '(Not in warranty)'
            warranty_e_date = datetime.datetime.strptime(item[14], "%Y-%m-%d") if item[14] else None
            amc_e_date = datetime.datetime.strptime(item[17], "%Y-%m-%d") if item[17] else None
            current_date = datetime.datetime.now()
            if warranty_e_date and warranty_e_date >= current_date:
                warranty = '(In warranty)'
            if amc_e_date and amc_e_date >= current_date:
                warranty = '(In warranty)'
            product_names.append(f'{p_id} - {p_name} - {warranty}')
        c_name = data[0][2]
        c_id = data[0][1]
        return render_template('user_form.html', products=product_names, c_id=c_id, c_name=c_name, ex_work=ex_work_data)
    return 'No Products are listed to you'


@app.route('/thank_you')
@login_required
def thank_you():
    # otp = request.args.get('otp', None)
    comp_id = request.args.get('comp_id')
    p_name = request.args.get('p_name')
    c_name = request.args.get('c_name')
    email = request.args.get('email')
    mobile = request.args.get('mobile')
    to_add = [email]
    to_cc = []
    # Compose the email subject and body
    subject = f'Your Complaint ID: {comp_id}'
    body = f'Hello {c_name},\n\nThank you for your submission!\nYour Complaint ID: {comp_id}\nOne of our executive will address your query shortly. \n\nBest regards,\nShreenath Enterprise'

    # Send the email using your existing mail.send_mail function
    mail.send_mail(to_add=to_add, to_cc=to_cc, sub=subject, body=body)

    send_wp.send_wp_msg(mobile, msg=body)

    return render_template('thank_you.html', comp_id=comp_id)


if __name__ == '__main__':
    app.run(host='192.168.0.16', port=5021, debug=True)


