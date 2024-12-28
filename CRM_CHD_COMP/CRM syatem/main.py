from flask import Flask, render_template, request, redirect, jsonify, session, url_for
from functools import wraps
import db_connect as db
import logging
import random
import string
import datetime

app = Flask(__name__)

logging.basicConfig(filename='crm_data.log',
                    format='%(asctime)s - Line:%(lineno)s - %(levelname)s ::=> %(message)s',
                    filemode='w')

logger = logging.getLogger()
logger.setLevel(logging.INFO)

app.secret_key = '1234567890'

class User:
    def __init__(self, username, password):
        self.username = username
        self.password = password

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function


def authenticate(username, password):
    query = "SELECT * FROM crm.user_details WHERE user_name = %s AND pass_word = %s and ext_col_2 = 'ACTIVE';"
    params = [username, password]
    result = db.get_data_in_list_of_tuple(query, params)
    if result:
        user_data = result[0]
        user = User(user_data[1], user_data[2])
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
            # return 'Successfuly login'
            return redirect(url_for('all_accounts', username=user.username))
        else:
            return render_template('login.html', error=True)
    return render_template('login.html', error=False)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('home'))


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
            new_work_number = int(last_work_id[5:]) + 1
            new_work_id = f"LEAD{new_work_number:04}"
            return new_work_id
        else:
            return "LEAD0001"
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
        query = f"SELECT COUNT(*) FROM crm.account_master WHERE contact_phone = '{phone}' OR contact_email = '{email}'"
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
                "username": username
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
        if acc_create:
            return redirect("/accounts")
        return render_template("insert_account.html")
    return render_template("insert_account.html")

@app.route("/accounts")
@login_required
def all_accounts():
    accounts_df = db.get_row_as_dframe("SELECT * FROM crm.account_master")
    accounts = accounts_df.to_dict(orient='records')
    return render_template("accounts.html", accounts=accounts)


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

        # Update data in the database
        query = f"""UPDATE crm.account_master
                    SET acc_name = '{acc_name}', gst_no = '{GST_No}', street = '{street}', city = '{city}',
                        state = '{state}', country = '{country}', pincode = '{pincode}', contact_name = '{contact_name}',
                        contact_phone = '{contact_phone}', contact_email = '{contact_email}', catagory = '{catagory}'
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
                                                remarks, work_status, enable_credit, added_by, created_time)
                    VALUES ('{work_id}', '{acc_id}', '{work_name}', '{contact_id}', '{billing_date}', '{camc_warranty_start_date}',
                            '{camc_warranty_end_date}', '{amc_start_date}', '{amc_end_date}', '{cost}', '{location}',
                            '{remarks}', '{work_status}', '{enable_credit}', '{username}', '{to_day}')"""
        db.execute(query)

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
        work_name = request.form.get('work_name')
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
                        work_status = '{work_status}',
                        enable_credit = '{enable_credit}'
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
    leads_df = db.get_row_as_dframe("SELECT * FROM crm.leads_master")
    leads = leads_df.to_dict(orient='records')
    return render_template("leads.html", leads=leads)


@app.route("/insert_leads", methods=["GET", "POST"])
@login_required
def insert_leads():
    username = session.get('username')
    to_day = datetime.datetime.now().strftime("%d-%b-%Y %H:%M:%S")
    if request.method == "POST":
        # Retrieve lead information from the form
        lead_name = request.form.get("lead_name")
        street = request.form.get("street")
        city = request.form.get("city")
        state = request.form.get("state")
        country = request.form.get("country")
        pincode = request.form.get("pincode")
        c_name = request.form.get("c_name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        scheduled_time = request.form.get("scheduled_time")
        remarks = request.form.get("remarks")
        source = request.form.get("source")

        if is_duplicate('leads', phone, email):
            return "Error: The phone number or email already exists in the database."

        user_query = f"""select ext_col_1 from crm.user_details where user_name = '{username}' ;"""
        user_data = db.get_data_in_list_of_tuple(user_query)[0][0]

        lead_id = get_latest_id(leads=True)

        # Insert lead data into the database
        query = f""" INSERT INTO crm.leads_master (lead_id, lead_name, street, city, state, country, pincode, contact_name,
        contact_phone, contact_email, scheduled_time, remarks, status, source, owner, added_by, created_time)
        VALUES ('{lead_id}','{lead_name}','{street}','{city}','{state}','{country}','{pincode}','{c_name}','{phone}','{email}','{str(scheduled_time).replace("T"," ")}','{remarks}','OPEN','{source}','{user_data}','{user_data}','{to_day}') ;"""
        # VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) ;"""
        # values = (lead_id, lead_name, street, city, state, country, pincode, c_name, phone, email, str(scheduled_time).replace("T", " "), remarks, 'NEW', source, user_data, user_data, to_day)
        logger.info(query)
        db.execute(query)

        # Redirect to the page displaying all leads or a success page
        return redirect(url_for("all_leads"))

    # If it's a GET request, render the form
    return render_template("insert_leads.html")


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
        owner = request.form.get('owner')
        status = request.form.get("status")
        remarks = request.form.get("remarks")
        gst_no = request.form.get('gst')


        user_query = f"""select ext_col_1 from crm.user_details where user_name = '{username}' ;"""
        user_data = db.get_data_in_list_of_tuple(user_query)[0][0]

        # Update lead data in the database
        query = """UPDATE crm.leads_master
        SET contact_name = %s, contact_phone = %s, contact_email = %s,
        scheduled_time = %s, status = %s, remarks = %s, owner = %s, updated_by = %s, updated_time = %s
        WHERE lead_id = %s """
        values = (c_name, phone, email, str(scheduled_time.replace("T", " ")), status, remarks, owner, user_data, to_day, str(lead_id))
        db.execute(query, values)

        l_query = f"SELECT lead_name, street, city, state, country, pincode, contact_name, contact_phone, contact_email FROM crm.leads_master WHERE lead_id = '{str(lead_id)}' ;"
        l_data = db.get_data_in_list_of_tuple(l_query)

        if status == "DONE":
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
                return 'Please retry' 

        # Redirect to the page displaying all leads or a success page
        return redirect(url_for("all_leads"))

    # If it's a GET request, retrieve the current lead data and render the form
    lead_query = f"SELECT * FROM crm.leads_master WHERE lead_id = '{str(lead_id)}' ;"
    logger.info(lead_query)
    lead_data_df = db.get_row_as_dframe(lead_query)
    lead_data = lead_data_df.to_dict(orient='records')
    return render_template("edit_leads.html", lead=lead_data[0])



if __name__ == "__main__":
    app.run(host='192.168.0.16', port=5020, debug=True)


