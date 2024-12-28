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

app = Flask(__name__)

logging.basicConfig(filename='crm_data.log',
                    format='%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app.secret_key = '1234567890'

class User:
    def __init__(self, username, password, profile):
        self.username = username
        self.password = password
        self.profile = profile

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def authenticate(username, password):
    query = "SELECT name, passkey, profile FROM chd.office_passkey_details WHERE (mobile_no = %s or email_id = %s) AND passkey = %s AND status = 'ACTIVE' "
    params = [username, username, password]
    result = db.get_data_in_list_of_tuple(query, params)
    if result:
        user_data = result[0]
        user = User(user_data[0], user_data[1], user_data[2])
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
            # return 'Successfuly login'
            # return redirect(url_for('all_complaint'))
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

def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(len(length)))
    return password


@app.route('/all_complaint')
@login_required
def all_complaint():
    query = """select * from chd.query_table order by id desc"""
    c_data = db.get_row_as_dframe(query)
    return render_template('complaints.html', c_data=c_data)


@app.route('/complaint_details/<comp_id>')
@login_required
def complaint_details(comp_id):
    query = f"""
        SELECT comp_id, c_id, c_name, mobile_no, email_id, p_id, p_name, in_warranty,
               in_amc, assign_to, assign_date, complaint, complaint_status,
               complaint_remarks, complaint_review_by, work_rating, engineer_rating,
               is_reopen, reopen_date, reopen_times, ext_col_1
        FROM chd.query_table
        WHERE comp_id = '{comp_id}';"""
    # params = [comp_id]
    df = db.get_row_as_dframe(query)
    # Convert DataFrame to dictionary
    result = df.to_dict(orient='records')[0] if not df.empty else {}
    return render_template('complaint_details.html', complaint=result, type='lead')


@app.route('/update_work_details/<comp_id>', methods=['GET', 'POST'])
@login_required
def update_work_details(comp_id):
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

        user_details_query = """SELECT name FROM chd.office_passkey_details where ext_col_1 = 'ACTIVE' """
        if session['profile'] == 'user':
            assign_to = []
        if session['profile'] == 'super_admin':
            assign_to = [item[0] for item in db.get_data_in_list_of_tuple(user_details_query)]
        if session['profile'] == 'admin':
            user_details_query += f""" and profile IN ('{session['profile']}', 'user')"""
            assign_to = [item[0] for item in db.get_data_in_list_of_tuple(user_details_query)]

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
    selected_complaint = None
    default_assign = 'Lakhwinder Singh'
    if request.method == 'POST':
        form_type = request.form.get('form_type')
        if form_type == 'complaint':
            selected_comp_id = request.form.get('comp_id')
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
                logger.info(selected_complaint)
            except:
                selected_complaint = []
        elif form_type == 'update':
            selected_comp_id = request.form.get('comp_id_1')
            updated_status = request.form.get('complaint_status')
            updated_assign_to = request.form.get('assign_to')
            schedule_date = request.form.get('schedule_date')
            complaint_remarks = request.form.get('remarks')

            check_query_assign = f"""SELECT assign_to, complaint_status FROM chd.query_table_history
                    WHERE comp_id = '{selected_comp_id}' ;"""
            check_query_assign_data = db.get_data_in_list_of_tuple(check_query_assign)
            try:
                old_assign_to = check_query_assign_data[0][0]
                old_status = check_query_assign_data[1][0]
            except:
                old_assign_to = ''
                old_status = ''

            mail_query = f"""select mobile_no ,email_id, name from chd.office_passkey_details where id = '{updated_assign_to}';"""
            mail_data = db.get_data_in_list_of_tuple(mail_query)

            # Update the database with the new status and assign_to values
            update_query = f"""UPDATE chd.query_table SET complaint_status = '{updated_status}' """ 
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
                logger.info(selected_complaint)
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

            if old_assign_to != updated_assign_to:
                if old_status != updated_status:
                    if updated_status == 'Closed - Work Done':
                        # For JOB done/closed
                        body_wp = template_dict_wp['Job Completed To Customer'].format(selected_complaint['c_name'], selected_complaint['complaint_remarks'])
                        send_wp.send_wp_msg(selected_complaint['mobile_no'], body_wp)
                        mail.send_mail(to_add=selected_complaint['email_id'], to_cc=[], sub='Complaint Resolved', body=body_wp)
                        body_wp = template_dict_wp['Job Completed To Manager'].format(default_assign, selected_complaint['c_id'], session['username'], selected_complaint['complaint_remarks'], selected_complaint['c_id'], selected_complaint['complaint'], selected_complaint['c_name'])
                        send_wp.send_wp_msg('7347008010', body_wp)
                        mail.send_mail(to_add='installation@shreenathgroup.in', to_cc=[], sub='Complaint Resolved', body=body_wp)
                    else:
                        body_wp = template_dict_wp['Status Update To Customer'].format(selected_complaint['c_name'], selected_complaint['complaint_status'], selected_complaint['complaint_remarks'])
                        send_wp.send_wp_msg(selected_complaint['mobile_no'], body_wp)
                        mail.send_mail(to_add=selected_complaint['email_id'], to_cc=[], sub='Complaint Status Update', body=body_wp)
                        body_wp = template_dict_wp['Status Update To Manager'].format(default_assign, selected_complaint['c_id'], selected_complaint['complaint_status'], session['username'], selected_complaint['complaint_remarks'], selected_complaint['c_id'], selected_complaint['complaint'], selected_complaint['c_name'])
                        send_wp.send_wp_msg('7347008010', body_wp)
                        mail.send_mail(to_add='installation@shreenathgroup.in', to_cc=[], sub='Complaint Status Update', body=body_wp)
                else:
                    body_wp = template_dict_wp['Complaint assign to customer'].format(selected_complaint['c_name'], mail_data[0][2], mail_data[0][2], mail_data[0][0], mail_data[0][1])
                    send_wp.send_wp_msg(selected_complaint['mobile_no'], body_wp)
                    mail.send_mail(to_add=selected_complaint['email_id'], to_cc=[], sub='Complaint Assigned', body=body_wp)
                    body_wp = template_dict_wp['Complaint Assigned To Executive'].format(mail_data[0][2], selected_complaint['c_id'], selected_complaint['complaint'], '', selected_complaint['mobile_no'], selected_complaint['complaint_remarks'])
                    send_wp.send_wp_msg(mail_data[0][0], body_wp)       
                    mail.send_mail(to_add=mail_data[0][1], to_cc=[], sub='Complaint Assigned', body=body_wp)

    else:
        selected_complaint = None

    user_details_query = """SELECT name, id FROM chd.office_passkey_details where ext_col_1 = 'ACTIVE'"""
    if session['profile'] == 'user':
        assign_to = []
    if session['profile'] == 'super_admin':
        assign_to = db.get_data_in_list_of_tuple(user_details_query)
    if session['profile'] == 'admin':
        user_details_query += f""" and profile IN ('{session['profile']}', 'user') ;"""
        assign_to = db.get_data_in_list_of_tuple(user_details_query)

    # assign_query = f"""select "name", id from chd.office_passkey_details; """
    # assign_list = db.get_data_in_list_of_tuple(assign_query)

    pending_query = """SELECT comp_id FROM chd.query_table WHERE complaint_status not in ('Cancelld - By Customer', 'Cancelld - By Us', 'Closed - Work Done', 'Closed - Work Not Done');"""

    pending_df = db.get_row_as_dframe(pending_query)
    complaints_list = pending_df.to_dict(orient='records') if not pending_df.empty else {}

    return render_template('pending_complaints.html', complaints=complaints_list, selected_complaint=selected_complaint, assign_list=assign_to)


@app.route('/complaint_details_field/<comp_id>')
def complaint_details_field(comp_id):
    query = f"""
        SELECT comp_id, c_id, c_name, mobile_no, email_id, p_id, p_name, in_warranty,
               in_amc, assign_lead, assign_to, assign_date, complaint, complaint_status,
               complaint_remarks, complaint_review_by, work_rating, engineer_rating,
               is_reopen, reopen_date, reopen_times
        FROM chd.query_table
        WHERE comp_id = '{comp_id}';"""
    # params = [comp_id]
    df = db.get_row_as_dframe(query)
    # Convert DataFrame to dictionary
    result = df.to_dict(orient='records')[0] if not df.empty else {}
    return render_template('complaint_details.html', complaint=result, type='field')




if __name__ == "__main__":
    app.run(host='192.168.0.16', port=5022, debug=True)


