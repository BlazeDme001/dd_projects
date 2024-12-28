import pandas as pd
import db_connect as db
import mail
import send_wp
import schedule
import time
# import pdfkit
# from reportlab.lib import colors
# from reportlab.lib.pagesizes import letter
# from reportlab.platypus import SimpleDocTemplate, Table, TableStyle




# def generate_pdf_from_dataframe(df, pdf_file_path):
#     # Convert DataFrame to a list of lists (data for the table)
#     data = [df.columns.tolist()] + df.values.tolist()

#     # Create a PDF document with US Letter size
#     doc = SimpleDocTemplate(pdf_file_path, pagesize=letter)
    
#     # Calculate the number of columns
#     num_cols = len(data[0])
    
#     # Calculate the column width based on US Letter size and number of columns
#     col_width = letter[0] / num_cols
    
#     # Create a table from the data with fixed column width
#     table = Table(data, colWidths=[col_width] * num_cols)
    
#     # Style the table
#     style = TableStyle([('BACKGROUND', (0, 0), (-1, 0), colors.grey),
#                         ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
#                         ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
#                         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
#                         ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
#                         ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
#                         ('GRID', (0, 0), (-1, -1), 1, colors.black)])
    
#     table.setStyle(style)
    
#     # Allow content to wrap within cells
#     table.setStyle(TableStyle([('WORDWRAP', (0, 0), (-1, -1), 'TRUE')]))
    
#     # Add table to the PDF document
#     doc.build([table])



def main():
    query = f""" select t_id , t_name , s_id , to_char(start_dt, 'YYYY-MM-DD HH12:MI AM') as start_dt,
    to_char(ex_end_dt, 'YYYY-MM-DD HH12:MI AM') as ex_end_dt ,left(assign_to,3) as assign_to,remark ,status,
    priority from tms.task_assign where status not in ('Done', 'Hold') ; """
    data = db.get_row_as_dframe(query)
    
    assign_to_values = data['assign_to'].unique()
    data_frames = {}
    for assign_to_value in assign_to_values:
        data_frames[assign_to_value] = data[data['assign_to'] == assign_to_value]
    
        
    for user_id in data_frames:
        print(user_id)
        
        user_query = f""" select name, mobile , email  from ums.user_details ud where user_id = '{user_id}'; """
        user_data =  db.get_data_in_list_of_tuple(user_query)

        body = f"""Hello {user_data[0][0]},\nPlease complete the following task,\n\n"""
        
        for t_data in data_frames[user_id].iterrows():
            print(t_data)
            body += f""" Task ID: {t_data[1][0]}\nTask Name: {t_data[1][1]}\nStart Date: {t_data[1][3]}\nExpected End Date: {t_data[1][4]}\nStatus: {t_data[1][7]}\nPriority: {t_data[1][8]}\n
            ----------------------------\n\n
            """

        body += "Thanks and regards,\nTask Auto Mailler BOT"

        html_table = data_frames[user_id].to_html(index=False)
        # pdf_file_path = f"{user_id}_task_list.pdf"
        # pdfkit.from_string(html_table, pdf_file_path)
        # generate_pdf_from_dataframe(data_frames[user_id],pdf_file_path)
        print(body)            

        try:
            mail.send_mail(to_add=[user_data[0][2]], to_cc=[], sub='Testing mail', body=body)
            send_wp.send_wp_msg(user_data[0][1],body)
        except:
            print("Error in sending mail")
            

def job():
    main()

schedule.every().day.at("08:30").do(job)
schedule.every().day.at("14:30").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)
