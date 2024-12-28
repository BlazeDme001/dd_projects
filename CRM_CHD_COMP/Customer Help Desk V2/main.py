from flask import Flask,flash, request, render_template, redirect, url_for, send_file, session, make_response
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
        query = f"""SELECT cont_phone FROM CRM.contact_master WHERE cont_phone = '{identifier}' """
        result = db.get_row_as_dframe(query)
        if not result.empty:
            # Mobile number found in the database
            return User(identifier)
    elif is_valid_email(identifier):
        # Check if the email address is already present in the database
        query = f"""SELECT cont_email FROM CRM.contact_master WHERE cont_email = '{identifier}' """
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
        new_identifier = request.form['identifier']

        try:# Clear any existing session data
            session.pop('user_name', None)
            session.pop('user_mob_no', None)
            session.pop('user_email', None)
            session.pop('user_is_in_warranty', None)
            session.pop('user_location', None)
            session.pop('user_work_type', None)
            session.pop('user_remarks', None)

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
            send_otp_via_email(identifier, otp) if '@' in identifier else send_wp.send_otp_via_wp(identifier, otp)
            # get_acc_query = f"""select acc_id, cont_phone, cont_email, cont_name from crm.contact_master cm  where (cont_phone ilike '%{identifier}%' or cont_email ilike '%{identifier}%') limit 1;"""
            # data = db.get_data_in_list_of_tuple(get_acc_query)
            # if data:
            return redirect(url_for('verify_otp'))
            # return redirect(url_for('verify_otp_2'))

        except:
            return render_template('login.html', error_message="Invalid mobile number or email address")

    return render_template('login.html', error_message=None)


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

@app.route('/welcome', methods=['GET','POST'])
def welcome():
    username = session.get('identifier')

    get_acc_query = f"""select acc_id, cont_phone, cont_email, cont_name from crm.contact_master cm  where (cont_phone = '{username}' or cont_email = '{username}') limit 1;"""
    print('get_acc_query', get_acc_query)
    data_cont = db.get_data_in_list_of_tuple(get_acc_query)[0]
    get_acc_id = data_cont[0]
    session['user_name'] = data_cont[3]
    session['user_mob_no'] = data_cont[1]
    session['user_email'] = data_cont[2]

    return render_template('welcome.html')


@app.route('/verify_otp', methods=['GET', 'POST'])
def verify_otp():

    check_resp = session['otp_status']
    otp = session['otp']

    if request.method == 'POST':
        identifier = session['identifier']
        check = True if check_resp in ('True', True) else False
        otp = request.form['otp']
        if 'otp' in session and 'identifier' in session and session['otp'] == otp and session['identifier'] == identifier:
            session.pop('otp')
            if check:
                # return redirect(url_for('user_form'))
                return redirect(url_for('welcome'))

            # return redirect(url_for('work_form'))
            # return redirect(url_for('welcome'))
            return redirect(url_for('add_cont'))
        else:
            return render_template('verify_otp.html', error_message="Invalid OTP")

    return render_template('verify_otp.html', otp=otp, error_message=None)


@app.route('/add_cont', methods=['GET', 'POST'])
@login_required
def add_cont():
    p_holder_mob =  session['identifier'] if not '@' in session['identifier'] else 'Enter Your Mobile'
    p_holder_email = session['identifier'] if '@' in session['identifier'] else 'Enter Your E-Mail'
    if request.method == 'POST':

        otp = generate_otp()
        name = request.form['name']
        mob_no = request.form['mob_no']
        email = request.form['email']

        db_check_query = " SELECT COUNT(*) FROM CRM.contact_master WHERE "
        db_check_query += f" cont_phone = '{mob_no.strip()}' " if '@' in session['identifier'] else f" cont_email = '{email.strip()}' "
        print(db_check_query)
        check_data = db.get_data_in_list_of_tuple(db_check_query)

        if check_data and check_data[0][0] > 0 and request.form.get('forced_submit') != 'true':
            session['user_name'] = name
            session['user_mob_no'] = mob_no
            session['user_email'] = email
            quote = "'{}' This is already present please login with that.".format(
                mask_mobile(str(mob_no)) if not '@' in db_check_query else str(mask_email(email)))

            return render_template('add_cont.html', p_h_mob=p_holder_mob, p_h_email=p_holder_email, quote=quote)

        otp = generate_otp()

        if '@' in db_check_query:
            # Send OTP via email
            send_otp_via_email(email, otp)
            session['identifier'] = email
        else:
            send_wp.send_otp_via_wp(mob_no, otp)
            session['identifier'] = mob_no


        session['otp'] = otp
        session['user_name'] = name
        session['user_mob_no'] = mob_no
        session['user_email'] = email

        check_cust = f""" select cont_id from crm.contact_master order by id desc limit 1 """
        print(check_cust)
        check_cust_data = db.get_data_in_list_of_tuple(check_cust)
        print(check_cust_data)
        c_time = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        if check_cust_data:
            old_comp_id = check_cust_data[0][0] if check_cust_data[0] else 'CONT0001'
            numaric_part = int(old_comp_id[4:])
            new_numaric_part = numaric_part + 1
            new_comp_id = old_comp_id[:4] + f'{new_numaric_part:04d}' if new_numaric_part <= 999 else f'{new_numaric_part:05d}'
        cust_id = new_comp_id if check_cust_data else old_comp_id

        insert_query = f""" INSERT INTO crm.contact_master (cont_id,acc_id,cont_name,cont_phone,cont_email,is_master,added_by,created_time)
	                    VALUES ('{cust_id}','ACC0000','{name}','{mob_no}','{email}','No','user','{c_time}'); """
        # update_query = f""" update crm.contact_master set updated_by = '{str(session['identifier'])}' , updated_time = '{c_time}', """
        # update_query += f" cont_phone = '{mob_no}' where cont_email = '{email}' "  if '@' in db_check_query else f" cont_email = '{email}' where cont_phone = '{mob_no}' "

        # session['insert_query'] = update_query if request.form.get('forced_submit') == 'true' else insert_query
        session['insert_query'] = insert_query

        return redirect(url_for('verify_otp_2'))
    
    return render_template('add_cont.html', p_h_mob=p_holder_mob, p_h_email=p_holder_email, quote=request.args.get('quote'))


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
        # identifier = session['identifier_2']  # This can be either mobile or email
        # p_holder_mob =  session['identifier'] if not '@' in session['identifier'] else 'Enter Your Mobile'
        # p_holder_email = session['identifier'] if '@' in session['identifier'] else 'Enter Your E-Mail'
        mob_no = session['user_mob_no']
        email = session['user_email']
        name = session['user_name']
        # c_id = session['comp_id']
        query = session['insert_query']
        # para = session['para']
        print(f'l-281 {query}')
        otp = request.form['otp']
        if 'otp' in session and 'identifier' in session and session['otp'] == otp:
            # Clear the OTP and identifier from the session after successful verification
            session.pop('otp')
            print('executing')
            db.execute(query)
            # return render_template('work_form.html', p_h_mob=mob_no, p_h_email=email, quote=request.args.get('quote'))
            return render_template('welcome.html')
            # return redirect(url_for('thank_you', mobile=mob_no,email=email,c_name=name,comp_id=c_id))
        return render_template('verify_otp_2.html', error_message="Invalid OTP")
    return render_template('verify_otp_2.html', otp=otp, error_message=None)


@app.route('/resend_otp_2', methods=['POST'])
def resend_otp_2():
    identifier = session['identifier']      
    otp = generate_otp()
    session['otp'] = otp
    
    if '@' in identifier:
        send_otp_via_email(identifier, otp)
    else:
        send_wp.send_otp_via_wp(identifier, otp)
    mob_no = request.args.get('mobile')
    email = request.args.get('email')
    name = request.args.get('c_name')
    c_id = request.args.get('comp_id')
    insert_query = request.args.get('insert_query')
    para = request.args.get('para')
    return redirect(url_for('verify_otp_2', fs=True, mobile=mob_no,email=email,
                            c_name=name,comp_id=c_id, insert_query=insert_query, para=para))


@app.route('/list_of_complaints', methods=["GET","POST"])
@login_required
def list_of_complaints():
    username = session.get('identifier')

    if request.method == "POST":
            comp_id_to_reopen = request.form.get("comp_id")
            if comp_id_to_reopen:
                
                reopen_check_query = f""" select reopen_times from chd.query_table where comp_id = '{comp_id_to_reopen}' ;"""
                reopen_check_data = db.get_data_in_list_of_tuple(reopen_check_query)
                new_reopen = int(reopen_check_data[0][0]) + 1 if reopen_check_data and reopen_check_data[0][0] is not None else 1
                
                reopen_query = f""" update chd.query_table set complaint_status = 'OPEN', is_reopen = 'Yes', 
                                    reopen_date = LOCALTIMESTAMP, reopen_times = '{str(new_reopen)}'
                                    where comp_id = '{comp_id_to_reopen}' ;"""
                db.execute(reopen_query)


    get_list_of_comp_query = f""" select comp_id, c_id, c_name, mobile_no, email_id, p_id, p_name, in_warranty,
                                complaint, complaint_status, created_date, assign_to, assign_date, ext_col_1 
                                from chd.query_table where (mobile_no = '{username}' or email_id = '{username}') and 
                                (closed_time is null  or (closed_time :: date >= current_date - 3) or is_reopen = 'Yes') ;"""
    print(get_list_of_comp_query)
    get_list_of_comp_data = db.get_row_as_dframe(get_list_of_comp_query)
    # print(get_list_of_comp_data)
    
    return  render_template("list_of_comp.html", data=get_list_of_comp_data)

 

@app.route('/user_form', methods=['GET', 'POST'])
@login_required
def user_form():
    username = session.get('identifier')

    get_acc_query = f"""select acc_id, cont_phone, cont_email, cont_name from crm.contact_master cm  where (cont_phone = '{username.strip()}' or cont_email = '{username.strip()}') limit 1;"""
    print('get_acc_query', get_acc_query)
    data_cont = db.get_data_in_list_of_tuple(get_acc_query)[0]
    get_acc_id = data_cont[0]
    session['user_name'] = data_cont[3] if data_cont[3] != 'Not Register' else session['user_name']
    session['user_mob_no'] = data_cont[1]
    session['user_email'] = data_cont[2]
    # default_assign = 'Neeraj Kanwar'
    default_assign = 'Not Assigned'

    if request.method == 'POST':
        # Process the form data here
        # customer_id = session['username']
        location = ''
        remarks = ''
        product = request.form['product_name']
        if product == 'N_R':
            try:
                # Handle additional fields for "Not showing here" option
                product_txt = request.form['product_name_txt']
                location = request.form['location']
                is_in_warranty = request.form['is_in_warranty'].replace('not_sure', 'Not Sure')
                work_type = request.form['work_type']
                query_complaint = request.form['query_complaint']

                created_date = datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
                # check_comp = f""" select id from chd.work_form order by sl_no desc limit 1 """
                check_comp = f""" SELECT comp_id 
                FROM chd.query_table 
                ORDER BY CAST(SUBSTRING(comp_id, 3) AS INTEGER) DESC 
                LIMIT 1; """
                print(check_comp)
                check_comp_data = db.get_data_in_list_of_tuple(check_comp)
                print(check_comp_data)
                old_comp_id = 'T-1'
                if check_comp_data:
                    old_comp_id = check_comp_data[0][0] if check_comp_data[0] else 'T-1'
                    numaric_part = int(old_comp_id.split('-')[1])
                    new_numaric_part = int(numaric_part) + 1
                    new_comp_id = old_comp_id[:2] + f'{new_numaric_part}'
                c_id = new_comp_id if check_comp_data else old_comp_id
                new_comp_id = new_comp_id if check_comp_data else old_comp_id
                session['com_id'] = c_id
                c_name = session['user_name']
                mobile = session['user_mob_no']
                email = session['user_email']
                insert_query_1 = """INSERT INTO chd.work_form (id, name, mob_no, email, work_type, location, is_in_warranty, remarks, work_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"""
                para = (c_id, c_name, mobile, email, work_type, location, is_in_warranty, query_complaint, product_txt)
                print(insert_query_1)
                db.execute(insert_query_1,para)
                # insert_query_2 = f"""INSERT INTO chd.query_table (comp_id, c_id, c_name, mobile_no , email_id , p_id , p_name ,in_warranty , complaint, complaint_status , created_date, assign_to, assign_date, ext_col_1)
                # VALUES ('{new_comp_id}', '000', '{c_name}', '{mobile}', '{email}', '', '{product_txt}', '{is_in_warranty}','{query_complaint}', 'OPEN','{created_date}','{default_assign}', LOCALTIMESTAMP, 'Not Registered' ) ON CONFLICT DO NOTHING;"""
                insert_query_2 = f"""INSERT INTO chd.query_table (comp_id, c_id, c_name, mobile_no , email_id , p_id , p_name ,in_warranty , complaint, complaint_status , created_date, assign_to, assign_date, ext_col_1)
                VALUES ('{new_comp_id}', '{get_acc_id}', '{c_name}', '{mobile}', '{email}', '', '{product_txt}', '{is_in_warranty}','{query_complaint}', 'OPEN','{created_date}','{default_assign}', LOCALTIMESTAMP, 'Not Registered' ) ON CONFLICT DO NOTHING;"""

                # insert_query = f"""INSERT INTO chd.query_table (comp_id, otp, c_id, c_name, mobile_no , email_id , p_id , p_name ,in_warranty , in_amc, complaint, complaint_status , is_reopen , reopen_times , created_date, ex_work_id, ex_work_price, assign_to, assign_date)
                # VALUES ('{new_comp_id}', '{c_id}', '{c_name}', '{mobile}', '{email}', '{product_id}', '{product_name}', '{warranty}', '{amc}', '{query_complaint}', '{comp_status}', '{is_reopen}', '{reopen_times}', '{created_date}', '{ex_work_id}', '{ex_work_price}', '{default_assign}', now()) ON CONFLICT DO NOTHING;"""
                print(insert_query_2)
                db.execute(insert_query_2)
                remarks = f'Customer Name is {c_name}. The work type is {work_type}. Not showing option is selected. Kindly check and do the needful.'
            except:
                pass
        else:
            product_id = product.split('-', maxsplit=1)[0]
            query_complaint = request.form['query_complaint']

            ex_work_id = ""
            ex_work_price = ""
            ex_work = request.form.get('selected_work')
            if ex_work:
                ex_work_id = ex_work.split('-', maxsplit=1)[0]
                ex_work_price = ex_work.split('-', maxsplit=1)[1]

            # Fetch and display product details here
            product_details_query = f"""SELECT * FROM chd.cust_product_table WHERE c_id = '{get_acc_id}' AND p_id = '{product_id.strip()}';"""
            product_details_data = db.get_data_in_list_of_tuple(product_details_query)

            if not product_details_data:
                return 'Product details not found'

            # Process the product details data
            product_name = product_details_data[0][10]
            warranty = product_details_data[0][15]
            amc = 'NO' if product_details_data[0][18] in (None, 'none', 'NO') else 'YES'

            c_id = product_details_data[0][1]
            c_name = product_details_data[0][2]
            mobile = product_details_data[0][3]
            email = product_details_data[0][4]
            otp = generate_otp()
            comp_status = 'OPEN'
            is_reopen = 'NO'
            reopen_times = '0'
            created_date = datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
            check_comp = f""" SELECT comp_id 
            FROM chd.query_table 
            ORDER BY CAST(SUBSTRING(comp_id, 3) AS INTEGER) DESC 
            LIMIT 1; """
            print(check_comp)
            check_comp_data = db.get_data_in_list_of_tuple(check_comp)
            print(check_comp_data)
            old_comp_id = 'C-1'
            if check_comp_data:
                old_comp_id = check_comp_data[0][0] if check_comp_data[0] else 'C-1'
                numaric_part = int(old_comp_id.split('-')[1])
                new_numaric_part = numaric_part+1
                new_comp_id = old_comp_id[:2] + f'{new_numaric_part}'
            new_comp_id = new_comp_id if check_comp_data else old_comp_id
            session['com_id'] = new_comp_id
            # default_assign = 'Neeraj Kanwar'
            # Insert data into the respective table
            insert_query = f"""INSERT INTO chd.query_table (comp_id, otp, c_id, c_name, mobile_no , email_id , p_id , p_name ,in_warranty , in_amc, complaint, complaint_status , is_reopen , reopen_times , created_date, ex_work_id, ex_work_price, assign_to, assign_date, ext_col_1)
            VALUES ('{new_comp_id}', {int(otp)}, '{c_id}', '{c_name}', '{mobile}', '{email}', '{product_id}', '{product_name}', '{warranty}', '{amc}', '{query_complaint}', '{comp_status}', '{is_reopen}', '{reopen_times}', '{created_date}', '{ex_work_id}', '{ex_work_price}', '{default_assign}', LOCALTIMESTAMP, 'Registered' ) ON CONFLICT DO NOTHING;"""

            logger.info(insert_query)
            db.execute(insert_query)

            get_prod_loc_query = f"""SELECT location FROM crm.work_master WHERE work_id = '{product_id.strip()}' ; """
            print(get_prod_loc_query)
            get_prod_loc_data = db.get_data_in_list_of_tuple(get_prod_loc_query)
            location = get_prod_loc_data[0][0] if get_prod_loc_data else ''
            print(get_prod_loc_data)
            remarks = f'Customer Name is {c_name}. The work name is {product_name}. Kindly check and do the needful.'

        template_query = f""" select template_id, template_text, type, name from chd.templates where name in ('New complaint to customer', 'New complaint to manager') and type = 'whatsapp' ; """
        template_query_data = db.get_data_in_list_of_tuple(template_query)

        for i in range(len(template_query_data)):
            try:
                if template_query_data[i][2] == 'whatsapp':
                    if template_query_data[i][3] == 'New complaint to customer':
                        send_wp.send_wp_msg(mobile, template_query_data[i][1].format(c_name, new_comp_id, query_complaint,'', mobile, ''))
                        pass
                    elif template_query_data[i][3] == 'New complaint to manager':
                        # send_wp.send_wp_msg('7347008010', template_query_data[i][1].format(default_assign, new_comp_id, query_complaint, location, mobile, remarks))
                        # send_wp.send_wp_msg('9988880885', template_query_data[i][1].format('Ashish Gupta', new_comp_id, query_complaint, location, mobile, remarks))
                        # send_wp.send_wp_msg('9872724408', template_query_data[i][1].format('Prakash Kumar', new_comp_id, query_complaint, location, mobile, remarks))
                        send_wp.send_msg_in_group(group_id='120363287511346467@g.us', msg=template_query_data[i][1].format('Team', new_comp_id, query_complaint, location, mobile, remarks))
            except:
                pass
        # Add email also

        return redirect(url_for('thank_you'))

    get_acc_query = f"""SELECT acc_id, cont_phone, cont_email, cont_name FROM crm.contact_master cm WHERE (cont_phone = '{username}' OR cont_email = '{username}') LIMIT 1;"""
    data_cont = db.get_data_in_list_of_tuple(get_acc_query)[0]
    get_acc_id = data_cont[0]
    session['user_name'] = data_cont[3]
    session['user_mob_no'] = data_cont[1]
    session['user_email'] = data_cont[2]

    # query = f"""SELECT * FROM chd.cust_product_table WHERE c_id = '{get_acc_id}' ORDER BY id DESC; """
    query = f"""SELECT c_id, c_name, street , city , state , pincode , p_id, p_name , p_desc , p_bill_date ,
            warranty_start_date , warranty_end_date , amc_start_date , amc_end_date
            FROM chd.cust_product_table WHERE c_id = '{get_acc_id}' """
    # data = db.get_data_in_list_of_tuple(query)
    query += ' ORDER BY id DESC;' if get_acc_id != 'ACC0000' else f'''and (mobile_no = '{data_cont[1]}' or email_id = '{data_cont[2]}') ORDER BY id DESC;'''

    data = db.get_row_as_dframe(query)
    ex_work_query = """SELECT * FROM chd.ex_product_list;"""
    ex_work_data = db.get_data_in_list_of_tuple(ex_work_query)

    if not data.empty:
        product_names = []
        location_names = []
        for _, item in data.iterrows():
            # p_id = item[4]
            p_id = item['p_id']
            # p_name = item[5]
            p_name = item['p_name']
            street = item['street']
            city = item['city']
            state = item['state']
            pincode = item['pincode']
            warranty = '(Not in warranty)'
            # warranty_e_date = datetime.datetime.strptime(item[9], "%Y-%m-%d") if item['warranty_end_date'] and item['warranty_end_date'] != 'None' else None
            warranty_e_date = datetime.datetime.strptime(item['warranty_end_date'], "%Y-%m-%d") if item['warranty_end_date'] and item['warranty_end_date'] != 'None' else None
            # print(warranty_e_date)

            amc_e_date = datetime.datetime.strptime(item['amc_end_date'], "%Y-%m-%d") if item['amc_end_date'] and item['amc_end_date'] != 'None' else None

            current_date = datetime.datetime.now()
            if warranty_e_date and warranty_e_date >= current_date:
                warranty = '(In warranty)'
            if amc_e_date and amc_e_date >= current_date:
                warranty = '(In warranty)'
            product_names.append(f'{p_id} - {p_name} - {warranty}')
            location_names.append(f'{street}, {city}, {state}, {pincode}')
            c_name = item['c_id']
        c_id = get_acc_id
        return render_template('user_form.html', products=product_names, loc=location_names, c_id=c_id, c_name=c_name, ex_work=ex_work_data)
    return render_template('user_form.html', products=[], c_id=None, c_name=None, ex_work=ex_work_data)
    # return render_template('work_form.html',  p_h_mob=session['user_mob_no'], p_h_email=session['user_email'])


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
    body = f'Hello {c_name},\n\nThank you for your submission!\nYour Complaint ID: {comp_id}\nOne of our executive will address your query shortly. \n\nBest regards,\nShreenath Enterprise'
    print(session.keys())
    # Send the email using your existing mail.send_mail function
    # mail.send_mail(to_add=to_add, to_cc=to_cc, sub=subject, body=body)

    # send_wp.send_wp_msg(mobile, msg=body)

    return render_template('thank_you.html', comp_id=comp_id)


@app.route('/terms')
def terms():
    return render_template('terms.html')


if __name__ == '__main__':
    app.run(host='192.168.0.16', port=5021, debug=True)
    # app.run(debug=True)


