import time
import schedule
import update_main

def main():
    bot_list = ['AndamanTenders GOV NICGEP BOT', 'APTenders NICGEP BOT', 'Assam GOV NICGEP BOT',
                'Centerl GOV BOT', 'CHDTenders GOV NICGEP BOT', 'Coalindiatenders NIC Nicgep BOT',
                'Cpcletenders NIC Nicgep BOT', 'DadrahaveliTenders GOV NICGEP BOT', 'Defproc Nicgep BOT',
                'DelhiTenders GOV NICGEP BOT', 'Eproc Rajasthan GOV BOT', 'Eprocure Epublish BOT',
                'Eprocurebel Nicgep BOT', 'Eprocuregrse Nicgep BOT', 'Eprocuregsl Nic Nicgep BOT',
                'Eprocurehsl Nicgep BOT', 'Eprocuremdl Nic Nicgep BOT', 'Eprocurentpc Nic Nicgep BOT',
                'Etenders GOV BOT', 'Etenders UP NIC BOT']

    for bot in bot_list:
        # print(bot)
        if bot == 'AndamanTenders GOV NICGEP BOT':
            update_main.AndamanTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'APTenders NICGEP BOT':
            update_main.APTenders_NICGEP_BOT_main(bot)
        elif bot == 'Assam GOV NICGEP BOT':
            update_main.Assam_GOV_NICGEP_BOT_main(bot)
        elif bot == 'Centerl GOV BOT':
            update_main.Centerl_GOV_BOT_main(bot)
        elif bot == 'CHDTenders GOV NICGEP BOT':
            update_main.CHDTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'Coalindiatenders NIC Nicgep BOT':
            update_main.Coalindiatenders_NIC_Nicgep_BOT_main(bot)
        elif bot == 'Cpcletenders NIC Nicgep BOT':
            update_main.Cpcletenders_NIC_Nicgep_BOT_main(bot)
        elif bot == 'DadrahaveliTenders GOV NICGEP BOT':
            update_main.DadrahaveliTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'Defproc Nicgep BOT':
            update_main.Defproc_Nicgep_BOT_main(bot)
        elif bot == 'DelhiTenders GOV NICGEP BOT':
            update_main.DelhiTenders_GOV_NICGEP_BOT_main(bot)
        elif bot == 'Eproc Rajasthan GOV BOT':
            update_main.Eproc_Rajasthan_GOV_BOT_main(bot)
        elif bot == 'Eprocure Epublish BOT':
            update_main.Eprocure_Epublish_BOT_main(bot)
        elif bot == 'Eprocurebel Nicgep BOT':
            update_main.Eprocurebel_Nicgep_BOT_main(bot)
        elif bot == 'Eprocuregrse Nicgep BOT':
            update_main.Eprocuregrse_Nicgep_BOT_main(bot)
        elif bot == 'Eprocuregsl Nic Nicgep BOT':
            update_main.Eprocuregsl_Nic_Nicgep_BOT_main(bot)
        elif bot == 'Eprocurehsl Nicgep BOT':
            update_main.Eprocurehsl_Nicgep_BOT_main(bot)
        elif bot == 'Eprocuremdl Nic Nicgep BOT':
            update_main.Eprocuremdl_Nic_Nicgep_BOT_main(bot)
        elif bot == 'Eprocurentpc Nic Nicgep BOT':
            update_main.Eprocurentpc_Nic_Nicgep_BOT_main(bot)
        elif bot == 'Etenders GOV BOT':
            update_main.Etenders_GOV_BOT_main(bot)
        elif bot == 'Etenders UP NIC BOT':
            update_main.Etenders_UP_NIC_BOT_main(bot)


def job():
    try:
        main()
    except:
        pass
    print('BOT executed at 11:45 PM')


if __name__ == '__main__':
    schedule.every().day.at('23:45').do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)

