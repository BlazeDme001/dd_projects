from flask import Flask, request, render_template, redirect, url_for, session
import os
from werkzeug.utils import secure_filename
import paramiko
import db_connect as db
import requests
import logging
from tempfile import NamedTemporaryFile
import smtplib
from email.mime.text import MIMEText
from functools import wraps
import datetime
import mail
import pandas as pd
import send_wp

app = Flask(__name__)
app.secret_key = '1234567890'

logging.basicConfig(filename='ums_data.log',
                    format='%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class User:
    def __init__(self, user_id, name, user_name, mobile, email, profile, team):
        self.user_id = user_id
        self.name = name
        self.user_name = user_name
        self.email = email
        self.mobile = mobile
        self.profile = profile
        self.department = team

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def authenticate(identifier, password):
    query = """SELECT user_id, name, username, mobile, email, profile, team FROM ums.user_details WHERE (email = %s OR mobile = %s OR username = %s) and password = %s and status = 'ACTIVE' and profile = 'SUPER ADMIN'; """
    params = [identifier, identifier, identifier, password]
    result = db.get_data_in_list_of_tuple(query, params)
    if result:
        user_data = result[0]
        user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6])
        return user
    return None


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        identifier = request.form['identifier']
        password = request.form['password']
        user = authenticate(identifier, password)
        if user:
            session['logged_in'] = True
            session['user_id'] = user.user_id
            session['name'] = user.name
            session['user_name'] = user.user_name
            session['email'] = user.email
            session['mobile'] = user.mobile
            session['profile'] = user.profile
            session['department'] = user.department
            return redirect(url_for('dashboard'))
        return render_template('login.html', error=True)
    return render_template('login.html', error=False)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html')


@app.route('/all_app', methods=['GET'])
@login_required
def all_app():
    app_query = f""" select * from ums.app_data; """
    app_data = db.get_data_in_list_of_tuple(app_query)
    return render_template('all_app.html', app_data=app_data)


@app.route('/view_details/<id>', methods=['GET'])
@login_required
def view_details(id):
    user_data = pd.DataFrame([])
    app_data = pd.DataFrame([])
    # user_app_query = f""" select user_id,name,username,app_id,app_name,ext_col_1,profile from ums.user_app_connect where """
    user_app_query = f""" select uac.user_id,uac.name,uac.username,uac.app_id,uac.app_name,uac.ext_col_1,
                    uac.profile, concat('http://',ad.primary_ip,ad.login_url) as url  
                    from ums.user_app_connect uac left join ums.app_data ad on uac.app_id = ad.app_id 
                    where """
    print(user_app_query)
    if 'A' in id:
        app_query = f""" select * from ums.app_data where app_id = '{id}'; """
        app_data = db.get_row_as_dframe(app_query)
        user_app_query += f" uac.app_id = '{id}';"
    elif 'U' in id:
        user_query = f""" select * from ums.user_details where user_id = '{id}'; """
        user_data = db.get_row_as_dframe(user_query)
        user_app_query += f" uac.user_id = '{id}';"
    try:
        user_app_data = db.get_row_as_dframe(user_app_query)
    except:
        user_app_data = pd.DataFrame([])
    print(user_app_data)
    return render_template('view_details.html', app_data=app_data, user_data=user_data, user_app_data=user_app_data)


@app.route('/update_app_user/<id>', methods=['POST','GET'])
@login_required
def update_app_user(id):
    app_details,user_details,all_app_data,user_app_data,=None,None,None,None
    if 'A' in id:
        get_app_details_query = f""" select * from ums.app_data where app_id = '{id}'; """
        get_app_details_data = db.get_row_as_dframe(get_app_details_query)
        app_details = get_app_details_data.to_dict()
        if request.method == 'POST':
            updated_data = {
                'primary_ip': request.form['primary_ip'],
                'login_url': request.form['login_url'],
                'primary_table': request.form['primary_table'],
                'other_tables': request.form['other_tables'],
                'app_status': request.form['app_status'],
                'is_uploaded_github': request.form['is_uploaded_github'],
                'remarks': request.form['remarks'],
                'updated_by': session['user_name']
            }
            update_query = f"""UPDATE ums.app_data SET primary_ip = '{updated_data['primary_ip']}',
            login_url = '{updated_data['login_url']}', primary_table = '{updated_data['primary_table']}',
            other_tables = '{updated_data['other_tables']}',app_status = '{updated_data['app_status']}',
            is_uploaded_github = '{updated_data['is_uploaded_github']}',remarks = '{updated_data['remarks']}',
            updated_by = '{updated_data['updated_by']}', updated_time = now() where app_id = '{id}';"""
            db.execute(update_query)
            return redirect(url_for('view_details', id=id))
        return render_template('update_app_user.html', app_details=app_details, user_details=user_details,
                               all_app_data=all_app_data, user_app_data=user_app_data)

    elif 'U' in id:
        all_app_query = """ select app_id, app_name from ums.app_data ; """
        all_app_data = db.get_data_in_list_of_tuple(all_app_query)
        get_user_details_query = f""" select * from ums.user_details where user_id = '{id}'; """
        get_user_details_data = db.get_row_as_dframe(get_user_details_query)
        user_details = get_user_details_data.to_dict()
        user_app_query = f""" select app_id, app_name, profile, ext_col_1 from ums.user_app_connect where user_id = '{id}'; """
        user_app_data = db.get_data_in_list_of_tuple(user_app_query)
        if request.method == 'POST':
            updated_user_data = {
                "password": request.form['password'],
                "profile": request.form['profile'],
                "team": request.form['team'],
                "status": request.form['status'],
                "mobile": request.form['mobile'],
                "email": request.form['email']
            }
            update_user_query = f""" UPDATE ums.user_details set password = '{updated_user_data['password']}',
            profile = '{updated_user_data['profile']}', team = '{updated_user_data['team']}',
            status = '{updated_user_data['status']}', mobile = '{updated_user_data['mobile']}',
            email = '{updated_user_data['email']}' WHERE user_id = '{id}' ; """
            db.execute(update_user_query)

            if updated_user_data['status'] == 'INACTIVE':
                update_app_user_data_connect_query = f"""UPDATE ums.user_app_connect SET 
                                ext_col_1 = 'INACTIVE', updated_time = now(),
                                updated_by = '{session['user_name']}' WHERE user_id = '{id}' and 
                                ext_col_1 <> ''INACTIVE' ;"""
                db.execute(update_app_user_data_connect_query)
                remove_query = f"""UPDATE ums.user_app_connect SET 
                                        ext_col_1 = 'INACTIVE', updated_time = now(),
                                        updated_by = '{session['user_name']}' WHERE user_id = '{id}'"""
                db.execute(remove_query)
            elif updated_user_data['status'] == 'ACTIVE':
                apps_list = request.form.getlist('selected_apps[]')
                profile_list = request.form.getlist('profiles[]')
                remove_apps = []
                add_apps = []
                update_apps = []
                user_app_ids = [app[0] for app in user_app_data]
                for u_app_id in user_app_ids:
                    if u_app_id not in apps_list:
                        remove_apps.append(u_app_id)

                for app_id in apps_list:
                    if app_id not in user_app_ids:
                        add_apps.append(app_id)
                    elif app_id in user_app_ids:
                        update_apps.append(app_id)

                if remove_apps:
                    remove_query = f"""UPDATE ums.user_app_connect SET 
                                        ext_col_1 = 'INACTIVE', updated_time = now(),
                                        updated_by = '{session['user_name']}' WHERE user_id = '{id}' and 
                                        app_id in ({','.join([f"'{app}'" for app in remove_apps])});"""
                    db.execute(remove_query)
                for app in all_app_data:
                        if app[0] in add_apps:
                            profile = ''
                            for i in profile_list:
                                if app[0] in i:
                                    profile = i.split('&&')[0]
                                    break
                            insert_query_app_user = f""" INSERT INTO ums.user_app_connect 
                            (user_id,name,username,app_id,app_name, created_by, ext_col_1, profile)
                            values ('{id}','{user_details['name'][0]}','{user_details['username'][0]}','{app[0]}',
                            '{app[1]}','{session['user_name']}', 'ACTIVE', '{profile}') ; """
                            print(insert_query_app_user)
                            db.execute(insert_query_app_user)
                        if app[0] in update_apps:
                            profile = ''
                            for i in profile_list:
                                if app[0] in i:
                                    profile = i.split('&&')[0]
                                    break
                            print(profile)
                            update_query_app_user = f""" update ums.user_app_connect set ext_col_1 = 'ACTIVE',
                            profile = '{profile}', updated_time = now(), updated_by = '{session['user_name']}'
                            where app_id = '{app[0]}' and user_id = '{id}' ;"""
                            print(update_query_app_user)
                            db.execute(update_query_app_user)
            return redirect(url_for('view_details', id=id))
        profiles = ['ADMIN', 'USER', 'TRAIL']
        if session['profile'] == 'SUPER ADMIN':
            profiles.append('SUPER ADMIN')
        return render_template('update_app_user.html', app_details=app_details, 
                               user_details=user_details, all_app_data=all_app_data,
                               user_app_data=user_app_data, profiles=profiles)


@app.route('/all_user', methods=['GET'])
@login_required
def all_user():
    user_query = f""" select user_id, name, username, profile, mobile, email from ums.user_details; """
    users_data = db.get_data_in_list_of_tuple(user_query)
    return render_template('all_user.html', user_data=users_data)


def create_user_in_apps(ums_user_id,name, username, password, profile, \
                        team, status, mobile, email, apps, profiles):
    try:
        if not apps:
            return False
        isp_res, chd_res, crm_res, tender_res, tms_res = None, None, None, None, None
        app_id_list = []
        app_name_list = []
        pfl_list = []
        urls = []
        # app_query = "select app_id, app_name, concat(primary_ip,login_url) as urls from ums.app_data ad ;"
        # app_data = db.get_row_as_dframe(app_query)


        sub = 'User Login Details'
        body = f"""Hello {name},\n\nYour user id and passwords are listed below.\n\n"""
        for app in apps:
            app_id = app.split('@@')[0]
            app_name = app.split('@@')[1]
            if app_name == 'ISP Management System':
                for pfl in profiles:
                    if app_id in pfl:
                        pfl_list.append(pfl.split('&&')[0])
                app_id_list.append(app_id)
                app_name_list.append(app_name)
                # url = app_data[app_data['app_name'] == app_name].urls[0]
                # urls.append(url)
            elif app_name == 'Complaint Management System':
                for pfl in profiles:
                    if app_id in pfl:
                        pfl_list.append(pfl.split('&&')[0])
                app_id_list.append(app_id)
                app_name_list.append(app_name)
                # url = app_data[app_data['app_name'] == app_name].urls[0]
                # urls.append(url)
            elif app_name == 'Customer Management System':
                for pfl in profiles:
                    if app_id in pfl:
                        pfl_list.append(pfl.split('&&')[0])
                app_id_list.append(app_id)
                app_name_list.append(app_name)
                # url = app_data[app_data['app_name'] == app_name].urls[0]
                # urls.append(url)
            elif app_name == 'Tender Management System':
                for pfl in profiles:
                    if app_id in pfl:
                        pfl_list.append(pfl.split('&&')[0])
                app_id_list.append(app_id)
                app_name_list.append(app_name)
                # url = app_data[app_data['app_name'] == app_name].urls[0]
                # urls.append(url)
            elif app_name == 'Task Management System':
                for pfl in profiles:
                    if app_id in pfl:
                        pfl_list.append(pfl.split('&&')[0])
                app_id_list.append(app_id)
                app_name_list.append(app_name)
                # url = app_data[app_data['app_name'] == app_name].urls[0]
                # urls.append(url)
            elif app_name == 'User Managemnet System':
                for pfl in profiles:
                    if app_id in pfl:
                        pfl_list.append(pfl.split('&&')[0])
                app_id_list.append(app_id)
                app_name_list.append(app_name)
                # url = app_data[app_data['app_name'] == app_name].urls[0]
                # urls.append(url)
        # print(pfl_list)
        # print(app_id_list)
        # print(app_name_list)
        # print(name)
        body += f""" Login Details: \n Username: {username} \n Mobile: {mobile} \n Email: {email} \n Password: {password}"""
        # for i,j in zip(app_name_list,urls):
        #     body += f"""\n-------------------------\nPortal Name: {i}\nLogin Url: {j}\n-------------------------\n"""
        body += """\n\n\nThanks and Regards,\nUser Management BOT\n """
        print(body)
        to_add = [email]
        to_cc = ['ramit.shreenath@gmail.com', session['email']]
        mail.send_mail(to_add=to_add, to_cc=to_cc,sub=sub,body=body)
        send_wp.send_wp_msg(mob=mobile,msg=body)
        

        for appid,appname,app_pfl in zip(app_id_list,app_name_list,pfl_list):
            insert_query_app_user = f""" INSERT INTO ums.user_app_connect (user_id,name,username,app_id,app_name,created_by,ext_col_1,profile)
            values ('{ums_user_id}','{name}','{username}','{appid}','{appname}','{session['user_name']}', 'ACTIVE', '{app_pfl}') ; """
            db.execute(insert_query_app_user)
            # print(insert_query_app_user)
        return True
    except Exception as err:
        print(str(err))
        return False


@app.route('/add_user_or_app', methods=['GET','POST'])
@login_required
def add_user_or_app():
    error = ''
    get_app_query = """ select app_id, app_name from ums.app_data ; """
    get_app_data = db.get_data_in_list_of_tuple(get_app_query)
    if request.method == 'POST':
        type = request.form['type']
        if type == 'user':
            name = request.form['name']
            username = request.form['username']
            password = request.form['password']
            profile = request.form['profile']
            team = request.form['team']
            status = request.form['status']
            mobile = request.form.get('mobile').strip()
            email = request.form.get('email').strip()
            apps = request.form.getlist('appSelect')
            profiles = request.form.getlist('profiles[]')

            check_user_query = f""" select * from ums.user_details where mobile = '{mobile}'
                                or email = '{email}' or username = '{username}' ;"""
            check_user_data = db.get_data_in_list_of_tuple(check_user_query)
            if check_user_data:
                error = 'This user is already exist.'
            else:
                try:
                    check_user_id = f""" select user_id from ums.user_details order by id desc limit 1; """
                    old_user_id = db.get_data_in_list_of_tuple(check_user_id)[0][0]
                    new_user_id = f"U-{int(old_user_id.split('-')[1]) + 1}"
                except:
                    new_user_id = 'U-1'

                user_insert_query = f""" insert into ums.user_details (user_id, name, username, password, profile,
                                    team, status, mobile, email, created_by) values ('{new_user_id}', '{name}',
                                    '{username}', '{password}', '{profile}', '{team}', '{status}', '{mobile}',
                                    '{email}', '{session['user_name']}') """
                db.execute(user_insert_query)
                result = create_user_in_apps(new_user_id,name, username, password, profile, \
                                             team, status, mobile, email, apps, profiles)
                print(f'User app details insert: {"Sucess" if result else "Fail"}')


        elif type == 'app':
            app_name = request.form['appName']
            primary_ip = request.form['primaryIP']
            login_url = request.form['loginURL']
            primary_table = request.form['primaryTable']
            other_tables = request.form['otherTables']
            app_status = request.form['appStatus']
            is_uploaded_github = request.form['uploadedGitHub']
            remarks = request.form['remarks']

            try:
                check_app_id = f""" select app_id from ums.app_data order by id desc limit 1 ; """
                old_app_id = db.get_data_in_list_of_tuple(check_app_id)[0][0]
                new_app_id = f"A-{int(old_app_id.split('-')[1])+1}"
            except:
                new_app_id = 'A-1'

            app_insert_query = f""" insert into ums.app_data (app_id, app_name, primary_ip, login_url, primary_table,
                                other_tables, app_status, is_uploaded_github, remarks, created_by) values ('{new_app_id}',
                                '{app_name}', '{primary_ip}', '{login_url}', '{primary_table}', '{other_tables}',
                                '{app_status}', '{is_uploaded_github}','{remarks}', '{session['user_name']}') ;"""
            db.execute(app_insert_query)

    profile_list = ['ADMIN', 'USER', 'TRAIL']
    if session['profile'] == 'SUPER ADMIN':
        profile_list.append('SUPER ADMIN')
    return render_template('add_user_or_app.html', error=error, apps=get_app_data, profile_list=profile_list)


@app.route('/all_user_app_connect', methods=['GET','POST'])
@login_required
def all_user_app_connect():
    if request.method == 'POST':
        status = request.form.get('status_update')
        selected_rows = request.form.get('selected_rows').split(',') if 'selected_rows' in request.form else []
        print(status)
        print(selected_rows)
        if status and selected_rows:
            apps = []
            for row in selected_rows:
                print(row)
                user_id, app_id, app_name = row.split('@@')
                apps.append(f'{app_id}@@{app_name}')
                query = f"""UPDATE ums.user_app_connect SET ext_col_1 = '{status}', updated_time = now(), 
                updated_by = '{session['user_name']}' WHERE user_id = '{user_id}' AND app_id = '{app_id}';"""
                db.execute(query)
            return redirect('/all_user_app_connect')
    user_app_query = f""" select user_id,name,username,app_id,app_name, ext_col_1 from ums.user_app_connect ; """
    user_app_data = db.get_row_as_dframe(user_app_query)
    return render_template('user_app_connect.html', user_app_data=user_app_data)


if __name__ == '__main__':
    # app.run(debug=True)
    # app.run(host='192.168.2.37', port=5030, debug=True)
    app.run(host='0.0.0.0', port=5030, debug=True)
