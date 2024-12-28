from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import db_connect as db  
from datetime import datetime, timedelta
import mail
import send_wp


def strftime_filter(date, format='%d-%m-%Y %H:%M:%S'):
    if not date:
        return None
    return date.strftime(format)


app = Flask(__name__)
app.secret_key = "1234567890"
app.jinja_env.filters['strftime'] = strftime_filter


def login_required(route_function):
    @wraps(route_function)
    def decorated_function(*args, **kwargs):
        if 'username' not in session:
            return redirect(url_for('login'))
        return route_function(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['POST', 'GET'])
def login():
    # session
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # query = f"""select * from tms.login_details where (username = '{username}' or phone = '{username}' or email = '{username}') and password = '{password}' and ext_col_2 = 'ACTIVE' ;"""
        query = f""" select ud.user_id , ud."name" ,ud.username ,ud."password" ,uac.profile ,ud.team,
        ud.mobile,ud.email from ums.user_app_connect uac left join ums.user_details ud on uac.user_id = ud.user_id
        where (ud.mobile = '{username}' or ud.email = '{username}' or
        ud.username = '{username}') and ud."password" = '{password}' and ud.status = 'ACTIVE'
        and uac.app_id = 'A-6' and uac.ext_col_1 = 'ACTIVE'; """
        user_data = db.get_data_in_list_of_tuple(query)
        if user_data and user_data[0]:
            session['username'] = user_data[0][2]
            session['profile'] = user_data[0][4]
            session['team'] = user_data[0][5]
            session['name'] = user_data[0][1]
            session['email'] = user_data[0][7]
            session['mobile'] = user_data[0][6]
            flash("Login successful", "success")
            return redirect(url_for('main'))
        else:
            flash("Invalid username or password", "error")
    return render_template('login.html')


@app.route('/no_login', methods=['POST', 'GET'])
def no_login():
    if request.method == 'GET':
        username = request.args.get('username')
        password = request.args.get('password')
        t_id = request.args.get('t_id')
        s_id = request.args.get('s_id')

        if username and password:
            query = f""" select ud.user_id , ud."name" ,ud.username ,ud."password" ,uac.profile ,ud.team,
            ud.mobile,ud.email from ums.user_app_connect uac left join ums.user_details ud on uac.user_id = ud.user_id
            where (ud.mobile = '{username}' or ud.email = '{username}' or
            ud.username = '{username}') and ud."password" = '{password}' and ud.status = 'ACTIVE'
            and uac.app_id = 'A-6' and uac.ext_col_1 = 'ACTIVE'; """
            user_data = db.get_data_in_list_of_tuple(query)
            if user_data and user_data[0]:
                session['username'] = user_data[0][2]
                session['profile'] = user_data[0][4]
                session['team'] = user_data[0][5]
                session['name'] = user_data[0][1]
                session['email'] = user_data[0][7]
                session['mobile'] = user_data[0][6]
                flash("Login successful", "success")
                return redirect(url_for('update', t_id=t_id, s_id=s_id))
            else:
                flash("Invalid username or password", "error")
                return render_template('login.html')
        else:
            return render_template('login.html')
    else:
        return render_template('login.html')



@app.route('/main')
@login_required
def main():
    query = f"""SELECT * FROM tms.task_assign where assign_to ilike '%{session['name']}' and status <> 'Done' ; """
    tasks = db.get_data_in_list_of_tuple(query)
    return render_template('main.html', user=session['name'], tasks=tasks)



@app.route('/insert_task', methods=['POST', 'GET'])
@login_required
def insert_task():
    if request.method == 'POST':
        t_name = request.form['t_name']
        s_id = 'S001'
        assign_id = request.form['assign_to']
        # assign_details = db.get_data_in_list_of_tuple(f"""select * from tms.login_details ld where id = {assign_id};""")
        assign_details = db.get_data_in_list_of_tuple(f"""select name,email,mobile from ums.user_details ud where user_id  = '{assign_id}';""")
        assign_to = assign_details[0][0]
        assign_email = assign_details[0][1]
        assign_mobile = assign_details[0][2]
        priority = request.form['priority']
        assign_by = session['name']
        assign_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        remark = request.form['remark']
        task_type = request.form['type']
        assign_id_name = str(assign_id) + '-' + str(assign_to)
        if task_type == 'task':
            ex_end_dt = datetime.strptime(request.form['ex_end_dt'], '%Y-%m-%dT%H:%M')
            
            latest_t_id_tuple = db.get_data_in_list_of_tuple("SELECT t_id FROM tms.task_assign ORDER BY id DESC LIMIT 1;")
            if latest_t_id_tuple:
                latest_t_id = latest_t_id_tuple[0][0]
                next_number = int(latest_t_id.split('-')[1]) + 1
                next_t_id = f"T-{next_number:04d}"
            else:
                next_t_id = 'T-0001'
            inserted_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            inserted_by = session.get('username')
            insert_query = f"""
            INSERT INTO tms.task_assign (t_id, t_name, s_id, start_dt, ex_end_dt, assign_to,
            priority, assign_by, assign_dt, remark,inserted_dt, inserted_by)
            VALUES ('{next_t_id}', '{t_name}', '{s_id}', now(),'{ex_end_dt}', '{assign_id_name}', 
            '{priority}', '{assign_by}', '{assign_dt}', '{remark}', '{inserted_dt}','{inserted_by}' );"""
            # print(insert_query)
            body_1 = ' Please check it by login in to our portal.'
            sub = 'New Task Assign'
            to_add = [assign_email]
            to_cc = []

        elif task_type == "kra":
            kra_type = request.form['kra_type']
            frequency = request.form['frequency']
            kra_exp_tat = request.form['kra_exp_tat']
            recurring = request.form['recurring'] if request.form['recurring'] else 0
            # add ex_end_dt for KRA tasks is start date(frequency + TAT)
            pass
            latest_t_id_tuple = db.get_data_in_list_of_tuple("SELECT task_id FROM tms.kra_tasks ORDER BY id DESC LIMIT 1;")
            if latest_t_id_tuple:
                latest_t_id = latest_t_id_tuple[0][0]
                next_number = int(latest_t_id.split('-')[1]) + 1
                next_t_id = f"KRA-{next_number:04d}"
            else:
                next_t_id = 'KRA-0001'

            inserted_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            inserted_by = session.get('username') 
            insert_query = f"""
            INSERT INTO tms.kra_tasks (task_id, task_name, frequency, end_dt_freq, assign_to,
            priority, assigned_by, created_date, remarks,start_date, type, status, ext_col_1, recurring)
            VALUES ('{next_t_id}', '{t_name}', '{frequency}', '{kra_exp_tat}', '{assign_id_name}', 
            '{priority}', '{assign_by}', '{assign_dt}', '{remark}', '{inserted_dt}','{kra_type}',
            'ACTIVE', 'Not Assigned', {recurring});"""
            # print(insert_query)
            body_1 = ''
            sub = 'New KRA Task Assign'
            to_add = [assign_email]
            to_cc = []

        success = db.execute(insert_query)
        if success:
            body = f"""
            Hello {assign_to},
            
            A new {task_type} has been assigned to you.{body_1}
            ID : {next_t_id},
            Task: {t_name},
            Priority: {priority},
            Remarks: {remark}
            
            Thanks,
            Task Management System
            """
            mail.send_mail(to_add=to_add, to_cc=to_cc, sub=sub, body=body)
            send_wp.send_wp_msg(mob=assign_mobile,msg=body)
            flash("Task inserted successfully", "success")
        else:
            flash("Failed to insert the task", "error")

    # user_query = """ select user_id , name from ums.user_app_connect where app_id = 'A-6' """
    user_query = """ select uac.user_id , uac.name from ums.user_app_connect uac 
    left join ums.user_details ud on uac.user_id = ud.user_id where uac.app_id = 'A-6' """
    if session['profile'] == 'USER':
        user_query += f""" and ud.team = '{session['team']}' ;"""
        user_data = db.get_data_in_list_of_tuple(user_query)
        user_dict = {i[0]: i[1] for i in user_data}
        # names = [i[0] for i in user_data]
    if session['profile'] == 'SUPER ADMIN':
        user_data = db.get_data_in_list_of_tuple(user_query)
        # names = [i[0] for i in user_data]
        user_dict = {i[0]: i[1] for i in user_data}
    if session['profile'] == 'ADMIN':
        user_query += f""" and uac.profile in ('ADMIN','USER') ;"""
        user_data = db.get_data_in_list_of_tuple(user_query)
        # names = [i[0] for i in user_data]
        user_dict = {i[0]: i[1] for i in user_data}

    return render_template('insert_task.html', user_dict = user_dict)


@app.route('/all_tasks', methods=['GET'])
@login_required
def all_tasks():
    query = f"SELECT * FROM tms.task_assign where assign_to ilike '%{session['name']}' ;"
    if session['profile'] == 'SUPER ADMIN':
        query = f"SELECT * FROM tms.task_assign ;"
    tasks = db.get_data_in_list_of_tuple(query)
    return render_template('all_tasks.html', username=session['username'], tasks=tasks)


@app.route('/insert_step/<t_id>', methods=['GET', 'POST'])
@login_required
def insert_step(t_id):
    next_s_id = None

    # Fetch task details to inherit column values
    task_query = f"""SELECT t_name, assign_by, assign_dt, remark, status FROM tms.task_assign WHERE t_id = '{t_id}';"""
    task_data = db.get_data_in_list_of_tuple(task_query)

    if task_data:
        t_name, assign_by, assign_dt, remark, status = task_data[0]
    else:
        t_name = assign_by = assign_dt = remark = status = ""
    # print(task_data)
    if request.method == 'POST':
        print('Post request for step')
        s_name = request.form['s_name']
        assign_id = request.form['assign_to']
        assign_details = db.get_data_in_list_of_tuple(f"""select name from ums.user_details ud where user_id  = '{assign_id}';""")
        assign_to = assign_details[0][0]
        assign_id_name = str(assign_id) + '-' + str(assign_to)
        start_dt = datetime.strptime(request.form['start_dt'], '%Y-%m-%dT%H:%M')
        ex_end_dt = datetime.strptime(request.form['ex_end_dt'], '%Y-%m-%dT%H:%M')

        # time_difference = ex_end_dt - start_dt
        # days, seconds = divmod(time_difference.total_seconds(), 24 * 3600)
        # hours, seconds = divmod(seconds, 3600)
        # minutes = seconds // 60
        # formatted_tat = f"{int(days)} days {int(hours)} hrs {int(minutes)}"
        latest_s_id_tuple = db.get_data_in_list_of_tuple(
            f"""SELECT s_id FROM tms.task_assign WHERE t_id = '{t_id}'  ORDER BY s_id DESC LIMIT 1;"""
        )
        if latest_s_id_tuple:
            latest_s_id = latest_s_id_tuple[0][0]
            prefix = latest_s_id[0]
            number = int(latest_s_id[1:])
            next_number = number + 1
            next_s_id = f"{prefix}{next_number:03d}"
        else:
            next_s_id = 'S001'
        insert_query = f"""
        INSERT INTO tms.task_assign (t_id, s_id, t_name, s_name, assign_to, assign_by, start_dt, ex_end_dt, assign_dt, remark, status)
            VALUES ('{t_id}', '{next_s_id}', '{t_name}', '{s_name}', '{assign_id_name}', '{assign_by}', '{start_dt}', '{ex_end_dt}', '{assign_dt}', '{remark}', '{status}');"""
        try:
            print(insert_query)
            success = db.execute(insert_query)
            if success:
                flash("Task inserted successfully", "success")
            else:
                flash("Failed to insert the task", "error")
        except Exception as e:
            flash(f"An error occurred: {str(e)}", "error")
    task_query = f"SELECT t_name, s_id, s_name FROM tms.task_assign WHERE t_id = '{t_id}';"
    task_data = db.get_data_in_list_of_tuple(task_query)
    if task_data:
        t_name, s_id, s_name = task_data[0]
    tasks = db.get_data_in_list_of_tuple(
        f"""SELECT * FROM tms.task_assign WHERE t_id = '{t_id}' AND s_id = '{next_s_id}' ORDER BY t_id DESC LIMIT 1;"""
    )
    user_query = """ select uac.user_id , uac.name from ums.user_app_connect uac 
    left join ums.user_details ud on uac.user_id = ud.user_id where uac.app_id = 'A-6' """
    if session['profile'] == 'USER':
        user_query += f""" and ud.team = '{session['team']}' ;"""
        user_data = db.get_data_in_list_of_tuple(user_query)
        user_dict = {i[0]: i[1] for i in user_data}
        # names = [i[0] for i in user_data]
    if session['profile'] == 'SUPER ADMIN':
        user_data = db.get_data_in_list_of_tuple(user_query)
        # names = [i[0] for i in user_data]
        user_dict = {i[0]: i[1] for i in user_data}
    if session['profile'] == 'ADMIN':
        user_query += f""" and uac.profile in ('ADMIN','USER') ;"""
        user_data = db.get_data_in_list_of_tuple(user_query)
        # names = [i[0] for i in user_data]
        user_dict = {i[0]: i[1] for i in user_data}

    return render_template('insert_step.html', t_id=t_id, t_name=t_name, s_id=s_id, s_name=s_name, tasks=tasks, user_dict=user_dict)


@app.route('/get_step_names/<t_id>')
def get_step_names(t_id):
    step_query = f"""SELECT DISTINCT s_name FROM tms.task_assign WHERE t_id = '{t_id}';"""
    step_names = db.get_data_in_list_of_tuple(step_query)
    return jsonify({'step_names': [step[0] for step in step_names]})


@app.route('/update/<t_id>/<s_id>', methods=['GET', 'POST'])
@login_required
def update(t_id, s_id):

    task_query = f"SELECT t_name, s_name, start_dt, ex_end_dt, assign_to, assign_by,assign_dt, status, remark FROM tms.task_assign WHERE t_id = '{t_id}' AND s_id = '{s_id}';"
    task_data = db.get_data_in_list_of_tuple(task_query)
    # print(task_data)
    if task_data:
        t_name, s_name, start_dt, ex_end_dt, assign_to, assign_by,assign_dt, status, remark = task_data[0]
        get_email_mob_query = f"""select email , mobile  from ums.user_details ud where name = '{assign_by}';"""
        get_email_mob_data = db.get_data_in_list_of_tuple(get_email_mob_query)
        try:
            a_email = get_email_mob_data[0][0]
            a_mob = get_email_mob_data[0][1]
        except:
            a_mob = a_email = []

    formatted_tat = ""
    if request.method == 'POST':
        remark = request.form['remark']
        status = request.form['status']
        act_end_dt = str(datetime.now().strftime('%Y-%m-%d %H:%M:%S')) if status == 'Done' else ''
        updated_by = session.get('name') 

        update_query = f"""UPDATE tms.task_assign
                        SET remark = '{remark}', status = '{status}', updated_dt = now(), updated_by = '{updated_by}' """

        if status == 'Done':
            act_end_dt = datetime.strptime(str(act_end_dt).split('.')[0], '%Y-%m-%d %H:%M:%S')
            start_dt = datetime.strptime(str(start_dt).split('.')[0], '%Y-%m-%d %H:%M:%S')
            time_difference = act_end_dt - start_dt
            days, seconds = divmod(time_difference.total_seconds(), 24 * 3600)
            hours, seconds = divmod(seconds, 3600)
            minutes = seconds // 60
            formatted_tat = f"{int(days)} days {int(hours)} hrs {int(minutes)} min"
            update_query += f""", act_end_dt = '{act_end_dt}', tat = '{formatted_tat}' """
            
        update_query += f""" WHERE t_id = '{t_id}' AND s_id = '{s_id}'; """
        # print(update_query)
        success = db.execute(update_query)
        if success:
            flash("Task updated successfully", "success")
            if status == 'Done':
                sub = f'Task Completed Task:{t_id}'
                body = f"""Hello {session['name']},\n\n\n
                You have marked the below task completed.\n
                Task ID: {t_id}\nTask Name: {t_name}\nSub-task ID: {s_id}\nStatus: {status}\nRemarks: {remark}\n\n
                Thanks,\nTask Management System"""

                if a_email:
                    to_add = [a_email]
                    to_cc = []
                    mail.send_mail(to_add=to_add, to_cc=to_cc, sub=sub, body=body)
                if a_mob:
                    send_wp.send_wp_msg(mob=a_mob, msg=body)

                body_2 = f"""Hello Ashish,\n\n\n
                {session['name']} has marked the below task completed.\n
                Task ID: {t_id}\nTask Name: {t_name}\nSub-task ID: {s_id}\nStatus: {status}\nRemarks: {remark}\n\n
                Thanks,\nTask Management System"""
                send_wp.send_wp_msg(mob='9988880885', msg=body_2)
            

        else:
            flash("Failed to update the task", "error")
        return redirect(url_for('main'))
    return render_template('update.html', t_id=t_id, t_name=t_name, s_name=s_name, start_dt=start_dt,
                           ex_end_dt=ex_end_dt, s_id=s_id, assign_to=assign_to, assign_by=assign_by,
                           assign_dt=assign_dt, status=status, remark=remark)


@app.route('/all_kra', methods=['GET'])
@login_required
def all_kra():
    query = """select task_id ,task_name ,assign_to ,frequency ,end_dt_freq ,type, 
    created_date ,priority ,status ,remarks  from tms.kra_tasks ;"""
    tasks = db.get_data_in_list_of_tuple(query)
    return render_template('all_kra.html', username=session['username'], tasks=tasks)


@app.route('/update_kra/<id>', methods=['POST','GET'])
@login_required
def update_kra(id):
    if request.method == 'POST':
        priority = request.form['priority']
        type = request.form['type']
        frequency = request.form['freq']
        end_dt_freq = request.form['end_dt_freq']
        remark = request.form['remark']
        status = request.form['status']

        insert_query = f"""UPDATE tms.kra_tasks SET frequency = '{frequency}', end_dt_freq = '{end_dt_freq}', type = '{type}',
                        priority = '{priority}', status = '{status}', remarks = '{remark}' WHERE task_id = '{id}';"""
        db.execute(insert_query)

    query = f"""select task_id ,task_name ,assign_to ,frequency ,end_dt_freq ,type, 
    created_date ,priority ,status ,remarks  from tms.kra_tasks where task_id = '{id}';"""
    tasks = db.get_data_in_list_of_tuple(query)[0]
    return render_template('update_kra.html', username=session['username'], task=tasks)

# For Task Time log =================================================================
@app.route('/get_task_data/<t_id>')
def get_task_data(t_id):
    task_query = f"""SELECT t_name FROM tms.task_assign WHERE t_id = '{t_id}';"""
    task_data = db.get_data_in_list_of_tuple(task_query)
    if task_data:
        t_name = task_data[0]
        return jsonify({'task_name': t_name})
    return jsonify({'task_name': ''})


# @app.route('/task_time_log', methods=['POST', 'GET'])
# @login_required
# def task_time_log():
#     t_name = None
#     t_id_query = "SELECT DISTINCT t_id FROM tms.task_assign;"
#     t_ids = db.get_data_in_list_of_tuple(t_id_query)
#     if request.method == 'POST':
#         t_id = request.form['t_id']
#         s_name = request.form['s_name']
#         stage = request.form['stage']
#         what_you_did = request.form['what_you_did']
#         start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
#         end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
#         try:
#             time_spent = end_time - start_time
#             days, seconds = divmod(time_spent.total_seconds(), 24 * 3600)
#             hours, seconds = divmod(seconds, 3600)
#             minutes = seconds // 60
#             formatted_time_spent = f"{int(days)} days {int(hours)} hrs {int(minutes)} min"
#         except ValueError:
#             flash("Invalid time spent input. Please enter a valid number.", "error")
#             return redirect(url_for('main', t_id=t_id))
#         task_query = f"""SELECT t_name FROM tms.task_assign WHERE t_id = '{t_id}';"""
#         task_data = db.get_data_in_list_of_tuple(task_query)
#         if task_data:
#             t_name = task_data[0][0]
#         else:
#             t_name = ""

#         insert_query = f"""
#              INSERT INTO tms.task_time_log (t_id, t_name, s_name, start_time, end_time, time_spent, what_you_did, stage)
#              VALUES ('{t_id}', '{t_name}', '{s_name}', '{start_time}', '{end_time}', '{formatted_time_spent}', '{what_you_did}', '{stage}');"""
#         success = db.execute(insert_query)
#         if success:
#             flash(f"You have spent {time_spent} hours on task {t_id}. Time log added to the database.", "success")
#         else:
#             flash("Failed to log time in the database. Please try again.", "error")
#     return render_template('task_time_log.html', t_name=t_name, t_ids=t_ids)


# @app.route('/all_time_logs', methods=['GET'])
# @login_required
# def all_time_logs():
#     query = "SELECT * FROM tms.task_time_log;"
#     time_logs = db.get_data_in_list_of_tuple(query)
#     return render_template('all_time_logs.html', time_logs=time_logs)

# # =================================================================

@app.route('/insert_multiple_tasks', methods=['GET', 'POST'])
@login_required
def insert_multiple_tasks():
    if request.method == 'POST':
        num_tasks = int(request.form['num_tasks'])
        # ex_end_dt = datetime.strptime(request.form['ex_end_dt'], '%Y-%m-%dT%H:%M')
        assign_by = session['name']
        assign_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        inserted_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        inserted_by = session.get('username')
        s_id = 'S001'

        tasks = []
        tasks_by_assignee = {}
        for i in range(num_tasks):
            t_name = request.form.getlist('t_name[]')[i]
            ex_end_dt = datetime.strptime(request.form.getlist('ex_end_dt[]')[i], '%Y-%m-%dT%H:%M')
            assign_id = request.form.getlist('assign_to[]')[i]
            # 'assign_to': request.form.getlist('assign_to[]')[i]
            priority = request.form.getlist('priority[]')[i]
            remark = request.form.getlist('remark[]')[i]
            # assign_details = db.get_data_in_list_of_tuple(f"""select * from tms.login_details ld where id = {assign_id};""")
            assign_details = db.get_data_in_list_of_tuple(f"""select name,email,mobile from ums.user_details ud where user_id  = '{assign_id}';""")
            assign_to = assign_details[0][0]
            assign_email = assign_details[0][1]
            assign_mobile = assign_details[0][2]
            assign_id_name = str(assign_id) + '-' + str(assign_to)
            task_data = {
                't_name': t_name,
                'ex_end_dt': ex_end_dt,
                'assign_id': assign_id,
                'assign_to': assign_id_name,
                'assign_email': assign_email,
                'assign_mobile': assign_mobile,
                'priority': priority,
                'remark': remark,
            }
            assignee_key = assign_id
            if assignee_key not in tasks_by_assignee:
                tasks_by_assignee[assignee_key] = []
            
            tasks_by_assignee[assignee_key].append(task_data)
            tasks.append(task_data)
        print(tasks_by_assignee)
        # print('==========================================')
        for j in tasks:
            latest_t_id_tuple = db.get_data_in_list_of_tuple("SELECT t_id FROM tms.task_assign ORDER BY t_id DESC LIMIT 1;")
            if latest_t_id_tuple:
                latest_t_id = latest_t_id_tuple[0][0]
                next_number = int(latest_t_id.split('-')[1]) + 1
                next_t_id = f"T-{next_number:04d}"
            else:
                next_t_id = 'T-0001'
            insert_query = f"""
            INSERT INTO tms.task_assign (t_id, t_name, s_id, start_dt, ex_end_dt, assign_to,
            priority, assign_by, assign_dt, remark,inserted_dt, inserted_by)
            VALUES ('{next_t_id}', '{j['t_name']}', '{s_id}', now(),'{j['ex_end_dt']}', '{j['assign_to']}', 
            '{j['priority']}', '{assign_by}', '{assign_dt}', '{j['remark']}', '{inserted_dt}','{inserted_by}' );"""
            # print(insert_query)
            db.execute(insert_query)

        # Mail Logic ================================
        for assignee_key, assignee_tasks in tasks_by_assignee.items():
            combined_body = ""
            for task in assignee_tasks:
                combined_body += f"""
                Task: {task['t_name']},
                Priority: {task['priority']}\n
                """
            sub = 'New Task Assign (Please ignore, it is Testing)'
            body = f"""
            Hello {assignee_tasks[0]['assign_to']},
            
            New tasks/KRAs have been assigned to you. Please check them below:
            {combined_body}
            
            Thanks,
            Task Management System
            """

            to_add = [assignee_tasks[0]['assign_email']]
            to_cc = []
            mail.send_mail(to_add=to_add, to_cc=to_cc, sub=sub, body=body)
        # WP Logic ================================
            send_wp.send_wp_msg(mob=assign_mobile,msg=body)
        # return jsonify(tasks_by_assignee)
        return redirect(url_for('main'))

    # user_query = """ select id, ext_col_1 from tms.login_details """
    # if session['profile'] == 'user':
    #     user_query += f""" where teams = '{session['team']}' ;"""
    #     user_data = db.get_data_in_list_of_tuple(user_query)
    #     user_dict = {i[0]: i[1] for i in user_data}
    #     # names = [i[0] for i in user_data]
    # if session['profile'] == 'SUPER ADMIN':
    #     user_data = db.get_data_in_list_of_tuple(user_query)
    #     # names = [i[0] for i in user_data]
    #     user_dict = {i[0]: i[1] for i in user_data}
    # if session['profile'] in ('ADMIN'):
    #     user_query += f""" where teams = '{session['team']}' or profile = 'ADMIN' ;"""
    #     user_data = db.get_data_in_list_of_tuple(user_query)
    #     # names = [i[0] for i in user_data]
    #     user_dict = {i[0]: i[1] for i in user_data}
    user_query = """ select uac.user_id , uac.name from ums.user_app_connect uac 
    left join ums.user_details ud on uac.user_id = ud.user_id where uac.app_id = 'A-6' """
    if session['profile'] == 'USER':
        user_query += f""" and ud.team = '{session['team']}' ;"""
        user_data = db.get_data_in_list_of_tuple(user_query)
        user_dict = {i[0]: i[1] for i in user_data}
        # names = [i[0] for i in user_data]
    if session['profile'] == 'SUPER ADMIN':
        user_data = db.get_data_in_list_of_tuple(user_query)
        # names = [i[0] for i in user_data]
        user_dict = {i[0]: i[1] for i in user_data}
    if session['profile'] in ('ADMIN'):
        user_query += f""" and uac.profile in ('ADMIN','USER') ;"""
        user_data = db.get_data_in_list_of_tuple(user_query)
        # names = [i[0] for i in user_data]
        user_dict = {i[0]: i[1] for i in user_data}


    return render_template('insert_multiple_tasks.html', user_dict=user_dict)


if __name__ == '__main__':
    # app.run(host='192.168.0.3', port='5191', debug=True)
    # app.run(host='0.0.0.0', port='5001', debug=True)
    app.run(host='192.168.0.16', port=5023, debug=True)
