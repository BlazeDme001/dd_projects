from flask import Flask, render_template, request, redirect, jsonify, session, url_for, flash
from functools import wraps
import db_connect as db
import logging
import random
import string
import datetime
import pandas as pd
import mail
import send_wp
import requests

app = Flask(__name__)

logging.basicConfig(filename='crm_data.log',
                    format='%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app.secret_key = '1234567890'

class User:
    def __init__(self, username, profile, mobile, email):
        self.username = username
        self.profile = profile
        self.mobile = mobile
        self.email = email

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def authenticate(username, password):
    # query = "SELECT name, passkey, profile FROM chd.office_passkey_details WHERE (mobile_no = %s or email_id = %s) AND passkey = %s AND status = 'ACTIVE' "
    query = """select ud.username, uac.profile, ud.mobile, ud.email from ums.user_app_connect uac left join
    ums.user_details ud on uac.user_id = ud.user_id where (ud.mobile = %s or ud.email = %s or ud.username = %s)
    and ud.status = 'ACTIVE' and ud."password" = %s and uac.app_id = 'A-5' and uac.ext_col_1 = 'ACTIVE'; """
    params = [username, username, username, password]
    result = db.get_data_in_list_of_tuple(query, params)
    if result:
        user_data = result[0]
        user = User(user_data[0], user_data[1], user_data[2], user_data[3])
        return user
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = authenticate(username, password)
        if user:
            session['logged_in'] = True
            session['username'] = user.username
            session['profile'] = user.profile
            return redirect(url_for('pending_complaints'))
        else:
            return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('home'))

# ===============================================
@app.route('/manager')
@login_required
def manager():
    # Retrieve all users for display
    users_query = "SELECT id, name, mobile_no, email_id, ext_col_2, profile, ext_col_1 FROM chd.office_passkey_details ;"
    users_data = db.get_data_in_list_of_tuple(users_query)
    return render_template('manager.html', users=users_data)

@app.route('/update_user/<user_id>', methods=['GET', 'POST'])
@login_required
def update_user(user_id):
    user_query = "SELECT id, name, mobile_no, email_id, ext_col_2, profile, ext_col_1 FROM chd.office_passkey_details WHERE id = %s"
    user_data = db.get_data_in_list_of_tuple(user_query, [user_id])

    if not user_data:
        flash('User not found!', 'error')
        return redirect(url_for('manager'))

    user_data = user_data[0]

    if request.method == 'POST':
        # Handle form submission for updating user data
        updated_name = request.form.get('name')
        updated_mobile_no = request.form.get('mobile_no')
        updated_email_id = request.form.get('email_id')
        updated_profile = request.form.get('profile')
        updated_dpt = request.form.get('dpt')
        updated_status = request.form.get('status')

        update_query = """UPDATE chd.office_passkey_details
                          SET name = %s, mobile_no = %s, email_id = %s, ext_col_2 = %s, profile = %s, ext_col_1 = %s
                          WHERE id = %s"""
        update_params = [updated_name, updated_mobile_no, updated_email_id, updated_dpt, updated_profile, updated_status, user_id]
        db.execute(update_query, update_params)

        flash('User updated successfully!', 'success')
        return redirect(url_for('manager'))
    return render_template('update_user.html', user=user_data)


@app.route('/insert_user', methods=['GET', 'POST'])
@login_required
def insert_user():
    if request.method == 'POST':
        new_name = request.form.get('name')
        new_mobile_no = request.form.get('mobile_no')
        new_email_id = request.form.get('email_id')
        new_profile = request.form.get('profile')
        new_dpt = request.form.get('dpt')
        status = 'ACTIVE'

        password = generate_password(new_name)

        insert_query = """INSERT INTO chd.office_passkey_details (name, passkey, mobile_no, email_id, ext_col_2, profile, ext_col_1)
                          VALUES (%s, %s, %s, %s, %s, %s, %s) ;"""
        insert_params = [new_name, password, new_mobile_no, new_email_id,new_dpt, new_profile, status]
        db.execute(insert_query, insert_params)

        flash('User inserted successfully!', 'success')
        return redirect(url_for('manager'))
    return render_template('insert_user.html')


# def generate_password_2(name):
#     # Extract initials from the name
#     initials = ''.join(word[0].upper() for word in name.split())
#     random_numbers = ''.join(secrets.choice(string.digits) for _ in range(4))
#     special_characters = ''.join(secrets.choice(string.punctuation) for _ in range(3))
#     password = f'{initials}{random_numbers}{special_characters}'
    
#     return password
# ====================================================

def generate_password(length=None):
    try:
        characters = string.ascii_letters + string.digits + string.punctuation
        password = ''.join(random.choice(characters) for _ in range(len(length)))
    except:
        password = ''.join(random.choice(characters) for _ in range(8))
    return password


@app.route('/all_complaint')
@login_required
def all_complaint():
    query = """select * from chd.query_table order by id desc;"""
    c_data = db.get_row_as_dframe(query)
    # c_data['closed_time'] = pd.to_datetime(c_data['closed_time'], errors='coerce')
    return render_template('complaints.html', c_data=c_data)


@app.route('/complaint_details/<comp_id>')
@login_required
def complaint_details(comp_id):
    query = f"""
        SELECT comp_id, c_id, c_name, mobile_no, email_id, p_id, p_name, in_warranty,
               in_amc, assign_to, assign_date, complaint, complaint_status,
               complaint_remarks, complaint_review_by, work_rating, engineer_rating,
               is_reopen, reopen_date, reopen_times, closed_time, ext_col_1
        FROM chd.query_table
        WHERE comp_id = '{comp_id}';"""
    # params = [comp_id]
    df = db.get_row_as_dframe(query)
    result = df.to_dict(orient='records')[0] if not df.empty else {}
    
    hist_query = f"""
        SELECT comp_id, c_id, c_name, p_name, in_warranty,
               in_amc, assign_to, assign_date, complaint, complaint_status,
               complaint_remarks, is_reopen, reopen_date, reopen_times, ext_col_1, ext_col_2,change_timestamp 
        FROM chd.query_table_history
        WHERE comp_id = '{comp_id}';"""
    hist_df = db.get_row_as_dframe(hist_query)
    return render_template('complaint_details.html', complaint=result, hist=hist_df, type='lead')


@app.route('/update_work_details/<comp_id>', methods=['GET', 'POST'])
@login_required
def update_work_details(comp_id):
    user_name = session['username']
    if request.method == 'POST':
        # Get the updated values from the form
        in_warranty = request.form.get('in_warranty')
        in_amc = request.form.get('in_amc')
        assign_lead = request.form.get('assign_lead', '')
        assign_to = request.form.get('assign_to')
        complaint_status = request.form.get('complaint_status')
        complaint_remarks = request.form.get('complaint_remarks')
        complaint_review_by = request.form.get('complaint_review_by')
        work_rating = request.form.get('work_rating')
        is_reopen = request.form.get('is_reopen')

        query = f"""UPDATE chd.query_table
            SET in_warranty = '{in_warranty}', 
                in_amc = '{in_amc}', 
                assign_lead = '{assign_lead}', 
                assign_to = '{assign_to}', 
                complaint_status = '{complaint_status}', 
                complaint_remarks = '{complaint_remarks}', 
                complaint_review_by = '{complaint_review_by}', 
                work_rating = '{work_rating}', 
                ext_col_2 = '{user_name}',
                is_reopen = '{is_reopen}' """

        if complaint_status in ('Closed - Work Done', 'Closed - Work Not Done', 'Cancelld - By Customer', 'Cancelld - By Us'):
            query += f""" , closed_time = now() """

        query += f""" WHERE comp_id = '{comp_id}' """
        print(query)
        db.execute(query)
        return redirect(url_for('complaint_details', comp_id=comp_id))

    else:
        query = f"""SELECT in_warranty, in_amc, assign_lead, assign_to, complaint_status,
                   complaint_remarks, complaint_review_by, work_rating, is_reopen
            FROM chd.query_table
            WHERE comp_id = '{comp_id}' """
        result = db.get_data_in_list_of_tuple(query)

        # user_details_query = """SELECT name FROM chd.office_passkey_details where ext_col_1 = 'ACTIVE' """
        user_details_query = """ select uac.user_id , uac.name from ums.user_app_connect uac 
        left join ums.user_details ud on uac.user_id = ud.user_id where uac.app_id = 'A-5' and uac.ext_col_1 = 'ACTIVE' """
        if session['profile'] == 'USER':
            assign_to = []
        if session['profile'] == 'SUPER ADMIN':
            assign_to = db.get_data_in_list_of_tuple(user_details_query)
        if session['profile'] == 'ADMIN':
            user_details_query += f""" and uac.profile in ('ADMIN','USER'); """
            assign_to = db.get_data_in_list_of_tuple(user_details_query)

        if result:
            complaint_details = {
                'comp_id': comp_id,
                'in_warranty': result[0][0],
                'in_amc': result[0][1],
                'assign_to': result[0][3],
                'complaint_status': result[0][4],
                'complaint_remarks': result[0][5],
                'complaint_review_by': result[0][6],
                'work_rating': result[0][7],
                'is_reopen': result[0][8]
            }

            return render_template('update_work_details.html', complaint=complaint_details, assign_to=assign_to)


@app.route('/pending_complaints', methods=['GET', 'POST'])
@login_required
def pending_complaints():
    user_name = session['username']
    selected_complaint = None
    default_assign = 'Neeraj Kanwar'
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'complaint':
            comp_all_data = request.form.get('comp_id')
            selected_comp_id = comp_all_data.split('---')[0].strip()
            query = f"""SELECT comp_id, c_id, c_name, mobile_no, email_id, p_id, p_name, in_warranty,
                    in_amc, assign_to, assign_date, complaint, complaint_status,
                    complaint_remarks, complaint_review_by, work_rating, engineer_rating,
                    is_reopen, reopen_date, reopen_times, ext_col_1
                FROM chd.query_table
                WHERE comp_id = '{selected_comp_id}' ;"""
            logger.info(query)
            df = db.get_row_as_dframe(query)
            try:
                selected_complaint = df.to_dict(orient='records')[0]
                session['comp_id'] = selected_comp_id
                session['name'] = selected_complaint['c_name']
                session['mobile_no'] = selected_complaint['mobile_no']
                session['email_id'] = selected_complaint['email_id']
                # get_acc_id_query = f""" select acc_id from crm.contact_master cm where cont_phone = '{selected_complaint['mobile_no']}' and cont_email = '{selected_complaint['email_id']}'; """
                # try:
                #     get_acc_id_data = db.get_data_in_list_of_tuple(get_acc_id_query)[0][0]
                # except:
                #     get_acc_id_data = ''
                # get_acc_id_data = selected_complaint['c_id']
                # session['acc_id'] = get_acc_id_data
            except:
                selected_complaint = []
        elif form_type == 'update':
            selected_comp_id = request.form.get('comp_id_1')
            updated_status = request.form.get('complaint_status')
            updated_assign_to = request.form.get('assign_to')
            schedule_date = request.form.get('schedule_date')
            complaint_remarks = request.form.get('remarks')

            check_query_assign = f"""SELECT assign_to, complaint_status FROM chd.query_table
                    WHERE comp_id = '{selected_comp_id}' order by id desc limit 1;"""
            check_query_assign_data = db.get_data_in_list_of_tuple(check_query_assign)
            try:
                old_assign_to = check_query_assign_data[0][0]
                old_status = check_query_assign_data[0][1]
            except:
                old_assign_to = ''
                old_status = ''

            mail_query = f"""select mobile ,email , name from ums.user_details where user_id = '{updated_assign_to}';"""
            mail_data = db.get_data_in_list_of_tuple(mail_query)

            # Update the database with the new status and assign_to values
            update_query = f"""UPDATE chd.query_table SET complaint_status = '{updated_status}', ext_col_2 = '{user_name}' """ 
            if updated_assign_to:
                update_query += f""" , assign_to = '{mail_data[0][2]}' """

            if schedule_date:
                update_query += f""" , schedule_date = '{str(schedule_date).replace("T", " ")}' """

            if complaint_remarks:
                update_query += f""" , complaint_remarks = '{str(complaint_remarks).replace("'", "''")}' """
                
            if updated_status in ('Closed - Work Done', 'Closed - Work Not Done', 'Cancelld - By Customer', 'Cancelld - By Us'):
                update_query += f""" , closed_time = now() """

            update_query += f"""WHERE comp_id = '{selected_comp_id}' ;"""

            db.execute(update_query)

            # Now, retrieve the updated complaint details
            query = f"""SELECT comp_id, c_id, c_name, mobile_no, email_id, p_id, p_name, in_warranty,
                    in_amc, assign_to, assign_date, complaint, complaint_status,
                    complaint_remarks, complaint_review_by, work_rating, engineer_rating,
                    is_reopen, reopen_date, reopen_times, ext_col_1
                FROM chd.query_table
                WHERE comp_id = '{selected_comp_id}' ;"""
            logger.info(query)
            df = db.get_row_as_dframe(query)
            try:
                selected_complaint = df.to_dict(orient='records')[0]
                # logger.info(selected_complaint)
            except:
                selected_complaint = []


            # to_add = ['ramit.shreenath@gmail.com', mail_data[0][1]]
            # sub = f'Complaint details for {selected_comp_id}'
            # body = f"""Complaint details: \nComplaint ID: {selected_comp_id}\nAssign To: {mail_data[0][2]}\nComplaint Status: {updated_status}
            # \n\n Link: http://192.168.0.16:5022/complaint_details_field/{selected_comp_id} \n\nPlease checkout the link for more details about the complaint."""
            # mail.send_mail(to_add=to_add, to_cc=[], sub=sub, body=body)

            template_query = """ select name, template_text, type from chd.templates where name in ('Complaint assign to customer','Complaint Assigned To Executive', 
                            'Status Update To Customer', 'Job Completed To Customer', 'Status Update To Manager', 'Job Completed To Manager') order by template_id  asc ; """
            template_data = db.get_data_in_list_of_tuple(template_query)

            template_dict_mail = {key: value for key, value, type in template_data if type != 'whatsapp'}
            template_dict_wp = {key: value for key, value, type in template_data if type == 'whatsapp'}

            # return (old_assign_to, updated_assign_to, old_status, updated_status)
            dict = {
                "oat": old_assign_to,
                "uat": mail_data[0][2],
                "os": old_status,
                "us": updated_status,
                "Comp_id": selected_comp_id
            }

            if old_assign_to != mail_data[0][2]:
                if old_status and updated_status and old_status.upper() != updated_status.upper() and update_user != 'WIP - Assigned' :
                    if updated_status == 'Closed - Work Done':
                        # For JOB done/closed
                        body_wp = template_dict_wp['Job Completed To Customer'].format(selected_complaint['c_name'], selected_complaint['complaint_remarks'])
                        send_wp.send_wp_msg(selected_complaint['mobile_no'], body_wp)
                        mail.send_mail(to_add=selected_complaint['email_id'], to_cc=[], sub='Complaint Resolved', body=body_wp)
                        body_wp = template_dict_wp['Job Completed To Manager'].format('Team', selected_complaint['comp_id'], session['username'], selected_complaint['complaint_remarks'], selected_complaint['c_id'], selected_complaint['complaint'], selected_complaint['c_name'])
                        # body_wp = template_dict_wp['Job Completed To Manager'].format(default_assign, selected_complaint['comp_id'], session['username'], selected_complaint['complaint_remarks'], selected_complaint['c_id'], selected_complaint['complaint'], selected_complaint['c_name'])
                        # send_wp.send_wp_msg('7347008010', body_wp)
                        send_wp.send_msg_in_group(msg=body_wp)
                        mail.send_mail(to_add='installation@shreenathgroup.in', to_cc=[], sub='Complaint Resolved', body=body_wp)
                        # dict['line'] = '356'
                        # return dict
                    else:
                        body_wp = template_dict_wp['Status Update To Customer'].format(selected_complaint['c_name'], selected_complaint['complaint_status'], selected_complaint['complaint_remarks'])
                        send_wp.send_wp_msg(selected_complaint['mobile_no'], body_wp)
                        mail.send_mail(to_add=selected_complaint['email_id'], to_cc=[], sub='Complaint Status Update', body=body_wp)
                        body_wp = template_dict_wp['Status Update To Manager'].format('Team', selected_complaint['comp_id'], selected_complaint['complaint_status'], session['username'], selected_complaint['complaint_remarks'], selected_complaint['c_id'], selected_complaint['complaint'], selected_complaint['c_name'])
                        # body_wp = template_dict_wp['Status Update To Manager'].format(default_assign, selected_complaint['comp_id'], selected_complaint['complaint_status'], session['username'], selected_complaint['complaint_remarks'], selected_complaint['c_id'], selected_complaint['complaint'], selected_complaint['c_name'])
                        # send_wp.send_wp_msg('7347008010', body_wp)
                        send_wp.send_msg_in_group(msg=body_wp)
                        mail.send_mail(to_add='installation@shreenathgroup.in', to_cc=[], sub='Complaint Status Update', body=body_wp)
                        # dict['line'] = '365'
                        # return dict
                else:
                    body_wp = template_dict_wp['Complaint assign to customer'].format(selected_complaint['c_name'], mail_data[0][2], mail_data[0][2], mail_data[0][0], mail_data[0][1])
                    send_wp.send_wp_msg(selected_complaint['mobile_no'], body_wp)
                    mail.send_mail(to_add=selected_complaint['email_id'], to_cc=[], sub='Complaint Assigned', body=body_wp)
                    body_wp = template_dict_wp['Complaint Assigned To Executive'].format('Team', selected_complaint['comp_id'], selected_complaint['complaint'], '', selected_complaint['mobile_no'], selected_complaint['complaint_remarks'],'https://bit.ly/comp_check')
                    # body_wp = template_dict_wp['Complaint Assigned To Executive'].format(mail_data[0][2], selected_complaint['comp_id'], selected_complaint['complaint'], '', selected_complaint['mobile_no'], selected_complaint['complaint_remarks'],'https://bit.ly/comp_check')
                    # send_wp.send_wp_msg(mail_data[0][0], body_wp)
                    send_wp.send_msg_in_group(msg=body_wp)
                    # return mail_data[0][0]
                    mail.send_mail(to_add=mail_data[0][1], to_cc=[], sub='Complaint Assigned', body=body_wp)
                    # dict['line'] = '375'
                    # return dict
            else:
                if old_status and updated_status and old_status.upper() != updated_status.upper():
                    if updated_status == 'Closed - Work Done':
                        # For JOB done/closed
                        body_wp = template_dict_wp['Job Completed To Customer'].format(selected_complaint['c_name'], selected_complaint['complaint_remarks'])
                        send_wp.send_wp_msg(selected_complaint['mobile_no'], body_wp)
                        mail.send_mail(to_add=selected_complaint['email_id'], to_cc=[], sub='Complaint Resolved', body=body_wp)
                        body_wp = template_dict_wp['Job Completed To Manager'].format(default_assign, selected_complaint['comp_id'], session['username'], selected_complaint['complaint_remarks'], selected_complaint['c_id'], selected_complaint['complaint'], selected_complaint['c_name'])
                        send_wp.send_wp_msg('7347008010', body_wp)
                        mail.send_mail(to_add='installation@shreenathgroup.in', to_cc=[], sub='Complaint Resolved', body=body_wp)
                        # dict['line'] = '387'
                        # return dict
                    else:
                        body_wp = template_dict_wp['Status Update To Customer'].format(selected_complaint['c_name'], selected_complaint['complaint_status'], selected_complaint['complaint_remarks'])
                        send_wp.send_wp_msg(selected_complaint['mobile_no'], body_wp)
                        mail.send_mail(to_add=selected_complaint['email_id'], to_cc=[], sub='Complaint Status Update', body=body_wp)
                        body_wp = template_dict_wp['Status Update To Manager'].format(default_assign, selected_complaint['comp_id'], selected_complaint['complaint_status'], session['username'], selected_complaint['complaint_remarks'], selected_complaint['c_id'], selected_complaint['complaint'], selected_complaint['c_name'])
                        send_wp.send_wp_msg('7347008010', body_wp)
                        mail.send_mail(to_add='installation@shreenathgroup.in', to_cc=[], sub='Complaint Status Update', body=body_wp)
                        # dict['line'] = '396'
                        # return dict

    else:
        selected_complaint = None

    # user_details_query = """SELECT name, id FROM chd.office_passkey_details where ext_col_1 = 'ACTIVE'"""
    user_details_query = """ select uac.user_id , uac.name from ums.user_app_connect uac 
    left join ums.user_details ud on uac.user_id = ud.user_id where uac.app_id = 'A-5' and uac.ext_col_1 = 'ACTIVE' """
    if session['profile'] == 'USER':
        assign_to = []
    if session['profile'] == 'SUPER ADMIN':
        assign_to = db.get_data_in_list_of_tuple(user_details_query)
    if session['profile'] == 'ADMIN':
        user_details_query += f""" and uac.profile in ('ADMIN','USER') ;"""
        assign_to = db.get_data_in_list_of_tuple(user_details_query)

    # assign_query = f"""select "name", id from chd.office_passkey_details; """
    # assign_list = db.get_data_in_list_of_tuple(assign_query)

    pending_query = """SELECT concat(comp_id,' --- ',concat(left(complaint,20),'...')) as comp_id FROM chd.query_table WHERE complaint_status not in ('Cancelld - By Customer', 'Cancelld - By Us', 'Closed - Work Done', 'Closed - Work Not Done') order by id asc;"""
    # pending_query = """SELECT comp_id FROM chd.query_table WHERE complaint_status not in ('Cancelld - By Customer', 'Cancelld - By Us', 'Closed - Work Done', 'Closed - Work Not Done');"""

    pending_df = db.get_row_as_dframe(pending_query)
    complaints_list = pending_df.to_dict(orient='records') if not pending_df.empty else {}

    return render_template('pending_complaints.html', complaints=complaints_list, selected_complaint=selected_complaint, assign_list=assign_to)


def get_latest_id(leads=None, accounts=None, contacts=None, work=None):
    if leads:
        query = "SELECT lead_id FROM crm.leads_master ORDER BY lead_id DESC LIMIT 1"
        result = db.get_data_in_list_of_tuple(query)
        if result:
            last_work_id = result[0][0]
            new_work_number = int(last_work_id.split('-')[1]) + 1
            new_work_id = f"L-{new_work_number}"
            return new_work_id
        else:
            return "L-1"
    elif accounts:
        query = "SELECT acc_id FROM crm.account_master ORDER BY acc_id DESC LIMIT 1"
        result = db.get_data_in_list_of_tuple(query)
        if result:
            last_account_id = result[0][0]
            new_account_number = int(last_account_id[3:]) + 1
            new_account_id = f"ACC{new_account_number:04}"
            return new_account_id
        else:
            return "ACC0001"
    elif contacts:
        query = "SELECT cont_id FROM crm.contact_master ORDER BY cont_id DESC LIMIT 1"
        result = db.get_data_in_list_of_tuple(query)
        if result:
            last_contact_id = result[0][0]
            new_contact_number = int(last_contact_id[4:]) + 1
            new_contact_id = f"CONT{new_contact_number:04}"
            return new_contact_id
        else:
            return "CONT0001"
    elif work:
        query = "SELECT work_id FROM crm.work_master ORDER BY work_id DESC LIMIT 1"
        result = db.get_data_in_list_of_tuple(query)
        if result:
            last_work_id = result[0][0]
            new_work_number = int(last_work_id[5:]) + 1
            new_work_id = f"WORK{new_work_number:04}"
            return new_work_id
        else:
            return "WORK0001"


def is_duplicate(table, phone, email):
    if table == 'account':
        query = f"SELECT COUNT(*) FROM crm.account_master WHERE (contact_phone = '{phone}' OR contact_email = '{email}') and acc_id <> 'ACC0000' "
        result = db.get_data_in_list_of_tuple(query)
        return result[0][0] > 0
    elif table == 'contact':
        query = f"SELECT COUNT(*) FROM crm.contact_master WHERE (cont_phone = '{phone}' OR cont_email = '{email}') and acc_id <> 'ACC0000' "
        result = db.get_data_in_list_of_tuple(query)
        return result[0][0] > 0
    elif table == 'leads':
        query = f"SELECT COUNT(*) FROM crm.leads_master WHERE contact_phone = '{phone}' OR contact_email = '{email}'"
        result = db.get_data_in_list_of_tuple(query)
        return result[0][0] > 0

def create_acc(data_dict):
    try:
        # Check if the phone number or email already exists
        if is_duplicate('account', data_dict['contact_phone'], data_dict['contact_email']):
            raise Exception("Error: The phone number or email already exists in the database.")
            # return "Error: The phone number or email already exists in the database."
        # to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        # Insert data into the database
        query = f"""INSERT INTO crm.account_master (acc_id, acc_name, gst_no, street, city, state, country, pincode,
                                                    contact_name, contact_phone, contact_email, catagory, added_by, created_time)
                    VALUES ('{data_dict["acc_id"]}', '{data_dict["acc_name"]}', '{data_dict["GST_No"]}', '{data_dict["street"]}', '{data_dict["city"]}', '{data_dict["state"]}', '{data_dict["country"]}',
                            '{data_dict["pincode"]}', '{data_dict["contact_name"]}', '{data_dict["contact_phone"]}', '{data_dict["contact_email"]}', '{data_dict["catagory"]}', '{data_dict["username"]}', LOCALTIMESTAMP) ;"""
        # print(query)
        db.execute(query)

        # cont_id = get_latest_contact_id()
        # cont_id = get_latest_id(contacts=True)
        is_master = 'Yes'
        # Insert data into the contact_master table
        query_contact = f"""INSERT INTO crm.contact_master (cont_id, acc_id, cont_name, cont_phone, cont_email, is_master, added_by, created_time)
                    VALUES ('{data_dict["cont_id"]}', '{data_dict["acc_id"]}', '{data_dict["contact_name"]}', '{data_dict["contact_phone"]}', 
                    '{data_dict["contact_email"]}', '{is_master}', '{data_dict["username"]}', '{data_dict["to_day"]}') ;"""
        # print(query_contact)
        db.execute(query_contact)

        # new_pass = generate_password()

        query_cont_pass = f"""INSERT into chd.user_passkey_details (c_id, c_name, passkey, mobile_no, email_id, created_date) 
        values ('{data_dict["acc_id"]}', '{data_dict["acc_name"]}', '{data_dict["new_pass"]}', '{data_dict["contact_phone"]}', '{data_dict["contact_email"]}', '{data_dict["to_day"]}')"""
        db.execute(query_cont_pass)
        return True
    except Exception as err:
        print(str(err))
        return err

def get_state_country(pincode):
    state = country = city = ''
    url = f"http://www.postalpincode.in/api/pincode/{pincode}"
    payload = {}
    headers = {}
    try:
        response = requests.request("GET", url, headers=headers, data=payload, timeout=60)
        if response.status_code == 200 and response.json() and response.json()['Status'] == 'Success':
            rep_json = response.json()
            state = rep_json['PostOffice'][0]['State']
            country = rep_json['PostOffice'][0]['Country']
            city = rep_json['PostOffice'][0]['District']
            return ('S', state, country, city)
        return ('F', state, country, city)
    except:
        return ('E', state, country, city)


@app.route("/insert_account/<id>", methods=["GET", "POST"])
# @app.route("/insert_account", methods=["GET", "POST"])
@login_required
def insert_account(id):
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    if request.method == "POST":

        pincode = request.form.get("pincode")
        state_country_data = get_state_country(pincode.strip())

        if state_country_data[0] == 'S':
            state = state_country_data[1]
            country = state_country_data[2]
            city = state_country_data[3]
        else:
            state = country = city = ''

        data_dict = {
                "acc_id": get_latest_id(accounts=True),
                "cont_id": get_latest_id(contacts=True),
                "acc_name": request.form.get("acc_name"),
                "GST_No": request.form.get("GST_No"),
                "street": request.form.get("street"),
                "city": city,
                "state": state,
                "country": country,
                "pincode": pincode,
                "contact_name": request.form.get("contact_name"),
                "contact_phone": request.form.get("contact_phone"),
                "contact_email": request.form.get("contact_email"),
                "catagory": request.form.get("catagory"),
                "to_day": to_day,
                "new_pass": generate_password(),
                "username": username
        }

        acc_create = create_acc(data_dict)
        if acc_create:
            # query = f""" update chd.query_table set c_id = '{acc_create['acc_id']}' where mobile_no = '{data_dict['contact_phone']}' ;"""
            
            # db.execute(query)
            delete_query = f""" delete from crm.contact_master where acc_id = 'ACC0000' and cont_phone = '{data_dict['contact_phone']}' and cont_email = '{data_dict['contact_email']}' ; """
            db.execute(delete_query)
            
            query = f""" update chd.query_table set c_id = '{data_dict['acc_id']}' , ext_col_2 = '{username}'  where comp_id = '{id}' ;"""
            db.execute(query)

            # return redirect("/pending_complaints")
        return redirect("/pending_complaints")
    return render_template("insert_account.html", id=id)


@app.route("/insert_contact/<id>", methods=["GET", "POST"])
@login_required
def insert_contact(id):
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    if request.method == "POST":
        # Get form data
        acc_id = request.form.get("acc_id")
        # cont_id = get_latest_contact_id()
        try:
            cont_id_query = f""" select cont_id from crm.contact_master where cont_phone = '{cont_phone}' and cont_email = '{cont_email}'; """
            cont_id = db.get_data_in_list_of_tuple(cont_id_query)[0][0]
        except:
            cont_id = get_latest_id(contacts=True)
        cont_name = request.form.get("cont_name")
        cont_phone = request.form.get("cont_phone")
        cont_email = request.form.get("cont_email")

        is_dup = is_duplicate(table='contact', phone=cont_phone, email=cont_email)

        # Check if the contact ID already exists
        query = f"SELECT COUNT(*) FROM crm.contact_master WHERE cont_id = '{cont_id}'"
        result = db.get_data_in_list_of_tuple(query)
        if result[0][0] > 0 or is_dup:
            if cont_email or cont_phone:
                acc_check_query = f""" select cont_id from crm.contact_master where acc_id = '{acc_id}' """ 
                if cont_phone:
                    acc_check_query += f""" and cont_phone = '{cont_phone}' """ 
                if cont_email:
                    acc_check_query += f""" and cont_email = '{cont_email}'; """
                print(acc_check_query)
                try:
                    acc_check_data = db.get_data_in_list_of_tuple(acc_check_query)[0][0]
                except:
                    acc_check_data = ''
                if acc_check_data:
                    delete_query = f""" delete from crm.contact_master where acc_id = 'ACC0000' and cont_phone = '{cont_phone}' and cont_email = {cont_email}; """
                    db.execute(delete_query)
                    
                    query = f""" update chd.query_table set c_id = '{acc_id}'  where comp_id = '{id}' ;"""
                    db.execute(query)
                else:
                    return "Error: The contact ID already exists in the database."
            else:
                return "Error: The contact ID already exists in the database."
            return redirect("/pending_complaints")
        is_master = 'No'
        # Insert data into the database
        query = f"""INSERT INTO crm.contact_master (cont_id, acc_id, cont_name, cont_phone, cont_email, is_master, added_by, created_time)
                    VALUES ('{cont_id}', '{acc_id}', '{cont_name}', '{cont_phone}', '{cont_email}', '{is_master}', '{username}', '{to_day}')"""
        db.execute(query)
        
        delete_query = f""" delete from crm.contact_master where acc_id = 'ACC0000' and cont_phone = '{cont_phone}' and cont_email = {cont_email}; """
        db.execute(delete_query)
        
        query = f""" update chd.query_table set c_id = '{acc_id}', ext_col_2 = '{username}'  where comp_id = '{id}' ;"""
        db.execute(query)

        return redirect("/pending_complaints")

    query = "SELECT acc_id, acc_name FROM crm.account_master"
    # accounts = db.get_data_in_list_of_tuple(query)
    accounts_df = db.get_row_as_dframe(query)
    accounts = accounts_df.to_dict(orient='records')

    return render_template("insert_contact.html", accounts=accounts, id=id)


@app.route("/insert_work_details/<id>/<comp_id>", methods=["GET", "POST"])
@login_required
def insert_work_details(id,comp_id):
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    today_date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    if request.method == "POST":
        # Get form data
        acc_id = request.form.get("acc_id").split('-', maxsplit=1)[0].strip()
        acc_name = request.form.get("acc_id").split('-', maxsplit=1)[1].strip()
        work_name = request.form.get('work_name')
        # contact_id = request.form.get("contact_id")
        billing_date = request.form.get("billing_date")
        camc_warranty_start_date = request.form.get("camc_warranty_start_date")
        camc_warranty_end_date = request.form.get("camc_warranty_end_date")
        amc_start_date = request.form.get("amc_start_date")
        amc_end_date = request.form.get("amc_end_date")
        cost = request.form.get("cost")
        location = request.form.get("location")
        remarks = request.form.get("remarks")
        work_status = request.form.get("work_status")
        enable_credit = request.form.get("enable_credit")

        contact_id = None
        c_ph = None
        c_email = None

        # Generate new work ID
        # work_id = get_latest_work_id()
        work_id = get_latest_id(work=True)
        # query = f"""select cont_id, cont_phone, cont_email from CRM.contact_master cm  where acc_id = '{acc_id.strip()}' and is_master in 'Yes';"""
        query = f"""select cont_id, cont_phone, cont_email, is_master from CRM.contact_master cm  where acc_id = '{acc_id.strip()}' """
        c_data_all = db.get_row_as_dframe(query)
        c_data_mas = c_data_all[c_data_all['is_master'] == 'Yes']
        c_data_nor = c_data_all[c_data_all['is_master'] == 'No']
        c_data_1 = c_data_nor if c_data_mas.empty else c_data_mas

        for _, row in c_data_1.iterrows():
            c_data = row
            break

        if not c_data.empty:
            contact_id = c_data['cont_id']
            c_ph = c_data['cont_phone']
            c_email = c_data['cont_email']

        query = f"""INSERT INTO crm.work_master (work_id, acc_id, work_name, cont_id, billing_date, camc_war_s_date,
                                                camc_war_e_date, amc_s_date, amc_e_date, cost, location,
                                                remarks, work_status, enable_credit, added_by, created_time)
                    VALUES ('{work_id}', '{acc_id}', '{work_name}', '{contact_id}', '{billing_date}', '{camc_warranty_start_date}',
                            '{camc_warranty_end_date}', '{amc_start_date}', '{amc_end_date}', '{cost}', '{location}',
                            '{remarks}', '{work_status}', '{enable_credit}', '{username}', '{to_day}')"""
        db.execute(query)
        query_2 = f"""INSERT INTO chd.cust_product_table (c_id, c_name, mobile_no, email_id, p_id, p_name, p_desc, p_bill_date, warranty_start_date, warranty_end_date, amc_start_date, amc_end_date, created_date) 
        VALUES ('{acc_id}', '{acc_name}', '{c_ph}', '{c_email}', '{work_id}', '{work_name}', '{remarks}', '{billing_date}', '{camc_warranty_start_date}', '{camc_warranty_end_date}', '{amc_start_date}', '{amc_end_date}', '{today_date}') """
        db.execute(query_2)
        query_3 = f""" update chd.query_table set p_id = '{work_id}', ext_col_1 = 'Registered', , ext_col_2 = '{username}'  where comp_id = '{comp_id}' ;"""
        db.execute(query_3)
        return redirect("/pending_complaints")

    else:
        query = f"SELECT acc_id, acc_name FROM crm.account_master where acc_id = '{id}' ;"
        accounts_df = db.get_row_as_dframe(query)
        accounts = accounts_df.to_dict(orient='records')

        return render_template("insert_work.html", accounts=accounts, id=id, comp_id=comp_id)



@app.route("/assign_work/<id>/<comp_id>", methods=["GET", "POST"])
@login_required
def assign_work(id,comp_id):
    username = session['username']
    if request.method == "POST":
        work_id = request.form.get('work_id')
        query_3 = f""" update chd.query_table set p_id = '{work_id}', ext_col_1 = 'Registered', ext_col_2 = '{username}'   where comp_id = '{comp_id}' ;"""
        db.execute(query_3)
        return redirect("/pending_complaints")

    get_work_query = f""" select work_id, acc_id, work_name, cont_id, billing_date, camc_war_s_date,
    camc_war_e_date, amc_s_date, amc_e_date, cost, location, remarks, work_status, enable_credit
    from crm.work_master where acc_id = '{id}' ;"""
    get_work_data = db.get_row_as_dframe(get_work_query)

    return render_template('assign_work.html', get_work_data=get_work_data, id=id, comp_id=comp_id)


if __name__ == "__main__":
    app.run(host='192.168.0.16', port=5022, debug=True)


