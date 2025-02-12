import main_tenders
import schedule
import time
import os


def all_main():
        bot_list = ['andamantenders_nicgep_tenders_main','aptenders_nicgep_tenders_main',
                    'assamtenders_gov_tenders_main','Centerl_GOV_BOT_main',
                    'CHDTenders_GOV_NICGEP_BOT_main','Coalindiatenders_NIC_Nicgep_BOT_main',
                    'Cpcletenders_NIC_Nicgep_BOT_main','DadrahaveliTenders_GOV_NICGEP_BOT_main',
                    'Defproc_Nicgep_BOT_main','DelhiTenders_GOV_NICGEP_BOT_main']
        for bot in bot_list:
            try:
                key_list = ['camera', 'CCTV', 'LAN', 'network', 'surveillance', 'switch', 'Unmanned Aerial Vehicle', 'UAV', 'Drone']
                for key_word in key_list:
                    print(key_word)
                    if bot == 'andamantenders_nicgep_tenders_main':
                        main_tenders.andamantenders_nicgep_tenders_main(key_word)
                    elif bot == 'aptenders_nicgep_tenders_main':
                        main_tenders.aptenders_nicgep_tenders_main(key_word)
                    elif bot == 'assamtenders_gov_tenders_main':
                        main_tenders.assamtenders_gov_tenders_main(key_word)
                    elif bot == 'Centerl_GOV_BOT_main':
                        main_tenders.Centerl_GOV_BOT_main(key_word)
                    elif bot == 'CHDTenders_GOV_NICGEP_BOT_main':
                        main_tenders.CHDTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'Coalindiatenders_NIC_Nicgep_BOT_main':
                        main_tenders.Coalindiatenders_NIC_Nicgep_BOT_main(key_word)
                    elif bot == 'Cpcletenders_NIC_Nicgep_BOT_main':
                        main_tenders.Cpcletenders_NIC_Nicgep_BOT_main(key_word)
                    elif bot == 'DadrahaveliTenders_GOV_NICGEP_BOT_main':
                        main_tenders.DadrahaveliTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'Defproc_Nicgep_BOT_main':
                        main_tenders.Defproc_Nicgep_BOT_main(key_word)
                    elif bot == 'DelhiTenders_GOV_NICGEP_BOT_main':
                        main_tenders.DelhiTenders_GOV_NICGEP_BOT_main(key_word)
            except Exception as err:
                print(str(err))

# all_main()

def job():
    all_main()
    print('BOT executed at 22:00 AM')



if __name__ == '__main__':
    schedule.every().day.at('11:21').do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
