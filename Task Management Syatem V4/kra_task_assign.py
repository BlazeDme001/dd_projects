import db_connect as db
import time
from datetime import datetime, timedelta
import mail
import schedule
import send_wp

def task_assign(task):
        t_name = task['task_name']
        s_id = 'S001'
        assign_id = 'U-'+task['assign_to'].split('-')[1]
        # assign_details = db.get_data_in_list_of_tuple(f"""select * from tms.login_details ld where id = {assign_id.split('-')[0]};""")
        assign_details = db.get_data_in_list_of_tuple(f"""select name,email,mobile from ums.user_details ud where user_id  = '{assign_id}';""")
        assign_to = assign_details[0][6]
        assign_email = assign_details[0][8]
        assign_mobile = assign_details[0][9]
        priority = task['priority']
        assign_by = task['assigned_by']
        remark = task['remarks']
        frequency = task['frequency']
        # frequency = '1'
        end_dt_freq = task['end_dt_freq']
        type = task['type']

        assign_dt,ex_end_dt = '',''

        if type == 'daily':
            assign_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ex_end_dt = (datetime.now()+timedelta(days=int(end_dt_freq))).strftime('%Y-%m-%d %H:%M:%S')
        elif type == 'weekly':
            current_day_of_week = (datetime.now().weekday() + 1) % 7
            if current_day_of_week == int(frequency):
                assign_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ex_end_dt = (datetime.now()+timedelta(days=int(end_dt_freq))).strftime('%Y-%m-%d %H:%M:%S')
        elif type == 'monthly':
            if datetime.now().month in (4,6,9,11):
                frequency = frequency if frequency != '30' else '29'
            elif datetime.now().month in (2):
                year = datetime.now().year
                if (year%4==0 and year%100!=0) or (year%400==0):
                    frequency = '28' if frequency in ('29','30') else frequency
                else:
                    frequency = '27' if frequency in ('28','29','30') else frequency
            if datetime.now().day == int(frequency):
                assign_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ex_end_dt = (datetime.now()+timedelta(days=int(end_dt_freq))).strftime('%Y-%m-%d %H:%M:%S')
        elif type == 'yearly':
            if datetime.now().month == int(frequency) and datetime.now().day == 1:
                assign_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ex_end_dt = (datetime.now()+timedelta(days=int(end_dt_freq))).strftime('%Y-%m-%d %H:%M:%S')
        elif type == 'quarterly':
            current_month = datetime.now().month
            current_quarter = (current_month - 1) // 3 + 1
            if current_quarter in [1, 2, 3, 4] and datetime.now().month == int(frequency) and datetime.now().day == 1:
                assign_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ex_end_dt = (datetime.now() + timedelta(days=int(end_dt_freq))).strftime('%Y-%m-%d %H:%M:%S')
        elif type == 'halfyearly':
            current_month = datetime.now().month
            current_half_year = (current_month - 1) // 6 + 1
            if current_half_year in [1, 2] and datetime.now().month == int(frequency) and datetime.now().day == 1:
                assign_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                ex_end_dt = (datetime.now() + timedelta(days=int(end_dt_freq))).strftime('%Y-%m-%d %H:%M:%S')

        if not assign_dt and not ex_end_dt:
            print('Empty dates')
            return None
        latest_t_id_tuple = db.get_data_in_list_of_tuple("SELECT t_id FROM tms.task_assign ORDER BY id DESC LIMIT 1;")
        if latest_t_id_tuple:
            latest_t_id = latest_t_id_tuple[0][0]
            next_number = int(latest_t_id.split('-')[1]) + 1
            next_t_id = f"T-{next_number:04d}"
        else:
            next_t_id = 'T-0001'
        inserted_dt = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        inserted_by = 'KRA Task BOT'
        insert_query = f""" INSERT INTO tms.task_assign (t_id, t_name, s_id, start_dt,
        ex_end_dt, assign_to, priority, assign_by, assign_dt, remark, inserted_dt, inserted_by)
        VALUES ('{next_t_id}', '{t_name}', '{s_id}', now(),'{ex_end_dt}', '{task['assign_to']}', 
        '{priority}', '{assign_by}', '{assign_dt}', '{remark}', '{inserted_dt}','{inserted_by}');"""
        success = db.execute(insert_query)

        update_kra_query = f""" UPDATE tms.kra_tasks SET current_recurring=(current_recurring+1) WHERE task_id='{next_t_id}' """
        db.execute(update_kra_query)

        if success:
            sub = 'New Task Assign'
            to_add = [assign_email]
            to_cc = ['ashish@shreenathgroup.in']
            body = f"""
            Hello {assign_email},
            
            A new task/KRA has been assigned to you. Please check it by login into our portal.
            ID : {next_t_id},
            Task: {t_name},
            Priority: {priority}
            
            Thanks,
            Task Management System
            """
            mail.send_mail(to_add=to_add, to_cc=to_cc, sub=sub, body=body)
            send_wp.send_wp_msg(mob=assign_mobile, msg=body)

def main():
    query = """ select * from tms.kra_tasks where status = 'ACTIVE' and ext_col_1 = 'Not Assigned' and 
    (recurring = 0 or recurring <> current_recurring) ; """
    kra_data = db.get_row_as_dframe(query)
    if not kra_data.empty:
        for _, task in kra_data.iterrows():
            print(task)
            task_assign(task)


def job():
    main()


schedule.every().day.at("06:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)