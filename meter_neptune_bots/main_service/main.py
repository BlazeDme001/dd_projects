from flask import Flask, jsonify, render_template, request, redirect, url_for, session
import db_connect as db
from functools import wraps
import mail
import requests
import json


app = Flask(__name__)
app.secret_key = 'nirwana7301'


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        check_query = f"""select name, username, mobile, profile from ums.user_details ud 
        where (mobile = '{username}' or email = '{username}' or username = '{username}') 
        and password = '{password}' and status = 'ACTIVE' and username in ('RamitC','AshishG') ;"""
        # print(check_query)
        user = db.get_data_in_list_of_tuple(check_query)

        if user:
            session['user'] = username
            session['name'] = user[0][0]
            session['mobile'] = user[0][2]
            session['email'] = user[0][3]
            return redirect(url_for('home'))
        else:
            return render_template('login.html', error='Invalid Credentials')
    
    return render_template('login.html')


@app.route('/main', methods=['GET', 'POST'])
@login_required
def home():
    check_query = """SELECT id, project, sub_project, service, status, insert_date, update_date, ext_col_1 FROM services.services;"""
    check_data = db.get_data_in_list_of_tuple(check_query)

    check_user_query = f""" select req_bal from meter_api.meter_user_details where status = 'Active' limit 1 ; """
    check_user_data = db.get_data_in_list_of_tuple(check_user_query)
    cur_min_bal = '0'
    if check_user_data:
        cur_min_bal = check_user_data[0][0]

    if request.method == 'POST':
        for service in check_data:
            service_id = service[0]
            new_status = request.form.get(f'status_{service_id}')
            check_time = request.form.get(f'check_time_{service_id}')
            min_bal = request.form.get(f'min_bal_{service_id}')
            print(f"{min_bal} -- {service_id}")
            update_fields = []
            
            # If status changed, add it to the update query
            if new_status and new_status != service[4]:
                update_fields.append(f"status = '{new_status}'")

            # If min_balance is provided, update it
            if check_time:
                update_fields.append(f"ext_col_1 = '{check_time}'")

            # Execute update query if there are changes
            if update_fields:
                update_query = f""" UPDATE services.services SET {', '.join(update_fields)}, 
                update_by = '{session["user"]}', update_date = NOW() WHERE id = '{service_id}'; """
                print(update_query)
                db.execute(update_query)
            if min_bal:
                update_user_query = f""" update meter_api.meter_user_details set req_bal = '{min_bal}' where STATUS = 'Active' ;"""
                db.execute(update_user_query)

        return redirect(url_for('home'))
    return render_template('main.html', services=check_data, cur_min_bal=cur_min_bal)


@app.route('/logout')
@login_required
def logout():
    session.pop('user', None)
    session.pop('name', None)
    session.pop('mobile', None)
    session.pop('email', None)
    return redirect(url_for('login'))


# ==============================================================================================================
@app.route('/api/services', methods=['POST'])
def get_services():
    user = False
    data = request.get_json()  # Get JSON data from request body
    username = data.get("username")
    password = data.get("password")
    project = data.get("project")
    sub_project = data.get("sub_project")
    service = data.get("service")

    # Authenticate user
    if username == 'Nirwana_API' and password == 'Qn@62':
        user = True

    if not user:
        return jsonify({"error": "Invalid Credentials"}), 401

    # Fetch services data if authentication succeeds
    check_query = f""" SELECT id, status, ext_col_1 FROM services.services where project = '{project}'
                    and sub_project = '{sub_project}' and service = '{service}' ;"""
    check_data = db.get_data_in_list_of_tuple(check_query)
    services_list = [
            {
                "id": row[0],
                "status": row[1],
                "check_time": str(row[2]) if row[2] else '30'
            }
        for row in check_data
    ]

    return jsonify({"services": services_list})


@app.route('/api/receive_data', methods=['POST'])
def receive_meter_user_data():
    try:
        data = request.get_json()  # Get JSON request body
        if not data or 'meter_users' not in data:
            return jsonify({"error": "Invalid or missing data"}), 400

        meter_users = data['meter_users']
        if not isinstance(meter_users, list):
            return jsonify({"error": "Invalid format"}), 400

        updated_records = []
        inserted_records = []

        for user in meter_users:
            # Check if the record already exists
            check_query = f""" SELECT ca_no, device_sl_no, customer_name, customer_address, mobile, email, 
                       power_mode, op_blance, pv_blance, recharge, status, last_update_date, remarks 
                FROM meter_neptune.meter_user_data WHERE device_sl_no = '{user["device_sl_no"]}'; """
            existing_data = db.get_data_in_list_of_tuple(check_query)

            if existing_data:
                # Extract existing record
                existing_record = existing_data[0]

                # Check for mismatch
                received_values = (
                    user["ca_no"], user["device_sl_no"], user["customer_name"], user["customer_address"],
                    user["mobile"], user["email"], user["power_mode"], user["op_blance"], user["pv_blance"],
                    user["recharge"], user["status"], user["last_update_date"], user["remarks"]
                )
                if received_values == existing_record:
                    continue
                elif received_values != existing_record:
                    # If mismatch found, update the record
                    update_query = f"""
                        UPDATE meter_neptune.meter_user_data SET ca_no = '{user["ca_no"]}'
                        customer_name = '{user["customer_name"]}', customer_address = '{user["customer_address"]}',
                        mobile = '{user["mobile"]}', email = '{user["email"]}', power_mode = '{user["power_mode"]}', 
                        op_blance = '{user["op_blance"]}', pv_blance = '{user["pv_blance"]}', recharge = '{user["recharge"]}', 
                        status = '{user["status"]}', last_update_date = '{user["last_update_date"]}', update_date = NOW(), 
                        update_by = '{user["update_by"]}', remarks = '{user["remarks"]}', main_db = '{user["main_db"]}', 
                        ext_col_1 = '{user["ext_col_1"]}', ext_col_2 = '{user["ext_col_2"]}'
                        WHERE device_sl_no = '{user["device_sl_no"]}' ;"""
                    db.execute(update_query)
                    updated_records.append(user["device_sl_no"])  # Keep track of updated records

            else:
                # Insert new record if not found
                insert_query = f"""
                    INSERT INTO meter_neptune.meter_user_data 
                    (ca_no, device_sl_no, customer_name, customer_address, mobile, email, power_mode, 
                    op_blance, pv_blance, recharge, status, last_update_date, insert_date, insert_by, 
                    update_date, update_by, remarks, main_db, ext_col_1, ext_col_2)
                    VALUES 
                    ('{user["ca_no"]}', '{user["device_sl_no"]}', '{user["customer_name"]}', 
                    '{user["customer_address"]}', '{user["mobile"]}', '{user["email"]}', 
                    '{user["power_mode"]}', '{user["op_blance"]}', '{user["pv_blance"]}', 
                    '{user["recharge"]}', '{user["status"]}', '{user["last_update_date"]}', 
                    NOW(), '{user["insert_by"]}', NOW(), '{user["update_by"]}', '{user["remarks"]}', 
                    '{user["main_db"]}', '{user["ext_col_1"]}', '{user["ext_col_2"]}')
                """
                db.execute(insert_query)
                inserted_records.append(user["device_sl_no"])  # Keep track of inserted records

        if inserted_records or updated_records:
            to_add = ['ramit.shreenath@gmail.com']
            to_cc = []
            sub = 'Neptune DB backup'
            body = f""" Hello Ramit,\nBelow are the list of records updated or inserted.
            \n\nInserted: {''.join(inserted_records)} \n\nUpdated: {''.join(updated_records)}\n\nThanks """
            mail.send_mail(to_add=to_add, to_cc=to_cc, sub=sub, body=body)

        return jsonify({
            "message": "Data processed successfully",
            "inserted": inserted_records,
            "updated": updated_records
        }), 200

    except Exception as e:
        return jsonify({"error": "Failed to process data", "details": str(e)}), 500


if __name__ == '__main__':
    # app.run(host='0.0.0.0', port=5023, debug=True)
    app.run(host='0.0.0.0', port=5025, debug=True)
