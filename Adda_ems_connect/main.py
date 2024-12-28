from flask import Flask, request, Response
from collections import OrderedDict
import json
# import db_connect as db
import ems_api_calls as eac
from datetime import datetime, timedelta 

app = Flask(__name__)

@app.route('/UpdateMeter', methods=['POST'])
def UpdateMeter():
    try:
        data = request.get_json()

        site_id = data.get('SiteID')
        vendor_id = data.get('VendorID')
        password = data.get('Password')
        meter_id = data.get('MeterID')
        amount = data.get('Amount', '0')
        txn_id = data.get('TxnID')
        recharge_type = data.get('RechargeType')
        transaction_type = data.get('TransactionType')
        
        # site_id= "12345"
        # vendor_id= "ADDA01"
        # password= "1234"
        # meter_id= 888339
        # amount= 5.00
        # txn_id = "TCA009387711"
        # recharge_type = "M"
        # transaction_type = "C"

        if vendor_id == 'ADDA01' and password == '1234':
            if not site_id:
                raise Exception('Site ID is not present')
            if not meter_id:
                raise Exception('Meter ID is not present')
            if not txn_id:
                raise Exception('TXN ID is not present')

            # ============================================
            # EMPS Operation to be done here
            try:
                master_data = eac.get_master_data()
                ca_no = ''
                if master_data[0] == 200 and master_data[1]['Status'] == 'Success':
                    for i in master_data[1]['data']:
                        # print(i)
                        if str(i['DEVICE_SLNO']) == str(meter_id):
                            ca_no = str(i['ca_no'])
                            break
                print(ca_no)
                data = eac.recharge(ca_no=ca_no, ref_no=meter_id, payment_type=transaction_type, amt=amount,to_acc='BANK',uti=txn_id)
                if data[0] != 200:
                    raise Exception('Bad request')
            except:
                raise Exception('No Data Found')
            # ============================================
        else:
            raise Exception('Authentication failure')

        response = OrderedDict([
            ("SiteID", site_id),
            ("MeterID", meter_id),
            ("Amount", amount),
            ("TxnID", txn_id),
            ("Status", "Success"),
            ("Message", str(data[1]))
        ])
        response_json = json.dumps(response)
        return Response(response=response_json, status=200, mimetype='application/json')

    except Exception as err:
        error_response = json.dumps({"error": str(err)})
        return Response(response=error_response, status=400, mimetype='application/json')


@app.route('/GetMeterUsage', methods=['POST'])
def GetMeterUsage():
    try:
        data = request.get_json()

        site_id = data.get('SiteID','')
        meter_id = data.get('MeterID','')

        if not site_id:
            raise Exception('Site ID is not present')

        # =====================================
        # EMPS Meter Usage
        # query = f""" select usage from meter_table where site_id = '{site_id}' """
        # if meter_id:
        #     query += f""" and meter_id = '{meter_id}' """
        # usage_data = db.get_row_as_dframe(query)
        usage_data = ''
        data = ''
        usage = ''
        data = eac.get_daily_reading(date=(datetime.today() - timedelta(days=1)).strftime("%Y%m%d"))
        if data[0] == 200 and data[1]['Status'] == 'Success':
            usage_data = data[1]['data']
            if meter_id:
                for i in usage_data:
                    print(i)
                    if str(i['DEVICE_SLNO']) == meter_id:
                        usage = i['EB_PV_READING']
                        data = i
                        break
            else:
                data = usage_data
        # =====================================

        if usage_data:
            response = OrderedDict([
                ("SiteID", site_id),
                # ("MeterID", meter_id),
                ("Usage", usage),
                ("data", data)
            ])
            response_json = json.dumps(response)
            return Response(response=response_json, status=200, mimetype='application/json')
        else:
            raise Exception('Meter usage data not found')

    except Exception as err:
        error_response = json.dumps({"error": str(err)})
        return Response(response=error_response, status=400, mimetype='application/json')




if __name__ == '__main__':
    # app.run(debug=True)
    app.run(host='192.168.0.16', port=5031, debug=True)
