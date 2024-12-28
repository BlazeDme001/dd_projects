import requests
import json

def recharge(ca_no, ref_no, payment_type, amt, to_acc, uti):
    url = "https://emsprepaidapi.neptuneenergia.com/service.asmx/liveEmsTransaction"

    # ca_no = '7'
    # ref_no = '888339'
    # payment_type = 'CASH'
    # amt = '100'
    # to_acc = 'BANK'
    # uti = '1123'

    # data = "{CA_no:'7',Reference_No:'888339', Payment_Mode:'CASH',TRN_Amt:100,To_Account:'BANK',Unique_Transaction_Id:'1111234'}"
    data = f"CA_no:'{ca_no}',Reference_No:'{ref_no}', Payment_Mode:'{payment_type}',TRN_Amt:{amt},To_Account:'{to_acc}',Unique_Transaction_Id:'{uti}'"

    payload = json.dumps({
      "TXN_NAME": "RECHARGE",
      "DATA": '{'+data+'}',
      "username": "Admin",
      "password": "NIRWANA#4321#ADMIN",
      "SITECODE": "160"
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload, timeout=60)

    return response.status_code, json.loads(response.text.split('}{"d":')[0]+'}')


def get_master_data():
    url = "https://emsprepaidapi.neptuneenergia.com/service.asmx/liveEmsTransaction"

    payload = json.dumps({
      "TXN_NAME": "MASTERDATA",
      "DATA": "",
      "username": "Admin",
      "password": "NIRWANA#4321#ADMIN",
      "SITECODE": "160"
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    # print(response.text)
    # json.loads(response.text)
    return response.status_code, json.loads(response.text.split('}{"d":')[0]+'}')


def get_daily_reading(date):
    url = "https://emsprepaidapi.neptuneenergia.com/service.asmx/liveEmsTransaction"
    DATA ="{Date:"+date+"}"
    payload = json.dumps({
      "TXN_NAME": "DAILYCONSUMPTION",
      "DATA": DATA,
      "username": "Admin",
      "password": "NIRWANA#4321#ADMIN",
      "SITECODE": "160"
    })
    headers = {
      'Content-Type': 'application/json'
    }

    response = requests.request("POST", url, headers=headers, data=payload)

    return response.status_code, json.loads(response.text.split('}{"d":')[0]+'}')