import pandas as pd
import db_connect as db


df = pd.read_csv('df.csv')

df_1 = df[str(df['Meter Serial No']) != '']

no = df['Meter Serial No'].astype('int').astype('str').tolist()
# no = df['Flat No'].astype('int').astype('str').tolist()

df['PHONE'] = df['PHONE'].astype('str')
df['EMAIL'] = df['EMAIL'].astype('str')

for _, row in df.iterrows():
    dev_no = int(row['Meter Serial No'])
    email = str(row['EMAIL']) if (row['EMAIL'] and row['EMAIL'] != 'nan') else '' 
    mobile = str(int(row['PHONE'].replace('.0', ''))) if (row['PHONE'] and row['PHONE'] != 'nan')  else ''

    print(dev_no,'-', email, '-', mobile)

# s_query = f""" select * from meter_api.meter_user_details where DEVICE_SLNO = '{int(row['Flat No'])}' """
# s_query = f""" select * from meter_api.meter_user_details where DEVICE_SLNO in {tuple(no)} """

# s_rec = db.get_data_in_list_of_tuple(s_query)

    update_query = f""" UPDATE meter_api.meter_user_details SET mobile = '{mobile}', 
        email = '{email}' WHERE DEVICE_SLNO = '{dev_no}'; """
    db.execute(update_query)