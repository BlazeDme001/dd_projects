from flask import Flask, request, render_template, redirect, url_for, send_file, session, make_response, jsonify,flash, send_from_directory
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
# import plotly.graph_objs as go
import json
import pandas as pd

app = Flask(__name__)
app.secret_key = '1234567890'

logging.basicConfig(filename='isp_data.log',
                    format='%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class User:
    def __init__(self, user_id, name, email, mobile, profile, department,username):
        self.user_id = user_id
        self.name = name
        self.username = username
        self.email = email
        self.mobile = mobile
        self.profile = profile
        self.department = department

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def authenticate(username, password):
    # query = """SELECT user_id, name, email, mobile, profile, department FROM isp.office_user WHERE (email = %s OR mobile = %s) and pass_key = %s and status = 'ACTIVE' ; """
    query = """select ud.user_id, ud."name", ud.email, ud.mobile, uac.profile, ud.team, ud.username
        from ums.user_app_connect uac left join ums.user_details ud on uac.user_id = ud.user_id 
        where (ud.mobile = %s or email = %s or ud.username = %s) and ud.status = 'ACTIVE'
        and ud."password" = %s and uac.app_id = 'A-2' and uac.ext_col_1 = 'ACTIVE'; """
    params = [username, username, username, password]
    result = db.get_data_in_list_of_tuple(query, params)
    if result:
        user_data = result[0]
        user = User(user_data[0], user_data[1], user_data[2], user_data[3], user_data[4], user_data[5], user_data[6])
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
            session['user_id'] = user.user_id
            session['name'] = user.name
            session['username'] = user.username
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

@app.route('/products')
@login_required
def products():
    query = """
    SELECT prod_id, name, description, serial_no, mac_no, type, sub_type, created_time, created_by
    FROM isp.products;
    """
    products = db.get_data_in_list_of_tuple(query)
    return render_template('products.html', products=products)


@app.route('/insert_product', methods=['POST','GET'])
@login_required
def insert_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        serial_no = request.form['serial_no']
        mac_no = request.form['mac_no']
        type = request.form['type']
        sub_type = request.form['sub_type']
        quentity = request.form['quentity']

        mac_ids = mac_no.split(',')
        serial_ids = serial_no.split(',')
        for i in range(int(quentity)):
            check_prod_query = 'select prod_id from isp.products order by id desc limit 1; '
            check_prod_data = db.get_data_in_list_of_tuple(check_prod_query)
            new_id = 'P-1'
            if check_prod_data:
                new_id = 'P-' + str(int(check_prod_data[0][0].split("P-")[-1]) + 1)

            insert_query = """
            INSERT INTO isp.products (prod_id, name, description, serial_no, mac_no, type, sub_type, created_time, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, now(), %s)
            """
            params = [new_id, name, description, serial_ids[i], mac_ids[i], type, sub_type, session['username']]

            db.execute(insert_query, params)
        return redirect(url_for('products'))
    return render_template('insert_product.html')


@app.route('/update_product/<string:prod_id>', methods=['GET', 'POST'])
@login_required
def update_product(prod_id):
    if request.method == 'POST':
        # name = request.form['name']
        description = request.form['description']
        serial_no = request.form['serial_no']
        mac_no = request.form['mac_no']
        type = request.form['type']
        sub_type = request.form['sub_type']

        # Update Product Details
        update_product_query = f"""
        UPDATE isp.products
        SET description = '{description}',
            serial_no = '{serial_no}',
            mac_no = '{mac_no}',
            type = '{type}',
            sub_type = '{sub_type}'
        WHERE prod_id = '{prod_id}';
        """
        db.execute(update_product_query)

        return redirect(url_for('products'))

    # Fetch existing product details for pre-filling the form
    query = f"""
    SELECT name, description, serial_no, mac_no, type, sub_type
    FROM isp.products
    WHERE prod_id = '{prod_id}';
    """
    product_data = db.get_data_in_list_of_tuple(query)

    return render_template('update_product.html', product_data=product_data[0], prod_id=prod_id)


@app.route('/isp_details')
@login_required
def isp_details():
    query = """ select p.isp_id , i.name as isp_name, p.name as plan_name, p.amnt,
            p.net_spped , p.duration , p.status , p.ext_col_1, p.created_by, p.created_time, p.id
            from isp.isp_plans as p left join isp.isp_details i on p.isp_id = i.isp_id ; """
    isp = db.get_data_in_list_of_tuple(query)
    return render_template('isp_details.html', isp=isp)


@app.route('/insert_isp', methods=['GET', 'POST'])
@login_required
def insert_isp():
    if request.method == 'POST':
        isp_name = request.form.get('isp_name')
        plan_name = request.form.get('plan_name')
        amnt = request.form['amnt']
        amnt2 = request.form['amnt2']
        net_speed = request.form['net_speed']
        net_speed2 = request.form['net_speed2']
        duration = request.form.get('duration')
        # status = request.form.get('status')
        features = request.form.get('features')

        check_isp_present_query = f""" select isp_id from isp.isp_details where name = '{isp_name}'; """
        check_isp_present_data = db.get_data_in_list_of_tuple(check_isp_present_query)
        
        if check_isp_present_data:
            new_id = check_isp_present_data[0][0]
        else:
            check_isp_query = 'select isp_id from isp.isp_details order by id desc limit 1; '
            check_isp_data = db.get_data_in_list_of_tuple(check_isp_query)
            new_id = 'ISP-1'
            if check_isp_data:
                new_id = 'ISP-' + str(int(check_isp_data[0][0].split("ISP-")[-1]) + 1)

            ins_isp_details = f""" insert into isp.isp_details (isp_id, name, created_by, created_time) 
            values ('{new_id}', '{isp_name}', '{session['username']}', now()) ; """

            db.execute(ins_isp_details)

        ins_isp_plans = f""" insert into isp.isp_plans (isp_id , name, amnt, net_spped,
                        duration , status , ext_col_1, created_by, created_time) values ('{new_id}', '{plan_name}',
                        '{str(amnt)+' '+str(amnt2)}', '{str(net_speed)+' '+str(net_speed2)}', '{duration}',
                        'ACTIVE', '{features}', '{session['username']}', now()) ;"""

        db.execute(ins_isp_plans)

        return redirect(url_for('isp_details'))

    return render_template('insert_isp.html')


@app.route('/update_isp/<string:isp_id>/<string:p_id>', methods=['GET', 'POST'])
@login_required
def update_isp(isp_id, p_id):
    if request.method == 'POST':
        plan_name = request.form.get('plan_name')
        amnt = request.form['amnt']
        amnt2 = request.form['amnt2']
        net_speed = request.form['net_speed']
        net_speed2 = request.form['net_speed2']
        duration = request.form.get('duration')
        features = request.form.get('features')

        update_isp_plans = f"""
        UPDATE isp.isp_plans 
        SET name = '{plan_name}',
            amnt = '{str(amnt) + ' ' + str(amnt2)}',
            net_spped = '{str(net_speed) + ' ' + str(net_speed2)}',
            duration = '{duration}',
            ext_col_1 = '{features}'
        WHERE isp_id = '{isp_id}' and id = '{p_id}';
        """
        db.execute(update_isp_plans)

        return redirect(url_for('isp_details'))

    # Fetch existing ISP details for pre-filling the form
    query = f"""SELECT i.name as isp_name, p.name as plan_name, p.amnt, p.net_spped, 
                    p.duration, p.ext_col_1, p.id
                FROM isp.isp_plans as p 
                LEFT JOIN isp.isp_details i ON p.isp_id = i.isp_id
                WHERE p.isp_id = '{isp_id}' and p.id = '{p_id}' ;
            """
    isp_data = db.get_data_in_list_of_tuple(query)

    return render_template('update_isp.html', isp_data=isp_data[0], isp_id=isp_id, p_id=p_id)



@app.route('/pending_verification')
@login_required
def pending_verification():
    query = """ select cust_id, cust_name,isp_name,plan ,amount ,status, created_time 
    from isp.cust_isp_details cid where status in ('Pending Verification', 'Pending Verification - Payment', 'Pending Verification - DOC') ; """
    pending_ver = db.get_data_in_list_of_tuple(query)
    return render_template('pending_verification.html', pending_ver=pending_ver)


@app.route('/view_details/<cust_id>', methods=['GET','POST'])
@login_required
def view_details(cust_id):
    get_cust_query = f""" SELECT cust_id, cust_name, isp_name, plan, amount, status, created_time,
                                    payment_done, folder_path, prod_id
                         FROM isp.cust_isp_details cid
                         WHERE cust_id = '{cust_id}' ; """
    get_cust_data = db.get_data_in_list_of_tuple(get_cust_query)[0]
    
    cust_details_query = f""" select cust_id , ph , email , flat_no , tower_no , apartment_name 
                            from isp.user_details WHERE cust_id = '{cust_id}' ; """
    cust_details_data = db.get_data_in_list_of_tuple(cust_details_query)[0]
    
    plan_details_query = f""" SELECT isp_id, "name", amnt, net_spped, duration, status, ext_col_1
                              FROM isp.isp_plans
                              WHERE id = '{get_cust_data[3].split('-')[0]}' ; """
    plan_details_data = db.get_data_in_list_of_tuple(plan_details_query)

    prod_details_query = f""" select prod_id, name, description , serial_no , mac_no , type from isp.products """

    prod_details_data = db.get_row_as_dframe(prod_details_query)

    filtered_rows = prod_details_data[prod_details_data['prod_id'] == get_cust_data[9]]
    matching_data = pd.DataFrame([])
    if not filtered_rows.empty:
        # Access the matching rows
        matching_data = filtered_rows.iloc[0]  # Assuming you want the first matching row

    prod_names = []
    for _,row in prod_details_data.iterrows():
        prod_names.append(row['name'])

    unique_product_names = set(prod_names)

    folder_path = os.path.join('/mnt/isp')
    try:
        for path in get_cust_data[8].split('/'):
            if path:
                folder_path = os.path.join(folder_path, path)
        files_list = [file for file in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, file))]
    except:
        files_list = ''
        
    # print(folder_path)
    if request.method == 'POST':
        if 'update_payment_status' in request.form:
            payment_status = request.form.get('payment_status','')
            doc_status = request.form.get('doc_status','')
            status='Pending Verification'
            if payment_status == 'true' and doc_status == 'true':
                status='Pending Product Allocation'
            elif payment_status == 'true' and doc_status == 'false':
                status = 'Pending Verification - DOC'
            elif  payment_status == 'false' and doc_status=='true':
                status='Pending Verification - Payment'
            update_status = f""" update isp.cust_isp_details set status='{status}' where  cust_id='{cust_id}'; """
            db.execute(update_status)
            return redirect(url_for('pending_verification'))
        elif 'Allocate_Product' in request.form:
            pass
            prod_name = request.form.get('product_name')
            prod_type = request.form.get('product_type')
            prod_mac = request.form.get('mac_no')
            prod_serial = request.form.get('serial_no')
            
            select_prod_query = f""" select prod_id name, description , serial_no , mac_no , type 
                                from isp.products where name = '{prod_name}' and serial_no = '{prod_serial}'
                                and mac_no = '{prod_mac}' and type = '{prod_type}'; """
            select_prod_data = db.get_data_in_list_of_tuple(select_prod_query)
            prod_id = ''
            if select_prod_data:
                prod_id = select_prod_data[0][0]

            update_product_query = f""" update isp.cust_isp_details set prod_id = '{prod_id}' where cust_id='{cust_id}'; """
            db.execute(update_product_query)
            return redirect(url_for('pending_prod'))

    return render_template("view_details.html", cust_data=get_cust_data, 
                           plan_details_data=plan_details_data, cust_details_data=cust_details_data,
                           folder_path=folder_path.replace('/','@@'),files_list=files_list, 
                           current_assigned_prod=matching_data, uniqueProductNames=unique_product_names,
                           prod_details_data=prod_details_data.to_dict(orient='records'))


@app.route('/pending_prod')
@login_required
def pending_prod():
    query = """ select cust_id, cust_name,isp_name,plan ,amount ,status, created_time 
    from isp.cust_isp_details cid where status in ('Pending Product Allocation') ; """
    pending_prod = db.get_data_in_list_of_tuple(query)
    return render_template('pending_prod.html', pending_prod=pending_prod)




@app.route('/download_file/<folder_path>/<file_name>')
def download_file(folder_path, file_name):
    # Assuming files are stored in a folder named 'downloads' under folder_path
    file_path = os.path.join(folder_path.replace('@@','/'), file_name)
    print(file_path)
    # return send_from_directory(file_path, file_name, as_attachment=True)
    return send_file(file_path, as_attachment=False)

if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='192.168.0.16', port=5027, debug=True)