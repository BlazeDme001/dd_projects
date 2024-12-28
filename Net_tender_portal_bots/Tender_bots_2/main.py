import main_tenders
import schedule
import time
import os


def all_main():
        bot_list = ['Eproc_Rajasthan_GOV_BOT_main','Eprocure_Epublish_BOT_main',
                    'Eprocurebel_Nicgep_BOT_main','Eprocuregrse_Nicgep_BOT_main',
                    'Eprocuregsl_Nic_Nicgep_BOT_main','Eprocurehsl_Nicgep_BOT_main',
                    'Eprocuremdl_Nic_Nicgep_BOT_main','Eprocurentpc_Nic_Nicgep_BOT_main',
                    'Etenders_GOV_BOT_main','Etenders_UP_NIC_BOT_main']
        for bot in bot_list:
            try:
                key_list = ['camera', 'CCTV', 'LAN', 'network', 'surveillance', 'switch', 'Unmanned Aerial Vehicle', 'UAV', 'Drone']
                for key_word in key_list:
                    print(key_word)
                    if bot == 'Eproc_Rajasthan_GOV_BOT_main':
                        main_tenders.Eproc_Rajasthan_GOV_BOT_main(key_word)
                    elif bot == 'Eprocure_Epublish_BOT_main':
                        main_tenders.Eprocure_Epublish_BOT_main(key_word)
                    elif bot == 'Eprocurebel_Nicgep_BOT_main':
                        main_tenders.Eprocurebel_Nicgep_BOT_main(key_word)
                    elif bot == 'Eprocuregrse_Nicgep_BOT_main':
                        main_tenders.Eprocuregrse_Nicgep_BOT_main(key_word)
                    elif bot == 'Eprocuregsl_Nic_Nicgep_BOT_main':
                        main_tenders.Eprocuregsl_Nic_Nicgep_BOT_main(key_word)
                    elif bot == 'Eprocurehsl_Nicgep_BOT_main':
                        main_tenders.Eprocurehsl_Nicgep_BOT_main(key_word)
                    elif bot == 'Eprocuremdl_Nic_Nicgep_BOT_main':
                        main_tenders.Eprocuremdl_Nic_Nicgep_BOT_main(key_word)
                    elif bot == 'Eprocurentpc_Nic_Nicgep_BOT_main':
                        main_tenders.Eprocurentpc_Nic_Nicgep_BOT_main(key_word)
                    elif bot == 'Etenders_GOV_BOT_main':
                        main_tenders.Etenders_GOV_BOT_main(key_word)
                    elif bot == 'Etenders_UP_NIC_BOT_main':
                        main_tenders.Etenders_UP_NIC_BOT_main(key_word)
            except Exception as err:
                print(str(err))

# all_main()

def job():
    all_main()
    print('BOT executed at 1:00 AM')



if __name__ == '__main__':
    schedule.every().day.at('01:00').do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
