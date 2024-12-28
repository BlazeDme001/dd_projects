import main_tenders
import schedule
import time
import os


def all_main():
        bot_list = ['ManipurTenders_GOV_NICGEP_BOT','MeghTenders_GOV_NICGEP_BOT_main',
                    'MizoramTenders_GOV_NICGEP_BOT_main','Mptenders_GOV_BOT_main',
                    'NagalandTenders_GOV_NICGEP_BOT_main','Pmgsytenders_GOV_Nicgep_BOT_main',
                    'PuducherryTenders_GOV_NICGEP_BOT_main','PBTenders_GOV_NICGEP_BOT_main',
                    'SikkimTenders_GOV_NICGEP_BOT_main','Tendersodisha_GOV_BOT_main']
        for bot in bot_list:
            try:
                key_list = ['camera', 'CCTV', 'LAN', 'network', 'surveillance', 'switch', 'Unmanned Aerial Vehicle', 'UAV', 'Drone']
                for key_word in key_list:
                    print(key_word)
                    if bot == 'ManipurTenders_GOV_NICGEP_BOT':
                        main_tenders.ManipurTenders_GOV_NICGEP_BOT(key_word)
                    elif bot == 'MeghTenders_GOV_NICGEP_BOT_main':
                        main_tenders.MeghTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'MizoramTenders_GOV_NICGEP_BOT_main':
                        main_tenders.MizoramTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'Mptenders_GOV_BOT_main':
                        main_tenders.Mptenders_GOV_BOT_main(key_word)
                    elif bot == 'NagalandTenders_GOV_NICGEP_BOT_main':
                        main_tenders.NagalandTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'Pmgsytenders_GOV_Nicgep_BOT_main':
                        main_tenders.Pmgsytenders_GOV_Nicgep_BOT_main(key_word)
                    elif bot == 'PuducherryTenders_GOV_NICGEP_BOT_main':
                        main_tenders.PuducherryTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'PBTenders_GOV_NICGEP_BOT_main':
                        main_tenders.PBTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'SikkimTenders_GOV_NICGEP_BOT_main':
                        main_tenders.SikkimTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'Tendersodisha_GOV_BOT_main':
                        main_tenders.Tendersodisha_GOV_BOT_main(key_word)
            except Exception as err:
                print(str(err))


def job():
    all_main()
    print('BOT executed at 7:00 AM')



if __name__ == '__main__':
    schedule.every().day.at('07:00').do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
