from flask import Flask, render_template, request, redirect, jsonify, session, url_for
from functools import wraps
import db_connect as db
import logging
import random
import string
import datetime
import requests
import mail
import send_wp as wp

app = Flask(__name__)

logging.basicConfig(filename='crm_data.log',
                    format='%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app.secret_key = '1234567890'

class User:
    def __init__(self, username, profile, team, u_id):
        self.username = username
        self.profile = profile
        self.team = team
        self.u_id = u_id

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def authenticate(username, password):
    # query = "SELECT * FROM crm.user_details WHERE user_name = %s AND pass_word = %s and ext_col_2 = 'ACTIVE';"
    query = """select ud.username, uac.profile, ud.team, ud.user_id from ums.user_app_connect uac left join ums.user_details ud 
    on uac.user_id = ud.user_id where (ud.mobile = %s or ud.email = %s or ud.username = %s) and
    ud.status = 'ACTIVE' and ud."password" = %s and uac.app_id = 'A-4' and uac.ext_col_1 = 'ACTIVE';"""
    params = [username, username, username, password]
    result = db.get_data_in_list_of_tuple(query, params)
    if result:
        user = User(result[0][0],result[0][1], result[0][2], result[0][3])
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
            session['team'] = user.team
            session['profile'] = user.profile
            session['u_id'] = user.u_id
            session['users'] = get_all_user()
            return redirect(url_for('all_accounts', username=user.username))
        else:
            return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('home'))


def get_loc(long, lat):
    api_key = ''  # Replace with your OpenCage API key
    # api_key = 'f3203f8b6faa441a93ea2a587bf3db1a'  # Replace with your OpenCage API key
    url = f"https://api.opencagedata.com/geocode/v1/json?q={lat}+{long}&key={api_key}"
    response = requests.get(url)
    data = response.json()
    
    if data['results']:
        return data['results'][0]['formatted']
    else:
        return "Unknown Location"

@app.route('/attendance', methods=["GET", "POST"])
@login_required
def attendance():
    if request.method == 'POST':
        check_in = request.form.get("check_in", '')
        check_in_long = request.form.get("check_in_long", '')
        check_in_lat = request.form.get("check_in_lat", '')
        check_out = request.form.get("check_out", '')
        check_out_long = request.form.get("check_out_long", '')
        check_out_lat = request.form.get("check_out_lat", '')

        if check_in:
            loc = get_loc(check_in_long, check_in_lat)
            print(check_in_long)
            print(check_in_lat)
            print(loc)
            query = f"""
                INSERT INTO crm.attendence (u_id, type, check_time, long, lat, loc) 
                VALUES ('{session['u_id']}', 'CHECK IN', NOW(), '{check_in_long}', '{check_in_lat}', '{loc}');
            """
            db.execute(query)
        elif check_out:
            loc = get_loc(check_out_long, check_out_lat)
            print(check_out_long)
            print(check_out_lat)
            print(loc)
            query = f"""
                INSERT INTO crm.attendence (u_id, type, check_time, long, lat, loc) 
                VALUES ('{session['u_id']}', 'CHECK OUT', NOW(), '{check_out_long}', '{check_out_lat}', '{loc}');
            """
            db.execute(query)

        return redirect(url_for('all_accounts', username=session['username']))

    return render_template('attendance.html')



def get_all_user():
    users = ''
    user_name = session['username']
    profile = session['profile']
    team = session['team']
    get_user_query = """select ud.username from ums.user_app_connect uac left join ums.user_details ud 
    on uac.user_id = ud.user_id where ud.status = 'ACTIVE' and uac.app_id = 'A-4' and uac.ext_col_1 = 'ACTIVE' """
    if profile == 'ADMIN':
        get_user_query += f""" and uac.profile in ('ADMIN','USER') and ud.team = '{team}'; """
    elif profile == 'USER':
        get_user_query += f""" and ud.username = '{user_name}' ; """


    get_user_data = db.get_data_in_list_of_tuple(get_user_query)
    if get_user_data:
        if len(get_user_data) > 1:
            users = ','.join([i[0] for i in get_user_data])
        else:
            users = get_user_data[0][0]
    return users


def generate_password(length=8):
    characters = string.ascii_letters + string.digits + string.punctuation
    password = ''.join(random.choice(characters) for _ in range(length))
    return password

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
        if phone and email:
            query = f"SELECT COUNT(*) FROM crm.account_master WHERE contact_phone = '{phone}' OR contact_email = '{email}';"
        elif phone:
            query = f"SELECT COUNT(*) FROM crm.account_master WHERE contact_phone = '{phone}' ;"
        elif email:
            query = f"SELECT COUNT(*) FROM crm.account_master WHERE contact_email = '{email}' ;"
        result = db.get_data_in_list_of_tuple(query)
        return result[0][0] > 0
    elif table == 'contact':
        query = f"SELECT COUNT(*) FROM crm.contact_master WHERE cont_phone = '{phone}' OR cont_email = '{email}'"
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
                                                    contact_name, contact_phone, contact_email, catagory, added_by, created_time, enable_credit)
                    VALUES ('{data_dict["acc_id"]}', '{data_dict["acc_name"]}', '{data_dict["GST_No"]}', '{data_dict["street"]}',
                    '{data_dict["city"]}', '{data_dict["state"]}', '{data_dict["country"]}', '{data_dict["pincode"]}', '{data_dict["contact_name"]}',
                    '{data_dict["contact_phone"]}', '{data_dict["contact_email"]}', '{data_dict["catagory"]}', '{data_dict["username"]}',
                    LOCALTIMESTAMP, '{data_dict['enable_credit']}') ;"""
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

@app.route("/insert_account", methods=["GET", "POST"])
@login_required
def insert_account():
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    if request.method == "POST":

        data_dict = {
                "acc_id": get_latest_id(accounts=True),
                "cont_id": get_latest_id(contacts=True),
                "acc_name": request.form.get("acc_name"),
                "GST_No": request.form.get("GST_No"),
                "street": request.form.get("street"),
                "city": request.form.get("city"),
                "state": request.form.get("state"),
                "country": request.form.get("country"),
                "pincode": request.form.get("pincode"),
                "contact_name": request.form.get("contact_name"),
                "contact_phone": request.form.get("contact_phone"),
                "contact_email": request.form.get("contact_email"),
                "catagory": request.form.get("catagory"),
                "to_day": to_day,
                "new_pass": generate_password(),
                "username": username,
                "enable_credit": request.form.get('enable_credit')
        }

        acc_create = create_acc(data_dict)
        # # Check if the phone number or email already exists
        # if is_duplicate('account', data_dict['contact_phone'], data_dict['contact_email']):
        #     return "Error: The phone number or email already exists in the database."
        # # to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
        # # Insert data into the database
        # query = f"""INSERT INTO crm.account_master (acc_id, acc_name, gst_no, street, city, state, country, pincode,
        #                                             contact_name, contact_phone, contact_email, catagory, added_by, created_time)
        #             VALUES ('{data_dict["acc_id"]}', '{data_dict["acc_name"]}', '{data_dict["GST_No"]}', '{data_dict["street"]}', '{data_dict["city"]}', '{data_dict["state"]}', '{data_dict["country"]}',
        #                     '{data_dict["pincode"]}', '{data_dict["contact_name"]}', '{data_dict["contact_phone"]}', '{data_dict["contact_email"]}', '{data_dict["catagory"]}', '{data_dict["username"]}', '{data_dict["to_day"]}') ;"""
        # db.execute(query)

        # # cont_id = get_latest_contact_id()
        # # cont_id = get_latest_id(contacts=True)
        # is_master = 'Yes'
        # # Insert data into the contact_master table
        # query_contact = f"""INSERT INTO crm.contact_master (cont_id, acc_id, cont_name, cont_phone, cont_email, is_master, added_by, created_time)
        #             VALUES ('{data_dict["cont_id"]}', '{data_dict["acc_id"]}', '{data_dict["contact_name"]}', '{data_dict["contact_phone"]}', '{data_dict["contact_email"]}', '{data_dict["is_master"]}', '{data_dict["username"]}', '{data_dict["to_day"]}') ;"""
        # db.execute(query_contact)

        # # new_pass = generate_password()

        # query_cont_pass = f"""INSERT into chd.user_passkey_details (c_id, c_name, passkey, mobile_no, email_id, created_date) 
        # values ('{data_dict["acc_id"]}', '{data_dict["acc_name"]}', '{data_dict["new_pass"]}', '{data_dict["contact_phone"]}', '{data_dict["contact_email"]}', '{data_dict["to_day"]}')"""
        # db.execute(query_cont_pass)
        if acc_create == True:
            return redirect("/accounts")
        return render_template("insert_account.html")
    return render_template("insert_account.html")

@app.route("/accounts")
@login_required
def all_accounts():
    query = f"SELECT * FROM crm.account_master "
    if session['users'] and session['profile'] not in ('SUPER ADMIN', 'ADMIN'):
        all_users = session['users'].split(',')
        query += f" where owner in {tuple(all_users)} " if all_users and len(all_users) > 1 else f" where owner = {all_users} "
        
    accounts_df = db.get_row_as_dframe(query)
    try:
        accounts = accounts_df.to_dict(orient='records')
    except:
        accounts = {}
    return render_template("accounts.html", accounts=accounts, query=query, users=session['users'])


@app.route("/edit_account/<acc_id>", methods=["GET", "POST"])
@login_required
def edit_account(acc_id):
    if request.method == "POST":
        # Get form data
        acc_name = request.form.get("acc_name")
        GST_No = request.form.get("GST_No")
        street = request.form.get("street")
        city = request.form.get("city")
        state = request.form.get("state")
        country = request.form.get("country")
        pincode = request.form.get("pincode")
        contact_name = request.form.get("contact_name")
        contact_phone = request.form.get("contact_phone")
        contact_email = request.form.get("contact_email")
        catagory = request.form.get("catagory")
        enable_credit = request.form.get("enable_credit")

        # Update data in the database
        query = f"""UPDATE crm.account_master
                    SET acc_name = '{acc_name}', gst_no = '{GST_No}', street = '{street}', city = '{city}',
                        state = '{state}', country = '{country}', pincode = '{pincode}', contact_name = '{contact_name}',
                        contact_phone = '{contact_phone}', contact_email = '{contact_email}', catagory = '{catagory}',
                        enable_credit = '{enable_credit}'
                    WHERE acc_id = '{acc_id}'"""
        db.execute(query)

        return redirect("/accounts")

    # Get account details from the database to pre-fill the form
    query = f"SELECT * FROM crm.account_master WHERE acc_id = '{acc_id}'"
    account_df = db.get_row_as_dframe(query)
    account = account_df.to_dict(orient='records')[0]

    return render_template("edit_account.html", account=account)

# Contacts ===============================================================

# def get_latest_contact_id():
#     query = "SELECT cont_id FROM crm.contact_master ORDER BY cont_id DESC LIMIT 1"
#     result = db.get_data_in_list_of_tuple(query)
#     if result:
#         last_contact_id = result[0][0]
#         new_contact_number = int(last_contact_id[4:]) + 1
#         new_contact_id = f"CONT{new_contact_number:04}"
#         return new_contact_id
#     else:
#         return "CONT0001"

@app.route("/insert_contact", methods=["GET", "POST"])
@login_required
def insert_contact():
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    if request.method == "POST":
        # Get form data
        acc_id = request.form.get("acc_id")
        # cont_id = get_latest_contact_id()
        cont_id = get_latest_id(contacts=True)
        cont_name = request.form.get("cont_name")
        cont_phone = request.form.get("cont_phone")
        cont_email = request.form.get("cont_email")

        # Check if the contact ID already exists
        query = f"SELECT COUNT(*) FROM crm.contact_master WHERE cont_id = '{cont_id}'"
        result = db.get_data_in_list_of_tuple(query)
        if result[0][0] > 0:
            return "Error: The contact ID already exists in the database."
        is_master = 'No'
        # Insert data into the database
        query = f"""INSERT INTO crm.contact_master (cont_id, acc_id, cont_name, cont_phone, cont_email, is_master, added_by, created_time)
                    VALUES ('{cont_id}', '{acc_id}', '{cont_name}', '{cont_phone}', '{cont_email}', '{is_master}', '{username}', '{to_day}')"""
        db.execute(query)

        return redirect(f"/contacts/{acc_id}")

    # Get all account IDs and names from the database
    query = "SELECT acc_id, acc_name FROM crm.account_master"
    # accounts = db.get_data_in_list_of_tuple(query)
    accounts_df = db.get_row_as_dframe(query)
    accounts = accounts_df.to_dict(orient='records')
    # account_name = accounts_df['acc_name'].tolist()

    return render_template("insert_contact.html", accounts=accounts)


@app.route("/contacts")
@app.route("/contacts/<account_id>")
@login_required
def all_contacts(account_id=None):
    if account_id:
        contacts_df = db.get_row_as_dframe(f"SELECT * FROM crm.contact_master WHERE acc_id = '{account_id}'")
    else:
        contacts_df = db.get_row_as_dframe("SELECT * FROM crm.contact_master")

    contacts = contacts_df.to_dict(orient='records')
    return render_template("contacts.html", contacts=contacts)


@app.route("/edit_contact/<cus_id>", methods=["GET", "POST"])
@login_required
def edit_contact(cus_id):
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    # Get contacts details from the database to pre-fill the form
    query = f"SELECT * FROM crm.contact_master WHERE cont_id = '{cus_id}'"
    cont_df = db.get_row_as_dframe(query)
    cont = cont_df.to_dict(orient='records')[0]
    acc_id = cont['acc_id']
    if request.method == "POST":

        cont_phone = request.form.get("contact_phone")
        cont_email = request.form.get("contact_email")

        # Update data in the database
        query = f"""UPDATE crm.contact_master
                    SET cont_phone = '{cont_phone}', cont_email = '{cont_email}', updated_by = '{username}', updated_time = '{to_day}'
                    WHERE cont_id = '{cus_id}'"""
        db.execute(query)

        return redirect(f"/contacts/{acc_id}")


    return render_template("edit_contact.html", cont=cont)


# Work ====================================================================
# def get_latest_work_id():
#     query = "SELECT work_id FROM crm.work_master ORDER BY work_id DESC LIMIT 1"
#     result = db.get_data_in_list_of_tuple(query)
#     if result:
#         last_work_id = result[0][0]
#         new_work_number = int(last_work_id[5:]) + 1
#         new_work_id = f"WORK{new_work_number:04}"
#         return new_work_id
#     else:
#         return "WORK0001"

@app.route("/insert_work_details", methods=["GET", "POST"])
@login_required
def insert_work_details():
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    today_date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    if request.method == "POST":
        # Get form data
        acc_id = request.form.get("acc_id").split('-', maxsplit=1)[0].strip()
        acc_name = request.form.get("acc_id").split('-', maxsplit=1)[1].strip()
        work_name = request.form.get('work_name').replace("'","''")
        # contact_id = request.form.get("contact_id")
        work_status = request.form.get("work_status")
        # billing_date = ''
        # camc_warranty_start_date = ''
        # camc_warranty_end_date = ''
        # if work_status == 'Completed':
        billing_date = request.form.get("billing_date",'')
        camc_warranty_start_date = request.form.get("camc_warranty_start_date",'')
        camc_warranty_end_date = request.form.get("camc_warranty_end_date",'')
        amc_start_date = request.form.get("amc_start_date",'')
        amc_end_date = request.form.get("amc_end_date",'')
        cost = request.form.get("cost")
        location = request.form.get("location")
        remarks = request.form.get("remarks").replace("'","''")
        # enable_credit = request.form.get("enable_credit")

        contact_id = None
        c_ph = None
        c_email = None

        # Generate new work ID
        # work_id = get_latest_work_id()
        work_id = get_latest_id(work=True)
        query = f"""select cont_id, cont_phone, cont_email from CRM.contact_master cm  where acc_id = '{acc_id.strip()}' and is_master in 'Yes';"""
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
                                                remarks, work_status, added_by, created_time)
                    VALUES ('{work_id}', '{acc_id}', '{work_name}', '{contact_id}', '{billing_date}', '{camc_warranty_start_date}',
                            '{camc_warranty_end_date}', '{amc_start_date}', '{amc_end_date}', '{cost}', '{location}',
                            '{remarks}', '{work_status}', '{username}', '{to_day}')"""
        db.execute(query)
        logger.info(query)
        query_2 = f"""INSERT INTO chd.cust_product_table (c_id, c_name, mobile_no, email_id, p_id, p_name, p_desc, p_bill_date, warranty_start_date, warranty_end_date, amc_start_date, amc_end_date, created_date) 
        VALUES ('{acc_id}', '{acc_name}', '{c_ph}', '{c_email}', '{work_id}', '{work_name}', '{remarks}', '{billing_date}', '{camc_warranty_start_date}', '{camc_warranty_end_date}', '{amc_start_date}', '{amc_end_date}', '{today_date}') """
        db.execute(query_2)
        return redirect("/work")

    else:
        query = "SELECT acc_id, acc_name FROM crm.account_master"
        # accounts = db.get_data_in_list_of_tuple(query)
        accounts_df = db.get_row_as_dframe(query)
        accounts = accounts_df.to_dict(orient='records')
        return render_template("insert_work.html", accounts=accounts)


@app.route("/work")
@app.route("/work/<account_id>")
@app.route("/work/<account_id>/<contact_id>")
@login_required
def all_work(account_id=None, contact_id=None):
    if contact_id:
        work_data_df = db.get_row_as_dframe(f"SELECT * FROM crm.work_master WHERE cont_id = '{contact_id}'")
    elif account_id:
        work_data_df = db.get_row_as_dframe(f"SELECT * FROM crm.work_master WHERE acc_id = '{account_id}'")
    else:
        work_data_df = db.get_row_as_dframe("SELECT * FROM crm.work_master")

    work_data = work_data_df.to_dict(orient='records')
    return render_template("work.html", work_data=work_data)


@app.route("/edit_work_details/<string:work_id>", methods=["GET", "POST"])
@login_required
def edit_work_details(work_id):
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    today_date = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    if request.method == "POST":
        work_name = request.form.get('work_name').replace("'","''")
        billing_date = request.form.get("billing_date")
        camc_warranty_start_date = request.form.get("camc_warranty_start_date")
        camc_warranty_end_date = request.form.get("camc_warranty_end_date")
        amc_start_date = request.form.get("amc_start_date")
        amc_end_date = request.form.get("amc_end_date")
        cost = request.form.get("cost")
        location = request.form.get("location")
        remarks = request.form.get("remarks").replace("'","''")
        work_status = request.form.get("work_status")
        # enable_credit = request.form.get("enable_credit")

        contact_id = None

        # Check if the work ID exists in the database
        existing_work = get_work_by_id(work_id)
        if not existing_work:
            return "Error: The work ID does not exist in the database."

        # query = f"""select cont_id, cont_phone, cont_email from CRM.contact_master cm  where acc_id = '{acc_id.strip()}' and is_master = 'Yes';"""
        # c_data = db.get_data_in_list_of_tuple(query)
        # if c_data:
        #     contact_id = c_data[0][0]
        #     c_ph = c_data[0][1]
        #     c_email = c_data[0][2]
        # Update data in the database
        query = f"""UPDATE crm.work_master
                    SET work_name = '{work_name}',
                        billing_date = '{billing_date}',
                        camc_war_s_date = '{camc_warranty_start_date}',
                        camc_war_e_date = '{camc_warranty_end_date}',
                        amc_s_date = '{amc_start_date}',
                        amc_e_date = '{amc_end_date}',
                        cost = '{cost}',
                        location = '{location}',
                        remarks = '{remarks}',
                        work_status = '{work_status}'
                    WHERE work_id = '{work_id}' ;"""
        # return query
        db.execute(query)

        query_2 = f"""UPDATE chd.cust_product_table
                    SET p_name = '{work_name}',
                        p_desc = '{remarks}',
                        p_bill_date = '{billing_date}',
                        warranty_start_date = '{camc_warranty_start_date}',
                        warranty_end_date = '{camc_warranty_end_date}',
                        amc_start_date = '{amc_start_date}',
                        amc_end_date = '{amc_end_date}'
                    WHERE p_id = '{work_id}' ;"""
        db.execute(query_2)

        return redirect("/work")

    else:

        # Get the work information to populate the form
        work_info = get_work_by_id(work_id)
        if not work_info:
            return "Error: The work ID does not exist in the database."
        # Get all account IDs and names from the database
        query = f"SELECT acc_id, acc_name FROM crm.account_master where acc_id = '{work_info['acc_id']}' ;"
        accounts_df = db.get_row_as_dframe(query)
        accounts = accounts_df.to_dict(orient='records')

        return render_template("edit_work.html", work=work_info, accounts=accounts)


def get_work_by_id(work_id):
    query = f"SELECT * FROM crm.work_master WHERE work_id = '{work_id}'"
    result = db.get_data_in_list_of_tuple(query)
    if result:
        work_data = result[0]
        work_info = {
            "work_id": work_data[1],
            "acc_id": work_data[4],
            "work_name": work_data[2],
            "cont_id": work_data[3],
            "billing_date": work_data[8],
            "camc_war_s_date": work_data[9],
            "camc_war_e_date": work_data[10],
            "amc_s_date": work_data[11],
            "amc_e_date": work_data[12],
            "cost": work_data[6],
            "location": work_data[7],
            "remarks": work_data[13],
            "work_status": work_data[5],
            "enable_credit": work_data[20],
            "added_by": work_data[14],
            "created_time": work_data[15]
        }
        return work_info
    else:
        return None


@app.route("/leads")
@login_required
def all_leads():
    leads_df = db.get_row_as_dframe("""select lead_id ,lead_name , concat(street,', ',city,', ',state,', ',country,', ',pincode) as address, 
    contact_name , concat(contact_phone,', ',contact_phone_2) as contact_phone , contact_email , status , "owner" , remarks  from crm.leads_master  ;""")
    if session['users'] and session['profile'] != 'SUPER ADMIN':
        all_users = session['users'].split(',')
        query += f" where owner in {tuple(all_users)} " if all_users and len(all_users) > 1 else f" where owner = {all_users} "

    leads = leads_df.to_dict(orient='records')
    message = request.args.get('message')
    return render_template("leads.html", leads=leads, message=message)


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


@app.route("/insert_leads", methods=["GET", "POST"])
@login_required
def insert_leads():
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    get_user_query = """select ud.username from ums.user_app_connect uac left join ums.user_details ud 
    on uac.user_id = ud.user_id where ud.status = 'ACTIVE' and uac.app_id = 'A-4' and uac.ext_col_1 = 'ACTIVE';"""
    try:
        get_user_data = db.get_data_in_list_of_tuple(get_user_query)
    except:
        get_user_data = []
    if request.method == "POST":
        # Retrieve lead information from the form
        lead_name = request.form.get("lead_name").strip()
        street = request.form.get("street")
        # state = request.form.get("state")
        # country = request.form.get("country")
        pincode = request.form.get("pincode")
        c_name = request.form.get("c_name")
        phone = request.form.get("phone").strip()
        phone1 = request.form.get("phone1")
        email = request.form.get("email")
        scheduled_time = request.form.get("scheduled_time")
        remarks = request.form.get("remarks").replace("'","''")
        owner = request.form.get('owner')
        
        catagory = request.form.get('catagory')
        source = request.form.get("source")

        act_source = source

        if source == 'Reference':
            ref = request.form.get("reference")
            act_source = source + '-' + ref
        elif  source == 'Others':
            others = request.form.get("others")
            act_source = source + '-' + others

        if is_duplicate('leads', phone, email):
            return "Error: The phone number or email already exists in the database."

        state_country_data = get_state_country(pincode.strip())

        if state_country_data[0] == 'S':
            state = state_country_data[1]
            country = state_country_data[2]
            city = state_country_data[3]
        else:
            state = country = city = ''

        # user_query = f"""select ext_col_1 from crm.user_details where user_name = '{username}' ;"""
        # user_data = db.get_data_in_list_of_tuple(user_query)[0][0]

        lead_id = get_latest_id(leads=True)

        # Insert lead data into the database
        query = f""" INSERT INTO crm.leads_master (lead_id, lead_name, street, city, state, country, pincode, contact_name,
        contact_phone, contact_phone_2, contact_email, scheduled_time, remarks, status, source, owner, added_by, created_time,catagory)
        VALUES ('{lead_id}','{lead_name}','{street}','{city}','{state}','{country}','{pincode}','{c_name}','{phone}', '{phone1}',
        '{email}','{str(scheduled_time).replace("T"," ")}','{remarks}','OPEN','{act_source}','{owner}','{username}','{to_day}', '{catagory}') ;"""
        # VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ;"""
        # values = (lead_id, lead_name, street, city, state, country, pincode, c_name, phone, email, str(scheduled_time).replace("T", " "), remarks, 'NEW', source, user_data, user_data, to_day)
        logger.info(query)
        db.execute(query)

        # Redirect to the page displaying all leads or a success page
        return redirect(url_for("all_leads"))

    # If it's a GET request, render the form
    return render_template("insert_leads.html",get_user_data=get_user_data)


@app.route("/edit_leads/<lead_id>", methods=["GET", "POST"])
@login_required
def edit_leads(lead_id):
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    
    if request.method == "POST":
        c_name = request.form.get("c_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        scheduled_time = request.form.get("scheduled_time")
        remarks = request.form.get("remarks").replace("'","''")
        gst_no = request.form.get('gst')


        # user_query = f"""select ext_col_1 from crm.user_details where user_name = '{username}' ;"""
        # user_data = db.get_data_in_list_of_tuple(user_query)[0][0]

        # Update lead data in the database
        query = """UPDATE crm.leads_master
        SET contact_name = %s, contact_phone = %s, contact_email = %s,
        scheduled_time = %s, remarks = %s,updated_by = %s, updated_time = %s
        WHERE lead_id = %s """
        values = (c_name, phone, email, str(scheduled_time.replace("T", " ")), remarks, username, to_day, str(lead_id))
        db.execute(query, values)


        # Redirect to the page displaying all leads or a success page
        return redirect(url_for("all_leads"))

    # If it's a GET request, retrieve the current lead data and render the form
    lead_query = f"SELECT * FROM crm.leads_master WHERE lead_id = '{str(lead_id)}' ;"
    logger.info(lead_query)
    lead_data_df = db.get_row_as_dframe(lead_query)
    lead_data = lead_data_df.to_dict(orient='records')
    return render_template("edit_leads.html", lead=lead_data[0])


@app.route("/update_leads_status/<id>", methods=["GET", "POST"])
@login_required
def update_leads_status(id):
    username = session['username']
    if request.method == "POST":
        status = request.form.get("status")
        remarks = request.form.get("remarks").replace("'","''")
        quoteAmt = request.form.get('quoteAmt','')
        quoteId = request.form.get('quoteId','')
        is_quore = 'YES' if quoteId or quoteAmt else 'NO'
        owner = request.form.get('owner','')

        to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")

        query = """UPDATE crm.leads_master SET status = %s, remarks = %s, updated_by = %s, updated_time = %s,
        owner = %s, is_quote_send = %s, latest_quote_id = %s, total_quote_send = %s WHERE lead_id = %s """
        values = (status, remarks, username, to_day, owner, is_quore, quoteId, quoteAmt, str(id))
        db.execute(query, values)

        l_query = f"SELECT lead_name, street, city, state, country, pincode, contact_name, contact_phone, contact_email FROM crm.leads_master WHERE lead_id = '{str(id)}' ;"
        l_data = db.get_data_in_list_of_tuple(l_query)

        if status == "DONE":
            gst_no = request.form.get('gst','')
            data_dict = {
                "acc_id": get_latest_id(accounts=True),
                "cont_id": get_latest_id(contacts=True),
                "acc_name": l_data[0][0],
                "GST_No": gst_no,
                "street": l_data[0][1],
                "city": l_data[0][2],
                "state": l_data[0][3],
                "country": l_data[0][4],
                "pincode": l_data[0][5],
                "contact_name": l_data[0][6],
                "contact_phone": l_data[0][7],
                "contact_email": l_data[0][8],
                "catagory": 'NEW',
                "to_day": to_day,
                "new_pass": generate_password(),
                "username": username
            }
            acc = create_acc(data_dict)
            if acc != True:
                return render_template("update_leads_status.html", leads_data=get_leads_data, error='Account is already present')
        
    
    get_leads_query = f""" select * from crm.leads_master where lead_id = '{id}'; """
    get_leads_data = db.get_row_as_dframe(get_leads_query)
    
    get_user_query = """select ud.username from ums.user_app_connect uac left join ums.user_details ud 
    on uac.user_id = ud.user_id where ud.status = 'ACTIVE' and uac.app_id = 'A-4' and uac.ext_col_1 = 'ACTIVE';"""
    try:
        get_user_data = db.get_data_in_list_of_tuple(get_user_query)
    except:
        get_user_data = []

    lead_hist_query = f""" select lead_name, status, "owner" , remarks, updated_by , updated_time, change_timestamp 
                            from crm.leads_master_history where lead_id = '{id}' ; """
    lead_hist_data = db.get_row_as_dframe(lead_hist_query)

    return render_template("update_leads_status.html", leads_data=get_leads_data, get_user_data=get_user_data, error='', lead_hist_data=lead_hist_data)


@app.route("/create_com/<acc_id>", methods=["GET", "POST"])
@login_required
def create_com(acc_id):
    username = session.get('identifier')

    # get_cust_query = f"""select acc_id, cont_phone, cont_email, cont_name from crm.contact_master cm  where acc_id = '{acc_id}' ;"""
    # data_cont = db.get_row_as_dframe(get_cust_query)
    
    # default_assign = 'Neeraj Kanwar'

    if request.method == 'POST':
        # Process the form data here
        # customer_id = session['username']
        product = request.form['product_name']
        if product == 'N_R':
            # # Handle additional fields for "Not showing here" option
            # product_txt = request.form['product_name_txt']
            # location = request.form['location']
            # is_in_warranty = request.form['is_in_warranty'].replace('not_sure', 'Not Sure')
            # work_type = request.form['work_type']
            # query_complaint = request.form['query_complaint']

            # created_date = datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
            # check_comp = f""" select id from chd.work_form order by sl_no desc limit 1 """
            # print(check_comp)
            # check_comp_data = db.get_data_in_list_of_tuple(check_comp)
            # print(check_comp_data)
            # old_comp_id = 'T-1'
            # if check_comp_data:
            #     old_comp_id = check_comp_data[0][0] if check_comp_data[0] else 'T-1'
            #     numaric_part = int(old_comp_id.split('-')[1])
            #     new_numaric_part = int(numaric_part) + 1
            #     new_comp_id = old_comp_id[:2] + f'{new_numaric_part}'
            # c_id = new_comp_id if check_comp_data else old_comp_id
            # new_comp_id = new_comp_id if check_comp_data else old_comp_id
            # session['com_id'] = c_id
            # c_name = session['user_name']
            # mobile = session['user_mob_no']
            # email = session['user_email']
            # insert_query_1 = """INSERT INTO chd.work_form (id, name, mob_no, email, work_type, location, is_in_warranty, remarks, work_name) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);"""
            # para = (c_id, c_name, mobile, email, work_type, location, is_in_warranty, query_complaint, product_txt)
            # print(insert_query_1)
            # db.execute(insert_query_1,para)

            # insert_query_2 = f"""INSERT INTO chd.query_table (comp_id, c_id, c_name, mobile_no , email_id , p_id , p_name ,in_warranty , complaint, complaint_status , created_date, assign_to, assign_date, ext_col_1)
            # VALUES ('{new_comp_id}', '000', '{c_name}', '{mobile}', '{email}', '', '{product_txt}', '{is_in_warranty}','{query_complaint}', 'OPEN','{created_date}','{default_assign}', LOCALTIMESTAMP, 'Not Registered' ) ON CONFLICT DO NOTHING;"""

            # # insert_query = f"""INSERT INTO chd.query_table (comp_id, otp, c_id, c_name, mobile_no , email_id , p_id , p_name ,in_warranty , in_amc, complaint, complaint_status , is_reopen , reopen_times , created_date, ex_work_id, ex_work_price, assign_to, assign_date)
            # # VALUES ('{new_comp_id}', '{c_id}', '{c_name}', '{mobile}', '{email}', '{product_id}', '{product_name}', '{warranty}', '{amc}', '{query_complaint}', '{comp_status}', '{is_reopen}', '{reopen_times}', '{created_date}', '{ex_work_id}', '{ex_work_price}', '{default_assign}', now()) ON CONFLICT DO NOTHING;"""
            # print(insert_query_2)
            # db.execute(insert_query_2)
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
            product_details_query = f"""SELECT * FROM chd.cust_product_table WHERE c_id = '{acc_id}' AND p_id = '{product_id.strip()}';"""
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
            otp = '0000'
            comp_status = 'OPEN'
            is_reopen = 'NO'
            reopen_times = '0'
            created_date = datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
            check_comp = f""" select comp_id from chd.query_table order by id desc limit 1 """
            check_comp_data = db.get_data_in_list_of_tuple(check_comp)
            old_comp_id = 'C-1'
            if check_comp_data:
                old_comp_id = check_comp_data[0][0] if check_comp_data[0] else 'C-1'
                numaric_part = int(old_comp_id.split('-')[1])
                new_numaric_part = numaric_part+1
                new_comp_id = old_comp_id[:2] + f'{new_numaric_part}'
            new_comp_id = new_comp_id if check_comp_data else old_comp_id
            # session['com_id'] = new_comp_id
            # default_assign = 'Neeraj Kanwar'
            # Insert data into the respective table
            insert_query = f"""INSERT INTO chd.query_table (comp_id, otp, c_id, c_name, mobile_no , email_id , p_id , p_name ,in_warranty , in_amc, complaint, complaint_status , is_reopen , reopen_times , created_date, ex_work_id, ex_work_price, assign_to, assign_date, ext_col_1)
            VALUES ('{new_comp_id}', {int(otp)}, '{c_id}', '{c_name}', '{mobile}', '{email}', '{product_id}', '{product_name}', '{warranty}', '{amc}', '{query_complaint}', '{comp_status}', '{is_reopen}', '{reopen_times}', '{created_date}', '{ex_work_id}', '{ex_work_price}', 'Not Assigned', LOCALTIMESTAMP, 'Registered' ) ON CONFLICT DO NOTHING;"""

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
            if template_query_data[i][2] == 'whatsapp':
                if template_query_data[i][3] == 'New complaint to customer':
                    try:
                        wp.send_wp_msg(mobile, template_query_data[i][1].format(c_name, new_comp_id, query_complaint,'', mobile, ''))
                    except:
                        pass
                    # wp.send_wp_msg('6283287351', template_query_data[i][1].format(c_name, new_comp_id, query_complaint,'', mobile, ''))
                elif template_query_data[i][3] == 'New complaint to manager':
                    # wp.send_wp_msg('7347008010', template_query_data[i][1].format(default_assign, new_comp_id, query_complaint,'', mobile, ''))
                    # wp.send_msg_in_group(template_query_data[i][1].format('Ashish Gupta', new_comp_id, query_complaint,'', mobile, ''))
                    wp.send_msg_in_group(group_id='120363287511346467@g.us', msg=template_query_data[i][1].format('Team', new_comp_id, query_complaint, location, mobile, remarks))
                    # wp.send_msg_in_group(msg=f'This is testing comp... Please ignore. comp_id: {new_comp_id}')
                    # send_wp.send_wp_msg('6283287351', template_query_data[i][1].format(default_assign, new_comp_id, query_complaint,'', mobile, ''))

        return redirect(url_for('all_accounts'))


    # query = f"""SELECT * FROM chd.cust_product_table WHERE c_id = '{get_acc_id}' ORDER BY id DESC; """
    query = f"""SELECT c_id, c_name, street , city , state , pincode , p_id, p_name , p_desc , p_bill_date ,
            warranty_start_date , warranty_end_date , amc_start_date , amc_end_date
            FROM chd.cust_product_table WHERE c_id = '{acc_id}' ORDER BY id DESC; """

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
            print(warranty_e_date)

            amc_e_date = datetime.datetime.strptime(item['amc_end_date'], "%Y-%m-%d") if item['amc_end_date'] and item['amc_end_date'] != 'None' else None
            print(amc_e_date)

            # warranty_e_date = item[9].strftime("%Y-%m-%d") if item[9] else None
            print(warranty_e_date)
            # amc_e_date = item[11].strftime("%Y-%m-%d") if item[11] else None
            # amc_e_date = datetime.datetime.strftime("%Y-%m-%d") if item['amc_end_date'] and item['amc_end_date'] != 'None' else None
            print(amc_e_date)
            current_date = datetime.datetime.now()
            if warranty_e_date and warranty_e_date >= current_date:
                warranty = '(In warranty)'
            if amc_e_date and amc_e_date >= current_date:
                warranty = '(In warranty)'
            product_names.append(f'{p_id} - {p_name} - {warranty}')
            location_names.append(f'{street}, {city}, {state}, {pincode}')
            c_name = item['c_id']
        c_id = acc_id
        return render_template('create_complaint.html', products=product_names, loc=location_names, c_id=c_id, c_name=c_name, ex_work=ex_work_data)
    return render_template('create_complaint.html', products=[], c_id=None, c_name=None, ex_work=ex_work_data)


def delete_details(type,id):
    cur_dt = datetime.datetime.now().strftime('%d-%b-%Y %H:%M:%S')
    if type == 'Leads':
        table = 'leads_master'
        col = 'lead_id'
    elif type == 'Account':
        table = 'account_master'
        col = 'acc_id'
        remarks = f'''The account of {id} is deleted by {session['username']} at {cur_dt} '''
        update_query_cont_table = f""" update crm.contact_master set acc_id = 'ACC0000', updated_by = 'CRM Portal',
                        updated_time = '{cur_dt}', ext_col_1 = '{remarks}' where acc_id = '{id}'; """
        db.execute(update_query_cont_table)
        update_query_work_table = f""" update crm.work_master set acc_id = 'ACC0000', updated_by = 'CRM Portal',
                        updated_time = '{cur_dt}', ext_col_1 = '{remarks}' where acc_id = '{id}'; """
        db.execute(update_query_work_table)
    elif type == 'Contact':
        table = 'contact_master'
        col = 'cont_id'
    elif type == 'Work':
        table = 'work_master'
        col = 'work_id'


    query = f""" DELETE FROM crm.{table} where {col} = '{id}' ; """
    print(query)
    if session['u_id'] in ('U-1', 'U-2') or session['profile'] == 'SUPER ADMIN':
        res = db.execute(query)
        sub = f'Delete in CRM ID: {id}'
        body = f""" Hi all,\n\nA record is deleted. Details are follows,\n\nType: DELETE\nForm:{type}\nTable:{table}\nDeleted by:{session['username']}\n\n\nThanks,\nCRM BOT """
        if res:
            mail.send_mail(to_add=['ramit.shreenath@gmail.com'], to_cc=[], sub=sub, body=body)
            return 'Successfuly delete the record'
        return 'Error while deleting the record'
    else:
        return 'You do not have the permission for delete. Please connect with Admin'


@app.route('/delete/<table_name>/<item_id>', methods=['DELETE'])
@login_required
def delete_item(table_name, item_id):
    # Validate table_name to ensure it's a valid table (security measure)
    valid_tables = ['Leads', 'Account', 'Contact', 'Work']
    if table_name not in valid_tables:
        response = jsonify({'message': 'Invalid table name'})
        response.status_code = 400
        return response

    message = delete_details(table_name, item_id)  # Assuming delete_details function is available
    response = jsonify({'message': message})
    response.status_code = 200 if "Successfully" in message else 400
    return response


if __name__ == "__main__":
    # app.run(host='192.168.0.16', port=5020, debug=True)
    app.run(host='192.168.0.16', port=5020, debug=True)


