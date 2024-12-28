import main_tenders
import schedule
import time
import os


def all_main():
        bot_list = ['GoaTenders_GOV_NICGEP_BOT_main','HPtenders_GOV_NICGEP_BOT_main',
                    'HRYtenders_GOV_NICGEP_BOT_main','Iocletenders_NIC_Nicgep_BOT_main',
                    'J_KTenders_GOV_NICGEP_BOT_main','JKDTenders_GOV_NICGEP_BOT_main',
                    'KeralaTenders_GOV_NICGEP_BOT_main','LEHTenders_GOV_NICGEPBOT_main',
                    'LKDPTenders_GOV_NICGEP_BOT_main','Mahatenders_GOV_BOT_main']
        for bot in bot_list:
            try:
                key_list = ['camera', 'CCTV', 'LAN', 'network', 'surveillance', 'switch', 'Unmanned Aerial Vehicle', 'UAV', 'Drone']
                for key_word in key_list:
                    print(key_word)
                    if bot == 'GoaTenders_GOV_NICGEP_BOT_main':
                        main_tenders.GoaTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'HPtenders_GOV_NICGEP_BOT_main':
                        main_tenders.HPtenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'HRYtenders_GOV_NICGEP_BOT_main':
                        main_tenders.HRYtenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'Iocletenders_NIC_Nicgep_BOT_main':
                        main_tenders.Iocletenders_NIC_Nicgep_BOT_main(key_word)
                    elif bot == 'J_KTenders_GOV_NICGEP_BOT_main':
                        main_tenders.J_KTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'JKDTenders_GOV_NICGEP_BOT_main':
                        main_tenders.JKDTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'KeralaTenders_GOV_NICGEP_BOT_main':
                        main_tenders.KeralaTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'LEHTenders_GOV_NICGEPBOT_main':
                        main_tenders.LEHTenders_GOV_NICGEPBOT_main(key_word)
                    elif bot == 'LKDPTenders_GOV_NICGEP_BOT_main':
                        main_tenders.LKDPTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'Mahatenders_GOV_BOT_main':
                        main_tenders.Mahatenders_GOV_BOT_main(key_word)
            except Exception as err:
                print(str(err))

# all_main()

def job():
    all_main()
    print('BOT executed at 4:00 AM')



if __name__ == '__main__':
    schedule.every().day.at('04:00').do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
