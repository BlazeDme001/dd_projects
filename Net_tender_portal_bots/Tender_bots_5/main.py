import main_tenders
import schedule
import time
import os


def all_main():
        bot_list = ['Tntenders_GOV_NIC_BOT_main','TripuraTenders_GOV_NICGEP_BOT_main',
                    'UKtenders_GOV_NICGEP_BOT_main','WBtenders_GOV_NICGEP_BOT_main']
        for bot in bot_list:
            try:
                key_list = ['camera', 'CCTV', 'LAN', 'network', 'surveillance', 'switch', 'Unmanned Aerial Vehicle', 'UAV', 'Drone']
                for key_word in key_list:
                    print(key_word)
                    if bot == 'Tntenders_GOV_NIC_BOT_main':
                        main_tenders.Tntenders_GOV_NIC_BOT_main(key_word)
                    elif bot == 'TripuraTenders_GOV_NICGEP_BOT_main':
                        main_tenders.TripuraTenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'UKtenders_GOV_NICGEP_BOT_main':
                        main_tenders.UKtenders_GOV_NICGEP_BOT_main(key_word)
                    elif bot == 'WBtenders_GOV_NICGEP_BOT_main':
                        main_tenders.WBtenders_GOV_NICGEP_BOT_main(key_word)

            except Exception as err:
                print(str(err))


def job():
    all_main()
    print('BOT executed at 10:30 AM')



if __name__ == '__main__':
    schedule.every().day.at('10:30').do(job)

    while True:
        schedule.run_pending()
        time.sleep(1)
